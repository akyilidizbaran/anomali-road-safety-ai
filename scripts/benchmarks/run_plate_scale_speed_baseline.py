#!/usr/bin/env python3
"""Plate-scale monocular speed baseline.

This experiment estimates approximate speed from visible license plate crops.
It uses the Turkish long plate size prior (0.52 m x 0.11 m) and a configurable
monocular camera field-of-view estimate to turn plate pixel size into an
approximate depth signal. The output is intended for research/manual review,
not legal speed measurement.

Inputs:
  * POCR-EXP-005 plate detector smoke summary
  * POCR-EXP-007/006 CCT-XS per-crop OCR summary

Outputs:
  * model-derived speed CSV/JSON
  * concise Markdown report

The script does not re-run detection or OCR. It reads existing plate crop files
and, when available, full-frame plate bbox records from the plate detector
summary. Without full-frame bbox records it falls back to depth/range-rate from
crop dimensions only. With full-frame bbox records it estimates an approximate
X/Y/Z trajectory and computes 3D displacement speed candidates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLATE_DETECTION_SUMMARY = (
    ROOT / "models" / "benchmarks" / "artifacts" / "plate_detection" / "POCR-EXP-005-local-video-smoke-yolo-summary.json"
)
DEFAULT_OCR_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "plate_ocr"
    / "POCR-EXP-007-cct-xs-baseline-percrop"
    / "POCR-EXP-006-fast-plate-ocr-summary.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-001-plate-scale"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "speed_exp_001_plate_scale_baseline.md"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_rootish(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 4) if values else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 4) if values else None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[int(round((len(ordered) - 1) * 0.95))], 4)


def parse_frame(path_or_name: str | Path) -> int | None:
    match = re.search(r"frame_(\d+)", str(path_or_name))
    return int(match.group(1)) if match else None


def focal_from_fov(size_px: float, fov_deg: float) -> float:
    return size_px / (2.0 * math.tan(math.radians(fov_deg) / 2.0))


def vertical_fov_from_horizontal(width: float, height: float, horizontal_fov_deg: float) -> float:
    return math.degrees(2.0 * math.atan((height / width) * math.tan(math.radians(horizontal_fov_deg) / 2.0)))


def rolling_median(values: list[float], window: int) -> list[float]:
    if window <= 1:
        return values[:]
    half = window // 2
    out: list[float] = []
    for idx in range(len(values)):
        lo = max(0, idx - half)
        hi = min(len(values), idx + half + 1)
        out.append(float(statistics.median(values[lo:hi])))
    return out


def source_detection_by_video(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {video["video"]: video for video in summary.get("videos", []) if video.get("video")}


def source_ocr_by_video(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {video["video"]: video for video in summary.get("videos", []) if video.get("video")}


def per_frame_plate_index(video_detection_summary: dict[str, Any], detector_key: str) -> dict[int, dict[str, Any]]:
    per_frame = video_detection_summary.get("per_frame")
    if not isinstance(per_frame, list):
        return {}
    indexed: dict[int, dict[str, Any]] = {}
    for frame_row in per_frame:
        frame = int(frame_row.get("frame") or 0)
        model_info = (frame_row.get("models") or {}).get(detector_key) or {}
        detections = model_info.get("detections") or []
        if not frame or not detections:
            continue
        best = max(detections, key=lambda item: float(item.get("confidence") or 0.0))
        bbox = best.get("bbox_xyxy_frame")
        center = best.get("center_xy_frame")
        if not bbox or not center:
            continue
        indexed[frame] = {
            "frame": frame,
            "plate_bbox_xyxy_frame": [float(v) for v in bbox],
            "plate_center_xy_frame": [float(v) for v in center],
            "plate_width_px_frame": float(best.get("width_px") or (float(bbox[2]) - float(bbox[0]))),
            "plate_height_px_frame": float(best.get("height_px") or (float(bbox[3]) - float(bbox[1]))),
            "plate_detection_confidence": float(best.get("confidence") or 0.0),
            "vehicle_bbox_xyxy_frame": model_info.get("vehicle_bbox_xyxy_frame"),
            "vehicle_roi_xyxy_frame": model_info.get("vehicle_roi_xyxy_frame"),
            "vehicle_roi_origin_xy": model_info.get("vehicle_roi_origin_xy"),
        }
    return indexed


def usable_ocr_rows(video_ocr: dict[str, Any], min_ocr_confidence: float) -> list[dict[str, Any]]:
    rows = video_ocr.get("per_crop") or []
    usable = []
    for row in rows:
        frame = int(row.get("frame") or 0)
        crop_file = row.get("crop_file")
        if not frame or not crop_file:
            continue
        if not row.get("format_valid") or not row.get("province_code_valid"):
            continue
        if float(row.get("ocr_confidence") or 0.0) < min_ocr_confidence:
            continue
        usable.append(row)
    return sorted(usable, key=lambda item: int(item["frame"]))


def crop_measurements(rows: list[dict[str, Any]], plate_index: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    measured = []
    for row in rows:
        crop_path = resolve_rootish(row["crop_file"])
        img = cv2.imread(str(crop_path))
        if img is None:
            continue
        height_px, width_px = img.shape[:2]
        plate_frame = plate_index.get(int(row["frame"])) or {}
        full_width_px = float(plate_frame.get("plate_width_px_frame") or width_px)
        full_height_px = float(plate_frame.get("plate_height_px_frame") or height_px)
        full_center = plate_frame.get("plate_center_xy_frame")
        if width_px <= 0 or height_px <= 0:
            continue
        measured.append(
            {
                "frame": int(row["frame"]),
                "crop_file": rel(crop_path),
                "plate_width_px": full_width_px,
                "plate_height_px": full_height_px,
                "plate_area_px": float(full_width_px * full_height_px),
                "plate_aspect_ratio": round(float(full_width_px / full_height_px), 4),
                "crop_width_px": float(width_px),
                "crop_height_px": float(height_px),
                "crop_aspect_ratio": round(float(width_px / height_px), 4),
                "plate_bbox_xyxy_frame": plate_frame.get("plate_bbox_xyxy_frame"),
                "plate_center_xy_frame": full_center,
                "plate_detection_confidence": plate_frame.get("plate_detection_confidence"),
                "vehicle_bbox_xyxy_frame": plate_frame.get("vehicle_bbox_xyxy_frame"),
                "vehicle_roi_xyxy_frame": plate_frame.get("vehicle_roi_xyxy_frame"),
                "ocr_text": row.get("normalized_text"),
                "ocr_confidence": float(row.get("ocr_confidence") or 0.0),
            }
        )
    return measured


def estimate_positions(
    measurements: list[dict[str, Any]],
    frame_meta: dict[str, Any],
    horizontal_fov_deg: float,
    plate_width_m: float,
    plate_height_m: float,
) -> dict[str, list[dict[str, Any]]]:
    image_width = float(frame_meta.get("width") or 0)
    image_height = float(frame_meta.get("height") or 0)
    if image_width <= 0 or image_height <= 0:
        raise ValueError("frame_meta width/height missing")
    vertical_fov_deg = vertical_fov_from_horizontal(image_width, image_height, horizontal_fov_deg)
    fx = focal_from_fov(image_width, horizontal_fov_deg)
    fy = focal_from_fov(image_height, vertical_fov_deg)
    cx = image_width / 2.0
    cy = image_height / 2.0

    variants = {"width": [], "height": [], "geomean": []}
    for item in measurements:
        w_px = item["plate_width_px"]
        h_px = item["plate_height_px"]
        z_width = fx * plate_width_m / w_px
        z_height = fy * plate_height_m / h_px
        z_geomean = math.sqrt(max(0.0, z_width * z_height))
        for key, depth in [("width", z_width), ("height", z_height), ("geomean", z_geomean)]:
            center = item.get("plate_center_xy_frame")
            if center:
                u, v = float(center[0]), float(center[1])
                x_m = (u - cx) * depth / fx
                y_m = (v - cy) * depth / fy
            else:
                x_m = None
                y_m = None
            variants[key].append(
                {
                    **item,
                    "depth_m": round(depth, 4),
                    "x_m": round(x_m, 4) if x_m is not None else None,
                    "y_m": round(y_m, 4) if y_m is not None else None,
                    "fx_px": round(fx, 4),
                    "fy_px": round(fy, 4),
                    "cx_px": round(cx, 4),
                    "cy_px": round(cy, 4),
                    "horizontal_fov_deg": horizontal_fov_deg,
                    "vertical_fov_deg": round(vertical_fov_deg, 4),
                    "distance_method": key,
                }
            )
    return variants


def estimate_speed_series(
    positions: list[dict[str, Any]],
    fps: float,
    smoothing_window: int,
    max_speed_kmh: float,
) -> list[dict[str, Any]]:
    if len(positions) < 2 or fps <= 0:
        return []
    raw_segments: list[dict[str, Any]] = []
    for prev, cur in zip(positions, positions[1:], strict=False):
        frame_delta = int(cur["frame"]) - int(prev["frame"])
        if frame_delta <= 0:
            continue
        dt = frame_delta / fps
        delta_depth = float(cur["depth_m"]) - float(prev["depth_m"])
        use_xyz = prev.get("x_m") is not None and cur.get("x_m") is not None
        if use_xyz:
            dx = float(cur["x_m"]) - float(prev["x_m"])
            dy = float(cur["y_m"]) - float(prev["y_m"])
            distance_m = math.sqrt(dx * dx + dy * dy + delta_depth * delta_depth)
        else:
            dx = None
            dy = None
            distance_m = abs(delta_depth)
        speed_kmh = distance_m / dt * 3.6
        raw_segments.append(
            {
                "start_frame": int(prev["frame"]),
                "end_frame": int(cur["frame"]),
                "frame_delta": frame_delta,
                "dt_s": round(dt, 6),
                "depth_start_m": float(prev["depth_m"]),
                "depth_end_m": float(cur["depth_m"]),
                "delta_depth_m": round(delta_depth, 4),
                "delta_x_m": round(dx, 4) if dx is not None else None,
                "delta_y_m": round(dy, 4) if dy is not None else None,
                "distance_m": round(distance_m, 4),
                "speed_mode": "xyz_displacement" if use_xyz else "depth_range_rate",
                "speed_kmh_raw": round(speed_kmh, 4),
                "outlier": speed_kmh > max_speed_kmh,
            }
        )
    valid_values = [item["speed_kmh_raw"] for item in raw_segments if not item["outlier"]]
    smoothed = rolling_median(valid_values, smoothing_window)
    smooth_idx = 0
    for item in raw_segments:
        if item["outlier"]:
            item["speed_kmh_smoothed"] = None
            continue
        item["speed_kmh_smoothed"] = round(smoothed[smooth_idx], 4)
        smooth_idx += 1
    return raw_segments


def summarize_speed(series: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [float(item["speed_kmh_smoothed"]) for item in series if item.get("speed_kmh_smoothed") is not None]
    raw_valid = [float(item["speed_kmh_raw"]) for item in series if not item.get("outlier")]
    return {
        "segment_count": len(series),
        "valid_segment_count": len(valid),
        "outlier_count": len(series) - len(raw_valid),
        "mean_speed_kmh": mean(valid),
        "median_speed_kmh": median(valid),
        "p95_speed_kmh": p95(valid),
        "mean_raw_speed_kmh": mean(raw_valid),
        "median_raw_speed_kmh": median(raw_valid),
    }


def confidence_note(video_summary: dict[str, Any], variant: str) -> str:
    aspect_values = video_summary.get("plate_aspect_ratios") or []
    median_aspect = statistics.median(aspect_values) if aspect_values else None
    if median_aspect is None:
        return "low_no_plate_measurements"
    standard_aspect = 0.52 / 0.11
    if abs(median_aspect - standard_aspect) / standard_aspect > 0.25:
        return f"low_plate_crop_aspect_differs_from_standard_{variant}"
    return f"medium_assumes_standard_plate_and_camera_fov_{variant}"


def process_video(
    video_name: str,
    detection_summary: dict[str, Any],
    ocr_summary: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    det_video = detection_summary[video_name]
    rows = usable_ocr_rows(ocr_summary, args.min_ocr_confidence)
    plate_index = per_frame_plate_index(det_video, args.detector_key)
    if args.start_after_stable_frame:
        stable_frame = None
        # Prefer the first frame at which the same valid OCR value has appeared
        # stable_count times in the configured window.
        counts: dict[str, int] = defaultdict(int)
        recent: list[str] = []
        for row in rows:
            text = str(row.get("normalized_text") or "")
            recent.append(text)
            recent = recent[-args.stable_window_size :]
            counts = defaultdict(int)
            for seen in recent:
                if seen:
                    counts[seen] += 1
            if counts and max(counts.values()) >= args.stable_count:
                stable_frame = int(row["frame"])
                break
        if stable_frame is not None:
            rows = [row for row in rows if int(row["frame"]) >= stable_frame]

    measurements = crop_measurements(rows, plate_index)
    if args.limit_per_video:
        measurements = measurements[: args.limit_per_video]
    fps = float(det_video.get("frame_meta", {}).get("fps") or 0.0)
    positions_by_variant = estimate_positions(
        measurements,
        frame_meta=det_video.get("frame_meta") or {},
        horizontal_fov_deg=args.horizontal_fov_deg,
        plate_width_m=args.plate_width_m,
        plate_height_m=args.plate_height_m,
    )
    variant_payload: dict[str, Any] = {}
    aspect_values = [item["plate_aspect_ratio"] for item in measurements]
    for variant, positions in positions_by_variant.items():
        segments = estimate_speed_series(
            positions,
            fps=fps,
            smoothing_window=args.smoothing_window,
            max_speed_kmh=args.max_speed_kmh,
        )
        summary = summarize_speed(segments)
        summary["confidence_note"] = confidence_note({"plate_aspect_ratios": aspect_values}, variant)
        variant_payload[variant] = {
            "summary": summary,
            "positions_sample": positions[: args.sample_rows],
            "speed_segments_sample": segments[: args.sample_rows],
        }
    return {
        "video": video_name,
        "status": "completed" if measurements else "failed",
        "failure_reason": None if measurements else "no_usable_plate_ocr_crops",
        "fps": fps,
        "frame_meta": det_video.get("frame_meta"),
        "target_track_id": det_video.get("target_track_id"),
        "source_plate_detection_rate": (
            (det_video.get("models") or {}).get(args.detector_key, {}).get("plate_detection_rate")
        ),
        "full_frame_plate_bbox_available": bool(plate_index),
        "usable_measurement_count": len(measurements),
        "plate_aspect_ratio_median": median(aspect_values),
        "plate_aspect_ratio_mean": mean(aspect_values),
        "plate_width_px_median": median([item["plate_width_px"] for item in measurements]),
        "plate_height_px_median": median([item["plate_height_px"] for item in measurements]),
        "variants": variant_payload,
    }


def write_csv(summary: dict[str, Any], csv_path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for video in summary["videos"]:
        for variant, payload in video.get("variants", {}).items():
            s = payload["summary"]
            rows.append(
                {
                    "video": video["video"],
                    "variant": variant,
                    "full_frame_plate_bbox_available": video.get("full_frame_plate_bbox_available"),
                    "usable_measurement_count": video["usable_measurement_count"],
                    "plate_aspect_ratio_median": video["plate_aspect_ratio_median"],
                    "plate_width_px_median": video["plate_width_px_median"],
                    "plate_height_px_median": video["plate_height_px_median"],
                    "segment_count": s["segment_count"],
                    "valid_segment_count": s["valid_segment_count"],
                    "outlier_count": s["outlier_count"],
                    "mean_speed_kmh": s["mean_speed_kmh"],
                    "median_speed_kmh": s["median_speed_kmh"],
                    "p95_speed_kmh": s["p95_speed_kmh"],
                    "confidence_note": s["confidence_note"],
                }
            )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {summary['experiment_id']} Plate-Scale Monocular Speed Baseline",
        "",
        f"Tarih: `{summary['generated_at_utc']}`",
        "",
        "## Amaç",
        "",
        "Türkiye uzun plaka boyutu varsayımı (`0.52m x 0.11m`) ile plaka crop piksel "
        "ölçülerinden yaklaşık derinlik ve frame'ler arası göreli/mutlak hız adayları "
        "üretmek. Bu çalışma radar/hukuki hız ölçümü değildir; kalibrasyon gerektiren "
        "bir matematiksel baseline denemesidir.",
        "",
        "## Formül",
        "",
        "* `fx = image_width / (2 * tan(horizontal_fov / 2))`",
        "* `fy` yatay FOV ve görüntü oranından türetilen dikey FOV ile hesaplanır.",
        "* Width yöntemi: `Z = fx * 0.52 / plate_width_px`",
        "* Height yöntemi: `Z = fy * 0.11 / plate_height_px`",
        "* Geomean yöntemi: `Z = sqrt(Z_width * Z_height)`",
        "* Full-frame plate center varsa: `X=(u-cx)*Z/fx`, `Y=(v-cy)*Z/fy`",
        "* Hız: full-frame center varsa `sqrt(dX^2+dY^2+dZ^2)/dt*3.6`, yoksa `abs(dZ)/dt*3.6`",
        "",
        "## Konfigürasyon",
        "",
        f"* Horizontal FOV varsayımı: `{summary['config']['horizontal_fov_deg']}` derece",
        f"* Minimum OCR confidence: `{summary['config']['min_ocr_confidence']}`",
        f"* Smooth window: `{summary['config']['smoothing_window']}`",
        f"* Max speed outlier gate: `{summary['config']['max_speed_kmh']}` km/s",
        "",
        "## Özet",
        "",
        "| Video | Variant | Full BBox | Measurements | Aspect Median | Width px | Height px | Median km/h | Mean km/h | Outliers | Note |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for video in summary["videos"]:
        for variant, payload in video.get("variants", {}).items():
            s = payload["summary"]
            lines.append(
                f"| {video['video']} | {variant} | {video.get('full_frame_plate_bbox_available')} | "
                f"{video['usable_measurement_count']} | "
                f"{video['plate_aspect_ratio_median']} | {video['plate_width_px_median']} | "
                f"{video['plate_height_px_median']} | {s['median_speed_kmh']} | "
                f"{s['mean_speed_kmh']} | {s['outlier_count']} | {s['confidence_note']} |"
            )
    lines += [
        "",
        "## Yorum",
        "",
        "* Bu ilk deneme yalnız plaka görünür hedefler içindir.",
        "* Crop aspect ratio standart `4.73` değerinden belirgin saparsa sonuç düşük güvenli kabul edilir.",
        "* Kamera FOV ve plaka köşe/pose bilgisi gerçek kalibrasyonla doğrulanmadan mutlak km/s iddiası kurulmaz.",
        "* Sonraki iyileştirme: plaka 4 köşe tespiti + `solvePnP` veya saha kalibrasyon noktaları ile ölçek doğrulaması.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SPEED-EXP-001 plate-scale monocular speed baseline.")
    parser.add_argument("--experiment-id", default="SPEED-EXP-001")
    parser.add_argument("--plate-detection-summary", type=Path, default=DEFAULT_PLATE_DETECTION_SUMMARY)
    parser.add_argument("--ocr-summary", type=Path, default=DEFAULT_OCR_SUMMARY)
    parser.add_argument("--detector-key", default="yolo")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--summary-name", default="speed_exp_001_plate_scale_summary")
    parser.add_argument("--horizontal-fov-deg", type=float, default=70.0)
    parser.add_argument("--plate-width-m", type=float, default=0.52)
    parser.add_argument("--plate-height-m", type=float, default=0.11)
    parser.add_argument("--min-ocr-confidence", type=float, default=0.75)
    parser.add_argument("--stable-count", type=int, default=3)
    parser.add_argument("--stable-window-size", type=int, default=7)
    parser.add_argument("--start-after-stable-frame", action="store_true", default=True)
    parser.add_argument("--include-pre-stable-frames", dest="start_after_stable_frame", action="store_false")
    parser.add_argument("--smoothing-window", type=int, default=7)
    parser.add_argument("--max-speed-kmh", type=float, default=220.0)
    parser.add_argument("--limit-per-video", type=int, default=None)
    parser.add_argument("--sample-rows", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    detection_summary = load_json(args.plate_detection_summary.resolve())
    ocr_summary = load_json(args.ocr_summary.resolve())
    detection_by_video = source_detection_by_video(detection_summary)
    ocr_by_video = source_ocr_by_video(ocr_summary)

    videos = []
    for video_name in sorted(set(detection_by_video) & set(ocr_by_video)):
        videos.append(process_video(video_name, detection_by_video, ocr_by_video[video_name], args))

    payload = {
        "experiment_id": args.experiment_id,
        "stage": "plate_scale_monocular_speed_baseline",
        "generated_at_utc": now_utc(),
        "source_plate_detection_summary": rel(args.plate_detection_summary.resolve()),
        "source_ocr_summary": rel(args.ocr_summary.resolve()),
        "config": {
            "plate_size_prior": "turkey_long_plate_0.52m_x_0.11m",
            "plate_width_m": args.plate_width_m,
            "plate_height_m": args.plate_height_m,
            "horizontal_fov_deg": args.horizontal_fov_deg,
            "min_ocr_confidence": args.min_ocr_confidence,
            "stable_count": args.stable_count,
            "stable_window_size": args.stable_window_size,
            "start_after_stable_frame": args.start_after_stable_frame,
            "smoothing_window": args.smoothing_window,
            "max_speed_kmh": args.max_speed_kmh,
        },
        "videos": videos,
        "notes": [
            "Approximate baseline only; not legal speed measurement.",
            "Uses plate crop dimensions as bbox pixel scale.",
            "Requires camera calibration or PnP plate corners for stronger absolute km/h claims.",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / f"{args.summary_name}.json"
    csv_path = args.output_dir / f"{args.summary_name}.csv"
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(payload, csv_path)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(build_report(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": rel(summary_path),
                "csv": rel(csv_path),
                "report": rel(args.report.resolve()),
                "videos": len(videos),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
