#!/usr/bin/env python3
"""SPEED-EXP-004B plate-scale + VATTR sanity-check fusion.

This script connects three existing signals:
  * SPEED-EXP-004A relative track/bbox motion
  * SPEED-EXP-002 plate-scale monocular speed candidate
  * VATTR-EXP-001 vehicle body / dimension-prior classifier

It does not promote any result to legal/final km/h. The output is a conservative
Speed Fusion evidence block for event/evidence JSON.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004a.json"
DEFAULT_PLATE_SPEED = (
    ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-002-plate-bbox-xyz" / "speed_exp_002_plate_bbox_xyz_summary.json"
)
DEFAULT_CROP_DIR = ROOT / "runs" / "_archive" / "plate_ocr_v1_POCR-EXP-001-target-roi-crops" / "sample_frames"
DEFAULT_CHECKPOINT = ROOT / "models" / "checkpoints" / "vehicle_attribute" / "VATTR-EXP-001-efficientnet_b0-best.pth"
DEFAULT_LABEL_MAP = ROOT / "models" / "checkpoints" / "vehicle_attribute" / "VATTR-EXP-001-label-map.json"
DEFAULT_PRIORS = ROOT / "models" / "checkpoints" / "vehicle_attribute" / "VATTR-EXP-001-dimension-prior-table.json"
DEFAULT_OUTPUT_DIR = ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-004B-plate-vattr-sanity"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "speed_exp_004b_plate_vattr_sanity.md"
DEFAULT_ENRICHED_EVENTS = (
    ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004b.json"
)


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def round_or_none(value: float | None, ndigits: int = 6) -> float | None:
    return None if value is None else round(float(value), ndigits)


def create_model(backbone: str, num_classes: int) -> nn.Module:
    if backbone != "efficientnet_b0":
        raise ValueError(f"Unsupported VATTR backbone for local smoke: {backbone}")
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def load_vattr_model(checkpoint_path: Path, label_map_path: Path, device: torch.device) -> tuple[nn.Module, list[str], dict[str, Any]]:
    label_map = load_json(label_map_path)
    label_names = label_map["label_names"]
    checkpoint = torch.load(checkpoint_path, map_location=device)
    backbone = checkpoint.get("backbone", "efficientnet_b0")
    model = create_model(backbone, len(label_names)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, label_names, checkpoint


def event_crop_index(crop_dir: Path, events: list[dict[str, Any]]) -> dict[str, list[Path]]:
    all_crops = sorted(crop_dir.glob("*.jpg"))
    index: dict[str, list[Path]] = {}
    for event in events:
        event_id = event.get("event_id")
        if not event_id:
            continue
        index[event_id] = [path for path in all_crops if path.name.startswith(event_id + "_")]
    return index


def parse_frame_from_crop(path: Path) -> int | None:
    match = re.search(r"_frame_(\d+)_target_roi", path.name)
    return int(match.group(1)) if match else None


def predict_crops(
    model: nn.Module,
    label_names: list[str],
    crop_paths: list[Path],
    device: torch.device,
    batch_size: int,
) -> dict[str, Any]:
    tf = T.Compose(
        [
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    if not crop_paths:
        return {
            "status": "not_available",
            "failure_reason": "no_target_roi_crops",
            "crop_count": 0,
        }

    per_crop: list[dict[str, Any]] = []
    probs_accum: list[torch.Tensor] = []
    with torch.no_grad():
        for start in range(0, len(crop_paths), batch_size):
            paths = crop_paths[start : start + batch_size]
            images = []
            valid_paths = []
            for path in paths:
                try:
                    img = Image.open(path).convert("RGB")
                except OSError:
                    continue
                images.append(tf(img))
                valid_paths.append(path)
            if not images:
                continue
            batch = torch.stack(images).to(device)
            probs = torch.softmax(model(batch), dim=1).detach().cpu()
            for path, prob in zip(valid_paths, probs, strict=False):
                top_idx = int(torch.argmax(prob).item())
                top_prob = float(prob[top_idx].item())
                top3_idx = torch.topk(prob, k=min(3, len(label_names))).indices.tolist()
                per_crop.append(
                    {
                        "crop_uri": rel(path),
                        "frame": parse_frame_from_crop(path),
                        "predicted_label": label_names[top_idx],
                        "confidence": round(top_prob, 6),
                        "top3": [
                            {
                                "label": label_names[int(idx)],
                                "confidence": round(float(prob[int(idx)].item()), 6),
                            }
                            for idx in top3_idx
                        ],
                    }
                )
                probs_accum.append(prob)

    if not probs_accum:
        return {
            "status": "not_available",
            "failure_reason": "all_crops_unreadable",
            "crop_count": len(crop_paths),
        }

    mean_prob = torch.stack(probs_accum).mean(dim=0)
    top_idx = int(torch.argmax(mean_prob).item())
    top_conf = float(mean_prob[top_idx].item())
    top3_idx = torch.topk(mean_prob, k=min(3, len(label_names))).indices.tolist()
    vote_counts: dict[str, int] = defaultdict(int)
    for row in per_crop:
        vote_counts[row["predicted_label"]] += 1

    return {
        "status": "computed",
        "failure_reason": None,
        "crop_count": len(per_crop),
        "predicted_body_label": label_names[top_idx],
        "vehicle_attribute_confidence": round(top_conf, 6),
        "top3_mean_probabilities": [
            {
                "label": label_names[int(idx)],
                "confidence": round(float(mean_prob[int(idx)].item()), 6),
            }
            for idx in top3_idx
        ],
        "per_crop_vote_counts": dict(sorted(vote_counts.items())),
        "best_crop_uri": max(per_crop, key=lambda row: row["confidence"])["crop_uri"],
        "per_crop": per_crop,
    }


def plate_speed_by_video(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for video in summary.get("videos", []):
        variants = video.get("variants") or {}
        geomean = (variants.get("geomean") or {}).get("summary") or {}
        indexed[video.get("video")] = {
            "status": video.get("status"),
            "source_experiment": summary.get("experiment_id"),
            "source_variant": "geomean",
            "speed_kmh": geomean.get("median_speed_kmh"),
            "confidence": 0.28 if "low_" in str(geomean.get("confidence_note")) else 0.45,
            "confidence_note": geomean.get("confidence_note"),
            "usable_measurement_count": video.get("usable_measurement_count"),
            "plate_aspect_ratio_median": video.get("plate_aspect_ratio_median"),
            "full_frame_plate_bbox_available": video.get("full_frame_plate_bbox_available"),
        }
    return indexed


def make_speed_004b(
    event: dict[str, Any],
    vattr: dict[str, Any],
    prior_table: dict[str, Any],
    plate_candidate: dict[str, Any] | None,
    min_vattr_confidence: float,
) -> dict[str, Any]:
    speed_004a = event.get("speed_exp_004a") or {}
    relative_label = speed_004a.get("relative_speed_label")
    relative_confidence = float(speed_004a.get("fusion_confidence") or 0.0)
    predicted_label = vattr.get("predicted_body_label")
    prior = (prior_table.get("priors") or {}).get(predicted_label) if predicted_label else None
    vattr_conf = float(vattr.get("vehicle_attribute_confidence") or 0.0)
    use_vattr = bool(prior and prior.get("use_for_speed_fusion") and vattr_conf >= min_vattr_confidence)

    quality_flags = ["relative_track_speed_available"]
    warning_flags = ["not_absolute_kmh", "not_for_legal_enforcement"]
    candidate_speeds: list[dict[str, Any]] = [
        {
            "source": "relative_track_bbox",
            "speed_kmh": None,
            "relative_speed_score": speed_004a.get("relative_speed_score"),
            "relative_speed_label": relative_label,
            "confidence": relative_confidence,
            "quality_flags": speed_004a.get("quality_flags") or [],
            "failure_flags": speed_004a.get("warning_flags") or [],
        }
    ]

    if plate_candidate and plate_candidate.get("speed_kmh") is not None:
        candidate_speeds.append(
            {
                "source": "plate_scale_geomean",
                "speed_kmh": plate_candidate.get("speed_kmh"),
                "confidence": plate_candidate.get("confidence"),
                "quality_flags": ["full_frame_plate_bbox_available"]
                if plate_candidate.get("full_frame_plate_bbox_available")
                else ["plate_scale_available"],
                "failure_flags": [plate_candidate.get("confidence_note")] if plate_candidate.get("confidence_note") else [],
            }
        )
        warning_flags.append("plate_scale_low_confidence")
    else:
        warning_flags.append("plate_scale_unavailable")

    if use_vattr:
        quality_flags.append("vehicle_dimension_prior_available")
    elif prior:
        warning_flags.append("vehicle_attribute_low_confidence")
    else:
        warning_flags.append("vehicle_dimension_prior_unavailable")

    disagreement_flags: list[str] = []
    plate_speed = plate_candidate.get("speed_kmh") if plate_candidate else None
    if relative_label == "fast" and plate_speed is not None and float(plate_speed) < 20.0:
        disagreement_flags.append("relative_fast_plate_scale_low_disagreement")
        warning_flags.append("candidate_disagreement_high")
    if relative_label in {"slow", "normal"} and plate_speed is not None and float(plate_speed) > 80.0:
        disagreement_flags.append("relative_nonfast_plate_scale_high_disagreement")
        warning_flags.append("candidate_disagreement_high")

    vattr_bonus = 0.08 if use_vattr else 0.0
    plate_conf = float((plate_candidate or {}).get("confidence") or 0.0)
    plate_bonus = 0.04 if plate_candidate and plate_candidate.get("speed_kmh") is not None and plate_conf >= 0.40 else 0.0
    disagreement_penalty = 0.12 if disagreement_flags else 0.0
    fusion_confidence = max(0.0, min(0.90, relative_confidence + vattr_bonus + plate_bonus - disagreement_penalty))

    return {
        "experiment_id": "SPEED-EXP-004B",
        "speed_mode": "relative",
        "primary_speed_source": "relative_track_bbox",
        "candidate_speeds": candidate_speeds,
        "vehicle_dimension_prior": {
            "source": "VATTR-EXP-001",
            "status": vattr.get("status"),
            "predicted_body_label": predicted_label,
            "vehicle_attribute_confidence": round_or_none(vattr.get("vehicle_attribute_confidence"), 6),
            "use_for_speed_fusion": use_vattr,
            "prior": prior,
            "crop_count": vattr.get("crop_count"),
            "best_crop_uri": vattr.get("best_crop_uri"),
            "top3_mean_probabilities": vattr.get("top3_mean_probabilities"),
            "per_crop_vote_counts": vattr.get("per_crop_vote_counts"),
            "failure_reason": vattr.get("failure_reason"),
        },
        "plate_scale_sanity": plate_candidate,
        "sanity_check": {
            "decision": "use_relative_with_sanity_warnings" if disagreement_flags else "use_relative_with_supporting_priors",
            "disagreement_flags": disagreement_flags,
            "quality_flags": sorted(set(quality_flags)),
            "warning_flags": sorted(set(warning_flags)),
        },
        "fusion_confidence": round(fusion_confidence, 4),
        "fallback_reason": "no_reliable_metric_calibration",
        "limitations": [
            "VATTR is a body/dimension prior, not a direct speed estimator.",
            "Plate-scale candidate remains low-confidence without calibrated camera geometry.",
            "Final absolute km/h requires homography or measured reference.",
        ],
    }


def flatten(event: dict[str, Any], speed_004b: dict[str, Any]) -> dict[str, Any]:
    source = event.get("source") or {}
    target = event.get("target_vehicle") or {}
    vattr = speed_004b.get("vehicle_dimension_prior") or {}
    plate = speed_004b.get("plate_scale_sanity") or {}
    sanity = speed_004b.get("sanity_check") or {}
    return {
        "event_id": event.get("event_id"),
        "video": source.get("source_video"),
        "track_id": target.get("track_id"),
        "speed_mode": speed_004b.get("speed_mode"),
        "relative_label": (event.get("speed_exp_004a") or {}).get("relative_speed_label"),
        "plate_scale_kmh_geomean": plate.get("speed_kmh"),
        "plate_scale_confidence": plate.get("confidence"),
        "vattr_label": vattr.get("predicted_body_label"),
        "vattr_confidence": vattr.get("vehicle_attribute_confidence"),
        "vattr_use_for_speed_fusion": vattr.get("use_for_speed_fusion"),
        "wheelbase_m_mean": (vattr.get("prior") or {}).get("wheelbase_m_mean"),
        "fusion_confidence": speed_004b.get("fusion_confidence"),
        "sanity_decision": sanity.get("decision"),
        "warning_flags": "|".join(sanity.get("warning_flags") or []),
        "disagreement_flags": "|".join(sanity.get("disagreement_flags") or []),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_report(path: Path, rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    table = [
        "| Video | Track | Relative | Plate km/h | VATTR label | VATTR conf | Fusion conf | Warnings |",
        "|---|---:|---|---:|---|---:|---:|---|",
    ]
    for row in rows:
        table.append(
            "| {video} | {track_id} | {relative_label} | {plate_scale_kmh_geomean} | {vattr_label} | {vattr_confidence} | {fusion_confidence} | {warning_flags} |".format(
                **row
            )
        )

    content = f"""# SPEED-EXP-004B Plate-Scale + VATTR Sanity-Check

## Özet

Bu rapor `SPEED-EXP-004A` relative speed block'unu, `SPEED-EXP-002` plate-scale adayını ve
`VATTR-EXP-001` vehicle dimension prior çıktısını aynı event/evidence contract'ında birleştirir.

Sonuç: Bu aşama da **kesin km/s üretmez**. Plate-scale ve VATTR sinyalleri, relative speed
sonucunu destekleyen/çürüten yardımcı evidence olarak kullanılır.

## Inputlar

* Events: `{rel(args.events)}`
* Plate speed summary: `{rel(args.plate_speed)}`
* VATTR checkpoint: `{rel(args.checkpoint)}`
* VATTR label map: `{rel(args.label_map)}`
* VATTR dimension priors: `{rel(args.priors)}`
* Target ROI crops: `{rel(args.crop_dir)}`

## Sonuç Tablosu

{chr(10).join(table)}

## Yorum

* `speed_mode` hâlâ `relative` kalır.
* Plate-scale adayları düşük güvenlidir; mevcut sonuçlar kalibrasyon yokken mutlak hız olarak yorumlanmamalıdır.
* VATTR doğrudan hız değil, gövde tipi ve yaklaşık wheelbase/length prior sağlar.
* `candidate_disagreement_high` varsa sonraki homography/manuel review adımı önceliklendirilmelidir.

## Sonraki Adım

`SPEED-EXP-004C` için sabit kamera görüntüsünde yarı manuel homografi / ölçülü referans noktaları belirlenirse
`absolute_candidate` üretilebilir. 4B çıktısı bu adım için sanity-check katmanı olarak kalmalıdır.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--plate-speed", type=Path, default=DEFAULT_PLATE_SPEED)
    parser.add_argument("--crop-dir", type=Path, default=DEFAULT_CROP_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--label-map", type=Path, default=DEFAULT_LABEL_MAP)
    parser.add_argument("--priors", type=Path, default=DEFAULT_PRIORS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--enriched-events", type=Path, default=DEFAULT_ENRICHED_EVENTS)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--min-vattr-confidence", type=float, default=0.35)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_data = load_json(args.events)
    events = events_data.get("events") or []
    if not events:
        raise ValueError(f"No events found in {args.events}")

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model, label_names, checkpoint = load_vattr_model(args.checkpoint, args.label_map, device)
    prior_table = load_json(args.priors)
    plate_index = plate_speed_by_video(load_json(args.plate_speed))
    crop_index = event_crop_index(args.crop_dir, events)

    rows: list[dict[str, Any]] = []
    summary_events: list[dict[str, Any]] = []
    for event in events:
        event_id = event.get("event_id")
        video = (event.get("source") or {}).get("source_video")
        crop_paths = crop_index.get(event_id, [])
        vattr = predict_crops(model, label_names, crop_paths, device, args.batch_size)
        plate_candidate = plate_index.get(video)
        speed_004b = make_speed_004b(event, vattr, prior_table, plate_candidate, args.min_vattr_confidence)
        event["speed_exp_004b"] = speed_004b
        event["speed"]["fusion_confidence"] = speed_004b["fusion_confidence"]
        event["speed"]["candidate_count"] = len(speed_004b["candidate_speeds"])
        event["speed"]["warning_flags"] = sorted(
            set((event.get("speed") or {}).get("warning_flags") or []) | set(speed_004b["sanity_check"]["warning_flags"])
        )
        rows.append(flatten(event, speed_004b))
        summary_events.append(
            {
                "event_id": event_id,
                "video": video,
                "track_id": (event.get("target_vehicle") or {}).get("track_id"),
                "speed_exp_004b": speed_004b,
            }
        )

    output_dir = args.output_dir
    summary_path = output_dir / "speed_exp_004b_plate_vattr_sanity_summary.json"
    csv_path = output_dir / "speed_exp_004b_plate_vattr_sanity_summary.csv"
    summary = {
        "generated_at_utc": now_utc(),
        "experiment_id": "SPEED-EXP-004B",
        "purpose": "plate_scale_and_vehicle_dimension_prior_sanity_check",
        "input_event_json": rel(args.events),
        "source_plate_speed_summary": rel(args.plate_speed),
        "vattr_checkpoint": rel(args.checkpoint),
        "vattr_checkpoint_drive_id": "1tQVq24gKbbhODVqBYG7fG9g-0GYZgHt9",
        "event_count": len(summary_events),
        "events": summary_events,
        "limitations": [
            "No final km/h claim.",
            "VATTR is a body/dimension prior signal.",
            "Plate-scale candidate is low-confidence without homography/calibration.",
        ],
    }
    events_data["generated_at_utc"] = now_utc()
    events_data["event_stage"] = "speed_exp_004b_plate_vattr_sanity"
    events_data["source_event_stage"] = "speed_exp_004a_relative_track_bbox"
    events_data["speed_experiment_id"] = "SPEED-EXP-004B"

    write_json(summary_path, summary)
    write_csv(csv_path, rows)
    write_json(args.enriched_events, events_data)
    make_report(args.report, rows, args)

    print(f"Device: {device}")
    print(f"Checkpoint backbone: {checkpoint.get('backbone')}")
    print(f"Wrote summary: {rel(summary_path)}")
    print(f"Wrote csv: {rel(csv_path)}")
    print(f"Wrote enriched events: {rel(args.enriched_events)}")
    print(f"Wrote report: {rel(args.report)}")
    for row in rows:
        print(
            f"{row['video']} {row['track_id']} relative={row['relative_label']} "
            f"plate_kmh={row['plate_scale_kmh_geomean']} vattr={row['vattr_label']} "
            f"vattr_conf={row['vattr_confidence']} fusion_conf={row['fusion_confidence']}"
        )


if __name__ == "__main__":
    main()
