#!/usr/bin/env python3
"""Train a small temporal phone-call behavior head from object + arm evidence.

The trainer is intentionally conservative:

* Real training requires reviewed segment labels with at least two classes.
* The optional ``--smoke-pseudo-labels`` mode only verifies the pipeline and writes
  artifacts marked as not baseline-eligible.
* Splits are session-based, never frame-based, to avoid neighboring clips leaking
  between train and validation/test.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import torch


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARM_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json"
)
DEFAULT_PHONE_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-EXP-004-yolo26s_phone_windshield_seed_smoke-summary.json"
)
DEFAULT_LABELS = ROOT / "testing" / "templates" / "manual_phone_call_segments.csv"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_ARTIFACT = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-005-temporal_head_training.json"
)
DEFAULT_MODEL = ROOT / "models" / "checkpoints" / "cabin" / "phone_call_temporal_head_exp005.pt"

EXPERIMENT_ID = "PHONE-CALL-EXP-005"
MODEL_KEY = "phone_call_temporal_head_v1"
CLASS_NAMES = ["neutral", "face_touch_hard_negative", "phone_call"]
CLASS_TO_INDEX = {name: index for index, name in enumerate(CLASS_NAMES)}
POSITIVE_LABELS = {"phone_call", "positive"}
NEGATIVE_LABELS = {"neutral", "face_touch_hard_negative", "negative"}
TRAINABLE_LABELS = set(CLASS_TO_INDEX) | {"positive", "negative"}
FEATURE_NAMES = [
    "evaluable_rate",
    "hand_near_face_rate",
    "hand_near_ear_rate",
    "left_near_ear_rate",
    "right_near_ear_rate",
    "dominant_side_rate",
    "longest_near_ear_seconds",
    "mean_candidate_confidence",
    "complete_arm_rate",
    "optical_flow_point_rate",
    "phone_detected_rate",
    "phone_near_face_rate",
    "max_phone_confidence",
    "mean_phone_confidence",
]


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


@dataclass(frozen=True)
class SegmentLabel:
    video: str
    session_id: str
    split: str
    start_frame: int | None
    end_frame: int | None
    start_seconds: float | None
    end_seconds: float | None
    label: str
    source: str


@dataclass
class WindowSample:
    video: str
    session_id: str
    split: str
    label: str
    class_index: int
    start_frame: int
    end_frame: int
    features: list[float]


def parse_optional_int(value: str | None) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    return int(float(text))


def parse_optional_float(value: str | None) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    return float(text)


def normalize_label(label: str) -> str:
    normalized = str(label or "").strip().lower()
    if normalized == "positive":
        return "phone_call"
    if normalized == "negative":
        return "neutral"
    return normalized


def review_label_status(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    empty_rows = []
    unknown_rows = []
    trainable_rows = []
    unsupported_rows = []
    for row in rows:
        segment_id = str(row.get("segment_id") or row.get("video") or "").strip()
        raw_label = str(
            row.get("final_label")
            or row.get("label")
            or row.get("ground_truth")
            or ""
        ).strip()
        label = normalize_label(raw_label)
        if not label:
            empty_rows.append(segment_id)
        elif label == "unknown":
            unknown_rows.append(segment_id)
        elif label in TRAINABLE_LABELS:
            trainable_rows.append(segment_id)
        else:
            unsupported_rows.append({"segment_id": segment_id, "label": raw_label})
    return {
        "row_count": len(rows),
        "trainable_row_count": len(trainable_rows),
        "empty_label_rows": empty_rows,
        "unknown_label_rows": unknown_rows,
        "unsupported_rows": unsupported_rows,
        "final_label_counts": dict(
            Counter(
                normalize_label(
                    str(
                        row.get("final_label")
                        or row.get("label")
                        or row.get("ground_truth")
                        or ""
                    ).strip()
                )
                or "<empty>"
                for row in rows
            )
        ),
        "split_counts": dict(Counter(str(row.get("split") or "").strip() for row in rows)),
    }


def format_no_labels_error(path: Path, status: dict[str, Any]) -> str:
    empty_preview = ", ".join(status["empty_label_rows"][:8])
    unknown_preview = ", ".join(status["unknown_label_rows"][:8])
    parts = [
        f"No trainable phone-call labels found in {path}.",
        f"Rows: {status['row_count']}; trainable rows: {status['trainable_row_count']}.",
        f"Label counts: {status['final_label_counts']}.",
    ]
    if empty_preview:
        parts.append(f"Fill final_label for these rows first: {empty_preview}.")
    if unknown_preview:
        parts.append(f"Rows marked unknown are skipped: {unknown_preview}.")
    parts.append(
        "Allowed final_label values: phone_call, face_touch_hard_negative, neutral, unknown."
    )
    return "\n".join(parts)


def load_segment_labels(path: Path) -> list[SegmentLabel]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    labels: list[SegmentLabel] = []
    for row in rows:
        video = str(row.get("video") or "").strip()
        raw_label = str(
            row.get("final_label")
            or row.get("label")
            or row.get("ground_truth")
            or ""
        ).strip()
        label = normalize_label(raw_label)
        if not video or label in {"", "unknown"}:
            continue
        if label not in TRAINABLE_LABELS:
            raise ValueError(f"Unsupported phone-call segment label '{raw_label}' for {video}")
        labels.append(
            SegmentLabel(
                video=video,
                session_id=str(row.get("session_id") or video).strip() or video,
                split=str(row.get("split") or "train").strip().lower() or "train",
                start_frame=parse_optional_int(row.get("start_frame")),
                end_frame=parse_optional_int(row.get("end_frame")),
                start_seconds=parse_optional_float(row.get("start_seconds")),
                end_seconds=parse_optional_float(row.get("end_seconds")),
                label=label,
                source=rel(path),
            )
        )
    return labels


def auto_split_review_labels(
    labels: list[SegmentLabel],
) -> tuple[list[SegmentLabel], list[str]]:
    """Convert review-only labels into a deterministic session-level train/val split."""
    warnings: list[str] = []
    if not labels:
        return labels, warnings
    split_set = {label.split for label in labels}
    if "review" not in split_set:
        return labels, warnings
    known_splits = split_set & {"train", "val", "test"}
    if known_splits:
        converted = [
            replace(label, split="train") if label.split == "review" else label
            for label in labels
        ]
        warnings.append("review_split_rows_mapped_to_train")
        return converted, warnings

    sessions = sorted({label.session_id for label in labels})
    val_sessions = {sessions[-1]} if len(sessions) >= 2 else set()
    converted = [
        replace(label, split="val" if label.session_id in val_sessions else "train")
        for label in labels
    ]
    warnings.append(
        "review_split_auto_session_split:"
        f"train={len(set(sessions) - val_sessions)},val={len(val_sessions)}"
    )
    return converted, warnings


def smoke_pseudo_labels(videos: list[str]) -> list[SegmentLabel]:
    labels: list[SegmentLabel] = []
    for video in sorted(videos):
        label = "phone_call" if video == "video_2.mp4" else "neutral"
        split = "val" if video == "video_3.mp4" else "train"
        labels.append(
            SegmentLabel(
                video=video,
                session_id=f"smoke_{Path(video).stem}",
                split=split,
                start_frame=None,
                end_frame=None,
                start_seconds=None,
                end_seconds=None,
                label=label,
                source="smoke_pseudo_labels",
            )
        )
    return labels


def video_fps(videos_dir: Path, video: str) -> float:
    cap = cv2.VideoCapture(str((videos_dir / video).resolve()))
    if not cap.isOpened():
        return 25.0
    try:
        return float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    finally:
        cap.release()


def frame_bounds_for_label(label: SegmentLabel, fps: float, max_frame: int) -> tuple[int, int]:
    start = label.start_frame
    end = label.end_frame
    if start is None and label.start_seconds is not None:
        start = int(round(label.start_seconds * fps)) + 1
    if end is None and label.end_seconds is not None:
        end = int(round(label.end_seconds * fps))
    start = max(1, int(start or 1))
    end = min(max_frame, int(end or max_frame))
    if end < start:
        raise ValueError(f"Invalid segment bounds for {label.video}: {start}>{end}")
    return start, end


def is_candidate_frame(record: dict[str, Any]) -> tuple[bool, str | None, float]:
    if record.get("state") != "hand_near_face":
        return False, None, 0.0
    side_states = record.get("side_states") or {}
    for side in ("left", "right"):
        side_state = side_states.get(side) or {}
        if side_state.get("complete") and side_state.get("near_ear"):
            return True, side, float(record.get("state_confidence") or 0.0)
    return False, None, 0.0


def longest_streak(frames: list[int], max_gap: int = 2) -> int:
    longest = 0
    current = 0
    previous = None
    for frame in sorted(frames):
        if previous is None or frame - previous <= max_gap:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        previous = frame
    return longest


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def window_features(
    arm_records: list[dict[str, Any]],
    phone_records: list[dict[str, Any]],
    fps: float,
) -> list[float]:
    evaluable = [item for item in arm_records if item.get("decision_evaluable")]
    denominator = len(evaluable)
    candidates: list[tuple[int, str, float]] = []
    side_counts: Counter[str] = Counter()
    hand_near_face_count = 0
    complete_arm_count = 0
    optical_flow_points = 0
    for item in evaluable:
        if item.get("state") == "hand_near_face":
            hand_near_face_count += 1
        complete_arm_count += int(item.get("complete_arm_count") or 0)
        optical_flow_points += int(item.get("optical_flow_point_count") or 0)
        is_candidate, side, confidence = is_candidate_frame(item)
        if is_candidate and side is not None:
            frame = int(item.get("frame") or 0)
            candidates.append((frame, side, confidence))
            side_counts[side] += 1

    candidate_frames = sorted({frame for frame, _, _ in candidates})
    left_count = side_counts["left"]
    right_count = side_counts["right"]
    dominant_count = max(left_count, right_count)
    candidate_conf = [confidence for _, _, confidence in candidates]

    phone_evaluable = [item for item in phone_records if item.get("decision_evaluable")]
    phone_positive = [item for item in phone_evaluable if item.get("phone_detected") is True]
    phone_near_face = [item for item in phone_positive if item.get("object_near_face") is True]
    phone_confidences = [float(item.get("phone_confidence") or 0.0) for item in phone_positive]

    return [
        round(safe_div(denominator, len(arm_records)), 6),
        round(safe_div(hand_near_face_count, denominator), 6),
        round(safe_div(len(candidate_frames), denominator), 6),
        round(safe_div(left_count, denominator), 6),
        round(safe_div(right_count, denominator), 6),
        round(safe_div(dominant_count, len(candidates)), 6),
        round(longest_streak(candidate_frames) / max(fps, 1.0), 6),
        round(sum(candidate_conf) / len(candidate_conf), 6) if candidate_conf else 0.0,
        round(safe_div(complete_arm_count, max(1, denominator * 2)), 6),
        round(safe_div(optical_flow_points, max(1, denominator * 6)), 6),
        round(safe_div(len(phone_positive), len(phone_evaluable)), 6),
        round(safe_div(len(phone_near_face), len(phone_positive)), 6),
        round(max(phone_confidences), 6) if phone_confidences else 0.0,
        round(sum(phone_confidences) / len(phone_confidences), 6) if phone_confidences else 0.0,
    ]


def build_samples(
    arm_summary: dict[str, Any],
    phone_summary: dict[str, Any],
    labels: list[SegmentLabel],
    videos_dir: Path,
    window_seconds: float,
    stride_seconds: float,
) -> list[WindowSample]:
    arm_index = {item["video"]: item for item in arm_summary.get("videos", [])}
    phone_index = {item["video"]: item for item in phone_summary.get("videos", [])}
    labels_by_video: dict[str, list[SegmentLabel]] = defaultdict(list)
    for label in labels:
        labels_by_video[label.video].append(label)

    samples: list[WindowSample] = []
    for video, video_labels in labels_by_video.items():
        if video not in arm_index:
            raise ValueError(f"Arm summary missing video {video}")
        arm_records = sorted(
            arm_index[video].get("per_frame") or [],
            key=lambda item: int(item.get("frame") or 0),
        )
        phone_records = sorted(
            (phone_index.get(video) or {}).get("per_frame") or [],
            key=lambda item: int(item.get("frame") or 0),
        )
        phone_by_frame = {int(item.get("frame") or 0): item for item in phone_records}
        if not arm_records:
            continue
        fps = video_fps(videos_dir, video)
        window_frames = max(1, int(round(window_seconds * fps)))
        stride_frames = max(1, int(round(stride_seconds * fps)))
        max_frame = int(arm_records[-1].get("frame") or len(arm_records))
        arm_by_frame = {int(item.get("frame") or 0): item for item in arm_records}
        for label in video_labels:
            start, end = frame_bounds_for_label(label, fps, max_frame)
            class_label = normalize_label(label.label)
            class_index = CLASS_TO_INDEX[class_label]
            cursor = start
            while cursor <= end:
                window_end = min(end, cursor + window_frames - 1)
                selected_frames = range(cursor, window_end + 1)
                window_arm = [arm_by_frame[frame] for frame in selected_frames if frame in arm_by_frame]
                if not window_arm:
                    cursor += stride_frames
                    continue
                window_phone = [
                    phone_by_frame[frame] for frame in selected_frames if frame in phone_by_frame
                ]
                samples.append(
                    WindowSample(
                        video=video,
                        session_id=label.session_id,
                        split=label.split,
                        label=class_label,
                        class_index=class_index,
                        start_frame=cursor,
                        end_frame=window_end,
                        features=window_features(window_arm, window_phone, fps),
                    )
                )
                cursor += stride_frames
    return samples


def validate_samples(samples: list[WindowSample], smoke: bool) -> list[str]:
    warnings: list[str] = []
    if not samples:
        raise ValueError("No trainable phone-call windows were built from labels.")
    class_counts = Counter(sample.label for sample in samples)
    if len(class_counts) < 2:
        raise ValueError(
            "At least two reviewed classes are required for training; "
            f"got {dict(class_counts)}."
        )
    session_splits: dict[str, set[str]] = defaultdict(set)
    for sample in samples:
        session_splits[sample.session_id].add(sample.split)
    leaking = {
        session_id: sorted(splits)
        for session_id, splits in session_splits.items()
        if len(splits) > 1
    }
    if leaking:
        raise ValueError(f"Session split leakage detected: {leaking}")
    if smoke:
        warnings.append("smoke_pseudo_labels_not_for_baseline")
    return warnings


def split_samples(samples: list[WindowSample]) -> tuple[list[WindowSample], list[WindowSample]]:
    train = [sample for sample in samples if sample.split == "train"]
    eval_samples = [sample for sample in samples if sample.split in {"val", "test"}]
    if not train:
        raise ValueError("No train split samples available.")
    if not eval_samples:
        eval_samples = train
    return train, eval_samples


def standardize(
    train: torch.Tensor,
    eval_tensor: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    mean = train.mean(dim=0)
    std = train.std(dim=0)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    return (train - mean) / std, (eval_tensor - mean) / std, mean, std


def train_linear_head(
    samples: list[WindowSample],
    epochs: int,
    lr: float,
    seed: int,
) -> dict[str, Any]:
    torch.manual_seed(seed)
    train_samples, eval_samples = split_samples(samples)
    x_train = torch.tensor([sample.features for sample in train_samples], dtype=torch.float32)
    y_train = torch.tensor([sample.class_index for sample in train_samples], dtype=torch.long)
    x_eval = torch.tensor([sample.features for sample in eval_samples], dtype=torch.float32)
    y_eval = torch.tensor([sample.class_index for sample in eval_samples], dtype=torch.long)
    x_train_scaled, x_eval_scaled, mean, std = standardize(x_train, x_eval)
    model = torch.nn.Linear(len(FEATURE_NAMES), len(CLASS_NAMES))
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    losses: list[float] = []
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(model(x_train_scaled), y_train)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))

    with torch.no_grad():
        logits = model(x_eval_scaled)
        probabilities = torch.softmax(logits, dim=1)
        predictions = probabilities.argmax(dim=1)
    correct = int((predictions == y_eval).sum().item())
    eval_count = int(y_eval.numel())
    confusion: dict[str, dict[str, int]] = {
        actual: {predicted: 0 for predicted in CLASS_NAMES}
        for actual in CLASS_NAMES
    }
    for actual_index, predicted_index in zip(y_eval.tolist(), predictions.tolist(), strict=False):
        confusion[CLASS_NAMES[actual_index]][CLASS_NAMES[predicted_index]] += 1
    return {
        "model": model,
        "feature_mean": mean.tolist(),
        "feature_std": std.tolist(),
        "train_window_count": len(train_samples),
        "eval_window_count": len(eval_samples),
        "train_class_counts": dict(Counter(sample.label for sample in train_samples)),
        "eval_class_counts": dict(Counter(sample.label for sample in eval_samples)),
        "final_train_loss": round(losses[-1], 6) if losses else None,
        "eval_accuracy": round(correct / eval_count, 6) if eval_count else None,
        "confusion": confusion,
    }


def save_model(path: Path, train_result: dict[str, Any], metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "experiment_id": EXPERIMENT_ID,
            "model_key": MODEL_KEY,
            "class_names": CLASS_NAMES,
            "feature_names": FEATURE_NAMES,
            "feature_mean": train_result["feature_mean"],
            "feature_std": train_result["feature_std"],
            "state_dict": train_result["model"].state_dict(),
            "metadata": metadata,
        },
        path,
    )


def build_report_artifact(
    args: argparse.Namespace,
    labels: list[SegmentLabel],
    samples: list[WindowSample],
    train_result: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    label_counts = dict(Counter(label.label for label in labels))
    session_counts = {
        split: len({sample.session_id for sample in samples if sample.split == split})
        for split in sorted({sample.split for sample in samples})
    }
    positive_sessions = {
        sample.session_id for sample in samples if sample.label == "phone_call"
    }
    negative_sessions = {
        sample.session_id
        for sample in samples
        if sample.label in {"neutral", "face_touch_hard_negative"}
    }
    baseline_eligible = bool(
        not args.smoke_pseudo_labels
        and len(positive_sessions) >= args.min_positive_sessions
        and len(negative_sessions) >= args.min_negative_sessions
        and {"train", "val"}.issubset({sample.split for sample in samples})
    )
    baseline_blockers = [
        blocker
        for blocker in [
            "smoke_pseudo_labels_not_allowed" if args.smoke_pseudo_labels else None,
            (
                f"positive_sessions<{args.min_positive_sessions}"
                if len(positive_sessions) < args.min_positive_sessions
                else None
            ),
            (
                f"negative_sessions<{args.min_negative_sessions}"
                if len(negative_sessions) < args.min_negative_sessions
                else None
            ),
            (
                "missing_validation_split"
                if not {"train", "val"}.issubset({sample.split for sample in samples})
                else None
            ),
        ]
        if blocker is not None
    ]
    return {
        "experiment_id": EXPERIMENT_ID,
        "model_key": MODEL_KEY,
        "created_at_utc": now_utc(),
        "training_mode": "smoke_pseudo_labels" if args.smoke_pseudo_labels else "reviewed_segments",
        "baseline_eligible": baseline_eligible,
        "baseline_blockers": [] if baseline_eligible else baseline_blockers,
        "warnings": warnings,
        "inputs": {
            "arm_summary": rel(args.arm_summary),
            "phone_summary": rel(args.phone_summary),
            "segment_labels": rel(args.segment_labels),
            "videos_dir": rel(args.videos_dir),
        },
        "outputs": {
            "model_path": rel(args.model_output),
            "artifact": rel(args.artifact),
        },
        "classes": CLASS_NAMES,
        "feature_names": FEATURE_NAMES,
        "label_counts": label_counts,
        "window_count": len(samples),
        "session_counts_by_split": session_counts,
        "positive_session_count": len(positive_sessions),
        "negative_session_count": len(negative_sessions),
        "window_seconds": args.window_seconds,
        "stride_seconds": args.stride_seconds,
        "epochs": args.epochs,
        "lr": args.lr,
        "seed": args.seed,
        "train": {
            key: value
            for key, value in train_result.items()
            if key not in {"model", "feature_mean", "feature_std"}
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train phone-call temporal behavior head.")
    parser.add_argument("--arm-summary", type=Path, default=DEFAULT_ARM_SUMMARY)
    parser.add_argument("--phone-summary", type=Path, default=DEFAULT_PHONE_SUMMARY)
    parser.add_argument("--segment-labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--model-output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--window-seconds", type=float, default=2.0)
    parser.add_argument("--stride-seconds", type=float, default=0.5)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--lr", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-positive-sessions", type=int, default=3)
    parser.add_argument("--min-negative-sessions", type=int, default=5)
    parser.add_argument("--smoke-pseudo-labels", action="store_true")
    parser.add_argument(
        "--no-auto-split-review",
        action="store_false",
        dest="auto_split_review",
        help="Disable automatic session-level train/val split for rows with split=review.",
    )
    parser.set_defaults(auto_split_review=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    arm_summary = json.loads(args.arm_summary.resolve().read_text(encoding="utf-8"))
    phone_summary = json.loads(args.phone_summary.resolve().read_text(encoding="utf-8"))
    videos = [item["video"] for item in arm_summary.get("videos", [])]
    split_warnings: list[str] = []
    if args.smoke_pseudo_labels:
        labels = smoke_pseudo_labels(videos)
    else:
        labels = load_segment_labels(args.segment_labels)
        if not labels:
            status = review_label_status(args.segment_labels)
            raise SystemExit(format_no_labels_error(args.segment_labels, status))
        if args.auto_split_review:
            labels, split_warnings = auto_split_review_labels(labels)
    samples = build_samples(
        arm_summary,
        phone_summary,
        labels,
        args.videos_dir,
        window_seconds=args.window_seconds,
        stride_seconds=args.stride_seconds,
    )
    warnings = split_warnings + validate_samples(samples, smoke=args.smoke_pseudo_labels)
    train_result = train_linear_head(samples, epochs=args.epochs, lr=args.lr, seed=args.seed)
    artifact = build_report_artifact(args, labels, samples, train_result, warnings)
    save_model(args.model_output, train_result, metadata=artifact)
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.artifact.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
