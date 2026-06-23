#!/usr/bin/env python3
"""Export phone-positive review crops for manual labeling/fine-tune prep."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

try:
    from phone_utils import (
        driver_face_global_bbox,
        face_near_crop_bbox,
        phone_search_roi_bbox,
    )
except ImportError:
    from scripts.benchmarks.phone_utils import (
        driver_face_global_bbox,
        face_near_crop_bbox,
        phone_search_roi_bbox,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_OUTPUT_ROOT = ROOT / "runs" / "phone" / "finetune_samples"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def parse_frame_set(values: list[str]) -> set[int]:
    frames: set[int] = set()
    for value in values:
        if "-" in value:
            start, end = value.split("-", 1)
            frames.update(range(int(start), int(end) + 1))
        else:
            frames.add(int(value))
    return frames


def export_samples(
    video_path: Path,
    cabin_video: dict[str, Any],
    frames: set[int],
    output_root: Path,
    stride: int,
) -> list[dict[str, Any]]:
    records = {
        int(item["frame"]): item
        for item in cabin_video.get("per_frame", [])
    }
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    view_profile = str(cabin_video.get("view_profile") or "unknown")
    image_dir = output_root / video_path.stem / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        for frame_number in sorted(frames):
            if (frame_number - min(frames)) % max(1, stride):
                continue
            record = records.get(frame_number)
            if record is None:
                continue
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
            ok, frame = cap.read()
            if not ok:
                continue
            face_bbox = driver_face_global_bbox(record)
            phone_roi = phone_search_roi_bbox(record, width, height, view_profile)
            face_crop = face_near_crop_bbox(face_bbox, width, height) if face_bbox else None
            saved = {}
            for name, bbox in {
                "full": [0, 0, width, height],
                "driver_phone_roi": phone_roi,
                "face_near": face_crop,
            }.items():
                if bbox is None:
                    continue
                x1, y1, x2, y2 = bbox
                crop = frame[y1:y2, x1:x2].copy()
                path = image_dir / f"frame_{frame_number:06d}_{name}.jpg"
                cv2.imwrite(
                    str(path),
                    crop,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 95],
                )
                saved[name] = rel(path)
            rows.append(
                {
                    "video": video_path.name,
                    "frame": frame_number,
                    "visibility": record.get("visibility"),
                    "view_profile": view_profile,
                    "full_image_uri": saved.get("full"),
                    "driver_phone_roi_uri": saved.get("driver_phone_roi"),
                    "face_near_uri": saved.get("face_near"),
                    "phone_visible": "",
                    "phone_bbox_xyxy_in_face_near": "",
                    "phone_bbox_xyxy_in_driver_roi": "",
                    "phone_near_face": "",
                    "held_by_driver": "",
                    "reviewer_notes": "",
                }
            )
    finally:
        cap.release()
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export phone-positive frames for manual labeling."
    )
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--video", required=True)
    parser.add_argument(
        "--frames",
        nargs="+",
        required=True,
        help="Frame numbers or ranges, e.g. 30 50 70-120.",
    )
    parser.add_argument("--stride", type=int, default=10)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = json.loads(args.cabin_summary.resolve().read_text(encoding="utf-8"))
    cabin_video = next(
        (
            item
            for item in summary.get("videos", [])
            if item.get("video") == args.video
        ),
        None,
    )
    if cabin_video is None:
        raise SystemExit(f"Video not found in cabin summary: {args.video}")
    rows = export_samples(
        (args.videos_dir / args.video).resolve(),
        cabin_video,
        parse_frame_set(args.frames),
        args.output_root,
        args.stride,
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest = args.output_root / f"{Path(args.video).stem}_phone_manual_labels.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    metadata = {
        "created_at_utc": now_utc(),
        "video": args.video,
        "sample_count": len(rows),
        "manifest": rel(manifest),
    }
    metadata_path = args.output_root / f"{Path(args.video).stem}_phone_samples.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
