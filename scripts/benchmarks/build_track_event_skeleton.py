#!/usr/bin/env python3
"""Build target-vehicle and event/evidence skeletons from tracking summaries.

The input is a small benchmark summary JSON produced by
`run_tracking_baseline.py`. The output is intentionally lightweight: it does
not copy frames or crops, but it creates structured JSON records that later
plate, speed, QoD and evidence modules can attach to.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMMARY = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-summary.json"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "trk_exp_001_track_to_event_summary.md"

CLASS_PRIORITY = {
    "car": 1.0,
    "truck": 0.95,
    "bus": 0.9,
    "motorcycle": 0.75,
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def rounded(value: float | None, digits: int = 3) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def bbox_area(bbox: list[float] | None) -> float:
    if not bbox or len(bbox) != 4:
        return 0.0
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def bbox_center(bbox: list[float] | None) -> list[float] | None:
    if not bbox or len(bbox) != 4:
        return None
    x1, y1, x2, y2 = bbox
    return [round((x1 + x2) / 2.0, 2), round((y1 + y2) / 2.0, 2)]


def parse_resolution(value: str) -> tuple[int, int]:
    try:
        width, height = value.lower().split("x", 1)
        return int(width), int(height)
    except Exception:
        return 0, 0


def class_purity(track: dict[str, Any]) -> float:
    votes = track.get("class_votes") or {}
    total = sum(float(v) for v in votes.values())
    if total <= 0:
        return 0.0
    return max(float(v) for v in votes.values()) / total


def track_stability(track: dict[str, Any]) -> tuple[float, list[str], bool]:
    age = int(track.get("track_age_frames") or 0)
    missed = int(track.get("missing_frame_count") or 0)
    raw_switches = int(track.get("raw_class_switches") or 0)
    mean_conf = float(track.get("mean_confidence") or 0.0)
    purity = class_purity(track)

    age_score = clamp(age / 60.0)
    continuity_score = clamp(1.0 - (missed / max(age + missed, 1)))
    switch_penalty = clamp(raw_switches / max(age, 1) * 10.0)

    score = (
        0.35 * age_score
        + 0.25 * continuity_score
        + 0.25 * purity
        + 0.15 * clamp(mean_conf)
        - 0.10 * switch_penalty
    )
    score = clamp(score)

    reasons: list[str] = []
    if age_score >= 0.75:
        reasons.append("long_track_age")
    elif age_score >= 0.35:
        reasons.append("usable_track_age")
    else:
        reasons.append("short_track_age")

    if continuity_score >= 0.9:
        reasons.append("low_missing_frame_ratio")
    elif continuity_score < 0.75:
        reasons.append("missing_frames_present")

    if purity >= 0.9:
        reasons.append("class_vote_stable")
    elif purity < 0.75:
        reasons.append("class_vote_uncertain")

    if mean_conf >= 0.7:
        reasons.append("high_mean_confidence")
    elif mean_conf < 0.45:
        reasons.append("low_mean_confidence")

    id_switch_suspected = raw_switches > 2 or purity < 0.7
    if id_switch_suspected:
        reasons.append("id_or_class_switch_review_needed")

    return round(score, 3), reasons, id_switch_suspected


def target_score(track: dict[str, Any], width: int, height: int, stability: float) -> tuple[float, list[str]]:
    age = int(track.get("track_age_frames") or 0)
    mean_conf = float(track.get("mean_confidence") or 0.0)
    stable_class = str(track.get("stable_class") or "unknown")
    bbox = track.get("best_bbox_xyxy")

    frame_area = max(width * height, 1)
    area_ratio = bbox_area(bbox) / frame_area
    area_score = clamp(area_ratio * 8.0)
    age_score = clamp(age / 60.0)
    class_score = CLASS_PRIORITY.get(stable_class, 0.55)

    center = bbox_center(bbox)
    if center and width and height:
        dx = (center[0] - width / 2.0) / max(width / 2.0, 1)
        dy = (center[1] - height / 2.0) / max(height / 2.0, 1)
        center_score = clamp(1.0 - math.sqrt(dx * dx + dy * dy) / math.sqrt(2.0))
    else:
        center_score = 0.5

    score = (
        0.35 * stability
        + 0.20 * clamp(mean_conf)
        + 0.20 * area_score
        + 0.10 * age_score
        + 0.10 * center_score
        + 0.05 * class_score
    )

    reasons: list[str] = []
    if stability >= 0.75:
        reasons.append("track_stability_high")
    elif stability >= 0.5:
        reasons.append("track_stability_usable")
    else:
        reasons.append("track_stability_low")

    if area_score >= 0.5:
        reasons.append("large_visible_bbox")
    if center_score >= 0.55:
        reasons.append("near_frame_center")
    if mean_conf >= 0.7:
        reasons.append("detector_confidence_high")
    if age_score >= 0.75:
        reasons.append("long_enough_for_temporal_modules")
    if stable_class in {"car", "truck", "bus"}:
        reasons.append("vehicle_class_prioritized_for_plate_speed")

    return round(clamp(score), 3), reasons


def normalized_track(track: dict[str, Any], video: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    width, height = parse_resolution(video.get("resolution", "0x0"))
    stability, stability_reasons, id_switch_suspected = track_stability(track)
    score, selection_reasons = target_score(track, width, height, stability)
    bbox = track.get("best_bbox_xyxy")
    return {
        "track_id": f"TRK-{int(track['track_id']):03d}",
        "raw_track_id": track["track_id"],
        "video": video["video"],
        "frame_window": {
            "first_frame": track.get("first_frame"),
            "last_frame": track.get("last_frame"),
            "best_frame": track.get("best_frame_idx"),
            "track_age_frames": track.get("track_age_frames"),
        },
        "stable_class": track.get("stable_class"),
        "class_votes": track.get("class_votes") or {},
        "class_purity": rounded(class_purity(track)),
        "raw_class_switches": track.get("raw_class_switches"),
        "mean_confidence": track.get("mean_confidence"),
        "best_confidence": track.get("best_confidence"),
        "best_bbox_xyxy": bbox,
        "best_center_xy": bbox_center(bbox),
        "missing_frame_count": track.get("missing_frame_count"),
        "missing_gap_count": track.get("missing_gap_count"),
        "track_stability": stability,
        "track_stability_reasons": stability_reasons,
        "id_switch_suspected": id_switch_suspected,
        "target_selection_score": score,
        "target_selection_reasons": selection_reasons,
        "center_history_sample": track.get("center_history_sample", []),
        "bbox_history_sample": track.get("bbox_history_sample", []),
        "history_sample_available": bool(track.get("center_history_sample") or track.get("bbox_history_sample")),
        "tracker_version": summary.get("tracker"),
        "tracker_config": summary.get("tracker_config"),
        "detector_model": summary.get("model"),
        "condition_profile": summary.get("condition_profile"),
    }


def select_target(tracks: list[dict[str, Any]]) -> dict[str, Any] | None:
    usable = [track for track in tracks if track["track_stability"] >= 0.5]
    candidates = usable or tracks
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item["target_selection_score"], item["track_stability"], item["mean_confidence"] or 0))


def build_event(video: dict[str, Any], target: dict[str, Any], summary: dict[str, Any], output_json_name: str) -> dict[str, Any]:
    event_id = f"EVT-{summary['experiment_id']}-{Path(video['video']).stem}-{target['track_id']}"
    best_frame = target["frame_window"]["best_frame"]
    frame_id = f"{Path(video['video']).stem}:frame_{int(best_frame or 0):06d}"
    qod_status = "candidate" if target["track_stability"] < 0.75 else "not_needed"
    qod_reason = (
        "Track stability is usable but not high; QoD may improve evidence quality."
        if qod_status == "candidate"
        else "Track stability and evidence metadata are sufficient for this skeleton stage."
    )
    evidence_quality = round(
        clamp(
            0.45 * target["track_stability"]
            + 0.25 * float(target.get("best_confidence") or 0)
            + 0.20 * (1.0 if target.get("best_bbox_xyxy") else 0.0)
            + 0.10 * (1.0 if target.get("history_sample_available") else 0.0)
        ),
        3,
    )
    metadata_completeness = 0.88 if target.get("history_sample_available") else 0.72

    return {
        "event_id": event_id,
        "event_type": "target_vehicle_selected",
        "timestamp_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "frame_id": frame_id,
        "source": {
            "device_id": "local_macbook_edge_baseline",
            "session_id": summary["experiment_id"],
            "camera_mode": "offline_replay",
            "resolution": video.get("resolution"),
            "fps": video.get("fps_source"),
            "orientation": "landscape",
            "network_type": "not_available_offline",
            "calibration_profile_id": None,
            "source_video": video["video"],
        },
        "system": {
            "mode": "normal",
            "qod_status": qod_status,
            "number_verification_status": "not_available",
            "latency_ms": video.get("mean_pipeline_ms"),
            "pipeline_fps": video.get("processed_fps_wall"),
            "runtime_profile": "macbook_local_edge_offline_benchmark",
        },
        "frame_quality": {
            "status": "not_run",
            "quality_flags": ["condition_profile_from_benchmark_summary"],
        },
        "target_vehicle": {
            "status": "selected",
            "track_id": target["track_id"],
            "vehicle_type": target.get("stable_class"),
            "bbox": target.get("best_bbox_xyxy"),
            "bbox_xyxy": target.get("best_bbox_xyxy"),
            "bbox_xywh": None,
            "confidence": target.get("best_confidence"),
            "track_stability": target.get("track_stability"),
            "selection_score": target.get("target_selection_score"),
            "selection_reasons": target.get("target_selection_reasons"),
            "frame_window": target.get("frame_window"),
            "class_votes": target.get("class_votes"),
            "class_purity": target.get("class_purity"),
            "id_switch_suspected": target.get("id_switch_suspected"),
        },
        "scene": {
            "status": "not_run",
            "weather": "unknown",
            "lighting": summary.get("condition_profile", "unknown"),
            "visibility": "unknown",
            "confidence": None,
        },
        "plate": {
            "status": "not_run",
            "detected": None,
            "bbox": None,
            "ocr_status": "not_run",
            "ocr_text": None,
            "format_valid": None,
            "confidence": None,
            "failure_reason": "plate_baseline_not_connected_yet",
        },
        "speed": {
            "status": "not_run",
            "mode": "not_available",
            "estimated_kmh": None,
            "relative_motion_score": None,
            "motion_anomaly": None,
            "calibration_profile_id": None,
            "confidence": None,
        },
        "lane": {
            "status": "not_run",
            "lane_status": None,
            "lane_visibility": None,
            "lane_risk": None,
            "confidence": None,
        },
        "driver_cabin": {
            "status": "not_run",
            "visibility": "not_visible",
            "driver_detected": None,
            "passenger_count": None,
            "phone_risk": None,
            "seatbelt_status": None,
            "confidence": None,
            "failure_reason": "cabin_baseline_not_connected_yet",
        },
        "external_users": [],
        "risk": {
            "risk_score": round(clamp(target["target_selection_score"] * 0.55), 3),
            "risk_level": "low",
            "reasons": [
                "tracking_candidate_event_only",
                "target_vehicle_selected_for_downstream_experts",
            ],
            "fusion_confidence": target.get("track_stability"),
            "thresholds": {
                "critical_mode_activation": "not_run",
                "target_selection_score": 0.5,
            },
        },
        "routing_decision": {
            "experts_called": ["Vehicle Detection", summary.get("tracker", "Vehicle Tracking")],
            "routing_reasons": [
                "pretrained_detector_output_available",
                "track_stability_computed",
                "target_vehicle_selected_before_plate_speed_qod",
            ],
            "qod_reason": qod_reason,
            "condition_profile": summary.get("condition_profile"),
            "selected_detector": summary.get("model"),
            "fallback_detector": summary.get("model"),
            "routing_mode": "tracking_postprocess_baseline",
            "fallbacks_used": [],
        },
        "models": {
            "vehicle_detector": summary.get("model", "unknown"),
            "vehicle_tracker": f"{summary.get('tracker', 'unknown')}:{summary.get('tracker_config', 'unknown')}",
            "target_selector": "heuristic_track_target_selector_v1",
            "event_builder": "tracking_event_skeleton_builder_v1",
        },
        "evidence": {
            "status": "partial",
            "original_frame_uri": None,
            "overlay_image_uri": video.get("annotated_video"),
            "target_vehicle_crop_uri": None,
            "plate_crop_uri": None,
            "json_uri": f"models/benchmarks/artifacts/{output_json_name}",
            "evidence_quality_score": evidence_quality,
            "metadata_completeness_score": round(metadata_completeness, 3),
            "track_history": {
                "center_history_sample": target.get("center_history_sample", []),
                "bbox_history_sample": target.get("bbox_history_sample", []),
                "history_sample_available": target.get("history_sample_available"),
            },
        },
        "explanation": {
            "user_level_summary": "Takip edilen araç, sonraki plaka, hız ve QoD modüllerine hedef aday olarak seçildi.",
            "technical_summary": (
                f"{target['track_id']} için stable_class={target.get('stable_class')}, "
                f"track_stability={target.get('track_stability')}, "
                f"selection_score={target.get('target_selection_score')} hesaplandı. "
                "Bu kayıt gerçek risk kararı değil, takipten event/evidence hattına geçiş skeleton'ıdır."
            ),
            "llm_used": False,
            "llm_provider": None,
            "template_fallback_used": True,
            "source": "template",
        },
    }


def build_outputs(summary: dict[str, Any], output_json_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    postprocess = {
        "generated_at_utc": generated_at,
        "source_experiment_id": summary["experiment_id"],
        "source_tracker": summary.get("tracker"),
        "source_model": summary.get("model"),
        "condition_profile": summary.get("condition_profile"),
        "purpose": "tracking_output_normalization_target_selection",
        "videos": [],
        "limitations": [],
    }
    events = {
        "generated_at_utc": generated_at,
        "source_experiment_id": summary["experiment_id"],
        "event_stage": "tracking_candidate_event_skeleton",
        "events": [],
    }

    missing_history = False
    for video in summary.get("videos", []):
        width, height = parse_resolution(video.get("resolution", "0x0"))
        tracks = [normalized_track(track, video, summary) for track in video.get("tracks", [])]
        missing_history = missing_history or any(not track["history_sample_available"] for track in tracks)
        target = select_target(tracks)
        video_record = {
            "video": video["video"],
            "resolution": video.get("resolution"),
            "fps_source": video.get("fps_source"),
            "frames_processed": video.get("frames_processed"),
            "frame_size": {"width": width, "height": height},
            "track_count": len(tracks),
            "tracks": tracks,
            "selected_target_track_id": target["track_id"] if target else None,
            "selected_target_score": target["target_selection_score"] if target else None,
        }
        postprocess["videos"].append(video_record)
        if target:
            events["events"].append(build_event(video, target, summary, output_json_name))

    if missing_history:
        postprocess["limitations"].append(
            "Some source tracks do not include center/bbox history samples; rerun run_tracking_baseline.py after the 2026-06-11 update to populate them."
        )

    return postprocess, events


def write_report(path: Path, summary: dict[str, Any], postprocess: dict[str, Any], events: dict[str, Any]) -> None:
    rows = []
    for video in postprocess["videos"]:
        target_id = video["selected_target_track_id"]
        target = next((track for track in video["tracks"] if track["track_id"] == target_id), None)
        rows.append(
            [
                video["video"],
                str(video["track_count"]),
                target_id or "none",
                str(target["stable_class"] if target else "none"),
                str(target["track_stability"] if target else "none"),
                str(target["target_selection_score"] if target else "none"),
            ]
        )

    table = "\n".join(
        ["| Video | Track Count | Selected Target | Stable Class | Track Stability | Selection Score |",
         "|---|---:|---|---|---:|---:|"]
        + [f"| {' | '.join(row)} |" for row in rows]
    )
    content = f"""# TRK-EXP-001 Track-to-Event Summary

Tarih: 2026-06-11

## Amaç

ByteTrack çıktısını sistemin target vehicle selection ve event/evidence skeleton hattına bağlamak.

Bu rapor gerçek risk tespiti iddiası kurmaz. Üretilen eventler `target_vehicle_selected` seviyesinde ara kayıt/skeleton niteliğindedir.

## Kaynak

* Experiment: `{summary['experiment_id']}`
* Tracker: `{summary.get('tracker')}` / `{summary.get('tracker_config')}`
* Detector: `{summary.get('model')}`
* Condition profile: `{summary.get('condition_profile')}`

## Üretilen Artifactler

* Track post-process JSON: `models/benchmarks/artifacts/{summary['experiment_id']}-yolo11n-bytetrack-track-postprocess.json`
* Event skeleton JSON: `models/benchmarks/artifacts/{summary['experiment_id']}-yolo11n-bytetrack-event-skeletons.json`

## Seçilen Hedefler

{table}

## Uygulanan Heuristikler

* `track_stability`: track yaşı, missing frame oranı, confidence, class vote purity ve class switch sinyalinin birleşimi.
* `stable_class`: benchmark summary içindeki confidence ağırlıklı class vote sonucudur.
* `target_selection_score`: track stability, confidence, bbox görünürlüğü, frame merkezine yakınlık, track yaşı ve sınıf önceliğinin birleşimi.
* `qod_status`: bu aşamada gerçek QoD isteği değildir; skeleton event içinde evidence kalitesi düşükse `candidate`, aksi halde `not_needed` olarak işaretlenir.

## Sınırlamalar

* Bu aşamada speed, plate OCR, lane ve cabin modülleri çalıştırılmadı.
* Eventler karar destek skeleton'ıdır; kritik olay veya hukuki sonuç üretmez.
* History sample alanları yalnız güncel tracking benchmark script'iyle üretilmiş summary dosyalarında dolar.

## Sonraki Adım

Seçilen `target_track_id` üzerinden relative speed baseline kurulmalı. Ardından aynı track penceresi üstünde plate detection/OCR temporal voting eklenmelidir.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary_path = args.summary.resolve()
    artifact_dir = args.artifact_dir.resolve()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    stem = summary_path.stem.replace("-summary", "")
    postprocess_name = f"{stem}-track-postprocess.json"
    events_name = f"{stem}-event-skeletons.json"
    postprocess, events = build_outputs(summary, events_name)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / postprocess_name).write_text(json.dumps(postprocess, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (artifact_dir / events_name).write_text(json.dumps(events, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(args.report.resolve(), summary, postprocess, events)

    print(
        json.dumps(
            {
                "postprocess": str((artifact_dir / postprocess_name).relative_to(ROOT)),
                "events": str((artifact_dir / events_name).relative_to(ROOT)),
                "report": str(args.report.resolve().relative_to(ROOT)),
                "event_count": len(events["events"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
