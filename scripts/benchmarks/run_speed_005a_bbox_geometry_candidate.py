#!/usr/bin/env python3
"""SPEED-EXP-005A bbox-geometry automatic speed candidate.

This experiment reruns ByteTrack on the local demo videos, extracts full
per-frame target-track bbox timelines, and derives an automatic approximate
speed candidate from bbox geometry and vehicle dimension priors.

It does not require measured road reference points. It also does not produce a
legal/final speed measurement; every km/h value is an approximate candidate.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004b.json"
DEFAULT_MODEL = ROOT / "yolo11n.pt"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_PLATE_SPEED = (
    ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-002-plate-bbox-xyz" / "speed_exp_002_plate_bbox_xyz_summary.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-005A-bbox-geometry-auto"
DEFAULT_RUNS_DIR = ROOT / "runs" / "speed" / "SPEED-EXP-005A-bbox-geometry-auto"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "speed_exp_005a_bbox_geometry_auto_candidate.md"

VEHICLE_CLASS_NAMES = {"car", "motorcycle", "bus", "truck"}
DIMENSION_PRIORS_M = {
    "car": {"height": 1.55, "width": 1.8, "length": 4.5},
    "motorcycle": {"height": 1.25, "width": 0.8, "length": 2.1},
    "bus": {"height": 3.2, "width": 2.55, "length": 11.0},
    "truck": {"height": 3.0, "width": 2.5, "length": 8.0},
    "unknown": {"height": 1.55, "width": 1.8, "length": 4.5},
}


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


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def median(values: list[float]) -> float | None:
    return round(float(statistics.median(values)), 6) if values else None


def mean(values: list[float]) -> float | None:
    return round(float(statistics.fmean(values)), 6) if values else None


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return round(float(np.percentile(np.array(values, dtype=float), q)), 6)


def rolling_median(values: list[float | None], window: int) -> list[float | None]:
    result: list[float | None] = []
    for idx in range(len(values)):
        start = max(0, idx - window + 1)
        sample = [v for v in values[start : idx + 1] if v is not None and math.isfinite(v)]
        result.append(float(statistics.median(sample)) if sample else None)
    return result


def parse_raw_track_id(track_id: str | int | None) -> int | None:
    if track_id is None:
        return None
    if isinstance(track_id, int):
        return track_id
    digits = "".join(ch for ch in str(track_id) if ch.isdigit())
    return int(digits) if digits else None


def bbox_iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def resolve_vehicle_class_ids(model: YOLO) -> list[int]:
    names = getattr(model, "names", {}) or {}
    ids = [int(idx) for idx, name in names.items() if str(name) in VEHICLE_CLASS_NAMES]
    if not ids:
        raise SystemExit(f"No vehicle class ids found in model names: {names}")
    return ids


def event_index(events_path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(events_path)
    indexed: dict[str, dict[str, Any]] = {}
    for event in data.get("events", []):
        video = (event.get("source") or {}).get("source_video")
        if video:
            indexed[video] = event
    return indexed


def plate_speed_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json(path)
    indexed: dict[str, dict[str, Any]] = {}
    for video in data.get("videos", []):
        variants = video.get("variants") or {}
        geomean = (variants.get("geomean") or {}).get("summary") or {}
        indexed[video.get("video")] = {
            "source_experiment": data.get("experiment_id"),
            "source_variant": "geomean",
            "median_speed_kmh": geomean.get("median_speed_kmh"),
            "mean_speed_kmh": geomean.get("mean_speed_kmh"),
            "confidence_note": geomean.get("confidence_note"),
            "usable_measurement_count": video.get("usable_measurement_count"),
        }
    return indexed


def focal_lengths(width: int, height: int, horizontal_fov_deg: float) -> tuple[float, float]:
    hfov = math.radians(horizontal_fov_deg)
    fx = width / (2.0 * math.tan(hfov / 2.0))
    vfov = 2.0 * math.atan(math.tan(hfov / 2.0) * (height / max(width, 1)))
    fy = height / (2.0 * math.tan(vfov / 2.0))
    return fx, fy


def observation_from_box(
    frame_id: int,
    fps: float,
    track_id: int,
    class_name: str,
    confidence: float,
    bbox: list[float],
) -> dict[str, Any]:
    x1, y1, x2, y2 = [float(v) for v in bbox]
    width = max(0.0, x2 - x1)
    height = max(0.0, y2 - y1)
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    return {
        "frame_id": frame_id,
        "time_s": frame_id / fps if fps > 0 else None,
        "track_id": track_id,
        "class_name": class_name,
        "confidence": round(float(confidence), 6),
        "bbox_xyxy": [round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)],
        "bbox_width_px": round(width, 6),
        "bbox_height_px": round(height, 6),
        "bbox_area_px": round(width * height, 6),
        "center_xy": [round(center_x, 6), round(center_y, 6)],
        "bottom_center_xy": [round(center_x, 6), round(y2, 6)],
    }


def collect_video_tracks(
    model: YOLO,
    video_path: Path,
    event: dict[str, Any],
    tracker: str,
    device: str,
    imgsz: int,
    conf: float,
) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    class_ids = resolve_vehicle_class_ids(model)
    model_names = getattr(model, "names", {}) or {}
    expected_track_id = parse_raw_track_id((event.get("target_vehicle") or {}).get("track_id"))
    target_bbox = (event.get("target_vehicle") or {}).get("bbox_xyxy") or []
    best_frame = int(((event.get("target_vehicle") or {}).get("frame_window") or {}).get("best_frame") or 0)

    observations_by_track: dict[int, list[dict[str, Any]]] = defaultdict(list)
    best_frame_candidates: list[dict[str, Any]] = []
    frame_idx = 0
    start = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        results = model.track(
            frame,
            persist=True,
            tracker=tracker,
            classes=class_ids,
            conf=conf,
            imgsz=imgsz,
            device=device,
            verbose=False,
        )
        result = results[0]
        if result.boxes is None or not getattr(result.boxes, "is_track", False) or result.boxes.id is None:
            continue
        ids = result.boxes.id.int().cpu().tolist()
        cls = result.boxes.cls.int().cpu().tolist()
        scores = result.boxes.conf.cpu().tolist()
        boxes = result.boxes.xyxy.cpu().tolist()
        for raw_track_id, class_id, score, bbox in zip(ids, cls, scores, boxes, strict=False):
            class_name = str(model_names.get(int(class_id), class_id))
            obs = observation_from_box(frame_idx, fps, int(raw_track_id), class_name, float(score), [float(v) for v in bbox])
            observations_by_track[int(raw_track_id)].append(obs)
            if frame_idx == best_frame and len(target_bbox) == 4:
                best_frame_candidates.append(
                    {
                        "raw_track_id": int(raw_track_id),
                        "iou_to_event_target": round(bbox_iou([float(v) for v in target_bbox], [float(v) for v in bbox]), 6),
                        "bbox_xyxy": obs["bbox_xyxy"],
                        "class_name": class_name,
                        "confidence": obs["confidence"],
                    }
                )

    cap.release()
    wall_time_s = time.perf_counter() - start

    selected_track_id = expected_track_id if expected_track_id in observations_by_track else None
    selection_method = "event_track_id_match" if selected_track_id is not None else None
    if selected_track_id is None and best_frame_candidates:
        best = max(best_frame_candidates, key=lambda row: row["iou_to_event_target"])
        selected_track_id = int(best["raw_track_id"])
        selection_method = "best_frame_iou_match"

    if selected_track_id is None:
        selected_track_id = max(observations_by_track, key=lambda tid: len(observations_by_track[tid])) if observations_by_track else None
        selection_method = "longest_track_fallback" if selected_track_id is not None else "no_track_found"

    return {
        "video": video_path.name,
        "frame_count": frame_count,
        "frames_processed": frame_idx,
        "fps": round(fps, 6),
        "resolution": f"{width}x{height}",
        "width": width,
        "height": height,
        "selected_raw_track_id": selected_track_id,
        "expected_raw_track_id": expected_track_id,
        "selection_method": selection_method,
        "best_frame_candidates": best_frame_candidates,
        "observations": observations_by_track.get(int(selected_track_id), []) if selected_track_id is not None else [],
        "all_track_observation_counts": {str(k): len(v) for k, v in sorted(observations_by_track.items())},
        "tracking_wall_time_s": round(wall_time_s, 6),
    }


def compute_bbox_geometry_candidate(
    video_run: dict[str, Any],
    horizontal_fov_deg: float,
    smoothing_window: int,
    max_speed_kmh: float,
) -> dict[str, Any]:
    observations = video_run["observations"]
    width = int(video_run["width"])
    height = int(video_run["height"])
    fps = float(video_run["fps"] or 0.0)
    fx, fy = focal_lengths(width, height, horizontal_fov_deg)

    enriched_rows: list[dict[str, Any]] = []
    raw_segment_speeds: list[float | None] = []
    invalid_segment_reasons: dict[str, int] = defaultdict(int)
    class_name = observations[0]["class_name"] if observations else "unknown"
    prior = DIMENSION_PRIORS_M.get(class_name, DIMENSION_PRIORS_M["unknown"])

    prev: dict[str, Any] | None = None
    for obs in observations:
        bbox_w = fnum(obs["bbox_width_px"])
        bbox_h = fnum(obs["bbox_height_px"])
        z_from_h = fy * prior["height"] / bbox_h if bbox_h > 1 else None
        z_from_w = fx * prior["width"] / bbox_w if bbox_w > 1 else None
        z_candidates = [z for z in [z_from_h, z_from_w] if z is not None and math.isfinite(z) and z > 0]
        z_m = math.sqrt(z_candidates[0] * z_candidates[1]) if len(z_candidates) == 2 else (z_candidates[0] if z_candidates else None)
        bottom_x, bottom_y = obs["bottom_center_xy"]
        x_m = ((bottom_x - width / 2.0) * z_m / fx) if z_m is not None else None
        y_norm = (bottom_y / max(height, 1)) if height else None

        speed_kmh = None
        segment_valid = True
        segment_failure_reason = None
        if prev and z_m is not None and prev.get("z_m") is not None and x_m is not None and prev.get("x_m") is not None:
            frame_delta = max(1, int(obs["frame_id"]) - int(prev["frame_id"]))
            dt_s = frame_delta / fps if fps > 0 else None
            if dt_s and dt_s > 0:
                prev_h = float(prev.get("bbox_height_px") or 0.0)
                prev_area = float(prev.get("bbox_area_px") or 0.0)
                cur_area = fnum(obs["bbox_area_px"])
                height_delta_log = abs(math.log(max(bbox_h, 1.0) / max(prev_h, 1.0))) / frame_delta
                area_delta_log = abs(math.log(max(cur_area, 1.0) / max(prev_area, 1.0))) / frame_delta
                if bbox_h < 80 or prev_h < 80:
                    segment_valid = False
                    segment_failure_reason = "bbox_too_small"
                elif height_delta_log > 0.08:
                    segment_valid = False
                    segment_failure_reason = "bbox_height_jump"
                elif area_delta_log > 0.16:
                    segment_valid = False
                    segment_failure_reason = "bbox_area_jump"
                dx = x_m - float(prev["x_m"])
                dz = z_m - float(prev["z_m"])
                candidate_speed = math.hypot(dx, dz) / dt_s * 3.6
                if candidate_speed > max_speed_kmh:
                    segment_valid = False
                    segment_failure_reason = "speed_outlier_gate"
                if segment_valid:
                    speed_kmh = candidate_speed
                elif segment_failure_reason:
                    invalid_segment_reasons[segment_failure_reason] += 1
        raw_segment_speeds.append(speed_kmh)
        row = {
            **obs,
            "vehicle_dimension_prior": {
                "class_name": class_name,
                "height_m": prior["height"],
                "width_m": prior["width"],
                "length_m": prior["length"],
            },
            "z_from_height_m": round_or_none(z_from_h),
            "z_from_width_m": round_or_none(z_from_w),
            "z_m": round_or_none(z_m),
            "x_m": round_or_none(x_m),
            "bottom_y_norm": round_or_none(y_norm),
            "segment_speed_kmh_raw": round_or_none(speed_kmh),
            "segment_valid": bool(segment_valid) if prev else None,
            "segment_failure_reason": segment_failure_reason,
        }
        enriched_rows.append(row)
        prev = {
            "frame_id": obs["frame_id"],
            "z_m": z_m,
            "x_m": x_m,
            "bbox_height_px": bbox_h,
            "bbox_area_px": obs["bbox_area_px"],
        }

    smooth = rolling_median(raw_segment_speeds, smoothing_window)
    for row, value in zip(enriched_rows, smooth, strict=False):
        row["segment_speed_kmh_smooth"] = round_or_none(value)

    usable_raw = [v for v in raw_segment_speeds if v is not None and math.isfinite(v)]
    usable_smooth = [v for v in smooth if v is not None and math.isfinite(v)]
    heights = [fnum(row["bbox_height_px"]) for row in enriched_rows]
    z_values = [fnum(row["z_m"]) for row in enriched_rows if row.get("z_m") is not None]
    speed_cv = None
    if len(usable_smooth) > 2 and statistics.fmean(usable_smooth) > 0:
        speed_cv = statistics.pstdev(usable_smooth) / statistics.fmean(usable_smooth)

    warning_flags = ["approximate_monocular_speed", "auto_scale_approximation", "not_for_legal_enforcement"]
    quality_flags: list[str] = []
    failure_flags: list[str] = []
    if len(enriched_rows) >= 60:
        quality_flags.append("track_long")
    else:
        failure_flags.append("short_track")
    if median(heights) and (median(heights) or 0) >= 80:
        quality_flags.append("bbox_height_sufficient")
    else:
        warning_flags.append("small_bbox_height")
    if usable_smooth:
        quality_flags.append("speed_candidate_available")
    else:
        failure_flags.append("no_usable_speed_segments")
    if speed_cv is not None and speed_cv > 1.2:
        warning_flags.append("speed_candidate_jitter_high")
    if invalid_segment_reasons:
        warning_flags.append("invalid_segments_filtered")

    confidence = 0.20
    confidence += 0.22 * min(len(enriched_rows) / 240.0, 1.0)
    if median(heights):
        confidence += 0.18 * min((median(heights) or 0) / 300.0, 1.0)
    if usable_smooth:
        confidence += 0.15
    if speed_cv is not None:
        confidence += 0.12 * max(0.0, min(1.0, 1.0 - speed_cv / 1.2))
        confidence -= 0.18 * max(0.0, min(1.0, (speed_cv - 1.0) / 1.5))
    if invalid_segment_reasons:
        invalid_ratio = sum(invalid_segment_reasons.values()) / max(len(enriched_rows), 1)
        confidence -= 0.12 * min(invalid_ratio * 2.0, 1.0)
    confidence = max(0.0, min(0.72, confidence))

    return {
        "source": "bbox_geometry_auto_v0",
        "speed_mode": "approximate_candidate" if usable_smooth else "unavailable",
        "estimated_kmh": median(usable_smooth),
        "speed_range_kmh": [percentile(usable_smooth, 25), percentile(usable_smooth, 75)] if usable_smooth else [None, None],
        "mean_speed_kmh": mean(usable_smooth),
        "p95_speed_kmh": percentile(usable_smooth, 95),
        "raw_median_speed_kmh": median(usable_raw),
        "confidence": round(confidence, 4),
        "quality_flags": quality_flags,
        "warning_flags": warning_flags,
        "failure_flags": failure_flags,
        "assumptions": {
            "horizontal_fov_deg": horizontal_fov_deg,
            "class_dimension_prior": prior,
            "uses_measured_road_reference": False,
            "uses_manual_homography": False,
        },
        "diagnostics": {
            "observation_count": len(enriched_rows),
            "usable_segment_count": len(usable_smooth),
            "median_bbox_height_px": median(heights),
            "median_depth_m": median(z_values),
            "speed_cv": round_or_none(speed_cv),
            "invalid_segment_reasons": dict(sorted(invalid_segment_reasons.items())),
        },
        "timeseries": enriched_rows,
    }


def write_timeseries_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "video",
        "event_id",
        "frame_id",
        "time_s",
        "track_id",
        "class_name",
        "confidence",
        "bbox_width_px",
        "bbox_height_px",
        "bbox_area_px",
        "bottom_center_x",
        "bottom_center_y",
        "z_m",
        "x_m",
        "segment_speed_kmh_raw",
        "segment_speed_kmh_smooth",
        "segment_valid",
        "segment_failure_reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            bc = row.get("bottom_center_xy") or [None, None]
            writer.writerow(
                {
                    "video": row.get("video"),
                    "event_id": row.get("event_id"),
                    "frame_id": row.get("frame_id"),
                    "time_s": row.get("time_s"),
                    "track_id": row.get("track_id"),
                    "class_name": row.get("class_name"),
                    "confidence": row.get("confidence"),
                    "bbox_width_px": row.get("bbox_width_px"),
                    "bbox_height_px": row.get("bbox_height_px"),
                    "bbox_area_px": row.get("bbox_area_px"),
                    "bottom_center_x": bc[0],
                    "bottom_center_y": bc[1],
                    "z_m": row.get("z_m"),
                    "x_m": row.get("x_m"),
                    "segment_speed_kmh_raw": row.get("segment_speed_kmh_raw"),
                    "segment_speed_kmh_smooth": row.get("segment_speed_kmh_smooth"),
                    "segment_valid": row.get("segment_valid"),
                    "segment_failure_reason": row.get("segment_failure_reason"),
                }
            )


def plot_video_speed(video_result: dict[str, Any], output_path: Path) -> None:
    rows = video_result["timeseries"]
    times = [fnum(row.get("time_s")) for row in rows]
    raw = [row.get("segment_speed_kmh_raw") for row in rows]
    smooth = [row.get("segment_speed_kmh_smooth") for row in rows]
    heights = [row.get("bbox_height_px") for row in rows]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax1 = plt.subplots(figsize=(12, 6), dpi=160)
    ax1.plot(times, raw, color="0.72", linewidth=1.0, label="raw segment speed")
    ax1.plot(times, smooth, color="0.05", linewidth=2.0, label="rolling median speed")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Approx. speed candidate (km/h)")
    ax1.grid(True, color="0.88", linewidth=0.8)
    ax1.set_title(f"SPEED-EXP-005A bbox geometry candidate — {video_result['video']}")
    ax2 = ax1.twinx()
    ax2.plot(times, heights, color="0.45", linewidth=1.0, linestyle="--", label="bbox height")
    ax2.set_ylabel("BBox height (px)")
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper right")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# SPEED-EXP-005A BBox Geometry Auto Candidate",
        "",
        "Bu rapor, manuel yol referans noktası olmadan bbox geometry + araç boyutu prior ile üretilen ilk otomatik hız adayını özetler.",
        "",
        "## Kritik Not",
        "",
        "Bu deney hukuki/final hız ölçümü değildir. `estimated_kmh` alanı yalnız `approximate_candidate` olarak yorumlanmalıdır.",
        "",
        "## Konfigürasyon",
        "",
        f"* Model: `{summary['model']}`",
        f"* Tracker: `{summary['tracker']}`",
        f"* Horizontal FOV varsayımı: `{summary['horizontal_fov_deg']}` derece",
        f"* Smoothing window: `{summary['smoothing_window']}` frame",
        f"* Plate comparison source: `{summary.get('plate_speed_source') or '-'}`",
        "",
        "## Sonuç Tablosu",
        "",
        "| Video | Track | Mode | BBox geom km/h | Range km/h | Conf | Plate geomean km/h | Warnings | Plot |",
        "|---|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for row in summary["videos"]:
        candidate = row["bbox_geometry_candidate"]
        plate = row.get("plate_scale_comparison") or {}
        speed_range = candidate.get("speed_range_kmh") or [None, None]
        range_text = (
            f"{speed_range[0]:.2f}-{speed_range[1]:.2f}"
            if speed_range[0] is not None and speed_range[1] is not None
            else "-"
        )
        lines.append(
            f"| `{row['video']}` | {row.get('selected_raw_track_id')} | `{candidate['speed_mode']}` | "
            f"{candidate.get('estimated_kmh') if candidate.get('estimated_kmh') is not None else '-'} | "
            f"{range_text} | {candidate['confidence']} | "
            f"{plate.get('median_speed_kmh') if plate.get('median_speed_kmh') is not None else '-'} | "
            f"{'|'.join(candidate.get('warning_flags') or [])} | `{row.get('plot_uri')}` |"
        )
    lines.extend(
        [
            "",
            "## Yorum",
            "",
            "* Bu sonuçlar otomatik yaklaşık hız adayıdır; sahada gerçek km/s doğrulaması yoktur.",
            "* `video_3` yüksek/oynak aday üretirse bu, 004A relative fast sinyaliyle birlikte incelenmelidir.",
            "* Plate-scale ile büyük fark varsa `candidate_disagreement_high` sonraki fusion adımında işaretlenmelidir.",
            "* Grafikler `runs/` altında tutulur ve Git'e eklenmez.",
            "",
            "## Sonraki Adım",
            "",
            "1. PNG hız grafiklerini manuel incele.",
            "2. Bbox geometry adayının plate-scale ve relative speed ile çelişkisini değerlendir.",
            "3. Gerekirse FOV/prior sensitivity sweep ekle.",
            "4. Sonra `SPEED-EXP-005B` FARSEC-lite depth adayına geç.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--plate-speed", type=Path, default=DEFAULT_PLATE_SPEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--tracker", default="bytetrack.yaml")
    parser.add_argument("--device", default="mps")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--horizontal-fov-deg", type=float, default=70.0)
    parser.add_argument("--smoothing-window", type=int, default=7)
    parser.add_argument("--max-speed-kmh", type=float, default=220.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events = event_index(args.events)
    plate_index = plate_speed_index(args.plate_speed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.runs_dir.mkdir(parents=True, exist_ok=True)

    videos_summary: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for video, event in sorted(events.items()):
        video_path = args.videos_dir / video
        if not video_path.exists():
            raise FileNotFoundError(video_path)
        print(f"Running 005A tracking/timeseries for {video}")
        model = YOLO(str(args.model))
        run = collect_video_tracks(
            model=model,
            video_path=video_path,
            event=event,
            tracker=args.tracker,
            device=args.device,
            imgsz=args.imgsz,
            conf=args.conf,
        )
        candidate = compute_bbox_geometry_candidate(
            run,
            horizontal_fov_deg=args.horizontal_fov_deg,
            smoothing_window=args.smoothing_window,
            max_speed_kmh=args.max_speed_kmh,
        )
        for row in candidate["timeseries"]:
            row["video"] = video
            row["event_id"] = event.get("event_id")
            all_rows.append(row)
        plot_path = args.runs_dir / "plots" / f"{Path(video).stem}_speed_time_plot.png"
        plot_video_speed({"video": video, "timeseries": candidate["timeseries"]}, plot_path)
        videos_summary.append(
            {
                "video": video,
                "event_id": event.get("event_id"),
                "selected_raw_track_id": run.get("selected_raw_track_id"),
                "expected_raw_track_id": run.get("expected_raw_track_id"),
                "selection_method": run.get("selection_method"),
                "frame_count": run.get("frame_count"),
                "fps": run.get("fps"),
                "resolution": run.get("resolution"),
                "all_track_observation_counts": run.get("all_track_observation_counts"),
                "bbox_geometry_candidate": {k: v for k, v in candidate.items() if k != "timeseries"},
                "plate_scale_comparison": plate_index.get(video),
                "plot_uri": rel(plot_path),
                "tracking_wall_time_s": run.get("tracking_wall_time_s"),
            }
        )

    timeseries_csv = args.output_dir / "speed_exp_005a_bbox_geometry_timeseries.csv"
    write_timeseries_csv(timeseries_csv, all_rows)
    summary_path = args.output_dir / "speed_exp_005a_bbox_geometry_summary.json"
    summary = {
        "experiment_id": "SPEED-EXP-005A",
        "stage": "bbox_geometry_auto_candidate_v0",
        "created_at": now_utc(),
        "source_events": rel(args.events),
        "model": rel(args.model),
        "tracker": args.tracker,
        "device": args.device,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "horizontal_fov_deg": args.horizontal_fov_deg,
        "smoothing_window": args.smoothing_window,
        "max_speed_kmh": args.max_speed_kmh,
        "plate_speed_source": rel(args.plate_speed) if args.plate_speed.exists() else None,
        "timeseries_csv": rel(timeseries_csv),
        "runs_dir": rel(args.runs_dir),
        "videos": videos_summary,
        "limitations": [
            "No measured road reference points are used.",
            "Vehicle dimensions and camera FOV are approximate priors.",
            "Output is an approximate candidate, not legal/final speed.",
        ],
    }
    write_json(summary_path, summary)
    write_report(args.report, summary)
    print(json.dumps({"summary": rel(summary_path), "timeseries_csv": rel(timeseries_csv), "videos": len(videos_summary)}, indent=2))


if __name__ == "__main__":
    main()
