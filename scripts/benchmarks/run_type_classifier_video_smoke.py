#!/usr/bin/env python3
"""Run a vehicle type classifier checkpoint on target ROI clip videos."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Vehicle type classifier .pth checkpoint path.",
    )
    parser.add_argument(
        "--clips-dir",
        default="runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/clips",
        help="Directory containing target ROI clip videos.",
    )
    parser.add_argument(
        "--output-dir",
        default="runs/vehicle_type/TYPE-EXP-002-local-video-smoke",
        help="Output directory for CSV, JSON and annotated MP4 files.",
    )
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--min-confidence", type=float, default=0.60)
    parser.add_argument("--min-margin", type=float, default=0.15)
    return parser.parse_args()


def build_model(backbone: str, num_classes: int) -> nn.Module:
    if backbone == "mobilenet_v3_large":
        model = models.mobilenet_v3_large(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    if backbone == "efficientnet_b0":
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    raise ValueError(f"Unsupported checkpoint backbone: {backbone}")


def image_transform(image_size: int) -> T.Compose:
    return T.Compose(
        [
            T.Resize((image_size, image_size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def experiment_slug(value: str | None) -> str:
    value = value or "vehicle-type"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_").lower()


def infer_video_id(path: Path) -> str:
    match = re.search(r"video_\d+", path.name)
    return match.group(0) if match else path.stem


def load_checkpoint(path: Path) -> dict:
    checkpoint = torch.load(path, map_location="cpu")
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError(f"Unsupported checkpoint format: {path}")
    return checkpoint


def collect_clips(clips_dir: Path) -> list[Path]:
    clips = sorted(p for p in clips_dir.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS)
    if not clips:
        raise FileNotFoundError(f"No clip videos found under {clips_dir}")
    return clips


def predict_frame(
    model: nn.Module,
    transform: T.Compose,
    frame_bgr,
    id_to_label: dict[int, str],
) -> tuple[str, float, str, float, float, list[dict]]:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1).squeeze(0)
    values, indices = torch.topk(probs, k=min(3, probs.numel()))
    top1_id = int(indices[0].item())
    top1_conf = float(values[0].item())
    top2_id = int(indices[1].item()) if len(indices) > 1 else top1_id
    top2_conf = float(values[1].item()) if len(values) > 1 else 0.0
    top3 = [
        {"label": id_to_label[int(idx.item())], "confidence": float(value.item())}
        for value, idx in zip(values, indices)
    ]
    return id_to_label[top1_id], top1_conf, id_to_label[top2_id], top2_conf, top1_conf - top2_conf, top3


def draw_overlay(frame, row: dict, exp_id: str) -> None:
    gate = "PASS" if row["gate_pass"] else "LOW"
    lines = [
        f"{exp_id}",
        f"{row['video']} frame={row['frame_idx']}",
        f"type={row['top1_label']} conf={row['top1_confidence']:.2f}",
        f"top2={row['top2_label']} margin={row['top1_top2_margin']:.2f}",
        f"gate={gate}",
    ]
    x, y = 12, 24
    for line in lines:
        cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 1, cv2.LINE_AA)
        y += 23


def process_clip(
    clip_path: Path,
    model: nn.Module,
    transform: T.Compose,
    id_to_label: dict[int, str],
    output_dir: Path,
    exp_id: str,
    frame_stride: int,
    min_confidence: float,
    min_margin: float,
) -> list[dict]:
    video_id = infer_video_id(clip_path)
    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {clip_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_path = output_dir / f"{video_id}_{experiment_slug(exp_id)}_type_overlay.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    rows: list[dict] = []
    last_prediction = None
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % max(1, frame_stride) == 0 or last_prediction is None:
            top1, top1_conf, top2, top2_conf, margin, top3 = predict_frame(model, transform, frame, id_to_label)
            gate_pass = top1_conf >= min_confidence and margin >= min_margin
            last_prediction = {
                "clip_path": str(clip_path),
                "overlay_path": str(out_path),
                "video": video_id,
                "frame_idx": frame_idx,
                "top1_label": top1,
                "top1_confidence": top1_conf,
                "top2_label": top2,
                "top2_confidence": top2_conf,
                "top1_top2_margin": margin,
                "gate_pass": gate_pass,
                "top3": json.dumps(top3, ensure_ascii=False),
            }
            rows.append(last_prediction.copy())
        overlay_row = last_prediction.copy()
        overlay_row["frame_idx"] = frame_idx
        draw_overlay(frame, overlay_row, exp_id)
        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    return rows


def main() -> None:
    args = parse_args()
    checkpoint_path = Path(args.checkpoint)
    clips_dir = Path(args.clips_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = load_checkpoint(checkpoint_path)
    raw_id_to_label = checkpoint["id_to_label"]
    id_to_label = {int(k): v for k, v in raw_id_to_label.items()}
    exp_id = str(checkpoint.get("experiment_id", checkpoint_path.stem))
    backbone = str(checkpoint.get("backbone", "efficientnet_b0"))
    image_size = int(checkpoint.get("image_size", 224))

    model = build_model(backbone, len(id_to_label))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    transform = image_transform(image_size)

    rows: list[dict] = []
    for clip in collect_clips(clips_dir):
        rows.extend(
            process_clip(
                clip,
                model,
                transform,
                id_to_label,
                output_dir,
                exp_id,
                args.frame_stride,
                args.min_confidence,
                args.min_margin,
            )
        )

    if not rows:
        raise RuntimeError("No predictions were produced.")

    slug = experiment_slug(exp_id)
    csv_path = output_dir / f"{slug}_local_video_smoke_predictions.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_video = defaultdict(list)
    for row in rows:
        by_video[row["video"]].append(row)

    video_summary = {}
    for video, video_rows in sorted(by_video.items()):
        labels = Counter(r["top1_label"] for r in video_rows)
        gated_labels = Counter(r["top1_label"] for r in video_rows if r["gate_pass"])
        video_summary[video] = {
            "sampled_frames": len(video_rows),
            "top1_counts": dict(labels),
            "gate_pass_frames": sum(1 for r in video_rows if r["gate_pass"]),
            "gated_top1_counts": dict(gated_labels),
            "mean_top1_confidence": sum(float(r["top1_confidence"]) for r in video_rows) / len(video_rows),
            "mean_margin": sum(float(r["top1_top2_margin"]) for r in video_rows) / len(video_rows),
        }

    summary = {
        "experiment_id": f"{exp_id}-local-video-smoke",
        "source_checkpoint": str(checkpoint_path),
        "checkpoint_experiment_id": checkpoint.get("experiment_id"),
        "checkpoint_backbone": checkpoint.get("backbone"),
        "checkpoint_best_val_macro_f1": checkpoint.get("best_val_macro_f1"),
        "clips_dir": str(clips_dir),
        "frame_stride": args.frame_stride,
        "min_confidence": args.min_confidence,
        "min_margin": args.min_margin,
        "overall_top1_counts": dict(Counter(r["top1_label"] for r in rows)),
        "overall_gate_pass_frames": sum(1 for r in rows if r["gate_pass"]),
        "video_summary": video_summary,
        "csv": str(csv_path),
    }
    summary_path = output_dir / f"{slug}_local_video_smoke_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print("CSV:", csv_path)
    print("Overlays:", output_dir)


if __name__ == "__main__":
    main()

