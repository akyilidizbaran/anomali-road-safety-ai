import csv
from pathlib import Path

import cv2
import numpy as np

from scripts.benchmarks.prepare_phone_specialist_yolo_dataset import (
    build_dataset,
    clamp_xyxy,
    parse_xyxy,
    xyxy_to_yolo,
)


def test_parse_xyxy_accepts_common_manual_formats():
    assert parse_xyxy("1,2,3,4") == [1.0, 2.0, 3.0, 4.0]
    assert parse_xyxy("[1; 2; 3; 4]") == [1.0, 2.0, 3.0, 4.0]
    assert parse_xyxy("") is None


def test_clamp_xyxy_rejects_tiny_boxes():
    assert clamp_xyxy([-5, 1, 20, 30], 100, 100) == [0.0, 1.0, 20, 30]
    assert clamp_xyxy([10, 10, 11, 11], 100, 100) is None


def test_xyxy_to_yolo_normalizes_box():
    assert xyxy_to_yolo([10, 20, 30, 60], 100, 200) == (
        0.2,
        0.2,
        0.2,
        0.2,
    )


def test_build_dataset_writes_yolo_labels(tmp_path: Path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    image_path = image_dir / "sample.jpg"
    cv2.imwrite(str(image_path), np.zeros((100, 200, 3), dtype=np.uint8))
    manifest = tmp_path / "labels.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "video",
                "frame",
                "face_near_uri",
                "phone_visible",
                "phone_bbox_xyxy_in_face_near",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "video": "sample.mp4",
                "frame": "10",
                "face_near_uri": str(image_path),
                "phone_visible": "true",
                "phone_bbox_xyxy_in_face_near": "20,10,60,50",
            }
        )

    stats = build_dataset(
        manifest=manifest,
        output_root=tmp_path / "dataset_out",
        dataset_name="phone_seed",
        crop_column="face_near_uri",
        bbox_column="phone_bbox_xyxy_in_face_near",
        class_name="phone",
        val_every=0,
    )

    assert stats["accepted_count"] == 1
    label = next((tmp_path / "dataset_out" / "phone_seed" / "labels").glob("train/*.txt"))
    assert label.read_text(encoding="utf-8").startswith("0 0.200000 0.300000")
