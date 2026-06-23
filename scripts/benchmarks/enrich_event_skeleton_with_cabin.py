#!/usr/bin/env python3
"""Attach selected cabin baseline outputs to plate-enriched event skeletons."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
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
DEFAULT_REPORT = ROOT / "testing" / "reports" / "cabin_exp_003_event_enrichment_summary.md"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def video_name(event: dict[str, Any]) -> str | None:
    return (event.get("source") or {}).get("source_video")


def build_index(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["video"]): item
        for item in summary.get("videos", [])
        if item.get("video")
    }


def cabin_status(video_summary: dict[str, Any] | None) -> tuple[str, str | None]:
    if not video_summary or video_summary.get("status") != "completed":
        return "not_run", "cabin_summary_not_available"
    temporal = video_summary.get("temporal") or {}
    visibility = temporal.get("visibility")
    if visibility == "not_visible":
        return "not_visible", "cabin_not_visible"
    if visibility == "poor":
        return "visibility_poor", "cabin_visibility_poor"
    return "ok", None


def enrich_event(
    event: dict[str, Any],
    video_summary: dict[str, Any] | None,
    cabin_summary: dict[str, Any],
    output_name: str,
) -> dict[str, Any]:
    enriched = json.loads(json.dumps(event))
    temporal = (video_summary or {}).get("temporal") or {}
    status, failure_reason = cabin_status(video_summary)
    visibility = temporal.get("visibility") or "not_visible"
    driver_detected = temporal.get("driver_candidate_detected")
    role_status = temporal.get("role_assignment_status")
    if not str(role_status or "").startswith("assigned_"):
        driver_detected = None
    occupant_count = temporal.get("occupant_count_estimate")
    passenger_count = None
    if driver_detected is True and isinstance(occupant_count, int):
        passenger_count = max(0, occupant_count - 1)

    enriched["driver_cabin"] = {
        "status": status,
        "visibility": visibility,
        "driver_detected": driver_detected,
        "passenger_count": passenger_count,
        "phone_risk": None,
        "seatbelt_status": "unknown",
        "confidence": temporal.get("mean_visibility_score"),
        "failure_reason": failure_reason,
        "visibility_score": temporal.get("mean_visibility_score"),
        "visibility_reasons": sorted(
            ((video_summary or {}).get("visibility_reason_counts") or {}).keys()
        ),
        "face_count": occupant_count,
        "occupant_count_estimate": occupant_count,
        "driver_candidate_detected": driver_detected,
        "role_assignment_status": role_status,
        "temporal_detection_rate": temporal.get("temporal_detection_rate"),
        "best_frame": temporal.get("best_frame"),
        "source_roi_uri": temporal.get("best_roi_uri"),
        "model_version": cabin_summary.get("model_key"),
    }

    models = enriched.get("models") or {}
    models["cabin_visibility"] = "opencv_quality_gate_v1"
    models["cabin_face_detector"] = cabin_summary.get("model_key")
    models["cabin_role_policy"] = "view_profile_temporal_v1"
    enriched["models"] = models

    routing = enriched.get("routing_decision") or {}
    experts = list(routing.get("experts_called") or [])
    if "Cabin Driver" not in experts:
        experts.append("Cabin Driver")
    reasons = list(routing.get("routing_reasons") or [])
    reasons.append(
        "cabin_visibility_gate_passed"
        if status == "ok"
        else "cabin_visibility_gate_rejected"
    )
    routing["experts_called"] = experts
    routing["routing_reasons"] = reasons
    routing["selected_cabin_model"] = cabin_summary.get("model_key")
    routing["cabin_view_profile"] = (video_summary or {}).get("view_profile")
    enriched["routing_decision"] = routing

    evidence = enriched.get("evidence") or {}
    evidence["json_uri"] = f"models/benchmarks/artifacts/{output_name}"
    evidence["cabin_roi_uri"] = temporal.get("best_roi_uri")
    evidence["cabin_overlay_video_uri"] = (video_summary or {}).get("annotated_video")
    evidence["driver_cabin"] = {
        "visibility": visibility,
        "visibility_score": temporal.get("mean_visibility_score"),
        "occupant_count_estimate": temporal.get("occupant_count_estimate"),
        "driver_candidate_detected": driver_detected,
        "role_assignment_status": role_status,
        "temporal_detection_rate": temporal.get("temporal_detection_rate"),
        "phone_risk_status": "not_run",
        "seatbelt_status": "unknown",
    }
    evidence["metadata_completeness_score"] = round(
        min(1.0, float(evidence.get("metadata_completeness_score") or 0.0) + 0.06),
        3,
    )
    enriched["evidence"] = evidence

    explanation = enriched.get("explanation") or {}
    occupant = temporal.get("occupant_count_estimate")
    explanation["technical_summary"] = (
        f"{explanation.get('technical_summary', '').rstrip()} "
        f"Cabin visibility={visibility}, occupant_count={occupant}, "
        f"driver_candidate={driver_detected}, role_status={role_status}. "
        "Phone and seatbelt analysis were not run."
    ).strip()
    enriched["explanation"] = explanation

    # Occupant presence is evidence metadata only; risk score and fusion confidence
    # deliberately remain unchanged in this baseline.
    return enriched


def build_report(
    input_events: Path,
    cabin_summary_path: Path,
    output_name: str,
    events: list[dict[str, Any]],
) -> str:
    rows = []
    for event in events:
        cabin = event.get("driver_cabin") or {}
        rows.append(
            f"| {video_name(event)} | {event.get('event_id')} | "
            f"{cabin.get('visibility')} | {cabin.get('occupant_count_estimate')} | "
            f"{cabin.get('driver_candidate_detected')} | "
            f"{cabin.get('temporal_detection_rate')} |"
        )
    return "\n".join(
        [
            "# CABIN-EXP-003 Event Enrichment Summary",
            "",
            f"Tarih: {now_utc()}",
            "",
            "## Kaynaklar",
            "",
            f"* Input events: `{rel(input_events)}`",
            f"* Cabin summary: `{rel(cabin_summary_path)}`",
            "",
            "## Sonuç",
            "",
            "| Video | Event ID | Visibility | Occupant | Driver | Face Rate |",
            "|---|---|---|---:|---|---:|",
            *rows,
            "",
            "## Çıktı",
            "",
            f"* Enriched event JSON: `models/benchmarks/artifacts/{output_name}`",
            "",
            "Cabin occupant sinyali evidence metadata olarak eklenmiştir; risk skoru "
            "değiştirilmemiştir. Telefon ve kemer analizi çalıştırılmamıştır.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich events with cabin baseline.")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_path = args.events.resolve()
    cabin_path = args.cabin_summary.resolve()
    for required in (events_path, cabin_path):
        if not required.exists():
            raise SystemExit(f"Required input not found: {required}")

    events_data = load_json(events_path)
    cabin_summary = load_json(cabin_path)
    cabin_index = build_index(cabin_summary)
    output_name = f"{events_path.stem}-cabin.json"
    enriched_events = [
        enrich_event(
            event,
            cabin_index.get(video_name(event) or ""),
            cabin_summary,
            output_name,
        )
        for event in events_data.get("events", [])
    ]
    output = {
        **{key: value for key, value in events_data.items() if key != "events"},
        "source_event_stage": events_data.get("event_stage"),
        "event_stage": "cabin_driver_enriched_event_skeleton",
        "cabin_experiment_id": cabin_summary.get("experiment_id"),
        "created_at_utc": now_utc(),
        "events": enriched_events,
    }

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    output_path = args.artifact_dir / output_name
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(
        build_report(events_path, cabin_path, output_name, enriched_events) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "event_count": len(enriched_events),
                "output": rel(output_path),
                "report": rel(args.report),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
