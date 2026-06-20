#!/usr/bin/env python3
"""SPEED-EXP-005D candidate fusion.

This script closes the current speed-estimation track by fusing:
  * SPEED-EXP-004A relative track/bbox motion
  * SPEED-EXP-002 plate-scale XYZ candidate
  * SPEED-EXP-005A bbox-geometry automatic candidate

The output is still not a legal/final km/h measurement. It is a conservative
decision-support speed block that can support risk/evidence and slalom analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004b.json"
DEFAULT_RELATIVE_SUMMARY = (
    ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-004A-relative-track-bbox" / "speed_exp_004a_relative_track_speed_summary.json"
)
DEFAULT_PLATE_SUMMARY = (
    ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-002-plate-bbox-xyz" / "speed_exp_002_plate_bbox_xyz_summary.json"
)
DEFAULT_BBOX_SUMMARY = (
    ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-005A-bbox-geometry-auto" / "speed_exp_005a_bbox_geometry_summary.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-005D-candidate-fusion"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "speed_exp_005d_candidate_fusion.md"
DEFAULT_ENRICHED_EVENTS = (
    ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed005d.json"
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


def round_or_none(value: float | int | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def index_relative(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["video"]: row["speed_exp_004a"] for row in summary.get("events", [])}


def index_plate(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in summary.get("videos", []):
        variants = row.get("variants") or {}
        geomean = (variants.get("geomean") or {}).get("summary") or {}
        indexed[row["video"]] = {
            "source": "plate_scale_geomean",
            "speed_kmh": geomean.get("median_speed_kmh"),
            "mean_speed_kmh": geomean.get("mean_speed_kmh"),
            "confidence": 0.28 if "low_" in str(geomean.get("confidence_note")) else 0.45,
            "confidence_note": geomean.get("confidence_note"),
            "usable_measurement_count": row.get("usable_measurement_count"),
            "plate_aspect_ratio_median": row.get("plate_aspect_ratio_median"),
            "full_frame_plate_bbox_available": row.get("full_frame_plate_bbox_available"),
        }
    return indexed


def index_bbox(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in summary.get("videos", []):
        candidate = row.get("bbox_geometry_candidate") or {}
        indexed[row["video"]] = {
            "source": "bbox_geometry_auto",
            "speed_kmh": candidate.get("estimated_kmh"),
            "speed_range_kmh": candidate.get("speed_range_kmh"),
            "confidence": candidate.get("confidence"),
            "estimated_kmh_method": candidate.get("estimated_kmh_method"),
            "quality_flags": candidate.get("quality_flags") or [],
            "warning_flags": candidate.get("warning_flags") or [],
            "failure_flags": candidate.get("failure_flags") or [],
            "diagnostics": candidate.get("diagnostics") or {},
            "plot_uri": row.get("plot_uri"),
        }
    return indexed


def agreement_ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    denom = max(abs(a), abs(b), 1.0)
    return abs(a - b) / denom


def relative_support(relative_label: str | None, speed_kmh: float | None) -> bool:
    if speed_kmh is None or relative_label in {None, "unavailable", "unstable"}:
        return False
    if relative_label == "fast":
        return speed_kmh >= 8.0
    if relative_label in {"slow", "normal"}:
        return speed_kmh < 8.0
    return True


def fused_confidence(
    bbox_conf: float,
    plate_conf: float,
    relative_conf: float,
    agreement: float | None,
    relative_ok: bool,
) -> float:
    confidence = 0.20
    confidence += 0.38 * max(0.0, min(1.0, bbox_conf))
    confidence += 0.12 * max(0.0, min(1.0, plate_conf))
    confidence += 0.10 * max(0.0, min(1.0, relative_conf))
    if agreement is not None:
        confidence += 0.13 * max(0.0, min(1.0, 1.0 - agreement / 0.45))
    if relative_ok:
        confidence += 0.07
    return round(max(0.0, min(0.72, confidence)), 4)


def make_fusion(video: str, relative: dict[str, Any], plate: dict[str, Any], bbox: dict[str, Any], max_agreement_ratio: float) -> dict[str, Any]:
    bbox_speed = bbox.get("speed_kmh")
    plate_speed = plate.get("speed_kmh")
    relative_label = relative.get("relative_speed_label")
    relative_conf = float(relative.get("fusion_confidence") or 0.0)
    bbox_conf = float(bbox.get("confidence") or 0.0)
    plate_conf = float(plate.get("confidence") or 0.0)
    agreement = agreement_ratio(bbox_speed, plate_speed)
    relative_ok = relative_support(relative_label, bbox_speed)

    candidate_speeds = [
        {
            "source": "bbox_geometry_auto",
            "speed_kmh": round_or_none(bbox_speed),
            "speed_range_kmh": bbox.get("speed_range_kmh"),
            "confidence": round_or_none(bbox_conf, 4),
            "warnings": bbox.get("warning_flags") or [],
        },
        {
            "source": "plate_scale_geomean",
            "speed_kmh": round_or_none(plate_speed),
            "confidence": round_or_none(plate_conf, 4),
            "confidence_note": plate.get("confidence_note"),
        },
        {
            "source": "relative_track_bbox",
            "speed_kmh": None,
            "relative_speed_score": relative.get("relative_speed_score"),
            "relative_speed_label": relative_label,
            "confidence": round_or_none(relative_conf, 4),
        },
    ]

    warning_flags = [
        "not_for_legal_enforcement",
        "approximate_monocular_speed",
        "no_ground_truth_speed",
    ]
    quality_flags: list[str] = []
    failure_flags: list[str] = []
    decision = "fallback_relative"
    speed_mode = "relative"
    primary_source = "relative_track_bbox"
    estimated_kmh = None
    speed_range = [None, None]
    fallback_reason = "absolute_candidate_not_promoted"

    if bbox_speed is not None:
        quality_flags.append("bbox_geometry_candidate_available")
    else:
        failure_flags.append("bbox_geometry_unavailable")
    if plate_speed is not None:
        quality_flags.append("plate_scale_candidate_available")
    else:
        warning_flags.append("plate_scale_unavailable")
    if relative_label not in {None, "unavailable"}:
        quality_flags.append("relative_track_signal_available")

    if agreement is not None and agreement <= max_agreement_ratio:
        quality_flags.append("bbox_plate_candidates_agree")
    elif agreement is not None:
        warning_flags.append("candidate_disagreement_high")

    if relative_ok:
        quality_flags.append("relative_label_supports_bbox_candidate")
    else:
        warning_flags.append("relative_label_not_supportive_or_unavailable")

    if bbox_speed is not None and agreement is not None and agreement <= max_agreement_ratio and relative_ok:
        decision = "use_bbox_geometry_with_plate_relative_support"
        speed_mode = "approximate_candidate"
        primary_source = "bbox_geometry_auto"
        estimated_kmh = bbox_speed
        speed_range = bbox.get("speed_range_kmh") or [None, None]
        fallback_reason = None
    elif bbox_speed is not None and relative_ok:
        decision = "use_bbox_geometry_low_support"
        speed_mode = "approximate_candidate"
        primary_source = "bbox_geometry_auto"
        estimated_kmh = bbox_speed
        speed_range = bbox.get("speed_range_kmh") or [None, None]
        fallback_reason = "plate_candidate_disagreement_or_missing"

    confidence = fused_confidence(bbox_conf, plate_conf, relative_conf, agreement, relative_ok)
    if decision == "fallback_relative":
        confidence = round(min(confidence, relative_conf), 4)

    slalom_candidate = bool(relative_label == "fast" and relative.get("bbox_motion_jitter_score", 0) and relative.get("bbox_motion_jitter_score", 0) > 1.0)

    return {
        "experiment_id": "SPEED-EXP-005D",
        "video": video,
        "speed_mode": speed_mode,
        "primary_speed_source": primary_source,
        "estimated_kmh": round_or_none(estimated_kmh),
        "speed_range_kmh": speed_range,
        "relative_speed_label": relative_label,
        "relative_speed_score": relative.get("relative_speed_score"),
        "fusion_confidence": confidence,
        "decision": decision,
        "fallback_reason": fallback_reason,
        "candidate_agreement": {
            "bbox_vs_plate_relative_diff_ratio": round_or_none(agreement),
            "max_allowed_ratio": max_agreement_ratio,
            "relative_label_supports_candidate": relative_ok,
        },
        "candidate_speeds": candidate_speeds,
        "slalom_support": {
            "slalom_candidate": slalom_candidate,
            "source": "relative_track_bbox",
            "note": "Only a support signal for the FTR sofor_eylemi/slalom label; not a final action detector.",
        },
        "quality_flags": quality_flags,
        "warning_flags": warning_flags,
        "failure_flags": failure_flags,
        "limitations": [
            "No ground-truth speed is available for these videos.",
            "The km/h value is approximate and must not be used for legal enforcement.",
            "Camera FOV, vehicle dimensions and plate geometry are assumed priors.",
            "FTR results.json does not require a speed field; this block is support evidence.",
        ],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "video",
        "track_id",
        "speed_mode",
        "primary_speed_source",
        "estimated_kmh",
        "speed_range_min_kmh",
        "speed_range_max_kmh",
        "relative_speed_label",
        "relative_speed_score",
        "bbox_speed_kmh",
        "plate_speed_kmh",
        "agreement_ratio",
        "fusion_confidence",
        "decision",
        "fallback_reason",
        "warning_flags",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            fusion = row["speed_exp_005d"]
            candidates = {c["source"]: c for c in fusion["candidate_speeds"]}
            speed_range = fusion.get("speed_range_kmh") or [None, None]
            writer.writerow(
                {
                    "video": row["video"],
                    "track_id": row["track_id"],
                    "speed_mode": fusion["speed_mode"],
                    "primary_speed_source": fusion["primary_speed_source"],
                    "estimated_kmh": fusion.get("estimated_kmh"),
                    "speed_range_min_kmh": speed_range[0],
                    "speed_range_max_kmh": speed_range[1],
                    "relative_speed_label": fusion.get("relative_speed_label"),
                    "relative_speed_score": fusion.get("relative_speed_score"),
                    "bbox_speed_kmh": candidates.get("bbox_geometry_auto", {}).get("speed_kmh"),
                    "plate_speed_kmh": candidates.get("plate_scale_geomean", {}).get("speed_kmh"),
                    "agreement_ratio": fusion["candidate_agreement"].get("bbox_vs_plate_relative_diff_ratio"),
                    "fusion_confidence": fusion.get("fusion_confidence"),
                    "decision": fusion.get("decision"),
                    "fallback_reason": fusion.get("fallback_reason"),
                    "warning_flags": ",".join(fusion.get("warning_flags") or []),
                }
            )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# SPEED-EXP-005D Candidate Fusion",
        "",
        "Bu rapor, hız modülünü mevcut proje fazı için kapatmak amacıyla 004A relative, 002 plate-scale ve 005A bbox-geometry adaylarını tek karar ağacında birleştirir.",
        "",
        "## Kritik Not",
        "",
        "* Bu çıktı hukuki/final hız ölçümü değildir.",
        "* FTR `results.json` şeması hız alanı istemediği için bu modül submission ana çıktısı değildir.",
        "* Hız bloğu yalnız risk/evidence ve `slalom` destek sinyali olarak kullanılmalıdır.",
        "",
        "## Konfigürasyon",
        "",
        f"* Relative source: `{summary['sources']['relative_summary']}`",
        f"* Plate source: `{summary['sources']['plate_summary']}`",
        f"* BBox geometry source: `{summary['sources']['bbox_geometry_summary']}`",
        f"* Max agreement ratio: `{summary['settings']['max_agreement_ratio']}`",
        "",
        "## Final Hız Kararı",
        "",
        "| Video | Track | Mode | Primary | km/h | Range | Relative | Plate km/h | Agreement | Conf | Decision |",
        "|---|---|---|---|---:|---|---|---:|---:|---:|---|",
    ]
    for row in summary["events"]:
        fusion = row["speed_exp_005d"]
        candidates = {c["source"]: c for c in fusion["candidate_speeds"]}
        speed_range = fusion.get("speed_range_kmh") or [None, None]
        range_text = "-"
        if speed_range[0] is not None and speed_range[1] is not None:
            range_text = f"{speed_range[0]:.2f}-{speed_range[1]:.2f}"
        lines.append(
            f"| `{row['video']}` | `{row['track_id']}` | `{fusion['speed_mode']}` | `{fusion['primary_speed_source']}` | "
            f"{fusion.get('estimated_kmh') if fusion.get('estimated_kmh') is not None else '-'} | "
            f"{range_text} | `{fusion.get('relative_speed_label')}` | "
            f"{candidates.get('plate_scale_geomean', {}).get('speed_kmh') if candidates.get('plate_scale_geomean', {}).get('speed_kmh') is not None else '-'} | "
            f"{fusion['candidate_agreement'].get('bbox_vs_plate_relative_diff_ratio')} | "
            f"{fusion.get('fusion_confidence')} | `{fusion.get('decision')}` |"
        )
    lines.extend(
        [
            "",
            "## Yorum",
            "",
            "* `video_1` ve `video_2` düşük hız/normal hareket sınıfında kalır.",
            "* `video_3` hem relative fast hem de bbox/plate adaylarıyla daha hızlı aday üretir.",
            "* Bu kapanış sonrası hız modülü ana FTR geliştirme yolunu bloklamamalıdır.",
            "* Sonraki FTR odağı `arac_bilgisi` ve `tespitler` üretimidir.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--relative-summary", type=Path, default=DEFAULT_RELATIVE_SUMMARY)
    parser.add_argument("--plate-summary", type=Path, default=DEFAULT_PLATE_SUMMARY)
    parser.add_argument("--bbox-summary", type=Path, default=DEFAULT_BBOX_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--enriched-events", type=Path, default=DEFAULT_ENRICHED_EVENTS)
    parser.add_argument("--max-agreement-ratio", type=float, default=0.45)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_doc = load_json(args.events)
    events = deepcopy(events_doc.get("events") or [])
    relative_idx = index_relative(load_json(args.relative_summary))
    plate_idx = index_plate(load_json(args.plate_summary))
    bbox_idx = index_bbox(load_json(args.bbox_summary))

    rows: list[dict[str, Any]] = []
    for event in events:
        video = (event.get("source") or {}).get("source_video")
        if not video:
            continue
        fusion = make_fusion(
            video=video,
            relative=relative_idx.get(video, {}),
            plate=plate_idx.get(video, {}),
            bbox=bbox_idx.get(video, {}),
            max_agreement_ratio=args.max_agreement_ratio,
        )
        event["speed_exp_005d"] = fusion
        event["speed"] = {
            "status": "ok" if fusion["speed_mode"] != "relative" else "low_confidence",
            "mode": fusion["speed_mode"],
            "estimated_kmh": fusion.get("estimated_kmh"),
            "relative_motion_score": fusion.get("relative_speed_score"),
            "motion_anomaly": fusion.get("relative_speed_label"),
            "calibration_profile_id": None,
            "confidence": fusion.get("fusion_confidence"),
            "primary_speed_source": fusion.get("primary_speed_source"),
            "fallback_reason": fusion.get("fallback_reason"),
            "warning_flags": fusion.get("warning_flags"),
            "not_for_legal_enforcement": True,
            "ftr_submission_note": "Speed is not a required field in FTR results.json; support evidence only.",
        }
        rows.append(
            {
                "event_id": event.get("event_id"),
                "video": video,
                "track_id": (event.get("target_vehicle") or {}).get("track_id"),
                "speed_exp_005d": fusion,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "speed_exp_005d_candidate_fusion_summary.json"
    csv_path = args.output_dir / "speed_exp_005d_candidate_fusion_summary.csv"
    summary = {
        "generated_at_utc": now_utc(),
        "experiment_id": "SPEED-EXP-005D",
        "purpose": "Conservative fusion of existing speed candidates for support evidence.",
        "sources": {
            "events": rel(args.events),
            "relative_summary": rel(args.relative_summary),
            "plate_summary": rel(args.plate_summary),
            "bbox_geometry_summary": rel(args.bbox_summary),
        },
        "settings": {
            "max_agreement_ratio": args.max_agreement_ratio,
        },
        "event_count": len(rows),
        "events": rows,
        "summary_csv": rel(csv_path),
        "enriched_events": rel(args.enriched_events),
        "limitations": [
            "No ground-truth speed is available.",
            "This is not a legal/final speed measurement.",
            "FTR submission schema does not require speed.",
        ],
    }
    write_json(summary_path, summary)
    write_csv(csv_path, rows)
    write_report(args.report, summary)

    events_doc["events"] = events
    events_doc["speed_experiment_id"] = "SPEED-EXP-005D"
    events_doc["speed_experiment_note"] = "Candidate fusion support evidence; not required by FTR results.json."
    write_json(args.enriched_events, events_doc)
    print(
        json.dumps(
            {
                "summary": rel(summary_path),
                "csv": rel(csv_path),
                "report": rel(args.report),
                "enriched_events": rel(args.enriched_events),
                "events": len(rows),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
