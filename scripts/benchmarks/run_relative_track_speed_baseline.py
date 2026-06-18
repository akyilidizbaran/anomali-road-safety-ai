#!/usr/bin/env python3
"""SPEED-EXP-004A relative track/bbox speed baseline.

This experiment derives calibration-free motion signals from ByteTrack target
track history. It does not estimate legal or final km/h. The output is a
relative speed / motion anomaly signal for downstream Speed Fusion evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-fastplate.json"
DEFAULT_OUTPUT_DIR = ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-004A-relative-track-bbox"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "speed_exp_004a_relative_track_bbox_baseline.md"
DEFAULT_ENRICHED_EVENTS = (
    ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004a.json"
)


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


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 6) if values else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 6) if values else None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * 0.95))
    return round(ordered[idx], 6)


def stdev(values: list[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def round_or_none(value: float | None, ndigits: int = 6) -> float | None:
    return None if value is None else round(value, ndigits)


def bbox_dims(bbox: list[Any]) -> tuple[float, float, float]:
    x1, y1, x2, y2 = [fnum(v) for v in bbox]
    width = max(0.0, x2 - x1)
    height = max(0.0, y2 - y1)
    return width, height, width * height


def bottom_center(bbox: list[Any]) -> tuple[float, float]:
    x1, _y1, x2, y2 = [fnum(v) for v in bbox]
    return ((x1 + x2) / 2.0, y2)


def linspace_frames(first_frame: int, last_frame: int, count: int) -> list[int]:
    if count <= 0:
        return []
    if count == 1:
        return [first_frame]
    span = max(0, last_frame - first_frame)
    return [int(round(first_frame + (span * idx / (count - 1)))) for idx in range(count)]


def pairwise(values: list[Any]) -> list[tuple[Any, Any]]:
    return list(zip(values[:-1], values[1:], strict=False))


def label_relative_speed(score: float | None, jitter_score: float | None) -> str:
    if score is None:
        return "unavailable"
    if jitter_score is not None and jitter_score > 1.25:
        return "unstable"
    if score < 0.18:
        return "slow"
    if score < 0.55:
        return "normal"
    return "fast"


def compute_confidence(
    track_stability: float,
    history_count: int,
    bbox_jitter_score: float | None,
    height_median: float | None,
    id_switch_suspected: bool,
) -> float:
    confidence = 0.35 + 0.45 * clamp(track_stability, 0.0, 1.0)
    confidence += 0.10 * clamp(history_count / 30.0, 0.0, 1.0)
    if height_median is not None and height_median >= 80:
        confidence += 0.05
    if bbox_jitter_score is not None:
        confidence -= 0.12 * clamp(bbox_jitter_score / 1.25, 0.0, 1.0)
    if id_switch_suspected:
        confidence -= 0.25
    return round(clamp(confidence, 0.0, 0.95), 4)


def event_histories(event: dict[str, Any]) -> tuple[list[list[float]], list[list[float]]]:
    track_history = (event.get("evidence") or {}).get("track_history") or {}
    centers = track_history.get("center_history_sample") or []
    bboxes = track_history.get("bbox_history_sample") or []
    clean_centers = [[fnum(p[0]), fnum(p[1])] for p in centers if isinstance(p, list | tuple) and len(p) >= 2]
    clean_bboxes = [[fnum(v) for v in b[:4]] for b in bboxes if isinstance(b, list | tuple) and len(b) >= 4]
    return clean_centers, clean_bboxes


def compute_event_speed(
    event: dict[str, Any],
    min_track_stability: float,
    min_history_points: int,
    min_bbox_height: float,
) -> dict[str, Any]:
    target = event.get("target_vehicle") or {}
    source = event.get("source") or {}
    frame_window = target.get("frame_window") or {}
    track_stability = fnum(target.get("track_stability"))
    id_switch_suspected = bool(target.get("id_switch_suspected"))
    fps = fnum(source.get("fps"))
    centers, bboxes = event_histories(event)
    usable_count = min(len(centers), len(bboxes))
    centers = centers[:usable_count]
    bboxes = bboxes[:usable_count]

    quality_flags: list[str] = []
    warning_flags: list[str] = ["not_absolute_kmh", "no_metric_calibration"]
    fallback_reasons: list[str] = []

    if track_stability >= min_track_stability:
        quality_flags.append("track_stability_high")
    else:
        fallback_reasons.append("track_stability_below_threshold")

    if usable_count >= min_history_points:
        quality_flags.append("bbox_history_available")
    else:
        fallback_reasons.append("insufficient_track_history")

    if fps > 0:
        quality_flags.append("fps_available")
    else:
        fallback_reasons.append("fps_missing")

    if id_switch_suspected:
        warning_flags.append("id_switch_suspected")

    first_frame = int(fnum(frame_window.get("first_frame"), 0))
    last_frame = int(fnum(frame_window.get("last_frame"), first_frame + max(0, usable_count - 1)))
    sampled_frames = linspace_frames(first_frame, last_frame, usable_count)

    widths: list[float] = []
    heights: list[float] = []
    areas: list[float] = []
    bottom_centers: list[list[float]] = []
    for bbox in bboxes:
        width, height, area = bbox_dims(bbox)
        widths.append(width)
        heights.append(height)
        areas.append(area)
        bx, by = bottom_center(bbox)
        bottom_centers.append([round(bx, 4), round(by, 4)])

    median_height = statistics.median(heights) if heights else None
    if median_height is None or median_height < min_bbox_height:
        fallback_reasons.append("bbox_height_below_threshold")
    else:
        quality_flags.append("bbox_height_sufficient")

    segment_rows: list[dict[str, Any]] = []
    pixel_velocities_px_s: list[float] = []
    normalized_speeds: list[float] = []
    area_deltas: list[float] = []
    height_deltas: list[float] = []

    for idx, ((p0, p1), (bbox0, bbox1)) in enumerate(zip(pairwise(bottom_centers), pairwise(bboxes), strict=False)):
        frame0 = sampled_frames[idx]
        frame1 = sampled_frames[idx + 1]
        frame_delta = max(1, frame1 - frame0)
        dt_s = frame_delta / fps if fps > 0 else None
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        displacement = math.hypot(dx, dy)
        velocity_px_frame = displacement / frame_delta
        velocity_px_s = velocity_px_frame * fps if fps > 0 else None
        _w0, h0, area0 = bbox_dims(bbox0)
        _w1, h1, area1 = bbox_dims(bbox1)
        height_ref = max((h0 + h1) / 2.0, 1.0)
        area_ref = max((area0 + area1) / 2.0, 1.0)
        normalized = velocity_px_s / height_ref if velocity_px_s is not None else None
        h_delta = (h1 - h0) / height_ref
        area_delta = math.log(max(area1, 1.0) / max(area0, 1.0))

        if velocity_px_s is not None:
            pixel_velocities_px_s.append(velocity_px_s)
        if normalized is not None:
            normalized_speeds.append(normalized)
        height_deltas.append(h_delta)
        area_deltas.append(area_delta)

        segment_rows.append(
            {
                "segment_index": idx,
                "frame_start": frame0,
                "frame_end": frame1,
                "frame_delta": frame_delta,
                "dt_s": round_or_none(dt_s, 6),
                "bottom_center_start": p0,
                "bottom_center_end": p1,
                "dx_px": round(dx, 4),
                "dy_px": round(dy, 4),
                "pixel_displacement_px": round(displacement, 4),
                "pixel_velocity_px_per_frame": round(velocity_px_frame, 6),
                "pixel_velocity_px_s": round_or_none(velocity_px_s, 6),
                "bbox_height_start": round(h0, 4),
                "bbox_height_end": round(h1, 4),
                "bbox_height_delta_norm": round(h_delta, 6),
                "bbox_area_delta_log": round(area_delta, 6),
                "scale_normalized_speed": round_or_none(normalized, 6),
            }
        )

    normalized_median = median(normalized_speeds)
    normalized_p95 = p95(normalized_speeds)
    velocity_median = median(pixel_velocities_px_s)
    velocity_p95 = p95(pixel_velocities_px_s)
    height_delta_median = median(height_deltas)
    area_delta_median = median(area_deltas)
    bbox_jitter_score = None
    if normalized_speeds:
        denom = max(statistics.fmean(normalized_speeds), 1e-6)
        bbox_jitter_score = round(stdev(normalized_speeds) / denom, 6)

    relative_speed_score = normalized_median
    relative_speed_label = label_relative_speed(relative_speed_score, bbox_jitter_score)
    confidence = compute_confidence(track_stability, usable_count, bbox_jitter_score, median_height, id_switch_suspected)

    hard_fallback_reasons = [
        reason
        for reason in fallback_reasons
        if reason
        not in {
            "fps_missing",
        }
    ]
    gate_passed = not hard_fallback_reasons
    if not gate_passed:
        speed_mode = "unavailable"
        primary_source = None
        if relative_speed_label != "unstable":
            relative_speed_label = "unavailable"
    else:
        speed_mode = "relative" if relative_speed_label != "unstable" else "relative"
        primary_source = "bbox_bottom_center_relative"

    if relative_speed_label == "unstable":
        warning_flags.append("bbox_motion_jitter_high")
    if area_delta_median is not None and area_delta_median > 0.03:
        quality_flags.append("bbox_scale_increasing")
    elif area_delta_median is not None and area_delta_median < -0.03:
        quality_flags.append("bbox_scale_decreasing")
    else:
        quality_flags.append("bbox_scale_near_constant")

    fallback_reason = "no_reliable_metric_calibration" if speed_mode == "relative" else ";".join(hard_fallback_reasons)

    return {
        "experiment_id": "SPEED-EXP-004A",
        "speed_mode": speed_mode,
        "primary_speed_source": primary_source,
        "relative_speed_score": relative_speed_score,
        "relative_speed_label": relative_speed_label,
        "pixel_velocity_px_s_median": velocity_median,
        "pixel_velocity_px_s_p95": velocity_p95,
        "scale_normalized_speed_median": normalized_median,
        "scale_normalized_speed_p95": normalized_p95,
        "bbox_height_median": round_or_none(median_height, 4),
        "bbox_area_median": median(areas),
        "bbox_height_delta_norm_median": height_delta_median,
        "bbox_area_delta_log_median": area_delta_median,
        "bbox_motion_jitter_score": bbox_jitter_score,
        "fusion_confidence": confidence,
        "fallback_reason": fallback_reason,
        "quality_flags": sorted(set(quality_flags)),
        "warning_flags": sorted(set(warning_flags)),
        "history": {
            "sampled_frame_count": usable_count,
            "sampled_frames": sampled_frames,
            "sample_frame_note": "Frame ids are inferred by evenly spacing history samples across target_vehicle.frame_window.",
            "bottom_center_history_sample": bottom_centers,
            "bbox_width_median": median(widths),
            "bbox_height_median": round_or_none(median_height, 4),
        },
        "segments": segment_rows,
        "limitations": [
            "This output is calibration-free relative motion, not legal or final km/h.",
            "History sample frame ids are inferred because the upstream sample does not store per-point frame ids.",
            "Perspective and bbox clipping can affect score magnitude.",
        ],
    }


def flatten_row(event: dict[str, Any], speed: dict[str, Any]) -> dict[str, Any]:
    target = event.get("target_vehicle") or {}
    source = event.get("source") or {}
    return {
        "event_id": event.get("event_id"),
        "video": source.get("source_video"),
        "track_id": target.get("track_id"),
        "stable_class": target.get("vehicle_type"),
        "track_stability": target.get("track_stability"),
        "selection_score": target.get("selection_score"),
        "fps": source.get("fps"),
        "speed_mode": speed.get("speed_mode"),
        "primary_speed_source": speed.get("primary_speed_source"),
        "relative_speed_score": speed.get("relative_speed_score"),
        "relative_speed_label": speed.get("relative_speed_label"),
        "pixel_velocity_px_s_median": speed.get("pixel_velocity_px_s_median"),
        "pixel_velocity_px_s_p95": speed.get("pixel_velocity_px_s_p95"),
        "scale_normalized_speed_median": speed.get("scale_normalized_speed_median"),
        "scale_normalized_speed_p95": speed.get("scale_normalized_speed_p95"),
        "bbox_height_median": speed.get("bbox_height_median"),
        "bbox_area_median": speed.get("bbox_area_median"),
        "bbox_height_delta_norm_median": speed.get("bbox_height_delta_norm_median"),
        "bbox_area_delta_log_median": speed.get("bbox_area_delta_log_median"),
        "bbox_motion_jitter_score": speed.get("bbox_motion_jitter_score"),
        "fusion_confidence": speed.get("fusion_confidence"),
        "fallback_reason": speed.get("fallback_reason"),
        "quality_flags": "|".join(speed.get("quality_flags") or []),
        "warning_flags": "|".join(speed.get("warning_flags") or []),
        "sampled_frame_count": (speed.get("history") or {}).get("sampled_frame_count"),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_event_speed(event: dict[str, Any], speed: dict[str, Any]) -> None:
    event["speed_exp_004a"] = speed
    event["speed"] = {
        "status": "computed" if speed["speed_mode"] == "relative" else "not_available",
        "mode": speed["speed_mode"],
        "estimated_kmh": None,
        "relative_motion_score": speed.get("relative_speed_score"),
        "relative_motion_label": speed.get("relative_speed_label"),
        "motion_anomaly": speed.get("relative_speed_label") in {"fast", "unstable"},
        "calibration_profile_id": None,
        "confidence": speed.get("fusion_confidence"),
        "primary_speed_source": speed.get("primary_speed_source"),
        "fallback_reason": speed.get("fallback_reason"),
        "warning_flags": speed.get("warning_flags"),
    }


def make_report(
    path: Path,
    input_path: Path,
    summary_path: Path,
    csv_path: Path,
    enriched_path: Path,
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    label_counts: dict[str, int] = {}
    mode_counts: dict[str, int] = {}
    for row in rows:
        label_counts[str(row["relative_speed_label"])] = label_counts.get(str(row["relative_speed_label"]), 0) + 1
        mode_counts[str(row["speed_mode"])] = mode_counts.get(str(row["speed_mode"]), 0) + 1

    table_lines = [
        "| Video | Event | Track | Mode | Label | Score | px/s median | Confidence | Fallback |",
        "|---|---|---:|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        table_lines.append(
            "| {video} | {event_id} | {track_id} | {speed_mode} | {relative_speed_label} | {relative_speed_score} | {pixel_velocity_px_s_median} | {fusion_confidence} | {fallback_reason} |".format(
                **row
            )
        )

    content = f"""# SPEED-EXP-004A Relative Track/BBox Speed Baseline

## Özet

Bu rapor, ByteTrack target vehicle history çıktılarından kalibrasyonsuz göreli hız sinyali üretir.

Sonuç: Bu aşama **km/s üretmez**. Çıktı, `relative` / `unavailable` speed mode, göreli hız skoru, bbox scale dinamiği, güven skoru ve fallback gerekçesi üretir.

## Deney Bilgisi

* Experiment: `SPEED-EXP-004A`
* Input event JSON: `{rel(input_path)}`
* Summary JSON: `{rel(summary_path)}`
* Summary CSV: `{rel(csv_path)}`
* Enriched event JSON: `{rel(enriched_path)}`
* Minimum track stability: `{args.min_track_stability}`
* Minimum history points: `{args.min_history_points}`
* Minimum bbox height: `{args.min_bbox_height}`

## Üretilen Sinyaller

* `bottom_center_x/y`
* `pixel_velocity_px_s`
* `bbox_height`
* `bbox_area`
* `bbox_height_delta_norm`
* `bbox_area_delta_log`
* `scale_normalized_speed`
* `bbox_motion_jitter_score`

## Mod ve Label Dağılımı

```json
{json.dumps({"speed_mode": mode_counts, "relative_speed_label": label_counts}, indent=2, ensure_ascii=False)}
```

## Event Sonuçları

{chr(10).join(table_lines)}

## Yorum

Bu deney, sonraki `SPEED-EXP-004B` plate-scale + VATTR sanity-check aşamasına giriş olacak relative motion contract'ını üretir.

`fallback_reason = no_reliable_metric_calibration` değeri hata değildir. Bu, sabit kamera homografisi veya güvenilir metrik referans olmadığı için çıktının mutlak km/s olarak yorumlanmaması gerektiğini belirtir.

## Sınırlamalar

* Bu sonuç hukuki hız ölçümü değildir.
* `center_history_sample` ve `bbox_history_sample` içinde gerçek frame id saklanmadığı için frame index'leri `target_vehicle.frame_window` aralığına eşit dağıtılarak türetilmiştir.
* Bbox kırpılması, perspektif ve detector jitter skor büyüklüğünü etkileyebilir.
* `relative_speed_label` eşikleri ilk heuristic değerlerdir; manuel review sonrası ayarlanmalıdır.

## Sonraki Adım

1. Üç demo video için bu sonuçlar manuel gözle kontrol edilmeli.
2. `VATTR-EXP-001-efficientnet_b0-best.pth` target crop smoke test ile doğrulanmalı.
3. `SPEED-EXP-004B` içinde plate-scale ve VATTR signal, bu relative speed block üstüne sanity-check olarak bağlanmalı.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--enriched-events", type=Path, default=DEFAULT_ENRICHED_EVENTS)
    parser.add_argument("--min-track-stability", type=float, default=0.70)
    parser.add_argument("--min-history-points", type=int, default=8)
    parser.add_argument("--min-bbox-height", type=float, default=60.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_path = args.events.resolve()
    output_dir = args.output_dir.resolve()
    report_path = args.report.resolve()
    enriched_path = args.enriched_events.resolve()

    data = load_json(events_path)
    enriched = deepcopy(data)
    events = enriched.get("events") or []
    if not events:
        raise ValueError(f"No events found in {events_path}")

    event_results: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for event in events:
        speed = compute_event_speed(
            event,
            min_track_stability=args.min_track_stability,
            min_history_points=args.min_history_points,
            min_bbox_height=args.min_bbox_height,
        )
        update_event_speed(event, speed)
        event_results.append(
            {
                "event_id": event.get("event_id"),
                "video": (event.get("source") or {}).get("source_video"),
                "track_id": (event.get("target_vehicle") or {}).get("track_id"),
                "speed_exp_004a": speed,
            }
        )
        rows.append(flatten_row(event, speed))

    enriched["generated_at_utc"] = now_utc()
    enriched["event_stage"] = "speed_exp_004a_relative_track_bbox"
    enriched["source_event_stage"] = data.get("event_stage")
    enriched["speed_experiment_id"] = "SPEED-EXP-004A"
    enriched["speed_experiment_note"] = "Calibration-free relative speed signal; not legal/final km/h."

    summary_path = output_dir / "speed_exp_004a_relative_track_speed_summary.json"
    csv_path = output_dir / "speed_exp_004a_relative_track_speed_summary.csv"
    summary = {
        "generated_at_utc": now_utc(),
        "experiment_id": "SPEED-EXP-004A",
        "purpose": "calibration_free_relative_track_bbox_speed_baseline",
        "input_event_json": rel(events_path),
        "event_count": len(event_results),
        "limitations": [
            "Not absolute km/h.",
            "History sample frame ids are inferred from frame_window.",
            "Thresholds are initial heuristics and require manual review.",
        ],
        "settings": {
            "min_track_stability": args.min_track_stability,
            "min_history_points": args.min_history_points,
            "min_bbox_height": args.min_bbox_height,
        },
        "events": event_results,
    }

    write_json(summary_path, summary)
    write_csv(csv_path, rows)
    write_json(enriched_path, enriched)
    make_report(report_path, events_path, summary_path, csv_path, enriched_path, rows, args)

    print(f"Wrote summary: {rel(summary_path)}")
    print(f"Wrote csv: {rel(csv_path)}")
    print(f"Wrote enriched events: {rel(enriched_path)}")
    print(f"Wrote report: {rel(report_path)}")
    for row in rows:
        print(
            f"{row['video']} {row['track_id']} mode={row['speed_mode']} "
            f"label={row['relative_speed_label']} score={row['relative_speed_score']} "
            f"conf={row['fusion_confidence']}"
        )


if __name__ == "__main__":
    main()
