#!/usr/bin/env python3
"""Run CABIN-EXP-020A cabin-view gate on local demo videos.

This is a smoke test for the cabin/driver visibility gate, not driver action
recognition. The current demo videos are road-facing exterior videos, so a
healthy gate should mostly return `not_cabin_view`.
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
from PIL import Image
from torchvision import models, transforms


DEFAULT_CHECKPOINT = Path(
    "models/checkpoints/cabin_driver/CABIN-EXP-020A/"
    "CABIN-EXP-020A-mobilenet_v3_large-best.pth"
)
DEFAULT_LABEL_MAP = Path(
    "models/checkpoints/cabin_driver/CABIN-EXP-020A/cabin_exp_020a_label_map.json"
)
DEFAULT_VIDEOS_DIR = Path("Test")
DEFAULT_OUTPUT_DIR = Path("runs/cabin/CABIN-EXP-020A-local-video-smoke")
DEFAULT_ARTIFACT_DIR = Path(
    "models/benchmarks/artifacts/cabin_driver/CABIN-EXP-020A-local-video-smoke"
)
DEFAULT_REPORT = Path("testing/reports/cabin_exp_020a_local_video_smoke.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run CABIN-EXP-020A on Test/video_*.mp4 and render overlay outputs."
    )
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--label-map", type=Path, default=DEFAULT_LABEL_MAP)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--sample-every", type=int, default=5)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument(
        "--output-width",
        type=int,
        default=1280,
        help="Resize rendered review videos to this width. Use 0 to keep source size.",
    )
    parser.add_argument("--expected-label", default="not_cabin_view")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    return parser.parse_args()


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


def load_labels(label_map_path: Path, checkpoint: dict[str, Any]) -> list[str]:
    if label_map_path.exists():
        with label_map_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        labels = data.get("labels")
        if labels:
            return list(labels)
    labels = checkpoint.get("labels")
    if not labels:
        raise ValueError("Could not resolve labels from label map or checkpoint.")
    return list(labels)


def build_model(backbone: str, num_classes: int) -> torch.nn.Module:
    if backbone == "mobilenet_v3_large":
        model = models.mobilenet_v3_large(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = torch.nn.Linear(in_features, num_classes)
        return model
    if backbone == "efficientnet_b0":
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = torch.nn.Linear(in_features, num_classes)
        return model
    raise ValueError(f"Unsupported backbone: {backbone}")


def load_model(
    checkpoint_path: Path, label_map_path: Path, device: torch.device
) -> tuple[torch.nn.Module, list[str], int, dict[str, Any]]:
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    labels = load_labels(label_map_path, checkpoint)
    backbone = checkpoint.get("backbone", "mobilenet_v3_large")
    img_size = int(checkpoint.get("img_size", 224))
    model = build_model(backbone, len(labels))
    model.load_state_dict(checkpoint["state_dict"], strict=True)
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


def infer_frame(
    model: torch.nn.Module,
    labels: list[str],
    transform: transforms.Compose,
    device: torch.device,
    frame_bgr: np.ndarray,
) -> dict[str, Any]:
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame_rgb)
    tensor = transform(image).unsqueeze(0).to(device)
    with torch.inference_mode():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).detach().cpu().numpy()[0]
    pred_idx = int(np.argmax(probs))
    return {
        "label": labels[pred_idx],
        "confidence": float(probs[pred_idx]),
        "probabilities": {labels[i]: float(probs[i]) for i in range(len(labels))},
    }


def put_overlay(
    frame: np.ndarray,
    experiment_id: str,
    prediction: dict[str, Any],
    frame_idx: int,
    timestamp_sec: float,
    expected_label: str,
) -> np.ndarray:
    out = frame.copy()
    label = prediction["label"]
    confidence = prediction["confidence"]
    status = "OK" if label == expected_label else "CHECK"
    panel_w = min(out.shape[1] - 24, 640)
    panel_h = 122
    x0, y0 = 16, 16
    overlay = out.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
    out = cv2.addWeighted(overlay, 0.58, out, 0.42, 0)
    lines = [
        f"{experiment_id} cabin-view gate",
        f"pred: {label}  conf: {confidence:.3f}  status: {status}",
        f"frame: {frame_idx}  time: {timestamp_sec:.2f}s",
        "note: road-facing video should be not_cabin_view",
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
    border_color = (255, 255, 255) if status == "OK" else (180, 180, 180)
    cv2.rectangle(out, (x0, y0), (x0 + panel_w, y0 + panel_h), border_color, 2)
    return out


def safe_float(value: float) -> float | None:
    if math.isfinite(value):
        return float(value)
    return None


def process_video(
    video_path: Path,
    model: torch.nn.Module,
    labels: list[str],
    transform: transforms.Compose,
    device: torch.device,
    output_dir: Path,
    sample_every: int,
    max_frames: int,
    output_width: int,
    expected_label: str,
    experiment_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if output_width and output_width < width:
        output_height = int(round(height * output_width / width))
        if output_height % 2:
            output_height += 1
    else:
        output_width = width
        output_height = height
    output_dir.mkdir(parents=True, exist_ok=True)
    output_video = output_dir / f"{video_path.stem}_cabin020a_smoke.mp4"
    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (output_width, output_height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not create output video: {output_video}")

    rows: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    confidence_by_label: defaultdict[str, list[float]] = defaultdict(list)
    last_prediction: dict[str, Any] | None = None
    processed = 0
    sampled = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx = processed
        timestamp_sec = frame_idx / fps if fps else 0.0
        should_sample = frame_idx % sample_every == 0 or last_prediction is None
        if should_sample:
            prediction = infer_frame(model, labels, transform, device, frame)
            last_prediction = prediction
            sampled += 1
            row = {
                "video": video_path.name,
                "frame_idx": frame_idx,
                "timestamp_sec": round(timestamp_sec, 4),
                "pred_label": prediction["label"],
                "pred_confidence": round(prediction["confidence"], 6),
                "expected_label": expected_label,
                "expected_match": prediction["label"] == expected_label,
            }
            for label, prob in prediction["probabilities"].items():
                row[f"prob_{label}"] = round(prob, 6)
            rows.append(row)
            label_counts[prediction["label"]] += 1
            confidence_by_label[prediction["label"]].append(prediction["confidence"])
        assert last_prediction is not None
        annotated = put_overlay(
            frame,
            experiment_id=experiment_id,
            prediction=last_prediction,
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            expected_label=expected_label,
        )
        if (output_width, output_height) != (width, height):
            annotated = cv2.resize(
                annotated,
                (output_width, output_height),
                interpolation=cv2.INTER_AREA,
            )
        writer.write(annotated)
        processed += 1
        if max_frames and processed >= max_frames:
            break

    cap.release()
    writer.release()

    expected_count = label_counts.get(expected_label, 0)
    expected_ratio = expected_count / sampled if sampled else 0.0
    false_positive_count = sampled - expected_count
    false_positive_ratio = false_positive_count / sampled if sampled else 0.0
    max_driver_conf = 0.0
    driver_label = "driver_cabin_visible"
    if rows:
        max_driver_conf = max(float(row.get(f"prob_{driver_label}", 0.0)) for row in rows)

    summary = {
        "video": video_path.name,
        "input_video_uri": str(video_path),
        "output_video_uri": str(output_video),
        "fps": safe_float(fps),
        "resolution": {"width": width, "height": height},
        "output_resolution": {"width": output_width, "height": output_height},
        "total_frames_metadata": total_frames,
        "processed_frames": processed,
        "sampled_frames": sampled,
        "sample_every": sample_every,
        "expected_label": expected_label,
        "expected_label_ratio": round(expected_ratio, 6),
        "non_expected_label_ratio": round(false_positive_ratio, 6),
        "label_counts": dict(label_counts),
        "mean_confidence_by_label": {
            label: round(float(np.mean(values)), 6)
            for label, values in confidence_by_label.items()
            if values
        },
        "max_driver_cabin_visible_probability": round(max_driver_conf, 6),
        "status": "pass" if expected_ratio >= 0.95 else "needs_review",
    }
    return summary, rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    report_path: Path,
    summary: dict[str, Any],
    per_video: list[dict[str, Any]],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CABIN-EXP-020A Local Video Smoke Test",
        "",
        "## Scope",
        "",
        "This smoke test runs the CABIN-EXP-020A cabin/driver visibility gate on the local road-facing demo videos. It does not detect driver actions; it only checks whether the frame should be routed into cabin/driver analysis.",
        "",
        "Expected result for these exterior road videos: `not_cabin_view`.",
        "",
        "## Summary",
        "",
        f"- Experiment: `{summary['experiment_id']}`",
        f"- Checkpoint: `{summary['checkpoint']}`",
        f"- Backbone: `{summary['backbone']}`",
        f"- Device: `{summary['device']}`",
        f"- Sample every: `{summary['sample_every']}` frame(s)",
        f"- Generated at UTC: `{summary['created_at_utc']}`",
        "",
        "| Video | Sampled frames | Expected-label ratio | Non-expected ratio | Max driver-cabin probability | Status | Output video |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for item in per_video:
        lines.append(
            "| {video} | {sampled} | {expected:.3f} | {non_expected:.3f} | {max_driver:.3f} | {status} | `{output}` |".format(
                video=item["video"],
                sampled=item["sampled_frames"],
                expected=item["expected_label_ratio"],
                non_expected=item["non_expected_label_ratio"],
                max_driver=item["max_driver_cabin_visible_probability"],
                status=item["status"],
                output=item["output_video_uri"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `pass` means at least 95% of sampled frames matched `not_cabin_view`.",
            "- Any `driver_cabin_visible` prediction on these videos is treated as a cabin-gate false positive for manual review.",
            "- This result should not be used as evidence that driver action recognition works; that belongs to the next cabin/action classifier stage.",
            "",
            "## Artifacts",
            "",
            f"- Summary JSON: `{summary['summary_json']}`",
            f"- Per-frame CSV: `{summary['per_frame_csv']}`",
            f"- Video outputs directory: `{summary['output_dir']}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.sample_every <= 0:
        raise ValueError("--sample-every must be positive.")

    device = pick_device(args.device)
    model, labels, img_size, checkpoint = load_model(args.checkpoint, args.label_map, device)
    transform = make_transform(img_size)
    experiment_id = str(checkpoint.get("experiment_id", "CABIN-EXP-020A"))

    videos = sorted(args.videos_dir.glob("video_*.mp4"))
    if not videos:
        raise FileNotFoundError(f"No video_*.mp4 files found under {args.videos_dir}")

    all_rows: list[dict[str, Any]] = []
    per_video: list[dict[str, Any]] = []
    for video_path in videos:
        video_summary, rows = process_video(
            video_path=video_path,
            model=model,
            labels=labels,
            transform=transform,
            device=device,
            output_dir=args.output_dir,
            sample_every=args.sample_every,
            max_frames=args.max_frames,
            output_width=args.output_width,
            expected_label=args.expected_label,
            experiment_id=experiment_id,
        )
        per_video.append(video_summary)
        all_rows.extend(rows)
        print(
            f"{video_path.name}: status={video_summary['status']} "
            f"expected_ratio={video_summary['expected_label_ratio']:.3f} "
            f"output={video_summary['output_video_uri']}"
        )

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    per_frame_csv = args.artifact_dir / "cabin_exp_020a_local_video_smoke_frames.csv"
    summary_json = args.artifact_dir / "cabin_exp_020a_local_video_smoke_summary.json"
    write_csv(per_frame_csv, all_rows)

    summary = {
        "experiment_id": experiment_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint": str(args.checkpoint),
        "backbone": checkpoint.get("backbone"),
        "labels": labels,
        "device": str(device),
        "img_size": img_size,
        "sample_every": args.sample_every,
        "expected_label": args.expected_label,
        "videos_dir": str(args.videos_dir),
        "output_dir": str(args.output_dir),
        "summary_json": str(summary_json),
        "per_frame_csv": str(per_frame_csv),
        "report": str(args.report),
        "videos": per_video,
    }
    summary_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(args.report, summary, per_video)
    print(f"summary_json={summary_json}")
    print(f"per_frame_csv={per_frame_csv}")
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
