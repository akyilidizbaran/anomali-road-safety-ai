#!/usr/bin/env python3
"""Run a vehicle type classifier checkpoint on local target ROI crops.

The script was first used for TYPE-EXP-001, but it is intentionally checkpoint
driven: output names and summaries derive from ``checkpoint["experiment_id"]``.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        default="runs/vehicle_type/TYPE-EXP-001-local-smoke/artifacts/TYPE-EXP-001-efficientnet_b0-best.pth",
        help="Vehicle type classifier .pth checkpoint path.",
    )
    parser.add_argument(
        "--input-dir",
        default="runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames",
        help="Directory containing target vehicle ROI crop images.",
    )
    parser.add_argument(
        "--output-dir",
        default="runs/vehicle_type/TYPE-EXP-001-local-smoke",
        help="Output directory for CSV, JSON and contact sheet.",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--min-confidence", type=float, default=0.60)
    parser.add_argument("--min-margin", type=float, default=0.15)
    return parser.parse_args()


def build_model(num_classes: int) -> nn.Module:
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def experiment_slug(value: str | None) -> str:
    value = value or "vehicle-type"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_").lower()


def image_transform(image_size: int) -> T.Compose:
    return T.Compose(
        [
            T.Resize((image_size, image_size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def infer_video_id(path: Path) -> str:
    match = re.search(r"video_\d+", path.name)
    return match.group(0) if match else "unknown"


def infer_frame_id(path: Path) -> int | None:
    match = re.search(r"frame_(\d+)", path.name)
    return int(match.group(1)) if match else None


def load_checkpoint(path: Path) -> dict:
    checkpoint = torch.load(path, map_location="cpu")
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError(f"Unsupported checkpoint format: {path}")
    return checkpoint


def collect_images(input_dir: Path) -> list[Path]:
    paths = sorted(p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if not paths:
        raise FileNotFoundError(f"No crop images found under {input_dir}")
    return paths


def topk_prediction(probs: torch.Tensor, id_to_label: dict[int, str]) -> tuple[str, float, str, float, float]:
    values, indices = torch.topk(probs, k=min(3, probs.numel()))
    top1_id = int(indices[0].item())
    top1_conf = float(values[0].item())
    top2_id = int(indices[1].item()) if len(indices) > 1 else top1_id
    top2_conf = float(values[1].item()) if len(values) > 1 else 0.0
    return (
        id_to_label[top1_id],
        top1_conf,
        id_to_label[top2_id],
        top2_conf,
        top1_conf - top2_conf,
    )


def make_contact_sheet(rows: list[dict], output_path: Path, max_items: int = 42) -> None:
    thumbs = []
    font = ImageFont.load_default()
    for row in rows[:max_items]:
        img = Image.open(row["image_path"]).convert("RGB")
        img.thumbnail((220, 140))
        tile = Image.new("RGB", (240, 190), "white")
        tile.paste(img, ((240 - img.width) // 2, 8))
        draw = ImageDraw.Draw(tile)
        label = f"{row['video']} f{row['frame_id']}"
        pred = f"{row['top1_label']} {float(row['top1_confidence']):.2f}"
        second = f"2:{row['top2_label']} {float(row['top2_confidence']):.2f}"
        gate = "PASS" if row["gate_pass"] else "LOW"
        draw.text((8, 150), label, fill="black", font=font)
        draw.text((8, 164), pred, fill="black", font=font)
        draw.text((112, 164), second, fill="black", font=font)
        draw.text((8, 178), gate, fill="black", font=font)
        thumbs.append(tile)

    cols = 3
    rows_count = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 240, rows_count * 190), "white")
    for idx, tile in enumerate(thumbs):
        x = (idx % cols) * 240
        y = (idx // cols) * 190
        sheet.paste(tile, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=92)


def main() -> None:
    args = parse_args()
    checkpoint_path = Path(args.checkpoint)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = load_checkpoint(checkpoint_path)
    id_to_label = {int(k): v for k, v in checkpoint["id_to_label"].items()}
    image_size = int(checkpoint.get("image_size", 224))
    num_classes = len(id_to_label)

    model = build_model(num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    transform = image_transform(image_size)
    image_paths = collect_images(input_dir)

    rows: list[dict] = []
    with torch.no_grad():
        for start in range(0, len(image_paths), args.batch_size):
            batch_paths = image_paths[start : start + args.batch_size]
            tensors = []
            for path in batch_paths:
                image = Image.open(path).convert("RGB")
                tensors.append(transform(image))
            logits = model(torch.stack(tensors, dim=0))
            probs = torch.softmax(logits, dim=1)
            for path, prob in zip(batch_paths, probs):
                top1, top1_conf, top2, top2_conf, margin = topk_prediction(prob, id_to_label)
                gate_pass = top1_conf >= args.min_confidence and margin >= args.min_margin
                rows.append(
                    {
                        "image_path": str(path),
                        "image_name": path.name,
                        "video": infer_video_id(path),
                        "frame_id": infer_frame_id(path),
                        "top1_label": top1,
                        "top1_confidence": top1_conf,
                        "top2_label": top2,
                        "top2_confidence": top2_conf,
                        "top1_top2_margin": margin,
                        "gate_pass": gate_pass,
                    }
                )

    exp_id = checkpoint.get("experiment_id", "vehicle-type-local-smoke")
    slug = experiment_slug(str(exp_id))

    csv_path = output_dir / f"{slug}_local_smoke_predictions.csv"
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
            "frames": len(video_rows),
            "top1_counts": dict(labels),
            "gate_pass_frames": sum(1 for r in video_rows if r["gate_pass"]),
            "gated_top1_counts": dict(gated_labels),
            "mean_top1_confidence": sum(float(r["top1_confidence"]) for r in video_rows) / len(video_rows),
            "mean_margin": sum(float(r["top1_top2_margin"]) for r in video_rows) / len(video_rows),
        }

    summary = {
        "experiment_id": f"{exp_id}-local-smoke",
        "source_checkpoint": str(checkpoint_path),
        "checkpoint_experiment_id": checkpoint.get("experiment_id"),
        "checkpoint_backbone": checkpoint.get("backbone"),
        "checkpoint_epoch": checkpoint.get("epoch"),
        "checkpoint_val_macro_f1": checkpoint.get("val_macro_f1"),
        "checkpoint_val_accuracy": checkpoint.get("val_accuracy"),
        "input_dir": str(input_dir),
        "image_count": len(rows),
        "min_confidence": args.min_confidence,
        "min_margin": args.min_margin,
        "overall_top1_counts": dict(Counter(r["top1_label"] for r in rows)),
        "overall_gate_pass_frames": sum(1 for r in rows if r["gate_pass"]),
        "video_summary": video_summary,
        "csv": str(csv_path),
    }

    summary_path = output_dir / f"{slug}_local_smoke_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    sheet_path = output_dir / f"{slug}_local_smoke_contact_sheet.jpg"
    make_contact_sheet(rows, sheet_path)

    print(json.dumps(summary, indent=2))
    print("CSV:", csv_path)
    print("Contact sheet:", sheet_path)


if __name__ == "__main__":
    main()
