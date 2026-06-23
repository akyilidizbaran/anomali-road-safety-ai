#!/usr/bin/env python3
"""Build a readable phone-call demo summary from enriched event JSON."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-phone-call.json"
)
DEFAULT_ARTIFACT = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-PROVISIONAL-BASELINE-event-summary.json"
)
DEFAULT_REPORT = (
    ROOT
    / "testing"
    / "reports"
    / "phone_call_baseline_v2"
    / "provisional_baseline_event_summary.md"
)


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def source_video(event: dict[str, Any]) -> str:
    return str((event.get("source") or {}).get("source_video") or "unknown")


def summarize_event(event: dict[str, Any]) -> dict[str, Any]:
    cabin = event.get("driver_cabin") or {}
    evidence = event.get("evidence") or {}
    return {
        "event_id": event.get("event_id"),
        "video": source_video(event),
        "phone_object_status": cabin.get("phone_analysis_status"),
        "phone_detected": cabin.get("phone_detected"),
        "phone_call_status": cabin.get("phone_call_status") or "not_run",
        "phone_call_confidence": cabin.get("phone_call_confidence"),
        "phone_call_evidence_source": cabin.get("phone_call_evidence_source"),
        "phone_call_baseline_id": cabin.get("phone_call_baseline_id"),
        "pose_reliability": cabin.get("phone_call_pose_reliability"),
        "pose_policy": cabin.get("phone_call_pose_policy"),
        "phone_risk": cabin.get("phone_risk"),
        "final_baseline_accepted": evidence.get("phone_call_final_baseline_accepted"),
        "phone_call_overlay_video_uri": evidence.get("phone_call_overlay_video_uri"),
    }


def summarize_events(data: dict[str, Any]) -> dict[str, Any]:
    rows = [summarize_event(event) for event in data.get("events", [])]
    status_counts = dict(Counter(row["phone_call_status"] for row in rows))
    pose_counts = dict(Counter(row["pose_reliability"] for row in rows))
    risk_values = {row["phone_risk"] for row in rows}
    return {
        "created_at_utc": now_utc(),
        "source_events": rel(DEFAULT_EVENTS),
        "experiment_id": data.get("experiment_id"),
        "phone_call_baseline_id": data.get("phone_call_baseline_id"),
        "phone_call_final_baseline_accepted": data.get(
            "phone_call_final_baseline_accepted"
        ),
        "event_count": len(rows),
        "status_counts": status_counts,
        "pose_reliability_counts": pose_counts,
        "phone_risk_all_null": risk_values <= {None},
        "events": rows,
    }


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Phone-Call Provisional Baseline Event Summary",
        "",
        f"* Baseline: `{summary['phone_call_baseline_id']}`",
        f"* Final accepted: `{summary['phone_call_final_baseline_accepted']}`",
        f"* Event count: `{summary['event_count']}`",
        f"* Status counts: `{summary['status_counts']}`",
        f"* Pose reliability counts: `{summary['pose_reliability_counts']}`",
        f"* `phone_risk` all null: `{summary['phone_risk_all_null']}`",
        "",
        "| Video | Phone object | Call status | Confidence | Evidence | Pose | Risk | Overlay |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for row in summary["events"]:
        lines.append(
            "| {video} | {obj} | {status} | {conf} | {source} | {pose} | {risk} | `{overlay}` |".format(
                video=row["video"],
                obj=row["phone_object_status"],
                status=row["phone_call_status"],
                conf=row["phone_call_confidence"],
                source=row["phone_call_evidence_source"],
                pose=row["pose_reliability"],
                risk=row["phone_risk"],
                overlay=row["phone_call_overlay_video_uri"],
            )
        )
    lines.extend(
        [
            "",
            "Not: Bu rapor entegrasyon/demo çıktısıdır. Final kabul kapısı geçilmediği",
            "için `phone_risk=null` korunur.",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize enriched phone-call events.")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = json.loads(args.events.resolve().read_text(encoding="utf-8"))
    summary = summarize_events(data)
    summary["source_events"] = rel(args.events)
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.artifact.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(build_report(summary) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": rel(args.artifact), "report": rel(args.report)}, indent=2))


if __name__ == "__main__":
    main()
