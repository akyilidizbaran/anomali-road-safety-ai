#!/usr/bin/env python3
"""Attach phone object candidate metadata to cabin-enriched event skeletons."""

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
    / "phone_call_baseline_v2"
    / "PHONE-EXP-004-yolo26s_phone_windshield_seed_smoke-summary.json"
)
DEFAULT_PHONE_CALL_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-002-phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2-summary.json"
)
DEFAULT_PHONE_CALL_BASELINE = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-PROVISIONAL-BASELINE.json"
)
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "phone_exp_001_enrichment.md"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_video(event: dict[str, Any]) -> str | None:
    return (event.get("source") or {}).get("source_video")


def enrich_event(
    event: dict[str, Any],
    video_summary: dict[str, Any] | None,
    summary: dict[str, Any],
    phone_call_video: dict[str, Any] | None = None,
    phone_call_summary: dict[str, Any] | None = None,
    phone_call_baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    enriched = json.loads(json.dumps(event))
    cabin = enriched.setdefault("driver_cabin", {})
    temporal = (video_summary or {}).get("temporal") or {}
    status = temporal.get("status") or "not_evaluable"
    phone_detected = True if status == "detected" else False if status == "not_detected" else None
    cabin.update(
        {
            "phone_analysis_status": (
                "candidate"
                if status == "detected"
                else status
            ),
            "phone_detected": phone_detected,
            "phone_confidence": temporal.get("confidence"),
            "phone_detection_rate": temporal.get("detection_rate"),
            "phone_bbox": temporal.get("best_phone_bbox"),
            "phone_best_frame": temporal.get("best_frame"),
            "phone_source_roi_uri": temporal.get("best_phone_roi_uri"),
            "phone_model_version": summary.get("model_key"),
            "phone_risk": None,
            "hand_association_status": cabin.get("hand_association_status", "not_run"),
            "object_near_face_rate": temporal.get("object_near_face_rate"),
        }
    )
    models = enriched.setdefault("models", {})
    models["phone_object_detector"] = summary.get("model_key")
    evidence = enriched.setdefault("evidence", {})
    evidence["phone_overlay_video_uri"] = (video_summary or {}).get("annotated_video")
    evidence["phone_candidate_status"] = status
    evidence["phone_risk_enabled"] = False
    behavior = (phone_call_video or {}).get("behavior") or {}
    baseline_id = (phone_call_baseline or {}).get("baseline_id")
    if behavior:
        cabin.update(
            {
                "phone_call_status": behavior.get("phone_call_status"),
                "phone_call_confidence": behavior.get("phone_call_confidence"),
                "phone_call_evidence_source": behavior.get(
                    "phone_call_evidence_source"
                ),
                "hand_near_ear_candidate_rate": behavior.get(
                    "hand_near_ear_candidate_rate"
                ),
                "longest_hand_near_ear_seconds": behavior.get(
                    "longest_hand_near_ear_seconds"
                ),
                "dominant_hand_side": behavior.get("dominant_hand_side"),
                "phone_call_baseline_id": baseline_id,
                "phone_call_pose_reliability": behavior.get(
                    "pose_reliability_detail"
                ),
                "phone_call_pose_policy": behavior.get(
                    "pose_reliability_policy"
                ),
            }
        )
        models["phone_call_behavior"] = (phone_call_summary or {}).get(
            "model_key"
        )
        if baseline_id:
            models["phone_call_provisional_baseline"] = baseline_id
        evidence["phone_call_overlay_video_uri"] = (phone_call_video or {}).get(
            "annotated_video"
        )
        evidence["phone_call_risk_enabled"] = False
        evidence["phone_call_baseline_id"] = baseline_id
        evidence["phone_call_baseline_uri"] = (
            "models/benchmarks/artifacts/phone_call_baseline_v2/"
            "PHONE-CALL-PROVISIONAL-BASELINE.json"
            if baseline_id
            else None
        )
        evidence["phone_call_pose_reliability"] = behavior.get(
            "pose_reliability_detail"
        )
        evidence["phone_call_pose_policy"] = behavior.get(
            "pose_reliability_policy"
        )
        evidence["phone_call_final_baseline_accepted"] = (
            (phone_call_baseline or {}).get("final_baseline_accepted")
            if phone_call_baseline
            else None
        )
    explanation = enriched.setdefault("explanation", {})
    explanation["technical_summary"] = (
        f"{explanation.get('technical_summary', '').rstrip()} "
        f"Phone candidate={status}, rate={temporal.get('detection_rate')}. "
        f"Phone-call behavior={behavior.get('phone_call_status', 'not_run')}. "
        f"Phone-call baseline={baseline_id or 'not_run'}. "
        "Phone object visibility alone is not interpreted as a violation."
    ).strip()
    return enriched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich events with phone metadata.")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--phone-summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--phone-call-summary", type=Path, default=DEFAULT_PHONE_CALL_SUMMARY)
    parser.add_argument("--phone-call-baseline", type=Path, default=DEFAULT_PHONE_CALL_BASELINE)
    parser.add_argument(
        "--object-only",
        action="store_true",
        help="Skip phone-call provisional baseline enrichment and emit object metadata only.",
    )
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_data = json.loads(args.events.resolve().read_text(encoding="utf-8"))
    summary = json.loads(args.phone_summary.resolve().read_text(encoding="utf-8"))
    phone_call_summary = (
        json.loads(args.phone_call_summary.resolve().read_text(encoding="utf-8"))
        if args.phone_call_summary and not args.object_only
        else None
    )
    phone_call_baseline = (
        json.loads(args.phone_call_baseline.resolve().read_text(encoding="utf-8"))
        if args.phone_call_baseline and not args.object_only
        else None
    )
    index = {
        item["video"]: item
        for item in summary.get("videos", [])
        if item.get("video")
    }
    phone_call_index = {
        item["video"]: item
        for item in (phone_call_summary or {}).get("videos", [])
        if item.get("video")
    }
    events = [
        enrich_event(
            event,
            index.get(source_video(event)),
            summary,
            phone_call_index.get(source_video(event)),
            phone_call_summary,
            phone_call_baseline,
        )
        for event in events_data.get("events", [])
    ]
    output_name = (
        "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-phone-call.json"
        if phone_call_summary
        else "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-phone.json"
    )
    output = {
        **events_data,
        "experiment_id": (
            phone_call_baseline.get("baseline_id")
            if phone_call_baseline
            else phone_call_summary.get("experiment_id")
            if phone_call_summary
            else "PHONE-EXP-001"
        ),
        "created_at_utc": now_utc(),
        "phone_risk_enabled": False,
        "phone_call_baseline_id": (
            phone_call_baseline.get("baseline_id")
            if phone_call_baseline
            else None
        ),
        "phone_call_final_baseline_accepted": (
            phone_call_baseline.get("final_baseline_accepted")
            if phone_call_baseline
            else None
        ),
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
                "# PHONE-EXP-001 Event Enrichment",
                "",
                f"Tarih: {now_utc()}",
                "",
                f"* Events: `{len(events)}`",
                f"* Output: `{output_path.relative_to(ROOT)}`",
                f"* Phone-call baseline: `{(phone_call_baseline or {}).get('baseline_id')}`",
                f"* Final baseline accepted: `{(phone_call_baseline or {}).get('final_baseline_accepted')}`",
                "",
                "`phone_detected` candidate metadata'dır; `phone_risk=null` korunur.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"output": str(output_path.relative_to(ROOT)), "events": len(events)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
