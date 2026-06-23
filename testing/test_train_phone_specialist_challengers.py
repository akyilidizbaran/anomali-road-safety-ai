from argparse import Namespace
from pathlib import Path

import yaml

from scripts.benchmarks.train_phone_specialist_challengers import (
    dataset_inventory,
    training_plan,
)


def write_dataset(tmp_path: Path) -> Path:
    dataset = tmp_path / "dataset"
    for split in ("train", "val"):
        (dataset / "images" / split).mkdir(parents=True)
        (dataset / "labels" / split).mkdir(parents=True)
    (dataset / "images" / "train" / "positive.jpg").write_bytes(b"image")
    (dataset / "labels" / "train" / "positive.txt").write_text(
        "0 0.5 0.5 0.1 0.2\n", encoding="utf-8"
    )
    (dataset / "images" / "val" / "negative.jpg").write_bytes(b"image")
    (dataset / "labels" / "val" / "negative.txt").write_text("", encoding="utf-8")
    data_yaml = dataset / "data.yaml"
    data_yaml.write_text(
        yaml.safe_dump(
            {
                "path": str(dataset),
                "train": "images/train",
                "val": "images/val",
                "names": {0: "phone"},
            }
        ),
        encoding="utf-8",
    )
    return data_yaml


def test_dataset_inventory_counts_positive_and_negative_images(tmp_path: Path):
    inventory = dataset_inventory(write_dataset(tmp_path))
    assert inventory["image_count"] == 2
    assert inventory["positive_image_count"] == 1
    assert inventory["negative_image_count"] == 1
    assert inventory["missing_label_count"] == 0


def test_training_plan_keeps_shared_settings_for_both_variants(tmp_path: Path):
    data_yaml = write_dataset(tmp_path)
    args = Namespace(
        variants=["p2", "standard"],
        epochs=3,
        imgsz=640,
        batch=2,
        device="cpu",
        workers=0,
        seed=42,
        hsv_h=0.015,
        hsv_s=0.45,
        hsv_v=0.5,
        mosaic=0.5,
        close_mosaic=1,
    )
    plan = training_plan(args, dataset_inventory(data_yaml))
    assert plan["shared_config"]["imgsz"] == 640
    assert [item["experiment_id"] for item in plan["variants"]] == [
        "PHONE-EXP-003",
        "PHONE-EXP-004",
    ]
