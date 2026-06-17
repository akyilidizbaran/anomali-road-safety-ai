#!/usr/bin/env python3
"""Attach selected OCR baseline outputs to tracking event skeletons.

This script reads:
  * tracking event skeleton JSON from `build_track_event_skeleton.py`
  * selected OCR summary JSON from `run_plate_ocr_baseline.py`

and produces a new event artifact with the `plate`, `models`, `evidence`,
`routing_decision` and `explanation` sections enriched using the chosen OCR
baseline.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json"
DEFAULT_OCR_SUMMARY = ROOT / "models" / "benchmarks" / "artifacts" / "POCR-EXP-002-paddleocr-summary.json"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "trk_exp_001_plate_ocr_event_enrichment_summary.md"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_rootish(value: str | Path | None) -> Path:
    if not value:
        return ROOT
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_output_name(events_path: Path, ocr_summary: dict[str, Any]) -> str:
    stem = events_path.stem
    suffix = ocr_summary.get("ocr_engine") or "ocr"
    return f"{stem}-{suffix}.json"


def video_key_from_event(event: dict[str, Any]) -> str | None:
    source = event.get("source") or {}
    return source.get("source_video")


def build_ocr_index(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["video"]: item for item in summary.get("videos", []) if item.get("video")}


def plate_status(video_ocr: dict[str, Any], vote: dict[str, Any], best: dict[str, Any]) -> tuple[str, str, str | None]:
    if not video_ocr or video_ocr.get("status") != "completed":
        return "not_run", "not_run", "ocr_summary_video_missing"
    if vote.get("plate_text"):
        if float(vote.get("vote_confidence") or 0.0) >= 0.35 and vote.get("format_valid"):
            return "detected", "read", None
        return "low_confidence", "low_confidence", "temporal_vote_below_threshold"
    if best.get("raw_text") or video_ocr.get("ocr_read_count"):
        return "detected", "not_read", "raw_ocr_available_but_no_valid_vote"
    if video_ocr.get("crop_count", 0) > 0:
        return "not_visible", "not_read", "plate_crops_available_but_ocr_failed"
    return "not_detected", "not_read", "no_plate_crops_available"


def overlay_video_uri(engine: str, video_name: str) -> str | None:
    path = ROOT / "runs" / "plate_ocr" / "POCR-EXP-002-004-ocr" / "overlay" / engine / f"{Path(video_name).stem}_ocr_overlay.mp4"
    return rel(path) if path.exists() else None


def enrich_event(
    event: dict[str, Any],
    video_ocr: dict[str, Any] | None,
    ocr_summary: dict[str, Any],
    output_json_name: str,
) -> dict[str, Any]:
    enriched = json.loads(json.dumps(event))
    vote = (video_ocr or {}).get("temporal_vote") or {}
    best = (video_ocr or {}).get("highest_confidence_result") or {}
    plate_state, ocr_state, failure_reason = plate_status(video_ocr or {}, vote, best)
    video_name = video_key_from_event(event) or ""
    engine = ocr_summary.get("ocr_engine") or "ocr"

    plate_text = vote.get("plate_text") or best.get("normalized_text")
    plate_confidence = vote.get("vote_confidence")
    if plate_confidence is None:
        plate_confidence = best.get("ocr_confidence")

    enriched["plate"] = {
        "status": plate_state,
        "detected": bool((video_ocr or {}).get("crop_count")),
        "bbox": None,
        "ocr_status": ocr_state,
        "ocr_text": plate_text,
        "raw_text_best_frame": best.get("raw_text"),
        "format_valid": vote.get("format_valid") if vote else best.get("format_valid"),
        "province_code_valid": vote.get("province_code_valid") if vote else best.get("province_code_valid"),
        "confidence": round(float(plate_confidence), 4) if plate_confidence is not None else None,
        "vote_confidence": vote.get("vote_confidence"),
        "candidate_count": vote.get("candidate_count"),
        "best_frame": best.get("frame") or (video_ocr or {}).get("best_frame"),
        "source_crop_uri": best.get("crop_file"),
        "source_crop_dir": (video_ocr or {}).get("source_plate_crop_dir"),
        "ocr_engine": engine,
        "failure_reason": failure_reason,
    }

    models = enriched.get("models") or {}
    models["plate_detector"] = (ocr_summary.get("source_detector_key") or "unknown")
    models["plate_ocr"] = f"{ocr_summary.get('ocr_engine_label', engine)}:{ocr_summary.get('model_ref', engine)}"
    models["plate_postprocess"] = "turkish_regex_province_temporal_vote_v1"
    enriched["models"] = models

    routing = enriched.get("routing_decision") or {}
    experts_called = list(routing.get("experts_called") or [])
    if "Plate OCR" not in experts_called:
        experts_called.append("Plate OCR")
    routing_reasons = list(routing.get("routing_reasons") or [])
    if "selected_plate_ocr_baseline_connected" not in routing_reasons:
        routing_reasons.append("selected_plate_ocr_baseline_connected")
    routing["experts_called"] = experts_called
    routing["routing_reasons"] = routing_reasons
    routing["selected_plate_detector"] = ocr_summary.get("source_detector_key")
    routing["selected_plate_ocr_engine"] = ocr_summary.get("ocr_engine")
    enriched["routing_decision"] = routing

    evidence = enriched.get("evidence") or {}
    evidence["status"] = "partial" if ocr_state != "read" else "partial"
    evidence["plate_crop_uri"] = best.get("crop_file")
    evidence["ocr_overlay_video_uri"] = overlay_video_uri(engine, video_name)
    evidence["json_uri"] = f"models/benchmarks/artifacts/{output_json_name}"
    base_score = float(evidence.get("evidence_quality_score") or 0.0)
    base_meta = float(evidence.get("metadata_completeness_score") or 0.0)
    ocr_bonus = 0.12 if ocr_state == "read" else 0.04 if ocr_state == "low_confidence" else 0.0
    format_bonus = 0.05 if enriched["plate"].get("format_valid") else 0.0
    evidence["evidence_quality_score"] = round(clamp(base_score + ocr_bonus + format_bonus), 3)
    evidence["metadata_completeness_score"] = round(clamp(base_meta + 0.08), 3)
    evidence["plate_ocr"] = {
        "engine": engine,
        "final_text": plate_text,
        "vote_confidence": vote.get("vote_confidence"),
        "best_frame": enriched["plate"].get("best_frame"),
        "crop_count": (video_ocr or {}).get("crop_count"),
        "ocr_read_count": (video_ocr or {}).get("ocr_read_count"),
    }
    enriched["evidence"] = evidence

    risk = enriched.get("risk") or {}
    reasons = list(risk.get("reasons") or [])
    if ocr_state == "read":
        reasons.append("plate_ocr_final_decision_available")
    elif ocr_state == "low_confidence":
        reasons.append("plate_ocr_low_confidence")
    else:
        reasons.append("plate_ocr_not_available")
    risk["reasons"] = reasons
    risk["fusion_confidence"] = round(
        clamp(
            0.65 * float(risk.get("fusion_confidence") or 0.0)
            + 0.35 * float(enriched["plate"].get("confidence") or 0.0)
        ),
        3,
    )
    enriched["risk"] = risk

    explanation = enriched.get("explanation") or {}
    final_text = plate_text or "okunamadi"
    explanation["user_level_summary"] = (
        f"Hedef arac icin PaddleOCR tabanli plaka karari uretilmistir: {final_text}."
        if ocr_state == "read"
        else "Hedef arac icin plaka OCR denendi ancak guvenilir final karar uretilmedi."
    )
    explanation["technical_summary"] = (
        f"{explanation.get('technical_summary', '').rstrip()} "
        f"Plate OCR entegrasyonu sonrasi final_text={plate_text}, "
        f"ocr_status={ocr_state}, vote_confidence={vote.get('vote_confidence')}, "
        f"best_frame={enriched['plate'].get('best_frame')}."
    ).strip()
    enriched["explanation"] = explanation

    return enriched


def build_report(
    output_path: Path,
    input_events: Path,
    ocr_summary_path: Path,
    output_json_name: str,
    events: list[dict[str, Any]],
    ocr_summary: dict[str, Any],
) -> None:
    rows = []
    for event in events:
        source_video = video_key_from_event(event)
        plate = event.get("plate") or {}
        rows.append(
            f"| {source_video} | {event.get('event_id')} | {plate.get('ocr_text')} | "
            f"{plate.get('ocr_status')} | {plate.get('format_valid')} | "
            f"{plate.get('confidence')} | {plate.get('vote_confidence')} |"
        )

    content = "\n".join(
        [
            "# Track Event + Plate OCR Enrichment Summary",
            "",
            f"Tarih: {now_utc()}",
            "",
            "## Amaç",
            "",
            "Seçilen PaddleOCR baseline sonucunu tracking event skeleton kayıtlarına bağlamak.",
            "",
            "## Kaynaklar",
            "",
            f"* Input event skeleton: `{rel(input_events.resolve())}`",
            f"* OCR summary: `{rel(ocr_summary_path.resolve())}`",
            f"* OCR engine: `{ocr_summary.get('ocr_engine')}`",
            "",
            "## Sonuç",
            "",
            "| Video | Event ID | Final Plate | OCR Status | Format Valid | Confidence | Vote Conf |",
            "|---|---|---|---|---:|---:|---:|",
            *rows,
            "",
            "## Çıktı",
            "",
            f"* Enriched event JSON: `models/benchmarks/artifacts/{output_json_name}`",
            "",
            "## Sonraki Adım",
            "",
            "Plate/OCR baseline artık event/evidence hattına bağlı. Sonraki mantıklı faz speed estimation veya evidence package enrichment detaylandırmasıdır.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich tracking event skeletons with selected OCR baseline.")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--ocr-summary", type=Path, default=DEFAULT_OCR_SUMMARY)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_path = args.events.resolve()
    ocr_summary_path = args.ocr_summary.resolve()
    events_data = load_json(events_path)
    ocr_summary = load_json(ocr_summary_path)
    ocr_index = build_ocr_index(ocr_summary)

    output_json_name = select_output_name(events_path, ocr_summary)
    enriched_events = []
    for event in events_data.get("events", []):
        source_video = video_key_from_event(event)
        enriched_events.append(enrich_event(event, ocr_index.get(source_video or ""), ocr_summary, output_json_name))

    enriched_payload = {
        "generated_at_utc": now_utc(),
        "source_event_stage": events_data.get("event_stage"),
        "event_stage": "plate_ocr_enriched_event_skeleton",
        "source_experiment_id": events_data.get("source_experiment_id"),
        "source_ocr_experiment_id": ocr_summary.get("experiment_id"),
        "events": enriched_events,
    }

    artifact_dir = args.artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / output_json_name
    output_path.write_text(json.dumps(enriched_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    build_report(args.report.resolve(), events_path, ocr_summary_path, output_json_name, enriched_events, ocr_summary)

    print(
        json.dumps(
            {
                "output_json": rel(output_path),
                "report": rel(args.report.resolve()),
                "event_count": len(enriched_events),
                "ocr_engine": ocr_summary.get("ocr_engine"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
