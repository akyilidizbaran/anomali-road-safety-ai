#!/usr/bin/env python3
"""Attach seatbelt benchmark metadata to cabin-enriched event skeletons."""

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
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin.json"
)
DEFAULT_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "SEATBELT-EXP-001-opencv_diagonal_belt_evidence_v1-summary.json"
)
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "seatbelt_exp_002_enrichment.md"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_video(event: dict[str, Any]) -> str | None:
    return (event.get("source") or {}).get("source_video")


def enrich_event(
    event: dict[str, Any],
    video_summary: dict[str, Any] | None,
    summary: dict[str, Any],
    accept_decisions: bool = False,
) -> dict[str, Any]:
    enriched = json.loads(json.dumps(event))
    cabin = enriched.setdefault("driver_cabin", {})
    temporal = (video_summary or {}).get("temporal") or {}
    candidate_status = temporal.get("status")
    accepted_status = (
        candidate_status
        if accept_decisions and candidate_status in {"belted", "not_evaluable"}
        else "unknown"
    )
    cabin.update(
        {
            "seatbelt_status": accepted_status,
            "seatbelt_analysis_status": (
                "accepted"
                if accept_decisions and candidate_status == "belted"
                else (
                    "not_evaluable"
                    if candidate_status == "not_evaluable"
                    else "candidate"
                )
            ),
            "seatbelt_confidence": temporal.get("confidence"),
            "seatbelt_detection_rate": temporal.get("belted_evidence_rate"),
            "seatbelt_best_frame": temporal.get("best_frame"),
            "seatbelt_source_roi_uri": temporal.get("best_torso_roi_uri"),
            "seatbelt_model_version": summary.get("model_key"),
            "phone_detected": cabin.get("phone_detected"),
            "phone_bbox": cabin.get("phone_bbox"),
            "phone_model_version": cabin.get("phone_model_version"),
            "hand_association_status": cabin.get(
                "hand_association_status",
                "not_run",
            ),
            "object_near_face_rate": cabin.get("object_near_face_rate"),
            "smoking_status": cabin.get("smoking_status", "not_run"),
            "smoking_confidence": cabin.get("smoking_confidence"),
        }
    )
    models = enriched.setdefault("models", {})
    models["seatbelt_specialist"] = summary.get("model_key")
    evidence = enriched.setdefault("evidence", {})
    evidence["seatbelt_overlay_video_uri"] = (
        video_summary or {}
    ).get("annotated_video")
    evidence["seatbelt_candidate_status"] = candidate_status
    evidence["seatbelt_decision_accepted"] = bool(
        accept_decisions and candidate_status == "belted"
    )
    explanation = enriched.setdefault("explanation", {})
    explanation["technical_summary"] = (
        f"{explanation.get('technical_summary', '').rstrip()} "
        f"Seatbelt candidate={candidate_status}, accepted={accept_decisions}. "
        "Absence of diagonal evidence is not interpreted as unbelted."
    ).strip()
    return enriched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich events with seatbelt metadata.")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--seatbelt-summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--accept-decisions", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_data = json.loads(args.events.resolve().read_text(encoding="utf-8"))
    summary = json.loads(
        args.seatbelt_summary.resolve().read_text(encoding="utf-8")
    )
    index = {
        item["video"]: item
        for item in summary.get("videos", [])
        if item.get("video")
    }
    events = [
        enrich_event(
            event,
            index.get(source_video(event)),
            summary,
            args.accept_decisions,
        )
        for event in events_data.get("events", [])
    ]
    output_name = (
        "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-seatbelt.json"
    )
    output = {
        **events_data,
        "experiment_id": "SEATBELT-EXP-002",
        "created_at_utc": now_utc(),
        "seatbelt_decisions_accepted": args.accept_decisions,
        "events": events,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.artifact_dir / output_name
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        "\n".join(
            [
                "# SEATBELT-EXP-002 Event Enrichment",
                "",
                f"Tarih: {now_utc()}",
                "",
                f"* Events: `{len(events)}`",
                f"* Decisions accepted: `{args.accept_decisions}`",
                f"* Output: `{output_path.relative_to(ROOT)}`",
                "",
                "Varsayılan modda seatbelt aday metadata'sı eklenir ancak "
                "`seatbelt_status=unknown` korunur.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(output_path.relative_to(ROOT)), "events": len(events)}, indent=2))


if __name__ == "__main__":
    main()
