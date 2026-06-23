#!/usr/bin/env python3
"""Build a YOLO phone-specialist dataset from manual crop annotations."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    ROOT
    / "runs"
    / "phone"
    / "finetune_samples"
    / "video_2_phone_manual_labels.csv"
)
DEFAULT_OUTPUT_ROOT = ROOT / "runs" / "phone" / "specialist_datasets"
DEFAULT_DATASET_NAME = "phone_windshield_seed_v1"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "evet"}


def parse_xyxy(value: str | None) -> list[float] | None:
    if not value:
        return None
    cleaned = (
        value.strip()
        .removeprefix("[")
        .removesuffix("]")
        .replace(";", ",")
        .replace(" ", ",")
    )
    parts = [part for part in cleaned.split(",") if part.strip()]
    if len(parts) != 4:
        return None
    try:
        return [float(part) for part in parts]
    except ValueError:
        return None


def clamp_xyxy(
    bbox: list[float],
    width: int,
    height: int,
    min_size: float = 2.0,
) -> list[float] | None:
    x1, y1, x2, y2 = bbox
    x1 = max(0.0, min(float(width - 1), x1))
    y1 = max(0.0, min(float(height - 1), y1))
    x2 = max(1.0, min(float(width), x2))
    y2 = max(1.0, min(float(height), y2))
    if x2 - x1 < min_size or y2 - y1 < min_size:
        return None
    return [x1, y1, x2, y2]


def xyxy_to_yolo(
    bbox: list[float],
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = bbox
    box_width = x2 - x1
    box_height = y2 - y1
    center_x = x1 + box_width / 2.0
    center_y = y1 + box_height / 2.0
    return (
        center_x / width,
        center_y / height,
        box_width / width,
        box_height / height,
    )


def split_name(index: int, val_every: int) -> str:
    if val_every > 1 and (index + 1) % val_every == 0:
        return "val"
    return "train"


def image_size(image_path: Path) -> tuple[int, int]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Could not read image: {image_path}")
    height, width = image.shape[:2]
    return width, height


def draw_preview(image_path: Path, bbox: list[float], output_path: Path) -> None:
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Could not read image: {image_path}")
    x1, y1, x2, y2 = [int(round(value)) for value in bbox]
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
    cv2.putText(
        image,
        "phone seed",
        (x1, max(16, y1 - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])


def build_dataset(
    manifest: Path,
    output_root: Path,
    dataset_name: str,
    crop_column: str,
    bbox_column: str,
    class_name: str,
    val_every: int,
) -> dict[str, Any]:
    rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))
    dataset_dir = output_root / dataset_name
    stats = {
        "created_at_utc": now_utc(),
        "manifest": rel(manifest),
        "dataset_dir": rel(dataset_dir),
        "dataset_name": dataset_name,
        "class_name": class_name,
        "crop_column": crop_column,
        "bbox_column": bbox_column,
        "accepted_count": 0,
        "skipped_count": 0,
        "splits": {"train": 0, "val": 0},
        "skipped": [],
    }
    for split in ("train", "val"):
        (dataset_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (dataset_dir / "labels" / split).mkdir(parents=True, exist_ok=True)
    (dataset_dir / "previews").mkdir(parents=True, exist_ok=True)

    accepted_index = 0
    for row in rows:
        frame = str(row.get("frame") or "unknown")
        crop_uri = row.get(crop_column)
        bbox = parse_xyxy(row.get(bbox_column))
        if not parse_bool(row.get("phone_visible")) or not crop_uri or bbox is None:
            stats["skipped_count"] += 1
            stats["skipped"].append({"frame": frame, "reason": "missing_visible_crop_or_bbox"})
            continue
        source_image = (ROOT / crop_uri).resolve()
        width, height = image_size(source_image)
        bbox = clamp_xyxy(bbox, width, height)
        if bbox is None:
            stats["skipped_count"] += 1
            stats["skipped"].append({"frame": frame, "reason": "invalid_bbox"})
            continue
        split = split_name(accepted_index, val_every)
        stem = f"{Path(row.get('video') or 'video').stem}_frame_{int(frame):06d}_{crop_column}"
        image_target = dataset_dir / "images" / split / f"{stem}.jpg"
        label_target = dataset_dir / "labels" / split / f"{stem}.txt"
        shutil.copy2(source_image, image_target)
        yolo_box = xyxy_to_yolo(bbox, width, height)
        label_target.write_text(
            "0 " + " ".join(f"{value:.6f}" for value in yolo_box) + "\n",
            encoding="utf-8",
        )
        draw_preview(source_image, bbox, dataset_dir / "previews" / f"{stem}.jpg")
        accepted_index += 1
        stats["accepted_count"] += 1
        stats["splits"][split] += 1

    data_yaml = dataset_dir / "data.yaml"
    data_yaml.write_text(
        "\n".join(
            [
                f"path: {dataset_dir.resolve()}",
                "train: images/train",
                "val: images/val",
                "names:",
                f"  0: {class_name}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    readme = dataset_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# {dataset_name}",
                "",
                "Tiny seed dataset for a windshield/side-window phone specialist challenger.",
                "",
                "This is not an accepted benchmark dataset. It contains manually seeded",
                "positive crops from `video_2.mp4` and is intended for overfit/smoke",
                "fine-tuning before controlled positive/negative data collection.",
                "",
                "Train command:",
                "",
                "```bash",
                f"yolo detect train model=yolo11n.pt data={data_yaml.resolve()} epochs=80 imgsz=640 batch=8",
                "```",
                "",
                "Use the trained weights only as a challenger against held-out video clips;",
                "do not promote it without negative cases and manual overlay review.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    summary_path = dataset_dir / "dataset_summary.json"
    summary_path.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert manual phone crop annotations to a YOLO dataset."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--crop-column", default="face_near_uri")
    parser.add_argument("--bbox-column", default="phone_bbox_xyxy_in_face_near")
    parser.add_argument("--class-name", default="phone")
    parser.add_argument("--val-every", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = build_dataset(
        manifest=args.manifest.resolve(),
        output_root=args.output_root.resolve(),
        dataset_name=args.dataset_name,
        crop_column=args.crop_column,
        bbox_column=args.bbox_column,
        class_name=args.class_name,
        val_every=max(0, args.val_every),
    )
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
