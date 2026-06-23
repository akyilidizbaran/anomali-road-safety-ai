#!/usr/bin/env python3
"""Train comparable YOLO26 phone specialist smoke challengers."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = (
    ROOT
    / "runs"
    / "phone"
    / "specialist_datasets"
    / "phone_windshield_seed_v1"
    / "data.yaml"
)
DEFAULT_PROJECT = ROOT / "runs" / "phone" / "training"

VARIANTS = {
    "p2": {
        "experiment_id": "PHONE-EXP-003",
        "model_key": "yolo26s_p2_phone_windshield_seed_smoke",
        "architecture": "yolo26s-p2.yaml",
        "pretrained": "yolo26s.pt",
        "run_name": "phone_exp_003_yolo26s_p2_seed_smoke",
    },
    "standard": {
        "experiment_id": "PHONE-EXP-004",
        "model_key": "yolo26s_phone_windshield_seed_smoke",
        "architecture": None,
        "pretrained": "yolo26s.pt",
        "run_name": "phone_exp_004_yolo26s_seed_smoke",
    },
}

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_dataset_path(data_yaml: Path, value: str) -> Path:
    if Path(value).is_absolute():
        return Path(value)
    data = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    dataset_root = Path(data.get("path") or data_yaml.parent)
    if not dataset_root.is_absolute():
        dataset_root = (data_yaml.parent / dataset_root).resolve()
    return (dataset_root / value).resolve()


def label_path_for_image(image_path: Path) -> Path:
    parts = list(image_path.parts)
    image_index = max(index for index, part in enumerate(parts) if part == "images")
    parts[image_index] = "labels"
    return Path(*parts).with_suffix(".txt")


def dataset_inventory(data_yaml: Path) -> dict[str, Any]:
    data_yaml = data_yaml.resolve()
    data = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    result: dict[str, Any] = {
        "data_yaml": str(data_yaml),
        "class_names": data.get("names"),
        "splits": {},
        "image_count": 0,
        "positive_image_count": 0,
        "negative_image_count": 0,
        "missing_label_count": 0,
    }
    for split in ("train", "val"):
        split_value = data.get(split)
        if not split_value:
            continue
        image_dir = resolve_dataset_path(data_yaml, str(split_value))
        images = sorted(
            path
            for path in image_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        split_stats = {"images": len(images), "positive": 0, "negative": 0, "missing": 0}
        for image_path in images:
            label_path = label_path_for_image(image_path)
            if not label_path.exists():
                split_stats["missing"] += 1
            elif label_path.read_text(encoding="utf-8").strip():
                split_stats["positive"] += 1
            else:
                split_stats["negative"] += 1
        result["splits"][split] = split_stats
        result["image_count"] += split_stats["images"]
        result["positive_image_count"] += split_stats["positive"]
        result["negative_image_count"] += split_stats["negative"]
        result["missing_label_count"] += split_stats["missing"]
    return result


def resolve_device(device: str) -> str:
    if device != "auto":
        return device
    import torch

    if torch.cuda.is_available():
        return "0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def training_plan(args: argparse.Namespace, inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at_utc": now_utc(),
        "status": "positive_only_smoke_not_baseline",
        "dataset": inventory,
        "shared_config": {
            "epochs": args.epochs,
            "imgsz": args.imgsz,
            "batch": args.batch,
            "device": resolve_device(args.device),
            "workers": args.workers,
            "seed": args.seed,
            "hsv_h": args.hsv_h,
            "hsv_s": args.hsv_s,
            "hsv_v": args.hsv_v,
            "mosaic": args.mosaic,
            "close_mosaic": args.close_mosaic,
        },
        "variants": [{"variant": name, **VARIANTS[name]} for name in args.variants],
    }


def train_variant(
    variant_name: str,
    args: argparse.Namespace,
    device: str,
) -> dict[str, Any]:
    from ultralytics import YOLO

    variant = VARIANTS[variant_name]
    if variant["architecture"]:
        model = YOLO(str(variant["architecture"]))
        model.load(str(variant["pretrained"]))
    else:
        model = YOLO(str(variant["pretrained"]))
    model.train(
        data=str(args.data.resolve()),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        workers=args.workers,
        seed=args.seed,
        hsv_h=args.hsv_h,
        hsv_s=args.hsv_s,
        hsv_v=args.hsv_v,
        mosaic=args.mosaic,
        close_mosaic=args.close_mosaic,
        project=str(args.project.resolve()),
        name=str(variant["run_name"]),
        exist_ok=True,
        plots=True,
        verbose=True,
    )
    best_path = args.project.resolve() / str(variant["run_name"]) / "weights" / "best.pt"
    return {
        "variant": variant_name,
        "experiment_id": variant["experiment_id"],
        "model_key": variant["model_key"],
        "best_weights": str(best_path),
        "exists": best_path.exists(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train YOLO26s-P2 and standard YOLO26s phone smoke challengers."
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--variants", nargs="+", choices=tuple(VARIANTS), default=["p2", "standard"])
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--hsv-h", type=float, default=0.015)
    parser.add_argument("--hsv-s", type=float, default=0.45)
    parser.add_argument("--hsv-v", type=float, default=0.50)
    parser.add_argument("--mosaic", type=float, default=0.50)
    parser.add_argument("--close-mosaic", type=int, default=10)
    parser.add_argument("--allow-positive-only-smoke", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.data.exists():
        raise SystemExit(f"Dataset YAML not found: {args.data}")
    inventory = dataset_inventory(args.data)
    if inventory["missing_label_count"]:
        raise SystemExit("Dataset has images without label files.")
    if inventory["negative_image_count"] == 0 and not args.allow_positive_only_smoke:
        raise SystemExit(
            "Dataset has no negative images. Re-run with --allow-positive-only-smoke "
            "only for the requested manual overfit/smoke comparison."
        )
    plan = training_plan(args, inventory)
    args.project.mkdir(parents=True, exist_ok=True)
    plan_path = args.project / "phone_specialist_training_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    if args.dry_run:
        return
    device = str(plan["shared_config"]["device"])
    results = [train_variant(name, args, device) for name in args.variants]
    result_path = args.project / "phone_specialist_training_results.json"
    result_path.write_text(
        json.dumps({"plan": plan, "results": results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"results": results, "result_path": str(result_path)}, indent=2))


if __name__ == "__main__":
    main()
