#!/usr/bin/env python3
"""Promote cabin face/role evidence into a dedicated driver detection module.

This script does not run driver action recognition. It turns the selected
``CABIN-EXP-004`` face/occupant summary into a smaller driver-presence contract
that downstream phone, smoking, seatbelt, passenger, and action modules can
consume.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ID = "DRIVER-EXP-001"
EXPERIMENT_NAME = "yunet_view_policy_driver_presence_v1"

DEFAULT_EVENTS = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json"
)
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_MODULE_ARTIFACT_DIR = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "driver_detection"
    / f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"
)
DEFAULT_REPORT = ROOT / "testing" / "reports" / "driver_exp_001_driver_detection_summary.md"
DEFAULT_COMPARISON = ROOT / "models" / "benchmarks" / "cabin" / "driver_detection_baseline_comparison.csv"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def video_name(event: dict[str, Any]) -> str | None:
    return (event.get("source") or {}).get("source_video")


def cabin_index(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["video"]): item
        for item in summary.get("videos", [])
        if item.get("video")
    }


def score_driver_confidence(temporal: dict[str, Any], detected: bool) -> float | None:
    if not detected:
        return None
    visibility_score = float(temporal.get("mean_visibility_score") or 0.0)
    temporal_detection = float(temporal.get("temporal_detection_rate") or 0.0)
    driver_rate = float(temporal.get("driver_candidate_rate") or 0.0)
    score = 0.45 * driver_rate + 0.35 * temporal_detection + 0.20 * visibility_score
    return round(max(0.0, min(1.0, score)), 4)


def driver_detection_status(video_summary: dict[str, Any] | None) -> tuple[str, bool | None, str | None]:
    if not video_summary or video_summary.get("status") != "completed":
        return "not_run", None, "cabin_summary_not_available"

    temporal = video_summary.get("temporal") or {}
    visibility = temporal.get("visibility")
    role_status = str(temporal.get("role_assignment_status") or "")
    driver_detected = temporal.get("driver_candidate_detected")

    if visibility == "not_visible":
        return "not_visible", None, "cabin_not_visible"
    if visibility == "poor":
        return "not_evaluable", None, "cabin_visibility_poor"
    if role_status and not role_status.startswith("assigned_"):
        if int(temporal.get("occupant_count_estimate") or 0) > 0:
            return "ambiguous", None, role_status
        return "not_detected", False, role_status or "no_role_assignment"
    if driver_detected is True:
        return "detected", True, None
    if driver_detected is False:
        return "not_detected", False, "driver_candidate_temporal_gate_failed"
    return "unknown", None, "driver_candidate_unknown"


def build_driver_detection(
    video_summary: dict[str, Any] | None,
    cabin_summary: dict[str, Any],
) -> dict[str, Any]:
    temporal = (video_summary or {}).get("temporal") or {}
    status, detected, failure_reason = driver_detection_status(video_summary)
    occupant_count = temporal.get("occupant_count_estimate")
    passenger_count = None
    if detected is True and isinstance(occupant_count, int):
        passenger_count = max(0, occupant_count - 1)
    confidence = score_driver_confidence(temporal, detected is True)

    return {
        "experiment_id": EXPERIMENT_ID,
        "module": "driver_detection",
        "status": status,
        "driver_present": detected,
        "confidence": confidence,
        "risk_enabled": False,
        "action_enabled": False,
        "failure_reason": failure_reason,
        "view_profile": (video_summary or {}).get("view_profile"),
        "cabin_visibility": temporal.get("visibility") or "unknown",
        "cabin_visibility_score": temporal.get("mean_visibility_score"),
        "face_count": temporal.get("occupant_count_estimate"),
        "occupant_count_estimate": occupant_count,
        "passenger_count": passenger_count,
        "driver_candidate_rate": temporal.get("driver_candidate_rate"),
        "temporal_detection_rate": temporal.get("temporal_detection_rate"),
        "raw_face_detection_rate": temporal.get("raw_face_detection_rate"),
        "longest_eligible_face_miss_run": temporal.get("longest_eligible_face_miss_run"),
        "role_assignment_status": temporal.get("role_assignment_status"),
        "best_frame": temporal.get("best_frame"),
        "source_roi_uri": temporal.get("best_roi_uri"),
        "annotated_video_uri": (video_summary or {}).get("annotated_video"),
        "source_cabin_experiment_id": cabin_summary.get("experiment_id"),
        "model_version": cabin_summary.get("model_key"),
        "decision_note": (
            "Driver detection is a presence/role-assignment signal only. "
            "It does not infer phone, smoking, seatbelt, fatigue, or legal risk."
        ),
    }


def enrich_event(
    event: dict[str, Any],
    video_summary: dict[str, Any] | None,
    cabin_summary: dict[str, Any],
    output_name: str,
) -> dict[str, Any]:
    enriched = json.loads(json.dumps(event))
    driver_detection = build_driver_detection(video_summary, cabin_summary)
    enriched["driver_detection"] = driver_detection

    driver_cabin = enriched.get("driver_cabin") or {}
    driver_cabin.update(
        {
            "status": "ok" if driver_detection["status"] == "detected" else driver_detection["status"],
            "visibility": driver_detection["cabin_visibility"],
            "driver_detected": driver_detection["driver_present"],
            "passenger_count": driver_detection["passenger_count"],
            "phone_risk": driver_cabin.get("phone_risk"),
            "seatbelt_status": driver_cabin.get("seatbelt_status") or "unknown",
            "confidence": driver_detection["confidence"],
            "failure_reason": driver_detection["failure_reason"],
            "visibility_score": driver_detection["cabin_visibility_score"],
            "occupant_count_estimate": driver_detection["occupant_count_estimate"],
            "driver_candidate_detected": driver_detection["driver_present"],
            "role_assignment_status": driver_detection["role_assignment_status"],
            "temporal_detection_rate": driver_detection["temporal_detection_rate"],
            "best_frame": driver_detection["best_frame"],
            "source_roi_uri": driver_detection["source_roi_uri"],
            "model_version": driver_detection["model_version"],
        }
    )
    enriched["driver_cabin"] = driver_cabin

    models = enriched.get("models") or {}
    models["driver_detection"] = f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"
    models["cabin_face_detector"] = str(cabin_summary.get("model_key") or "unknown")
    enriched["models"] = models

    routing = enriched.get("routing_decision") or {}
    experts = list(routing.get("experts_called") or [])
    if "Driver Detection" not in experts:
        experts.append("Driver Detection")
    reasons = list(routing.get("routing_reasons") or [])
    reasons.append(
        "driver_presence_detected"
        if driver_detection["status"] == "detected"
        else f"driver_presence_{driver_detection['status']}"
    )
    routing["experts_called"] = experts
    routing["routing_reasons"] = reasons
    routing["driver_detection_status"] = driver_detection["status"]
    enriched["routing_decision"] = routing

    evidence = enriched.get("evidence") or {}
    evidence["json_uri"] = f"models/benchmarks/artifacts/{output_name}"
    evidence["driver_detection"] = {
        "status": driver_detection["status"],
        "driver_present": driver_detection["driver_present"],
        "confidence": driver_detection["confidence"],
        "view_profile": driver_detection["view_profile"],
        "roi_uri": driver_detection["source_roi_uri"],
        "annotated_video_uri": driver_detection["annotated_video_uri"],
        "model_version": driver_detection["model_version"],
    }
    evidence["metadata_completeness_score"] = round(
        min(1.0, float(evidence.get("metadata_completeness_score") or 0.0) + 0.04),
        3,
    )
    enriched["evidence"] = evidence

    explanation = enriched.get("explanation") or {}
    explanation["technical_summary"] = (
        f"{explanation.get('technical_summary', '').rstrip()} "
        f"Driver detection status={driver_detection['status']}, "
        f"view_profile={driver_detection['view_profile']}, "
        f"driver_present={driver_detection['driver_present']}. "
        "No driver action decision was produced."
    ).strip()
    enriched["explanation"] = explanation
    return enriched


def summarize_videos(video_items: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(item["driver_detection"]["status"] for item in video_items)
    detected = sum(1 for item in video_items if item["driver_detection"]["driver_present"] is True)
    confidences = [
        item["driver_detection"]["confidence"]
        for item in video_items
        if item["driver_detection"]["confidence"] is not None
    ]
    return {
        "video_count": len(video_items),
        "status_counts": dict(statuses),
        "driver_detected_video_count": detected,
        "mean_driver_confidence": round(sum(confidences) / len(confidences), 4)
        if confidences
        else None,
    }


def build_module_summary(
    events: list[dict[str, Any]],
    cabin_summary: dict[str, Any],
) -> dict[str, Any]:
    video_items = []
    for event in events:
        driver_detection = event.get("driver_detection") or {}
        driver_cabin = event.get("driver_cabin") or {}
        video_items.append(
            {
                "video": video_name(event),
                "event_id": event.get("event_id"),
                "track_id": (event.get("target_vehicle") or {}).get("track_id"),
                "driver_detection": driver_detection,
                "driver_cabin": {
                    "visibility": driver_cabin.get("visibility"),
                    "driver_detected": driver_cabin.get("driver_detected"),
                    "occupant_count_estimate": driver_cabin.get("occupant_count_estimate"),
                    "passenger_count": driver_cabin.get("passenger_count"),
                },
            }
        )
    return {
        "experiment_id": EXPERIMENT_ID,
        "experiment_name": EXPERIMENT_NAME,
        "stage": "driver_detection_event_enrichment",
        "created_at_utc": now_utc(),
        "source_cabin_experiment_id": cabin_summary.get("experiment_id"),
        "source_cabin_model": cabin_summary.get("model_key"),
        "risk_enabled": False,
        "action_enabled": False,
        "aggregate": summarize_videos(video_items),
        "videos": video_items,
    }


def build_report(
    events_path: Path,
    cabin_summary_path: Path,
    output_event_path: Path,
    module_summary: dict[str, Any],
) -> str:
    rows = []
    for item in module_summary.get("videos", []):
        driver = item.get("driver_detection") or {}
        rows.append(
            f"| {item.get('video')} | {item.get('event_id')} | {item.get('track_id')} | "
            f"{driver.get('status')} | {driver.get('driver_present')} | "
            f"{driver.get('confidence')} | {driver.get('view_profile')} | "
            f"{driver.get('occupant_count_estimate')} | {driver.get('passenger_count')} | "
            f"{driver.get('failure_reason')} |"
        )
    aggregate = module_summary.get("aggregate") or {}
    return "\n".join(
        [
            "# DRIVER-EXP-001 Driver Detection Summary",
            "",
            f"Tarih: {module_summary.get('created_at_utc')}",
            "",
            "## Amaç",
            "",
            "Bu modül sürücü eylemi tanımaz. Yalnız hedef araç içinde sürücü adayı "
            "var mı, rol ataması güvenilir mi ve sonraki driver-action uzmanları "
            "çalıştırılabilir mi sorusuna cevap verir.",
            "",
            "## Kaynaklar",
            "",
            f"* Input events: `{rel(events_path)}`",
            f"* Cabin summary: `{rel(cabin_summary_path)}`",
            f"* Enriched event JSON: `{rel(output_event_path)}`",
            "",
            "## Aggregate",
            "",
            f"* Video count: `{aggregate.get('video_count')}`",
            f"* Status counts: `{aggregate.get('status_counts')}`",
            f"* Driver detected video count: `{aggregate.get('driver_detected_video_count')}`",
            f"* Mean driver confidence: `{aggregate.get('mean_driver_confidence')}`",
            "",
            "## Video Sonuçları",
            "",
            "| Video | Event ID | Track | Status | Driver | Conf | View | Occupants | Passengers | Failure |",
            "|---|---|---|---|---|---:|---|---:|---:|---|",
            *rows,
            "",
            "## Karar",
            "",
            "`DRIVER-EXP-001`, mevcut faz için driver presence / role-assignment "
            "modülü olarak kabul edilebilir. Çıktı action, phone, smoking, seatbelt "
            "veya hukuki risk kararı değildir; yalnız sonraki uzman modellerin "
            "çalıştırılması için gate/evidence sinyalidir.",
        ]
    )


def update_comparison(path: Path, module_summary: dict[str, Any]) -> None:
    aggregate = module_summary.get("aggregate") or {}
    row = {
        "experiment_id": EXPERIMENT_ID,
        "model": EXPERIMENT_NAME,
        "status": "selected_presence_gate",
        "video_count": aggregate.get("video_count"),
        "driver_detected_video_count": aggregate.get("driver_detected_video_count"),
        "mean_driver_confidence": aggregate.get("mean_driver_confidence"),
        "risk_enabled": False,
        "action_enabled": False,
        "decision": "selected",
        "notes": "Dedicated driver presence contract extracted from CABIN-EXP-004 YuNet view-profile policy.",
    }
    header = list(row)
    lines = [",".join(header), ",".join(str(row[key]) for key in header)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create DRIVER-EXP-001 driver detection enrichment.")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--module-artifact-dir", type=Path, default=DEFAULT_MODULE_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_path = args.events.resolve()
    cabin_summary_path = args.cabin_summary.resolve()
    if not events_path.exists():
        raise SystemExit(f"Input events not found: {events_path}")
    if not cabin_summary_path.exists():
        raise SystemExit(f"Cabin summary not found: {cabin_summary_path}")

    events_data = load_json(events_path)
    cabin_summary = load_json(cabin_summary_path)
    index = cabin_index(cabin_summary)
    output_name = f"{events_path.stem}-driver-detection.json"
    enriched_events = [
        enrich_event(
            event,
            index.get(video_name(event) or ""),
            cabin_summary,
            output_name,
        )
        for event in events_data.get("events", [])
    ]
    output = {
        **{key: value for key, value in events_data.items() if key != "events"},
        "source_event_stage": events_data.get("event_stage"),
        "event_stage": "driver_detection_enriched_event_skeleton",
        "driver_detection_experiment_id": EXPERIMENT_ID,
        "driver_detection_experiment_name": EXPERIMENT_NAME,
        "created_at_utc": now_utc(),
        "events": enriched_events,
    }

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.module_artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    output_event_path = args.artifact_dir / output_name
    output_event_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    module_summary = build_module_summary(enriched_events, cabin_summary)
    module_summary_path = args.module_artifact_dir / "driver_exp_001_driver_detection_summary.json"
    module_summary_path.write_text(
        json.dumps(module_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(
        build_report(events_path, cabin_summary_path, output_event_path, module_summary) + "\n",
        encoding="utf-8",
    )
    update_comparison(args.comparison, module_summary)
    print(f"Wrote enriched events: {output_event_path}")
    print(f"Wrote module summary: {module_summary_path}")
    print(f"Wrote report: {args.report.resolve()}")
    print(f"Wrote comparison: {args.comparison.resolve()}")


if __name__ == "__main__":
    main()
