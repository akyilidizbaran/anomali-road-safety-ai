#!/usr/bin/env python3
"""Attach selected OCR baseline outputs to tracking event skeletons.

This script reads:
  * tracking event skeleton JSON from `build_track_event_skeleton.py`
  * selected OCR summary JSON from `run_plate_ocr_baseline.py`

and produces a new event artifact with the `plate`, `models`, `evidence`,
`routing_decision` and `explanation` sections enriched using the chosen OCR
baseline.

The active 2026-06-17 project decision is CCT-XS with a temporal stability
gate. A plate text is promoted into evidence only after the same
format-valid/province-valid OCR value is observed at least `stable_count`
times inside a sliding `window_size`, with per-crop confidence above
`min_confidence`.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json"
DEFAULT_OCR_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "plate_ocr"
    / "POCR-EXP-007-cct-xs-baseline-percrop"
    / "POCR-EXP-006-fast-plate-ocr-summary.json"
)
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_OUTPUT_DIR = (
    ROOT / "models" / "benchmarks" / "artifacts" / "plate_ocr" / "POCR-EXP-008-cct-xs-event-enrichment"
)
DEFAULT_REPORT = ROOT / "testing" / "reports" / "pocr_exp_008_cct_xs_event_evidence_enrichment.md"


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


def per_crop_rows(video_ocr: dict[str, Any]) -> list[dict[str, Any]]:
    rows = video_ocr.get("per_crop") or []
    if not isinstance(rows, list):
        return []
    return sorted(rows, key=lambda item: int(item.get("frame") or 0))


def temporal_stability_gate(
    video_ocr: dict[str, Any],
    stable_count: int,
    window_size: int,
    min_confidence: float,
) -> dict[str, Any]:
    rows = per_crop_rows(video_ocr)
    gate = {
        "stable_count_required": stable_count,
        "window_size": window_size,
        "min_confidence": min_confidence,
        "require_format_valid": True,
        "require_province_code_valid": True,
    }
    if not rows:
        return {
            "status": "failed",
            "gate": gate,
            "failure_reason": "per_crop_ocr_rows_missing",
            "first_stable_frame": None,
            "stable_text": None,
            "stable_observations": 0,
            "stable_crop_uri": None,
            "candidate_counts": {},
        }

    window: deque[dict[str, Any]] = deque(maxlen=window_size)
    global_counts: dict[str, int] = defaultdict(int)
    first_readable_frame: int | None = None
    first_format_valid_frame: int | None = None
    first_province_valid_frame: int | None = None
    for row in rows:
        frame = int(row.get("frame") or 0)
        text = str(row.get("normalized_text") or "")
        confidence = float(row.get("ocr_confidence") or 0.0)
        if text:
            global_counts[text] += 1
            first_readable_frame = first_readable_frame or frame
        if text and row.get("format_valid"):
            first_format_valid_frame = first_format_valid_frame or frame
        if text and row.get("format_valid") and row.get("province_code_valid"):
            first_province_valid_frame = first_province_valid_frame or frame

        usable = (
            bool(text)
            and confidence >= min_confidence
            and bool(row.get("format_valid"))
            and bool(row.get("province_code_valid"))
        )
        window.append(
            {
                "frame": frame,
                "text": text if usable else None,
                "crop_file": row.get("crop_file"),
                "confidence": confidence,
            }
        )
        counts: dict[str, int] = defaultdict(int)
        best_source: dict[str, Any] | None = None
        for seen in window:
            if not seen["text"]:
                continue
            counts[str(seen["text"])] += 1
            if seen["text"] == text:
                best_source = seen
        if not counts:
            continue
        stable_text, observations = max(counts.items(), key=lambda pair: (pair[1], pair[0]))
        if observations >= stable_count:
            return {
                "status": "passed",
                "gate": gate,
                "failure_reason": None,
                "first_readable_frame": first_readable_frame,
                "first_format_valid_frame": first_format_valid_frame,
                "first_province_valid_frame": first_province_valid_frame,
                "first_stable_frame": frame,
                "stable_text": stable_text,
                "stable_observations": observations,
                "stable_crop_uri": best_source.get("crop_file") if best_source else row.get("crop_file"),
                "candidate_counts": dict(sorted(global_counts.items(), key=lambda item: (-item[1], item[0]))),
            }

    return {
        "status": "failed",
        "gate": gate,
        "failure_reason": "stable_vote_threshold_not_reached",
        "first_readable_frame": first_readable_frame,
        "first_format_valid_frame": first_format_valid_frame,
        "first_province_valid_frame": first_province_valid_frame,
        "first_stable_frame": None,
        "stable_text": None,
        "stable_observations": 0,
        "stable_crop_uri": None,
        "candidate_counts": dict(sorted(global_counts.items(), key=lambda item: (-item[1], item[0]))),
    }


def plate_status(
    video_ocr: dict[str, Any],
    vote: dict[str, Any],
    best: dict[str, Any],
    stability: dict[str, Any],
) -> tuple[str, str, str | None]:
    if not video_ocr or video_ocr.get("status") != "completed":
        return "not_run", "not_run", "ocr_summary_video_missing"
    if stability.get("status") == "passed":
        if vote.get("plate_text") and vote.get("plate_text") != stability.get("stable_text"):
            return "detected", "unstable_conflict", "stable_gate_temporal_vote_conflict"
        return "detected", "stable_read", None
    if vote.get("plate_text"):
        return "detected", "low_confidence", stability.get("failure_reason") or "temporal_stability_gate_failed"
    if best.get("raw_text") or video_ocr.get("ocr_read_count"):
        return "detected", "not_read", "raw_ocr_available_but_no_valid_vote"
    if video_ocr.get("crop_count", 0) > 0:
        return "not_visible", "not_read", "plate_crops_available_but_ocr_failed"
    return "not_detected", "not_read", "no_plate_crops_available"


def overlay_video_uri(engine: str, video_name: str) -> str | None:
    candidates = [
        ROOT
        / "runs"
        / "plate_ocr"
        / "POCR-EXP-006-manual-video-review"
        / "cct-xs"
        / engine
        / f"{Path(video_name).stem}_ocr_overlay.mp4",
        ROOT
        / "runs"
        / "plate_ocr"
        / "POCR-EXP-006-manual-video-review"
        / engine
        / engine
        / f"{Path(video_name).stem}_ocr_overlay.mp4",
        ROOT / "runs" / "plate_ocr" / "POCR-EXP-002-004-ocr" / "overlay" / engine / f"{Path(video_name).stem}_ocr_overlay.mp4",
    ]
    for path in candidates:
        if path.exists():
            return rel(path)
    return None


def mask_plate_text(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 4)}"


def enrich_event(
    event: dict[str, Any],
    video_ocr: dict[str, Any] | None,
    ocr_summary: dict[str, Any],
    output_json_name: str,
    stability: dict[str, Any],
) -> dict[str, Any]:
    enriched = json.loads(json.dumps(event))
    vote = (video_ocr or {}).get("temporal_vote") or {}
    best = (video_ocr or {}).get("highest_confidence_result") or {}
    plate_state, ocr_state, failure_reason = plate_status(video_ocr or {}, vote, best, stability)
    video_name = video_key_from_event(event) or ""
    engine = ocr_summary.get("ocr_engine") or "ocr"

    plate_text = stability.get("stable_text") or vote.get("plate_text") or best.get("normalized_text")
    plate_confidence = vote.get("vote_confidence")
    if plate_confidence is None:
        plate_confidence = best.get("ocr_confidence")

    enriched["plate"] = {
        "status": plate_state,
        "detected": bool((video_ocr or {}).get("crop_count")),
        "bbox": None,
        "ocr_status": ocr_state,
        "ocr_text": plate_text,
        "ocr_text_masked": mask_plate_text(plate_text),
        "raw_text_best_frame": best.get("raw_text"),
        "format_valid": vote.get("format_valid") if vote else best.get("format_valid"),
        "province_code_valid": vote.get("province_code_valid") if vote else best.get("province_code_valid"),
        "confidence": round(float(plate_confidence), 4) if plate_confidence is not None else None,
        "vote_confidence": vote.get("vote_confidence"),
        "candidate_count": vote.get("candidate_count"),
        "best_frame": stability.get("first_stable_frame") or best.get("frame") or (video_ocr or {}).get("best_frame"),
        "source_crop_uri": stability.get("stable_crop_uri") or best.get("crop_file"),
        "source_crop_dir": (video_ocr or {}).get("source_plate_crop_dir"),
        "ocr_engine": engine,
        "ocr_model_ref": ocr_summary.get("model_ref"),
        "temporal_vote": {
            "text": vote.get("plate_text"),
            "confidence": vote.get("vote_confidence"),
            "candidate_count": vote.get("candidate_count"),
            "top_candidates": vote.get("top_candidates"),
        },
        "temporal_stability": stability,
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
    routing["plate_ocr_stability_gate"] = stability.get("gate")
    enriched["routing_decision"] = routing

    evidence = enriched.get("evidence") or {}
    evidence["status"] = "partial" if ocr_state != "read" else "partial"
    evidence["plate_crop_uri"] = enriched["plate"].get("source_crop_uri")
    evidence["ocr_overlay_video_uri"] = overlay_video_uri(engine, video_name)
    evidence["json_uri"] = f"models/benchmarks/artifacts/{output_json_name}"
    base_score = float(evidence.get("evidence_quality_score") or 0.0)
    base_meta = float(evidence.get("metadata_completeness_score") or 0.0)
    ocr_bonus = 0.12 if ocr_state == "stable_read" else 0.04 if ocr_state == "low_confidence" else 0.0
    format_bonus = 0.05 if enriched["plate"].get("format_valid") else 0.0
    evidence["evidence_quality_score"] = round(clamp(base_score + ocr_bonus + format_bonus), 3)
    evidence["metadata_completeness_score"] = round(clamp(base_meta + 0.08), 3)
    evidence["plate_ocr"] = {
        "engine": engine,
        "model_ref": ocr_summary.get("model_ref"),
        "final_text": plate_text,
        "masked_text": mask_plate_text(plate_text),
        "status": ocr_state,
        "vote_confidence": vote.get("vote_confidence"),
        "temporal_stability_status": stability.get("status"),
        "first_stable_frame": stability.get("first_stable_frame"),
        "stable_observations": stability.get("stable_observations"),
        "best_frame": enriched["plate"].get("best_frame"),
        "crop_count": (video_ocr or {}).get("crop_count"),
        "processed_crops": (video_ocr or {}).get("processed_crops"),
        "ocr_read_count": (video_ocr or {}).get("ocr_read_count"),
        "format_valid_count": (video_ocr or {}).get("format_valid_count"),
        "province_valid_count": (video_ocr or {}).get("province_valid_count"),
    }
    enriched["evidence"] = evidence

    risk = enriched.get("risk") or {}
    reasons = list(risk.get("reasons") or [])
    if ocr_state == "stable_read":
        reasons.append("plate_ocr_stable_temporal_decision_available")
    elif ocr_state == "low_confidence":
        reasons.append("plate_ocr_temporal_stability_gate_failed")
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
    masked_text = mask_plate_text(plate_text) or "okunamadi"
    explanation["user_level_summary"] = (
        f"Hedef arac icin CCT-XS OCR temporal stability gate sonrasi plaka karari uretilmistir: {masked_text}."
        if ocr_state == "stable_read"
        else "Hedef arac icin CCT-XS OCR denendi ancak stabil final karar uretilmedi."
    )
    explanation["technical_summary"] = (
        f"{explanation.get('technical_summary', '').rstrip()} "
        f"Plate OCR entegrasyonu sonrasi final_text={plate_text}, "
        f"ocr_status={ocr_state}, vote_confidence={vote.get('vote_confidence')}, "
        f"first_stable_frame={stability.get('first_stable_frame')}, "
        f"stable_observations={stability.get('stable_observations')}."
    ).strip()
    enriched["explanation"] = explanation

    return enriched


def model_count_row(event: dict[str, Any], video_ocr: dict[str, Any] | None, stability: dict[str, Any]) -> dict[str, Any]:
    source_video = video_key_from_event(event) or (video_ocr or {}).get("video")
    vote = (video_ocr or {}).get("temporal_vote") or {}
    top_candidates = vote.get("top_candidates") or []
    top_candidate = top_candidates[0] if top_candidates else {}
    target = event.get("target_vehicle") or {}
    return {
        "video": source_video,
        "event_id": event.get("event_id"),
        "track_id": target.get("track_id") or (video_ocr or {}).get("track_id"),
        "target_track_id_numeric": (video_ocr or {}).get("target_track_id"),
        "best_frame": (video_ocr or {}).get("best_frame") or (target.get("frame_window") or {}).get("best_frame"),
        "target_track_frames": (video_ocr or {}).get("crop_count"),
        "plate_detector_detection_rate": (video_ocr or {}).get("source_detector_plate_detection_rate"),
        "processed_crops": (video_ocr or {}).get("processed_crops"),
        "ocr_read_count": (video_ocr or {}).get("ocr_read_count"),
        "format_valid_count": (video_ocr or {}).get("format_valid_count"),
        "province_valid_count": (video_ocr or {}).get("province_valid_count"),
        "temporal_vote_text": vote.get("plate_text"),
        "temporal_vote_confidence": vote.get("vote_confidence"),
        "temporal_candidate_count": vote.get("candidate_count"),
        "top_candidate_count": top_candidate.get("count"),
        "top_candidate_max_confidence": top_candidate.get("max_confidence"),
        "stability_status": stability.get("status"),
        "first_readable_frame": stability.get("first_readable_frame"),
        "first_format_valid_frame": stability.get("first_format_valid_frame"),
        "first_province_valid_frame": stability.get("first_province_valid_frame"),
        "first_stable_frame": stability.get("first_stable_frame"),
        "stable_text": stability.get("stable_text"),
        "stable_observations": stability.get("stable_observations"),
        "mean_ocr_latency_ms": (video_ocr or {}).get("mean_ocr_latency_ms"),
        "p95_ocr_latency_ms": (video_ocr or {}).get("p95_ocr_latency_ms"),
        "model_review_note": (
            "model_output_only_manual_visual_review_required"
            if stability.get("status") != "passed"
            else "stable_temporal_ocr_candidate_from_model_outputs"
        ),
    }


def write_model_counts(rows: list[dict[str, Any]], csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "generated_at_utc": now_utc(),
                "note": "Model-derived counts for manual review. These are not manual accuracy labels.",
                "rows": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def build_report(
    output_path: Path,
    input_events: Path,
    ocr_summary_path: Path,
    output_json_name: str,
    events: list[dict[str, Any]],
    ocr_summary: dict[str, Any],
    model_count_rows: list[dict[str, Any]],
    count_csv_path: Path,
    count_json_path: Path,
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
    count_rows = []
    for row in model_count_rows:
        count_rows.append(
            f"| {row['video']} | {row['processed_crops']} | {row['ocr_read_count']} | "
            f"{row['format_valid_count']} | {row['province_valid_count']} | "
            f"{row['stable_text']} | {row['first_stable_frame']} | "
            f"{row['stability_status']} | {row['mean_ocr_latency_ms']} |"
        )

    content = "\n".join(
        [
            "# POCR-EXP-008 CCT-XS Event/Evidence Enrichment Summary",
            "",
            f"Tarih: {now_utc()}",
            "",
            "## Amaç",
            "",
            "Doğrulanan CCT-XS OCR baseline sonucunu tracking event skeleton kayıtlarına "
            "temporal stability gate ile bağlamak.",
            "",
            "## Kaynaklar",
            "",
            f"* Input event skeleton: `{rel(input_events.resolve())}`",
            f"* OCR summary: `{rel(ocr_summary_path.resolve())}`",
            f"* OCR engine: `{ocr_summary.get('ocr_engine')}`",
            f"* OCR model: `{ocr_summary.get('model_ref')}`",
            "* Stability gate: `stable_count=3`, `window_size=7`, `min_confidence=0.75`, "
            "`format_valid=True`, `province_code_valid=True`",
            "",
            "## Sonuç",
            "",
            "| Video | Event ID | Final Plate | OCR Status | Format Valid | Confidence | Vote Conf |",
            "|---|---|---|---|---:|---:|---:|",
            *rows,
            "",
            "## Model Çıktılarından Count Özeti",
            "",
            "| Video | Crops | OCR Read | Format Valid | Province Valid | Stable Text | First Stable Frame | Gate | Mean OCR ms |",
            "|---|---:|---:|---:|---:|---|---:|---|---:|",
            *count_rows,
            "",
            "## Çıktı",
            "",
            f"* Enriched event JSON: `models/benchmarks/artifacts/{output_json_name}`",
            f"* Model-derived count CSV: `{rel(count_csv_path.resolve())}`",
            f"* Model-derived count JSON: `{rel(count_json_path.resolve())}`",
            "",
            "## Sonraki Adım",
            "",
            "Plate/OCR baseline artık event/evidence hattına bağlı. Sonraki mantıklı faz "
            "relative speed / motion signal contract ve ilk speed baseline üretimidir.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich tracking event skeletons with CCT-XS OCR baseline.")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--ocr-summary", type=Path, default=DEFAULT_OCR_SUMMARY)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--stable-count", type=int, default=3)
    parser.add_argument("--window-size", type=int, default=7)
    parser.add_argument("--min-confidence", type=float, default=0.75)
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
    model_count_rows = []
    for event in events_data.get("events", []):
        source_video = video_key_from_event(event)
        video_ocr = ocr_index.get(source_video or "") or {}
        stability = temporal_stability_gate(
            video_ocr,
            stable_count=args.stable_count,
            window_size=args.window_size,
            min_confidence=args.min_confidence,
        )
        enriched_events.append(enrich_event(event, video_ocr, ocr_summary, output_json_name, stability))
        model_count_rows.append(model_count_row(event, video_ocr, stability))

    enriched_payload = {
        "generated_at_utc": now_utc(),
        "source_event_stage": events_data.get("event_stage"),
        "event_stage": "plate_ocr_enriched_event_skeleton",
        "source_experiment_id": events_data.get("source_experiment_id"),
        "source_ocr_experiment_id": ocr_summary.get("experiment_id"),
        "ocr_baseline_decision": "CCT-XS original + temporal stability gate",
        "stability_gate": {
            "stable_count": args.stable_count,
            "window_size": args.window_size,
            "min_confidence": args.min_confidence,
            "require_format_valid": True,
            "require_province_code_valid": True,
        },
        "events": enriched_events,
    }

    artifact_dir = args.artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / output_json_name
    output_path.write_text(json.dumps(enriched_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_dir = args.output_dir.resolve()
    count_csv_path = output_dir / "pocr_exp_008_cct_xs_model_counts.csv"
    count_json_path = output_dir / "pocr_exp_008_cct_xs_model_counts.json"
    write_model_counts(model_count_rows, count_csv_path, count_json_path)
    build_report(
        args.report.resolve(),
        events_path,
        ocr_summary_path,
        output_json_name,
        enriched_events,
        ocr_summary,
        model_count_rows,
        count_csv_path,
        count_json_path,
    )

    print(
        json.dumps(
            {
                "output_json": rel(output_path),
                "report": rel(args.report.resolve()),
                "model_count_csv": rel(count_csv_path),
                "model_count_json": rel(count_json_path),
                "event_count": len(enriched_events),
                "ocr_engine": ocr_summary.get("ocr_engine"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
