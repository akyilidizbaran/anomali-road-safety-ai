#!/usr/bin/env python3
"""Run DACT-EXP-020B on the three exterior demo videos.

This is a domain-transfer smoke test, not a validation of driver action
accuracy. DACT-EXP-020B was trained on in-cabin State Farm images; the Teknofest
demo videos are road-facing exterior videos. A healthy runtime integration must
therefore treat these scores as diagnostic unless a visibility/temporal gate
confirms that the cabin and driver action are actually observable.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


ROOT = Path(__file__).resolve().parents[2]

EXPERIMENT_ID = "DACT-EXP-020C"
EXPERIMENT_NAME = "external_video_domain_transfer_smoke_v1"
SOURCE_MODEL_EXPERIMENT_ID = "DACT-EXP-020B"

DEFAULT_CHECKPOINT = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin_driver"
    / "DACT-EXP-020B"
    / "DACT-EXP-020B-efficientnet_b0-best.pth"
)
DEFAULT_LABEL_MAP = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin_driver"
    / "DACT-EXP-020B"
    / "DACT-EXP-020B-label-map.json"
)
DEFAULT_EVENTS = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-driver-detection.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "driver_action" / f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"
DEFAULT_ARTIFACT_DIR = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "cabin_driver"
    / f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"
)
DEFAULT_REPORT = ROOT / "testing" / "reports" / "dact_exp_020c_external_video_smoke.md"

FALLBACK_LABELS = [
    "safe_or_no_event",
    "telefonla_konusma",
    "phone_use_non_call",
    "su_icme",
    "arkaya_bakma_candidate",
    "passenger_interaction_candidate",
    "other_distraction_hard_negative",
]

FTR_CANDIDATE_LABELS = {
    "telefonla_konusma",
    "su_icme",
    "arkaya_bakma_candidate",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run DACT-EXP-020B driver-action classifier on exterior demo videos "
            "for domain-transfer smoke testing."
        )
    )
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--label-map", type=Path, default=DEFAULT_LABEL_MAP)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--sample-every", type=int, default=10)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["full_frame", "target_vehicle", "cabin_candidate"],
        choices=["full_frame", "target_vehicle", "cabin_candidate"],
    )
    parser.add_argument(
        "--render-mode",
        default="cabin_candidate",
        choices=["full_frame", "target_vehicle", "cabin_candidate", "all", "none"],
        help="Which mode to render into annotated MP4 outputs.",
    )
    parser.add_argument("--output-width", type=int, default=1280)
    parser.add_argument("--temporal-threshold", type=float, default=0.75)
    parser.add_argument("--min-positive-rate", type=float, default=0.2)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def pick_device(requested: str) -> torch.device:
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "mps":
        return torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def normalize_state_dict_keys(state_dict: dict[str, Any]) -> dict[str, Any]:
    return {
        key.removeprefix("module."): value
        for key, value in state_dict.items()
    }


def build_model(backbone: str, num_classes: int) -> nn.Module:
    if backbone == "efficientnet_b0":
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    if backbone == "mobilenet_v3_large":
        model = models.mobilenet_v3_large(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    raise ValueError(f"Unsupported DACT backbone: {backbone}")


def load_labels(label_map_path: Path, checkpoint: dict[str, Any]) -> list[str]:
    if label_map_path.exists():
        with label_map_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        labels = data.get("labels")
        if labels:
            return list(labels)
    labels = checkpoint.get("labels") or checkpoint.get("classes")
    if labels:
        return list(labels)
    return list(FALLBACK_LABELS)


def load_model(checkpoint_path: Path, label_map_path: Path, device: torch.device) -> tuple[nn.Module, list[str], int, dict[str, Any]]:
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            "DACT checkpoint not found: "
            f"{checkpoint_path}\n"
            "Download/copy the Colab artifact here, or pass --checkpoint. Expected Drive source:\n"
            "/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/cabin_driver/"
            "DACT-EXP-020B/DACT-EXP-020B-efficientnet_b0-best.pth"
        )
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    labels = load_labels(label_map_path, checkpoint)
    backbone = str(checkpoint.get("backbone", "efficientnet_b0"))
    img_size = int(checkpoint.get("img_size", 224))
    state_dict = checkpoint.get("state_dict") or checkpoint.get("model_state_dict") or checkpoint
    model = build_model(backbone, len(labels))
    model.load_state_dict(normalize_state_dict_keys(state_dict), strict=True)
    model.to(device)
    model.eval()
    return model, labels, img_size, checkpoint


def make_transform(img_size: int) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


def load_events(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    events = data.get("events")
    if not isinstance(events, list):
        raise ValueError(f"Could not find events list in {path}")
    return events


def clamp_bbox(bbox: list[float], width: int, height: int) -> tuple[int, int, int, int] | None:
    if len(bbox) != 4:
        return None
    x1, y1, x2, y2 = [float(v) for v in bbox]
    x1 = max(0, min(width - 1, x1))
    y1 = max(0, min(height - 1, y1))
    x2 = max(0, min(width, x2))
    y2 = max(0, min(height, y2))
    if x2 <= x1 + 4 or y2 <= y1 + 4:
        return None
    return int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))


def crop_bbox(frame: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    return frame[y1:y2, x1:x2].copy()


def cabin_candidate_bbox(
    vehicle_bbox: tuple[int, int, int, int],
    frame_width: int,
    frame_height: int,
    view_profile: str | None,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = vehicle_bbox
    w = x2 - x1
    h = y2 - y1

    # Exterior windshield/window candidate. This is intentionally heuristic:
    # it is used for smoke testing domain transfer, not for final action proof.
    top = y1 + 0.08 * h
    bottom = y1 + 0.56 * h
    left = x1 + 0.06 * w
    right = x1 + 0.94 * w

    if view_profile == "front_lhd":
        # Earlier role assignment selected the right-side face in front view.
        left = x1 + 0.40 * w
        right = x1 + 0.96 * w
        bottom = y1 + 0.62 * h
    elif view_profile == "side_driver_window":
        left = x1 + 0.05 * w
        right = x1 + 0.75 * w

    return clamp_bbox([left, top, right, bottom], frame_width, frame_height) or vehicle_bbox


def infer_crop(
    model: nn.Module,
    labels: list[str],
    transform: transforms.Compose,
    device: torch.device,
    crop_bgr: np.ndarray,
) -> dict[str, Any]:
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(crop_rgb)
    tensor = transform(image).unsqueeze(0).to(device)
    with torch.inference_mode():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).detach().cpu().numpy()[0]
    order = np.argsort(probs)[::-1]
    pred_idx = int(order[0])
    return {
        "label": labels[pred_idx],
        "confidence": float(probs[pred_idx]),
        "top3": [
            {"label": labels[int(idx)], "probability": float(probs[int(idx)])}
            for idx in order[:3]
        ],
        "probabilities": {labels[i]: float(probs[i]) for i in range(len(labels))},
    }


def prepare_writer(video_path: Path, frame_width: int, frame_height: int, fps: float, output_width: int, output_path: Path) -> tuple[cv2.VideoWriter, tuple[int, int]]:
    if output_width and output_width < frame_width:
        output_height = int(round(frame_height * output_width / frame_width))
        if output_height % 2:
            output_height += 1
    else:
        output_width = frame_width
        output_height = frame_height
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (output_width, output_height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not create output video: {output_path}")
    return writer, (output_width, output_height)


def render_overlay(
    frame: np.ndarray,
    event: dict[str, Any],
    mode: str,
    mode_bbox: tuple[int, int, int, int] | None,
    prediction: dict[str, Any],
    frame_idx: int,
    timestamp_sec: float,
) -> np.ndarray:
    out = frame.copy()
    target_bbox = clamp_bbox(
        event.get("target_vehicle", {}).get("bbox_xyxy") or [],
        out.shape[1],
        out.shape[0],
    )
    if target_bbox:
        cv2.rectangle(out, target_bbox[:2], target_bbox[2:], (255, 255, 255), 2)
        cv2.putText(
            out,
            "target_vehicle",
            (target_bbox[0] + 8, max(24, target_bbox[1] - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    if mode_bbox:
        cv2.rectangle(out, mode_bbox[:2], mode_bbox[2:], (0, 0, 0), 3)
        cv2.rectangle(out, mode_bbox[:2], mode_bbox[2:], (255, 255, 255), 1)
        cv2.putText(
            out,
            mode,
            (mode_bbox[0] + 8, min(out.shape[0] - 16, mode_bbox[1] + 28)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    panel_w = min(out.shape[1] - 24, 790)
    panel_h = 148
    x0, y0 = 16, 16
    overlay = out.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
    out = cv2.addWeighted(overlay, 0.62, out, 0.38, 0)
    top3 = " | ".join(f"{item['label']} {item['probability']:.2f}" for item in prediction["top3"])
    lines = [
        f"{EXPERIMENT_ID} external video smoke",
        f"video={event['source']['source_video']} mode={mode} frame={frame_idx} t={timestamp_sec:.2f}s",
        f"top1={prediction['label']} conf={prediction['confidence']:.3f}",
        f"top3={top3}",
        "warning: exterior view; no final driver action without temporal/visibility gate",
    ]
    for i, text in enumerate(lines):
        cv2.putText(
            out,
            text,
            (x0 + 14, y0 + 28 + i * 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2 if i == 0 else 1,
            cv2.LINE_AA,
        )
    cv2.rectangle(out, (x0, y0), (x0 + panel_w, y0 + panel_h), (255, 255, 255), 2)
    return out


def mode_crop(
    frame: np.ndarray,
    event: dict[str, Any],
    mode: str,
) -> tuple[np.ndarray, tuple[int, int, int, int] | None]:
    h, w = frame.shape[:2]
    if mode == "full_frame":
        return frame, None
    target_bbox = clamp_bbox(
        event.get("target_vehicle", {}).get("bbox_xyxy") or [],
        w,
        h,
    )
    if target_bbox is None:
        return frame, None
    if mode == "target_vehicle":
        return crop_bbox(frame, target_bbox), target_bbox
    if mode == "cabin_candidate":
        view_profile = (event.get("driver_detection") or {}).get("view_profile")
        cabin_bbox = cabin_candidate_bbox(target_bbox, w, h, view_profile)
        return crop_bbox(frame, cabin_bbox), cabin_bbox
    raise ValueError(mode)


def aggregate_rows(
    event: dict[str, Any],
    mode: str,
    rows: list[dict[str, Any]],
    labels: list[str],
    temporal_threshold: float,
    min_positive_rate: float,
) -> dict[str, Any]:
    if not rows:
        return {
            "video": event["source"]["source_video"],
            "event_id": event["event_id"],
            "mode": mode,
            "status": "no_samples",
            "sample_count": 0,
        }
    counts = Counter(row["pred_label"] for row in rows)
    mean_conf = float(np.mean([row["pred_confidence"] for row in rows]))
    mean_probs = {
        label: float(np.mean([row[f"prob_{label}"] for row in rows]))
        for label in labels
    }
    temporal_vote_label, temporal_vote_count = counts.most_common(1)[0]
    temporal_vote_rate = temporal_vote_count / len(rows)
    positive_candidates = []
    for label in sorted(FTR_CANDIDATE_LABELS):
        positive_count = sum(
            1
            for row in rows
            if row["pred_label"] == label and row["pred_confidence"] >= temporal_threshold
        )
        positive_rate = positive_count / len(rows)
        if positive_rate >= min_positive_rate:
            positive_candidates.append(
                {
                    "label": label,
                    "positive_count": positive_count,
                    "positive_rate": round(positive_rate, 4),
                    "mean_probability": round(mean_probs.get(label, 0.0), 4),
                }
            )
    return {
        "video": event["source"]["source_video"],
        "event_id": event["event_id"],
        "track_id": event.get("target_vehicle", {}).get("track_id"),
        "mode": mode,
        "status": "external_smoke_only",
        "sample_count": len(rows),
        "temporal_vote_label": temporal_vote_label,
        "temporal_vote_rate": round(temporal_vote_rate, 4),
        "mean_top1_confidence": round(mean_conf, 4),
        "mean_probabilities": {k: round(v, 4) for k, v in mean_probs.items()},
        "top1_counts": dict(counts),
        "positive_candidates": positive_candidates,
        "should_emit_driver_action": False,
        "failure_reason": "exterior_view_domain_transfer_test_no_final_action",
        "view_profile": (event.get("driver_detection") or {}).get("view_profile"),
        "driver_detection_confidence": (event.get("driver_detection") or {}).get("confidence"),
    }


def process_event(
    event: dict[str, Any],
    videos_dir: Path,
    model: nn.Module,
    labels: list[str],
    transform: transforms.Compose,
    device: torch.device,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    video_name = event["source"]["source_video"]
    video_path = videos_dir / video_name
    if not video_path.exists():
        raise FileNotFoundError(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    window = event.get("target_vehicle", {}).get("frame_window") or {}
    first_frame = int(window.get("first_frame") or 0)
    last_frame = int(window.get("last_frame") or max(total_frames - 1, 0))
    if args.max_frames > 0:
        last_frame = min(last_frame, first_frame + args.max_frames - 1)

    writers: dict[str, cv2.VideoWriter] = {}
    writer_sizes: dict[str, tuple[int, int]] = {}
    rendered_paths: dict[str, str] = {}
    render_modes = args.modes if args.render_mode == "all" else [args.render_mode]
    for render_mode in render_modes:
        if render_mode == "none":
            continue
        render_path = args.runs_dir / "annotated" / f"{Path(video_name).stem}_{render_mode}_dact020c.mp4"
        writer, size = prepare_writer(video_path, frame_width, frame_height, fps, args.output_width, render_path)
        writers[render_mode] = writer
        writer_sizes[render_mode] = size
        rendered_paths[render_mode] = str(render_path.relative_to(ROOT))

    frame_rows: list[dict[str, Any]] = []
    mode_rows: dict[str, list[dict[str, Any]]] = {mode: [] for mode in args.modes}

    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx < first_frame:
            frame_idx += 1
            continue
        if frame_idx > last_frame:
            break
        if (frame_idx - first_frame) % args.sample_every != 0:
            frame_idx += 1
            continue

        timestamp_sec = frame_idx / fps if fps else 0.0
        predictions_by_mode: dict[str, tuple[dict[str, Any], tuple[int, int, int, int] | None]] = {}
        for mode in args.modes:
            crop, bbox = mode_crop(frame, event, mode)
            prediction = infer_crop(model, labels, transform, device, crop)
            row = {
                "video": video_name,
                "event_id": event["event_id"],
                "track_id": event.get("target_vehicle", {}).get("track_id"),
                "frame_idx": frame_idx,
                "timestamp_sec": round(timestamp_sec, 4),
                "mode": mode,
                "pred_label": prediction["label"],
                "pred_confidence": round(prediction["confidence"], 6),
                "crop_bbox_xyxy": list(bbox) if bbox else None,
            }
            row.update({f"prob_{label}": round(prediction["probabilities"].get(label, 0.0), 6) for label in labels})
            frame_rows.append(row)
            mode_rows[mode].append(row)
            predictions_by_mode[mode] = (prediction, bbox)

        for render_mode, writer in writers.items():
            if render_mode not in predictions_by_mode:
                continue
            prediction, bbox = predictions_by_mode[render_mode]
            rendered = render_overlay(frame, event, render_mode, bbox, prediction, frame_idx, timestamp_sec)
            out_w, out_h = writer_sizes[render_mode]
            if (rendered.shape[1], rendered.shape[0]) != (out_w, out_h):
                rendered = cv2.resize(rendered, (out_w, out_h), interpolation=cv2.INTER_AREA)
            writer.write(rendered)

        frame_idx += 1

    cap.release()
    for writer in writers.values():
        writer.release()

    summaries = [
        aggregate_rows(event, mode, mode_rows[mode], labels, args.temporal_threshold, args.min_positive_rate)
        for mode in args.modes
    ]
    return summaries, frame_rows, rendered_paths


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    summary: dict[str, Any],
    frame_csv: Path,
    summary_json: Path,
    summary_csv: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = summary["mode_summaries"]
    lines = [
        "# DACT-EXP-020C External Video Smoke Test",
        "",
        f"Tarih: {summary['created_at_utc']}",
        "",
        "## Amaç",
        "",
        (
            "DACT-EXP-020B iç-kabin State Farm görüntüleriyle eğitildi. Bu test, "
            "modelin yol dış-kamera videolarında doğrudan sürücü eylemi olarak "
            "kullanılıp kullanılamayacağını kontrol eden domain-transfer smoke testtir."
        ),
        "",
        "## Karar Politikası",
        "",
        "* Bu testte `should_emit_driver_action=false` sabittir.",
        "* Dış kamera görüntüsünde classifier skorları final eylem kararı değildir.",
        "* `telefonla_konusma` ve `su_icme` yalnız driver/cabin görünürlük + temporal gate sonrası event'e taşınabilir.",
        "* `arkaya_bakma_candidate` final `arkaya_bakma` değildir; head/torso yönü gerekir.",
        "",
        "## Genel Karar",
        "",
        f"* Karar: `{summary['overall_decision']}`",
        f"* Gerekçe: {summary['overall_reason']}",
        "",
        "## Özet Tablo",
        "",
        "| Video | Mode | Samples | Temporal vote | Vote rate | Mean conf | Top-1 counts | Positive candidates |",
        "|---|---|---:|---|---:|---:|---|---|",
    ]
    for row in rows:
        candidates = ", ".join(
            f"{item['label']}={item['positive_count']}/{row['sample_count']} ({item['positive_rate']})"
            for item in row.get("positive_candidates", [])
        ) or "-"
        top1_counts_text = ", ".join(
            f"{label}:{count}" for label, count in row.get("top1_counts", {}).items()
        ) or "-"
        lines.append(
            "| {video} | {mode} | {sample_count} | {temporal_vote_label} | {temporal_vote_rate} | "
            "{mean_top1_confidence} | {top1_counts_text} | {candidates} |".format(
                candidates=candidates,
                top1_counts_text=top1_counts_text,
                **row,
            )
        )
    lines.extend(
        [
            "",
            "## Çıktılar",
            "",
            f"* Summary JSON: `{summary_json.relative_to(ROOT)}`",
            f"* Summary CSV: `{summary_csv.relative_to(ROOT)}`",
            f"* Frame CSV: `{frame_csv.relative_to(ROOT)}`",
            "",
            "## Annotated Video Çıktıları",
            "",
        ]
    )
    for video_name, modes in summary.get("rendered_videos", {}).items():
        for mode, path_text in modes.items():
            lines.append(f"* `{video_name}` / `{mode}`: `{path_text}`")
    lines.extend(
        [
            "",
            "## Not",
            "",
            (
                "Bu test, State Farm iç-kabin modelinin dış-kamera verisine doğrudan "
                "transfer edilmesinin risklerini ölçmek içindir. Pozitif candidate "
                "çıksa bile bu aşamada event/evidence JSON'a final driver action "
                "olarak yazılmaz."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    device = pick_device(args.device)
    model, labels, img_size, checkpoint = load_model(args.checkpoint, args.label_map, device)
    transform = make_transform(img_size)
    events = load_events(args.events)

    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    all_summaries: list[dict[str, Any]] = []
    all_frame_rows: list[dict[str, Any]] = []
    rendered: dict[str, dict[str, str]] = {}
    for event in events:
        summaries, frame_rows, rendered_paths = process_event(
            event,
            args.videos_dir,
            model,
            labels,
            transform,
            device,
            args,
        )
        all_summaries.extend(summaries)
        all_frame_rows.extend(frame_rows)
        rendered[event["source"]["source_video"]] = rendered_paths

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "experiment_name": EXPERIMENT_NAME,
        "source_model_experiment_id": SOURCE_MODEL_EXPERIMENT_ID,
        "created_at_utc": now_utc(),
        "checkpoint": str(args.checkpoint.relative_to(ROOT)) if args.checkpoint.is_relative_to(ROOT) else str(args.checkpoint),
        "label_map": str(args.label_map.relative_to(ROOT)) if args.label_map.exists() and args.label_map.is_relative_to(ROOT) else str(args.label_map),
        "backbone": checkpoint.get("backbone", "efficientnet_b0"),
        "img_size": img_size,
        "labels": labels,
        "sample_every": args.sample_every,
        "temporal_threshold": args.temporal_threshold,
        "min_positive_rate": args.min_positive_rate,
        "overall_decision": "do_not_emit_driver_action_from_exterior_smoke",
        "overall_reason": (
            "DACT-EXP-020B State Farm iç-kabin görüntüleriyle eğitildi; test "
            "videoları ise yol/dış-kamera domain'inde. Bu nedenle pozitif "
            "aksiyon skorları cabin/driver visibility ve temporal gate olmadan "
            "final event/evidence kararı olarak yazılmayacak."
        ),
        "domain_policy": {
            "input_domain": "road_facing_exterior_demo_videos",
            "training_domain": "State Farm in-cabin driver images",
            "should_emit_driver_action": False,
            "reason": "domain_transfer_smoke_test_requires_visibility_and_temporal_gate",
        },
        "mode_summaries": all_summaries,
        "rendered_videos": rendered,
    }

    summary_json = args.artifact_dir / "dact_exp_020c_external_video_smoke_summary.json"
    summary_csv = args.artifact_dir / "dact_exp_020c_external_video_smoke_summary.csv"
    frame_csv = args.artifact_dir / "dact_exp_020c_external_video_smoke_frames.csv"
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(summary_csv, all_summaries)
    write_csv(frame_csv, all_frame_rows)
    write_report(args.report, summary, frame_csv, summary_json, summary_csv)

    print("summary:", summary_json)
    print("summary_csv:", summary_csv)
    print("frame_csv:", frame_csv)
    print("report:", args.report)
    if rendered:
        print("rendered:", json.dumps(rendered, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
