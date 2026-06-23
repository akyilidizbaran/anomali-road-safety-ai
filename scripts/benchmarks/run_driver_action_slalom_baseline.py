#!/usr/bin/env python3
"""DACT-EXP-001 track-residual slalom baseline.

This experiment does not train a model. It reads the existing target-track
timeseries produced by SPEED-EXP-005A, removes the dominant lateral trend, and
scores repeated lateral oscillation as a slalom candidate signal.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMESERIES = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "speed"
    / "SPEED-EXP-005A-bbox-geometry-auto"
    / "speed_exp_005a_bbox_geometry_timeseries.csv"
)
DEFAULT_EVENTS = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed005d.json"
)
DEFAULT_SPEED_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "speed"
    / "SPEED-EXP-005A-bbox-geometry-auto"
    / "speed_exp_005a_bbox_geometry_summary.json"
)
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_RUNS_DIR = ROOT / "runs" / "driver_action" / "slalom_exp_001"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "dact_exp_001_slalom_track_heuristic.md"
DEFAULT_VIDEOS_DIR = ROOT / "Test"

EXPERIMENT_ID = "DACT-EXP-001"
MODEL_KEY = "track_lateral_residual_slalom_heuristic_v1"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def inum(value: Any, default: int | None = None) -> int | None:
    if value in ("", None):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def rounded(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), digits)


def moving_average(values: np.ndarray, window: int) -> np.ndarray:
    if len(values) == 0:
        return values
    window = max(1, min(int(window), len(values)))
    if window % 2 == 0:
        window -= 1
    if window <= 1:
        return values.copy()
    pad = window // 2
    padded = np.pad(values, (pad, pad), mode="edge")
    return np.convolve(padded, np.ones(window) / window, mode="valid")


def load_timeseries(path: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            parsed = {
                "video": row.get("video"),
                "event_id": row.get("event_id"),
                "frame_id": inum(row.get("frame_id")),
                "time_s": fnum(row.get("time_s")),
                "track_id": row.get("track_id"),
                "class_name": row.get("class_name"),
                "confidence": fnum(row.get("confidence")),
                "bbox_width_px": fnum(row.get("bbox_width_px")),
                "bbox_height_px": fnum(row.get("bbox_height_px")),
                "bbox_area_px": fnum(row.get("bbox_area_px")),
                "bottom_center_x": fnum(row.get("bottom_center_x")),
                "bottom_center_y": fnum(row.get("bottom_center_y")),
                "segment_speed_kmh_moving_avg": fnum(row.get("segment_speed_kmh_moving_avg")),
                "segment_valid": str(row.get("segment_valid") or "").lower() == "true",
                "segment_failure_reason": row.get("segment_failure_reason") or None,
            }
            if parsed["video"]:
                grouped[str(parsed["video"])].append(parsed)
    for rows in grouped.values():
        rows.sort(key=lambda item: item.get("frame_id") or -1)
    return grouped


def event_by_video(events: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed = {}
    for event in events.get("events", []):
        video = (event.get("source") or {}).get("source_video")
        if video:
            indexed[str(video)] = event
    return indexed


def speed_summary_by_video(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json(path)
    return {str(item["video"]): item for item in data.get("videos", []) if item.get("video")}


def resolution_from_summary(video_summary: dict[str, Any] | None) -> tuple[int | None, int | None]:
    if not video_summary:
        return None, None
    value = str(video_summary.get("resolution") or "")
    if "x" not in value:
        return None, None
    left, right = value.lower().split("x", 1)
    try:
        return int(left), int(right)
    except ValueError:
        return None, None


def filter_rows(rows: list[dict[str, Any]], args: argparse.Namespace, frame_width: int | None) -> tuple[list[dict[str, Any]], Counter[str], Counter[str]]:
    drop_reasons: Counter[str] = Counter()
    diagnostic_reasons: Counter[str] = Counter()
    usable = []
    for row in rows:
        required = [
            row.get("frame_id"),
            row.get("time_s"),
            row.get("bottom_center_x"),
            row.get("bottom_center_y"),
            row.get("bbox_width_px"),
            row.get("bbox_height_px"),
            row.get("confidence"),
        ]
        if any(value is None for value in required):
            drop_reasons["missing_required_fields"] += 1
            continue
        if float(row["confidence"]) < args.min_confidence:
            drop_reasons["low_confidence"] += 1
            continue
        if float(row["bbox_width_px"]) < args.min_bbox_width:
            drop_reasons["bbox_too_narrow"] += 1
            continue
        if float(row["bbox_height_px"]) < args.min_bbox_height:
            drop_reasons["bbox_too_short"] += 1
            continue
        if frame_width:
            x = float(row["bottom_center_x"])
            half_w = float(row["bbox_width_px"]) / 2.0
            x1 = x - half_w
            x2 = x + half_w
            if x1 <= args.edge_margin_px or x2 >= frame_width - args.edge_margin_px:
                diagnostic_reasons["edge_cutoff_observed"] += 1
                if args.drop_edge_cutoff:
                    drop_reasons["edge_cutoff_dropped"] += 1
                    continue
        usable.append(row)
    return usable, drop_reasons, diagnostic_reasons


def count_direction_changes(smoothed: np.ndarray, times: np.ndarray, velocity_deadband: float) -> tuple[int, list[int], list[int], np.ndarray]:
    if len(smoothed) < 3:
        return 0, [], [], np.array([])
    dt = np.diff(times)
    dy = np.diff(smoothed)
    velocity = np.divide(dy, dt, out=np.zeros_like(dy), where=dt > 0)
    signs: list[int] = []
    for value in velocity:
        if abs(float(value)) < velocity_deadband:
            signs.append(0)
        else:
            signs.append(1 if value > 0 else -1)

    compressed: list[int] = []
    turn_indexes: list[int] = []
    last_sign = 0
    for idx, sign in enumerate(signs):
        if sign == 0:
            continue
        if last_sign and sign != last_sign:
            turn_indexes.append(idx + 1)
        if not compressed or compressed[-1] != sign:
            compressed.append(sign)
        last_sign = sign
    return max(0, len(compressed) - 1), compressed, turn_indexes, velocity


def slalom_status(
    valid_count: int,
    total_count: int,
    duration_s: float,
    amplitude_norm: float,
    rms_norm: float,
    direction_changes: int,
    args: argparse.Namespace,
) -> tuple[str, list[str], list[str]]:
    quality_flags: list[str] = []
    warning_flags: list[str] = ["relative_motion_only_no_lane_ground_truth"]
    valid_ratio = valid_count / max(total_count, 1)
    if duration_s >= args.min_track_duration:
        quality_flags.append("track_duration_sufficient")
    if valid_ratio >= args.min_valid_frame_ratio:
        quality_flags.append("valid_frame_ratio_sufficient")
    if direction_changes >= args.min_direction_changes:
        quality_flags.append("direction_changes_present")
    if amplitude_norm >= args.candidate_amplitude_norm:
        quality_flags.append("lateral_amplitude_candidate_level")
    elif amplitude_norm >= args.review_amplitude_norm:
        quality_flags.append("lateral_amplitude_review_level")

    if duration_s < args.min_track_duration:
        return "not_evaluable", quality_flags, warning_flags + ["track_too_short"]
    if valid_ratio < args.min_valid_frame_ratio:
        return "not_evaluable", quality_flags, warning_flags + ["insufficient_valid_frames"]
    if (
        direction_changes >= args.min_direction_changes
        and amplitude_norm >= args.candidate_amplitude_norm
        and rms_norm >= args.min_candidate_rms_norm
    ):
        return "candidate", quality_flags, warning_flags
    if direction_changes >= args.min_direction_changes and amplitude_norm >= args.review_amplitude_norm:
        return "review", quality_flags, warning_flags + ["below_candidate_amplitude_threshold"]
    return "not_detected", quality_flags, warning_flags


def compute_slalom(video: str, rows: list[dict[str, Any]], video_summary: dict[str, Any] | None, args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    frame_width, frame_height = resolution_from_summary(video_summary)
    usable_rows, drop_reasons, diagnostic_reasons = filter_rows(rows, args, frame_width)
    if len(usable_rows) < args.min_points:
        result = {
            "video": video,
            "event_id": rows[0].get("event_id") if rows else None,
            "status": "not_evaluable",
            "failure_reason": "insufficient_track_points",
            "total_points": len(rows),
            "valid_points": len(usable_rows),
            "dropped_reason_counts": dict(drop_reasons),
            "diagnostic_reason_counts": dict(diagnostic_reasons),
        }
        return result, []

    times = np.array([float(row["time_s"]) for row in usable_rows], dtype=float)
    times = times - times[0]
    x = np.array([float(row["bottom_center_x"]) for row in usable_rows], dtype=float)
    y = np.array([float(row["bottom_center_y"]) for row in usable_rows], dtype=float)
    widths = np.array([float(row["bbox_width_px"]) for row in usable_rows], dtype=float)
    heights = np.array([float(row["bbox_height_px"]) for row in usable_rows], dtype=float)
    confidences = np.array([float(row["confidence"]) for row in usable_rows], dtype=float)

    median_width = float(np.median(widths))
    degree = min(args.trend_degree, len(usable_rows) - 1)
    degree = max(1, degree)
    trend_coefficients = np.polyfit(times, x, degree)
    trend_x = np.polyval(trend_coefficients, times)
    residual_px = x - trend_x
    residual_norm = residual_px / max(median_width, 1.0)
    smoothed = moving_average(residual_norm, args.smoothing_window)

    duration_s = float(times[-1] - times[0]) if len(times) else 0.0
    amplitude_norm = float(np.percentile(smoothed, 95) - np.percentile(smoothed, 5))
    max_abs_norm = float(np.max(np.abs(smoothed)))
    rms_norm = float(math.sqrt(float(np.mean(smoothed**2))))
    roughness_norm = float(np.percentile(np.abs(np.diff(smoothed)), 95)) if len(smoothed) > 1 else 0.0
    velocity_seed = np.diff(smoothed) / np.maximum(np.diff(times), 1e-6) if len(smoothed) > 1 else np.array([])
    velocity_deadband = max(
        args.min_velocity_deadband_norm_s,
        float(np.percentile(np.abs(velocity_seed), 50)) * args.velocity_deadband_median_factor if len(velocity_seed) else 0.0,
    )
    direction_changes, compressed_signs, turn_indexes, velocity = count_direction_changes(smoothed, times, velocity_deadband)

    valid_ratio = len(usable_rows) / max(len(rows), 1)
    amplitude_score = clamp((amplitude_norm - args.low_amplitude_norm) / max(args.high_amplitude_norm - args.low_amplitude_norm, 1e-6))
    change_score = clamp(direction_changes / max(args.high_direction_changes, 1))
    rms_score = clamp(rms_norm / max(args.high_rms_norm, 1e-6))
    valid_score = clamp(valid_ratio)
    duration_score = clamp(duration_s / max(args.high_duration_s, 1e-6))
    jitter_penalty = clamp(roughness_norm / max(args.high_roughness_norm, 1e-6)) * args.roughness_penalty_weight
    score = clamp(
        0.42 * amplitude_score
        + 0.24 * change_score
        + 0.16 * rms_score
        + 0.10 * valid_score
        + 0.08 * duration_score
        - jitter_penalty
    )
    confidence = clamp(
        0.25
        + 0.35 * score
        + 0.20 * valid_score
        + 0.10 * clamp(float(np.mean(confidences)))
        + 0.10 * (1.0 - clamp(roughness_norm / max(args.high_roughness_norm, 1e-6)))
    )
    status, quality_flags, warning_flags = slalom_status(
        len(usable_rows),
        len(rows),
        duration_s,
        amplitude_norm,
        rms_norm,
        direction_changes,
        args,
    )
    failure_reason = None
    if status == "not_evaluable":
        failure_reason = "track_quality_insufficient"
    elif status == "not_detected":
        failure_reason = "slalom_thresholds_not_met"
    elif status == "review":
        failure_reason = "candidate_threshold_not_met_manual_review_required"

    enriched_rows: list[dict[str, Any]] = []
    velocity_by_index = [None] + [float(value) for value in velocity]
    turn_set = set(turn_indexes)
    for idx, row in enumerate(usable_rows):
        enriched_rows.append(
            {
                "video": video,
                "event_id": row.get("event_id"),
                "frame_id": row.get("frame_id"),
                "time_s": round(float(row["time_s"]), 6),
                "bottom_center_x": round(float(row["bottom_center_x"]), 6),
                "bottom_center_y": round(float(row["bottom_center_y"]), 6),
                "bbox_width_px": round(float(row["bbox_width_px"]), 6),
                "bbox_height_px": round(float(row["bbox_height_px"]), 6),
                "trend_x": round(float(trend_x[idx]), 6),
                "lateral_residual_px": round(float(residual_px[idx]), 6),
                "lateral_residual_norm": round(float(residual_norm[idx]), 6),
                "lateral_residual_norm_smooth": round(float(smoothed[idx]), 6),
                "lateral_velocity_norm_s": rounded(velocity_by_index[idx], 6),
                "direction_turn": idx in turn_set,
                "segment_speed_kmh_moving_avg": rounded(row.get("segment_speed_kmh_moving_avg"), 6),
            }
        )

    result = {
        "video": video,
        "event_id": usable_rows[0].get("event_id"),
        "status": status,
        "slalom_candidate": status == "candidate",
        "score": round(score, 6),
        "confidence": round(confidence, 6),
        "failure_reason": failure_reason,
        "method": MODEL_KEY,
        "total_points": len(rows),
        "valid_points": len(usable_rows),
        "valid_frame_ratio": round(valid_ratio, 6),
        "track_duration_seconds": round(duration_s, 6),
        "direction_change_count": direction_changes,
        "direction_sign_sequence": compressed_signs,
        "turn_frame_ids": [usable_rows[idx].get("frame_id") for idx in turn_indexes if idx < len(usable_rows)],
        "normalized_lateral_amplitude": round(amplitude_norm, 6),
        "normalized_lateral_rms": round(rms_norm, 6),
        "normalized_lateral_max_abs": round(max_abs_norm, 6),
        "residual_roughness_p95": round(roughness_norm, 6),
        "median_bbox_width_px": round(median_width, 6),
        "median_bbox_height_px": round(float(np.median(heights)), 6),
        "mean_confidence": round(float(np.mean(confidences)), 6),
        "velocity_deadband_norm_s": round(velocity_deadband, 6),
        "trend_degree": degree,
        "trend_coefficients": [round(float(value), 9) for value in trend_coefficients.tolist()],
        "quality_flags": quality_flags,
        "warning_flags": warning_flags,
        "dropped_reason_counts": dict(drop_reasons),
        "diagnostic_reason_counts": dict(diagnostic_reasons),
        "thresholds": {
            "min_track_duration": args.min_track_duration,
            "min_valid_frame_ratio": args.min_valid_frame_ratio,
            "min_direction_changes": args.min_direction_changes,
            "candidate_amplitude_norm": args.candidate_amplitude_norm,
            "review_amplitude_norm": args.review_amplitude_norm,
            "min_candidate_rms_norm": args.min_candidate_rms_norm,
        },
    }
    if frame_width and frame_height:
        result["source_resolution"] = f"{frame_width}x{frame_height}"
    return result, enriched_rows


def write_timeseries(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "video",
        "event_id",
        "frame_id",
        "time_s",
        "bottom_center_x",
        "bottom_center_y",
        "bbox_width_px",
        "bbox_height_px",
        "trend_x",
        "lateral_residual_px",
        "lateral_residual_norm",
        "lateral_residual_norm_smooth",
        "lateral_velocity_norm_s",
        "direction_turn",
        "segment_speed_kmh_moving_avg",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_video(video_result: dict[str, Any], rows: list[dict[str, Any]], output_dir: Path) -> str | None:
    if not rows:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    video_stem = Path(str(video_result["video"])).stem
    output_path = output_dir / f"{video_stem}_slalom_residual_plot.png"
    times = [float(row["time_s"]) for row in rows]
    residual = [float(row["lateral_residual_norm_smooth"]) for row in rows]
    velocity = [row["lateral_velocity_norm_s"] for row in rows]
    speed = [row["segment_speed_kmh_moving_avg"] for row in rows]
    turn_times = [float(row["time_s"]) for row in rows if row.get("direction_turn")]
    turn_values = [float(row["lateral_residual_norm_smooth"]) for row in rows if row.get("direction_turn")]

    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    fig.suptitle(
        f"{video_result['video']} | status={video_result['status']} | score={video_result['score']:.3f}",
        fontsize=12,
    )
    axes[0].plot(times, residual, linewidth=1.6, color="black", label="smoothed residual / bbox width")
    if turn_times:
        axes[0].scatter(turn_times, turn_values, s=28, color="dimgray", marker="x", label="direction turn")
    axes[0].axhline(0, color="gray", linewidth=0.8)
    axes[0].set_ylabel("lateral residual")
    axes[0].legend(loc="best", fontsize=8)
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(times, velocity, linewidth=1.2, color="black")
    axes[1].axhline(video_result["velocity_deadband_norm_s"], color="gray", linewidth=0.8, linestyle="--")
    axes[1].axhline(-video_result["velocity_deadband_norm_s"], color="gray", linewidth=0.8, linestyle="--")
    axes[1].set_ylabel("lateral velocity")
    axes[1].grid(True, alpha=0.25)

    axes[2].plot(times, speed, linewidth=1.2, color="black")
    axes[2].set_ylabel("speed cand. km/h")
    axes[2].set_xlabel("time (s)")
    axes[2].grid(True, alpha=0.25)
    axes[2].text(
        0.01,
        0.95,
        (
            f"amp={video_result['normalized_lateral_amplitude']:.3f}, "
            f"turns={video_result['direction_change_count']}, "
            f"conf={video_result['confidence']:.3f}"
        ),
        transform=axes[2].transAxes,
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "gray", "alpha": 0.85},
    )

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return rel(output_path)


def draw_label(frame: Any, text: str, org: tuple[int, int], color: tuple[int, int, int]) -> None:
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.68, color, 2, cv2.LINE_AA)


def make_overlay(video_path: Path, rows: list[dict[str, Any]], video_result: dict[str, Any], output_dir: Path) -> str | None:
    if not video_path.exists() or not rows:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    by_frame = {int(row["frame_id"]): row for row in rows if row.get("frame_id") is not None}
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    output_path = output_dir / f"{video_path.stem}_slalom_track_heuristic.mp4"
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        cap.release()
        return None

    path_points: list[tuple[int, int]] = []
    frame_index = 0
    status = str(video_result["status"])
    color = {
        "candidate": (0, 0, 255),
        "review": (0, 165, 255),
        "not_detected": (180, 180, 180),
        "not_evaluable": (120, 120, 120),
    }.get(status, (255, 255, 255))
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_index += 1
            row = by_frame.get(frame_index)
            if row:
                point = (int(float(row["bottom_center_x"])), int(float(row["bottom_center_y"])))
                path_points.append(point)
                if len(path_points) > 160:
                    path_points = path_points[-160:]
                for i in range(1, len(path_points)):
                    cv2.line(frame, path_points[i - 1], path_points[i], (220, 220, 220), 2, cv2.LINE_AA)
                cv2.circle(frame, point, 6, color, -1, cv2.LINE_AA)
                residual = float(row["lateral_residual_norm_smooth"])
                draw_label(frame, f"residual_norm: {residual:+.3f}", (32, 92), (255, 255, 255))
            draw_label(frame, f"slalom: {status}", (32, 36), color)
            draw_label(
                frame,
                f"score={video_result['score']:.3f} conf={video_result['confidence']:.3f} turns={video_result['direction_change_count']}",
                (32, 64),
                (255, 255, 255),
            )
            writer.write(frame)
    finally:
        cap.release()
        writer.release()
    return rel(output_path)


def enrich_events(events_data: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    by_event = {item.get("event_id"): item for item in results}
    enriched = json.loads(json.dumps(events_data))
    enriched["driver_action_experiment_id"] = EXPERIMENT_ID
    enriched["driver_action_note"] = "Slalom is a calibration-free track residual candidate, not a legal determination."
    for event in enriched.get("events", []):
        result = by_event.get(event.get("event_id"))
        if not result:
            continue
        driver_action = event.setdefault("driver_action", {})
        driver_action["slalom"] = {
            "status": result["status"],
            "detected": result["status"] == "candidate",
            "score": result["score"],
            "confidence": result["confidence"],
            "direction_change_count": result["direction_change_count"],
            "normalized_lateral_amplitude": result["normalized_lateral_amplitude"],
            "normalized_lateral_rms": result["normalized_lateral_rms"],
            "track_duration_seconds": result["track_duration_seconds"],
            "method": MODEL_KEY,
            "failure_reason": result["failure_reason"],
            "warning_flags": result["warning_flags"],
            "quality_flags": result["quality_flags"],
            "plot_uri": result.get("plot_uri"),
            "overlay_video_uri": result.get("overlay_video_uri"),
            "not_for_legal_enforcement": True,
        }
        risk = event.setdefault("risk", {})
        risk.setdefault("risk_factors", [])
        if result["status"] == "candidate" and "slalom_candidate" not in risk["risk_factors"]:
            risk["risk_factors"].append("slalom_candidate")
    return enriched


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DACT-EXP-001 Slalom Track Heuristic Baseline",
        "",
        f"Date: {summary['generated_at_utc']}",
        "",
        "## Purpose",
        "",
        "This experiment estimates a `slalom` driver-action candidate from the existing target vehicle track.",
        "It does not train a model and does not claim legal or final driving-behavior truth.",
        "",
        "## Inputs",
        "",
        f"* Timeseries: `{summary['inputs']['timeseries_csv']}`",
        f"* Events: `{summary['inputs']['events_json']}`",
        "",
        "## Method",
        "",
        "1. Read target-track bottom-center and bbox geometry from SPEED-EXP-005A.",
        "2. Fit a low-degree lateral trend to bottom-center x over time.",
        "3. Subtract the trend and normalize residuals by median bbox width.",
        "4. Smooth the normalized residual curve.",
        "5. Count meaningful lateral direction changes and score residual amplitude.",
        "6. Write `candidate`, `review`, `not_detected`, or `not_evaluable` into event/evidence JSON.",
        "",
        "## Results",
        "",
        "| Video | Status | Score | Confidence | Direction changes | Normalized amplitude | Track duration | Plot | Overlay |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in summary["videos"]:
        lines.append(
            "| {video} | {status} | {score:.3f} | {confidence:.3f} | {direction_change_count} | "
            "{normalized_lateral_amplitude:.3f} | {track_duration_seconds:.2f}s | `{plot}` | `{overlay}` |".format(
                video=item["video"],
                status=item["status"],
                score=float(item.get("score") or 0.0),
                confidence=float(item.get("confidence") or 0.0),
                direction_change_count=int(item.get("direction_change_count") or 0),
                normalized_lateral_amplitude=float(item.get("normalized_lateral_amplitude") or 0.0),
                track_duration_seconds=float(item.get("track_duration_seconds") or 0.0),
                plot=item.get("plot_uri") or "",
                overlay=item.get("overlay_video_uri") or "",
            )
        )
    lines.extend(
        [
            "",
        "## Interpretation",
        "",
        "* `candidate` means the current heuristic found repeated lateral oscillation with enough normalized amplitude.",
        "* `review` means direction changes exist but amplitude is below the candidate threshold.",
        "* `not_detected` means the thresholds were not met.",
        "* `not_evaluable` means the track quality or duration was insufficient.",
        "* `confidence` is confidence in the heuristic status decision, not ground-truth slalom accuracy.",
        "",
        "Default candidate gate:",
        "",
        "```text",
        "track_duration >= 2.0s",
        "valid_frame_ratio >= 0.70",
        "direction_change_count >= 2",
        "normalized_lateral_amplitude >= 0.30",
        "normalized_lateral_rms >= 0.08",
        "```",
        "",
        "This is a first smoke baseline. The output must be checked visually with the residual plots and overlay videos.",
            "",
            "## Limitations",
            "",
            "* No lane-line ground truth is used.",
            "* No human slalom annotation is used.",
            "* Perspective effects are reduced by trend removal and bbox-width normalization, but not fully solved.",
            "* Normal lane changes or curved-road camera geometry may still require manual review.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeseries", type=Path, default=DEFAULT_TIMESERIES)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--speed-summary", type=Path, default=DEFAULT_SPEED_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-confidence", type=float, default=0.25)
    parser.add_argument("--min-bbox-width", type=float, default=40.0)
    parser.add_argument("--min-bbox-height", type=float, default=40.0)
    parser.add_argument("--edge-margin-px", type=float, default=0.0)
    parser.add_argument("--drop-edge-cutoff", action="store_true")
    parser.add_argument("--min-points", type=int, default=40)
    parser.add_argument("--trend-degree", type=int, default=2)
    parser.add_argument("--smoothing-window", type=int, default=11)
    parser.add_argument("--min-track-duration", type=float, default=2.0)
    parser.add_argument("--min-valid-frame-ratio", type=float, default=0.70)
    parser.add_argument("--min-direction-changes", type=int, default=2)
    parser.add_argument("--candidate-amplitude-norm", type=float, default=0.30)
    parser.add_argument("--review-amplitude-norm", type=float, default=0.18)
    parser.add_argument("--min-candidate-rms-norm", type=float, default=0.08)
    parser.add_argument("--low-amplitude-norm", type=float, default=0.12)
    parser.add_argument("--high-amplitude-norm", type=float, default=0.45)
    parser.add_argument("--high-direction-changes", type=int, default=4)
    parser.add_argument("--high-rms-norm", type=float, default=0.16)
    parser.add_argument("--high-duration-s", type=float, default=6.0)
    parser.add_argument("--high-roughness-norm", type=float, default=0.025)
    parser.add_argument("--roughness-penalty-weight", type=float, default=0.08)
    parser.add_argument("--min-velocity-deadband-norm-s", type=float, default=0.03)
    parser.add_argument("--velocity-deadband-median-factor", type=float, default=0.40)
    parser.add_argument("--skip-overlays", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timeseries = load_timeseries(args.timeseries)
    events_data = load_json(args.events)
    events_index = event_by_video(events_data)
    summaries = speed_summary_by_video(args.speed_summary)

    artifact_root = args.artifact_dir / "driver_action" / f"{EXPERIMENT_ID}-slalom-track-heuristic"
    plots_dir = args.runs_dir / "plots"
    overlays_dir = args.runs_dir / "annotated"
    summary_path = artifact_root / "dact_exp_001_slalom_track_heuristic_summary.json"
    timeseries_path = artifact_root / "dact_exp_001_slalom_track_heuristic_timeseries.csv"
    enriched_events_path = args.artifact_dir / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-slalom.json"

    video_results: list[dict[str, Any]] = []
    enriched_rows: list[dict[str, Any]] = []
    for video, rows in sorted(timeseries.items()):
        result, rows_out = compute_slalom(video, rows, summaries.get(video), args)
        result["source_event_present"] = video in events_index
        plot_uri = plot_video(result, rows_out, plots_dir)
        result["plot_uri"] = plot_uri
        if not args.skip_overlays:
            overlay_uri = make_overlay(args.videos_dir / video, rows_out, result, overlays_dir)
            result["overlay_video_uri"] = overlay_uri
        else:
            result["overlay_video_uri"] = None
        video_results.append(result)
        enriched_rows.extend(rows_out)

    enriched_events = enrich_events(events_data, video_results)
    write_json(enriched_events_path, enriched_events)
    write_timeseries(timeseries_path, enriched_rows)

    summary = {
        "generated_at_utc": now_utc(),
        "experiment_id": EXPERIMENT_ID,
        "model_key": MODEL_KEY,
        "purpose": "Calibration-free slalom candidate from target-track lateral residual.",
        "inputs": {
            "timeseries_csv": rel(args.timeseries),
            "events_json": rel(args.events),
            "speed_summary_json": rel(args.speed_summary),
        },
        "outputs": {
            "summary_json": rel(summary_path),
            "timeseries_csv": rel(timeseries_path),
            "enriched_events_json": rel(enriched_events_path),
            "runs_dir": rel(args.runs_dir),
            "report": rel(args.report),
        },
        "settings": {
            "min_confidence": args.min_confidence,
            "trend_degree": args.trend_degree,
            "smoothing_window": args.smoothing_window,
            "min_track_duration": args.min_track_duration,
            "min_valid_frame_ratio": args.min_valid_frame_ratio,
            "min_direction_changes": args.min_direction_changes,
            "candidate_amplitude_norm": args.candidate_amplitude_norm,
            "review_amplitude_norm": args.review_amplitude_norm,
            "min_candidate_rms_norm": args.min_candidate_rms_norm,
        },
        "videos": video_results,
        "limitations": [
            "No lane-line ground truth.",
            "No human slalom labels.",
            "Calibration-free track residual signal only.",
            "Manual review required before using this as final FTR behavior evidence.",
        ],
    }
    write_json(summary_path, summary)
    write_report(args.report, summary)

    print(json.dumps({"summary": rel(summary_path), "report": rel(args.report), "videos": video_results}, indent=2))


if __name__ == "__main__":
    main()
