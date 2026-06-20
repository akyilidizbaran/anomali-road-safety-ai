#!/usr/bin/env python3
"""Apply SPEED-EXP-006B best geometry parameters to local demo videos.

This is a transfer smoke test, not the exported HuberRegressor inference model.
The 006B Colab run did not persist a final sklearn model artifact. Therefore
this script reuses the 006B best *geometry parameters* on the already extracted
005A target-track timeseries and produces plots for the three local demo videos.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


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
DEFAULT_005A_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "speed"
    / "SPEED-EXP-005A-bbox-geometry-auto"
    / "speed_exp_005a_bbox_geometry_summary.json"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "speed"
    / "SPEED-EXP-006B-demo-transfer"
)
DEFAULT_RUNS_DIR = ROOT / "runs" / "speed" / "SPEED-EXP-006B-demo-transfer"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "speed_exp_006b_demo_transfer.md"

BEST_006B_PARAMS = {
    "horizontal_fov_deg": 60.0,
    "vehicle_height_m": 1.5,
    "moving_average_window": 9,
    "max_segment_speed_kmh": 140.0,
    "segment_trim_fraction": 0.0,
    "min_bbox_height_ratio": 0.1,
}

BEST_006B_METRICS = {
    "method": "huber_features",
    "loo_mae_kmh": 2.7088,
    "loo_rmse_kmh": 3.4750,
    "loo_median_abs_error_kmh": 2.1109,
    "loo_p90_abs_error_kmh": 5.9034,
    "loo_mean_rel_error_pct": 4.0835,
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


def parse_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        val = float(value)
    except (TypeError, ValueError):
        return None
    return val if math.isfinite(val) else None


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def mean(values: list[float]) -> float | None:
    return float(statistics.fmean(values)) if values else None


def median(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * q / 100.0
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[int(pos)]
    return vals[lo] * (hi - pos) + vals[hi] * (pos - lo)


def robust_mean(values: list[float | None]) -> float | None:
    vals = sorted(v for v in values if v is not None and math.isfinite(v))
    if not vals:
        return None
    if len(vals) >= 8:
        lo = percentile(vals, 10)
        hi = percentile(vals, 90)
        vals = [v for v in vals if lo is not None and hi is not None and lo <= v <= hi]
    return mean(vals)


def moving_average(values: list[float | None], window: int) -> list[float | None]:
    result: list[float | None] = []
    for idx in range(len(values)):
        sample = [v for v in values[max(0, idx - window + 1) : idx + 1] if v is not None and math.isfinite(v)]
        result.append(mean(sample) if sample else None)
    return result


def focal_lengths(width: int, height: int, horizontal_fov_deg: float) -> tuple[float, float]:
    hfov = math.radians(horizontal_fov_deg)
    fx = width / (2.0 * math.tan(hfov / 2.0))
    vfov = 2.0 * math.atan(math.tan(hfov / 2.0) * (height / max(width, 1)))
    fy = height / (2.0 * math.tan(vfov / 2.0))
    return fx, fy


def read_timeseries(path: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            video = row["video"]
            row["frame_id"] = int(float(row["frame_id"]))
            for key in [
                "time_s",
                "confidence",
                "bbox_width_px",
                "bbox_height_px",
                "bbox_area_px",
                "bottom_center_x",
                "bottom_center_y",
            ]:
                row[key] = parse_float(row.get(key))
            grouped[video].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda item: item["frame_id"])
    return grouped


def summary_resolution_index(path: Path) -> dict[str, tuple[int, int]]:
    data = load_json(path)
    out: dict[str, tuple[int, int]] = {}
    for video in data.get("videos", []):
        res = str(video.get("resolution") or "")
        if "x" in res:
            w, h = res.lower().split("x", 1)
            out[video["video"]] = (int(float(w)), int(float(h)))
    return out


def summary_005a_index(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path)
    out: dict[str, dict[str, Any]] = {}
    for video in data.get("videos", []):
        candidate = video.get("bbox_geometry_candidate") or {}
        out[video["video"]] = {
            "speed_kmh": candidate.get("estimated_kmh"),
            "confidence": candidate.get("confidence"),
            "method": candidate.get("estimated_kmh_method"),
        }
    return out


def compute_006b_transfer(rows: list[dict[str, Any]], resolution: tuple[int, int], params: dict[str, Any]) -> dict[str, Any]:
    width, height = resolution
    fx, fy = focal_lengths(width, height, float(params["horizontal_fov_deg"]))
    cx = width / 2.0
    prior_height = float(params["vehicle_height_m"])
    max_speed = float(params["max_segment_speed_kmh"])

    enriched: list[dict[str, Any]] = []
    raw_speeds: list[float | None] = []
    invalid_reasons: dict[str, int] = defaultdict(int)
    prev: dict[str, Any] | None = None
    for row in rows:
        bbox_h = max(float(row.get("bbox_height_px") or 1.0), 1.0)
        z_m = fy * prior_height / bbox_h
        bottom_x = float(row.get("bottom_center_x") or cx)
        x_m = (bottom_x - cx) * z_m / fx
        out = dict(row)
        out["z_m_006b"] = z_m
        out["x_m_006b"] = x_m
        out["segment_speed_kmh_006b_raw"] = None
        out["segment_speed_kmh_006b_moving_avg"] = None
        out["segment_valid_006b"] = None
        out["segment_failure_reason_006b"] = None

        if prev is not None:
            dt = max(1e-6, float(out["time_s"] or 0.0) - float(prev["time_s"] or 0.0))
            dx = x_m - float(prev["x_m_006b"])
            dz = z_m - float(prev["z_m_006b"])
            speed = math.sqrt(dx * dx + dz * dz) / dt * 3.6
            valid = True
            reason = None
            if not math.isfinite(speed) or speed > max_speed:
                valid = False
                reason = "speed_outlier_gate"
            prev_h = max(float(prev.get("bbox_height_px") or 1.0), 1.0)
            height_ratio = max(bbox_h, prev_h) / max(1.0, min(bbox_h, prev_h))
            if height_ratio > 1.25:
                valid = False
                reason = "bbox_height_jump"
            if valid:
                out["segment_speed_kmh_006b_raw"] = speed
                raw_speeds.append(speed)
            else:
                raw_speeds.append(None)
                if reason:
                    invalid_reasons[reason] += 1
            out["segment_valid_006b"] = valid
            out["segment_failure_reason_006b"] = reason
        enriched.append(out)
        prev = out

    ma = moving_average(raw_speeds, int(params["moving_average_window"]))
    for row, value in zip(enriched[1:], ma, strict=False):
        row["segment_speed_kmh_006b_moving_avg"] = value

    candidate_rows = enriched[1:]
    trim = float(params.get("segment_trim_fraction", 0.0) or 0.0)
    if candidate_rows and trim > 0:
        start_idx = int(len(candidate_rows) * trim)
        end_idx = int(len(candidate_rows) * (1.0 - trim))
        candidate_rows = candidate_rows[start_idx : max(start_idx + 1, end_idx)]
    min_h_ratio = float(params.get("min_bbox_height_ratio", 0.0) or 0.0)
    if min_h_ratio > 0:
        min_h = height * min_h_ratio
        candidate_rows = [row for row in candidate_rows if float(row.get("bbox_height_px") or 0.0) >= min_h]

    ma_values = [row.get("segment_speed_kmh_006b_moving_avg") for row in candidate_rows]
    raw_values = [row.get("segment_speed_kmh_006b_raw") for row in candidate_rows]
    usable_ma = [v for v in ma_values if v is not None and math.isfinite(v)]
    usable_raw = [v for v in raw_values if v is not None and math.isfinite(v)]
    estimate = robust_mean(ma_values)
    valid_count = len(usable_raw)
    speed_std = statistics.pstdev(usable_ma) if len(usable_ma) > 1 else None
    speed_mean = mean(usable_ma)
    speed_cv = (speed_std / speed_mean) if speed_std is not None and speed_mean and speed_mean > 0 else None
    mean_det_conf = mean([float(row.get("confidence") or 0.0) for row in rows]) or 0.0

    coverage_quality = min(len(rows) / 180.0, 1.0)
    valid_ratio = valid_count / max(len(rows) - 1, 1)
    valid_ratio = max(0.0, min(1.0, valid_ratio))
    cv_quality = 0.0 if speed_cv is None else max(0.0, min(1.0, 1.0 - speed_cv / 0.35))
    det_conf_quality = max(0.0, min(1.0, mean_det_conf / 0.80))
    estimate_bonus = 0.10 if estimate is not None else 0.0
    confidence = 0.08 + 0.18 * coverage_quality + 0.22 * valid_ratio + 0.30 * cv_quality + 0.12 * det_conf_quality + estimate_bonus
    confidence = round(max(0.0, min(confidence, 0.90)), 4)

    return {
        "status": "ok" if estimate is not None else "failed",
        "failure_reason": None if estimate is not None else "no_speed_estimate",
        "estimated_raw_transfer_kmh": estimate,
        "raw_mean_kmh": robust_mean(raw_values),
        "moving_average_median_kmh": median(usable_ma),
        "p25_kmh": percentile(usable_ma, 25),
        "p75_kmh": percentile(usable_ma, 75),
        "p90_kmh": percentile(usable_ma, 90),
        "observation_count": len(rows),
        "valid_segment_count": valid_count,
        "selected_candidate_row_count": len(candidate_rows),
        "candidate_valid_ratio": valid_count / max(len(candidate_rows), 1),
        "speed_cv": speed_cv,
        "mean_detection_confidence": mean_det_conf,
        "confidence": confidence,
        "invalid_segment_reasons": dict(sorted(invalid_reasons.items())),
        "timeseries": enriched,
    }


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_line_plot(
    output: Path,
    title: str,
    times: list[float],
    series: list[tuple[str, list[float | None], tuple[int, int, int]]],
    secondary: tuple[str, list[float | None], tuple[int, int, int]] | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1600, 900
    margin_l, margin_r, margin_t, margin_b = 120, 120, 105, 115
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(34)
    label_font = load_font(22)
    small_font = load_font(18)
    axis_color = (35, 35, 35)
    grid_color = (220, 220, 220)

    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    x_min = min(times) if times else 0.0
    x_max = max(times) if times else 1.0
    y_values = [v for _, vals, _ in series for v in vals if v is not None and math.isfinite(v)]
    y_min = 0.0
    y_max = max(max(y_values) * 1.15, 1.0) if y_values else 1.0

    def x_px(x: float) -> int:
        return int(margin_l + (x - x_min) / max(x_max - x_min, 1e-6) * plot_w)

    def y_px(y: float) -> int:
        return int(margin_t + plot_h - (y - y_min) / max(y_max - y_min, 1e-6) * plot_h)

    draw.text((margin_l, 30), title, fill=(0, 0, 0), font=title_font)
    for i in range(6):
        y = y_min + (y_max - y_min) * i / 5
        py = y_px(y)
        draw.line((margin_l, py, width - margin_r, py), fill=grid_color, width=1)
        draw.text((20, py - 12), f"{y:.1f}", fill=axis_color, font=small_font)
    for i in range(6):
        x = x_min + (x_max - x_min) * i / 5
        px = x_px(x)
        draw.line((px, margin_t, px, height - margin_b), fill=(238, 238, 238), width=1)
        draw.text((px - 20, height - margin_b + 18), f"{x:.1f}", fill=axis_color, font=small_font)

    draw.rectangle((margin_l, margin_t, width - margin_r, height - margin_b), outline=axis_color, width=2)
    draw.text((width // 2 - 50, height - 55), "time (s)", fill=axis_color, font=label_font)
    draw.text((25, margin_t - 36), "km/h", fill=axis_color, font=label_font)

    legend_x = margin_l + 15
    legend_y = margin_t + 12
    for label, values, color in series:
        pts = [(x_px(t), y_px(v)) for t, v in zip(times, values, strict=False) if v is not None and math.isfinite(v)]
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=4)
        draw.line((legend_x, legend_y + 11, legend_x + 42, legend_y + 11), fill=color, width=4)
        draw.text((legend_x + 52, legend_y), label, fill=(0, 0, 0), font=small_font)
        legend_y += 28

    if secondary:
        label, values, color = secondary
        sec_vals = [v for v in values if v is not None and math.isfinite(v)]
        if sec_vals:
            s_min = 0.0
            s_max = max(sec_vals) * 1.15

            def y2_px(y: float) -> int:
                return int(margin_t + plot_h - (y - s_min) / max(s_max - s_min, 1e-6) * plot_h)

            pts = [(x_px(t), y2_px(v)) for t, v in zip(times, values, strict=False) if v is not None and math.isfinite(v)]
            if len(pts) >= 2:
                for a, b in zip(pts, pts[1:], strict=False):
                    draw.line((a, b), fill=color, width=2)
            draw.text((width - margin_r + 18, margin_t - 4), label, fill=color, font=small_font)
            draw.text((width - margin_r + 18, height - margin_b - 16), "bbox px", fill=color, font=small_font)

    img.save(output)


def draw_bar_chart(output: Path, rows: list[dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1500, 850
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(34)
    label_font = load_font(21)
    small_font = load_font(18)
    draw.text((90, 35), "SPEED-EXP-006B demo transfer summary", fill=(0, 0, 0), font=title_font)
    margin_l, margin_r, margin_t, margin_b = 110, 90, 130, 125
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    values = []
    for row in rows:
        values.extend([v for v in [row.get("speed_005a_kmh"), row.get("speed_006b_transfer_kmh")] if v is not None])
    y_max = max(max(values) * 1.25, 5.0) if values else 5.0

    def y_px(y: float) -> int:
        return int(margin_t + plot_h - y / y_max * plot_h)

    for i in range(6):
        y = y_max * i / 5
        py = y_px(y)
        draw.line((margin_l, py, width - margin_r, py), fill=(225, 225, 225), width=1)
        draw.text((35, py - 12), f"{y:.1f}", fill=(40, 40, 40), font=small_font)
    draw.rectangle((margin_l, margin_t, width - margin_r, height - margin_b), outline=(35, 35, 35), width=2)
    draw.text((35, margin_t - 38), "km/h", fill=(40, 40, 40), font=label_font)
    group_w = plot_w / max(len(rows), 1)
    bar_w = min(90, group_w * 0.25)
    colors = {"005A": (165, 165, 165), "006B": (45, 45, 45)}
    for idx, row in enumerate(rows):
        cx = margin_l + group_w * idx + group_w / 2
        for offset, key, label in [(-bar_w * 0.65, "speed_005a_kmh", "005A"), (bar_w * 0.65, "speed_006b_transfer_kmh", "006B")]:
            val = row.get(key)
            if val is None:
                continue
            x1 = int(cx + offset - bar_w / 2)
            x2 = int(cx + offset + bar_w / 2)
            y1 = y_px(float(val))
            y2 = height - margin_b
            draw.rectangle((x1, y1, x2, y2), fill=colors[label])
            draw.text((x1 - 5, y1 - 28), f"{float(val):.2f}", fill=(0, 0, 0), font=small_font)
        draw.text((int(cx - 48), height - margin_b + 24), row["video"].replace(".mp4", ""), fill=(0, 0, 0), font=label_font)
    draw.rectangle((margin_l + 25, margin_t + 20, margin_l + 55, margin_t + 42), fill=colors["005A"])
    draw.text((margin_l + 65, margin_t + 17), "005A moving-average candidate", fill=(0, 0, 0), font=small_font)
    draw.rectangle((margin_l + 25, margin_t + 52, margin_l + 55, margin_t + 74), fill=colors["006B"])
    draw.text((margin_l + 65, margin_t + 49), "006B best-params transfer candidate", fill=(0, 0, 0), font=small_font)
    img.save(output)


def write_transfer_csv(path: Path, rows_by_video: dict[str, list[dict[str, Any]]]) -> None:
    fields = [
        "video",
        "frame_id",
        "time_s",
        "bbox_height_px",
        "bottom_center_x",
        "z_m_006b",
        "x_m_006b",
        "segment_speed_kmh_006b_raw",
        "segment_speed_kmh_006b_moving_avg",
        "segment_valid_006b",
        "segment_failure_reason_006b",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for video, rows in rows_by_video.items():
            for row in rows:
                writer.writerow({field: row.get(field) if field != "video" else video for field in fields})


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# SPEED-EXP-006B Demo Transfer Smoke Test",
        "",
        "Bu rapor, VS13 üzerinde seçilen `SPEED-EXP-006B` en iyi geometry parametrelerinin yerel 3 demo videoya uygulanmasını özetler.",
        "",
        "## Kritik Sınır",
        "",
        "006B Colab koşusu `huber_features` metriklerini üretmiştir; ancak final sklearn model artifact'i export edilmemiştir. Bu nedenle bu lokal koşu, öğrenilmiş `huber_features` modelinin birebir inference'ı değil; 006B best geometry parametrelerinin transfer smoke test'idir.",
        "",
        "## 006B Referans Sonucu",
        "",
        f"* En iyi yöntem: `{BEST_006B_METRICS['method']}`",
        f"* VS13 LOO MAE: `{BEST_006B_METRICS['loo_mae_kmh']} km/h`",
        f"* VS13 LOO RMSE: `{BEST_006B_METRICS['loo_rmse_kmh']} km/h`",
        f"* VS13 P90 absolute error: `{BEST_006B_METRICS['loo_p90_abs_error_kmh']} km/h`",
        "",
        "## Demo Transfer Sonuçları",
        "",
        "| Video | 005A km/h | 006B transfer km/h | 006B median km/h | Conf | Valid segments | Speed CV | Plot |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["videos"]:
        lines.append(
            "| {video} | {s005a} | {s006b} | {median} | {conf} | {valid}/{selected} | {cv} | `{plot}` |".format(
                video=f"`{row['video']}`",
                s005a=row.get("speed_005a_kmh"),
                s006b=row.get("speed_006b_transfer_kmh"),
                median=row.get("speed_006b_median_kmh"),
                conf=row.get("confidence"),
                valid=row.get("valid_segment_count"),
                selected=row.get("selected_candidate_row_count"),
                cv=row.get("speed_cv"),
                plot=row.get("plot_uri"),
            )
        )
    lines.extend(
        [
            "",
            "## Yorum",
            "",
            "* Bu test, bizim üç videoda hız eğrisinin davranışını görmek içindir; ground-truth hız yoktur.",
            "* 006B transfer değerleri raporda `dataset_calibrated_parameter_transfer` veya `support_evidence` olarak anılmalıdır.",
            "* Final `huber_features` modelinin birebir lokal inference'ı istenirse Colab notebook'a `joblib.dump(final_model)` export cell'i eklenmelidir.",
            "* Demo videoda GT hız bulunmadığı için grafiklerin amacı anomali/pik, trend ve confidence kontrolüdür.",
            "",
            "## Üretilen Çıktılar",
            "",
            f"* Summary JSON: `{summary['summary_json']}`",
            f"* Timeseries CSV: `{summary['timeseries_csv']}`",
            f"* Summary plot: `{summary['summary_plot']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeseries", type=Path, default=DEFAULT_TIMESERIES)
    parser.add_argument("--summary-005a", type=Path, default=DEFAULT_005A_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    grouped = read_timeseries(args.timeseries)
    resolutions = summary_resolution_index(args.summary_005a)
    old_summary = summary_005a_index(args.summary_005a)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.runs_dir.mkdir(parents=True, exist_ok=True)

    videos = []
    output_rows_by_video: dict[str, list[dict[str, Any]]] = {}
    for video, rows in sorted(grouped.items()):
        if video not in resolutions:
            raise RuntimeError(f"Resolution missing for {video} in {args.summary_005a}")
        result = compute_006b_transfer(rows, resolutions[video], BEST_006B_PARAMS)
        output_rows_by_video[video] = result["timeseries"]
        times = [float(row.get("time_s") or 0.0) for row in result["timeseries"]]
        raw = [row.get("segment_speed_kmh_006b_raw") for row in result["timeseries"]]
        ma = [row.get("segment_speed_kmh_006b_moving_avg") for row in result["timeseries"]]
        heights = [row.get("bbox_height_px") for row in result["timeseries"]]
        plot_path = args.runs_dir / "plots" / f"{Path(video).stem}_speed_006b_transfer.png"
        draw_line_plot(
            plot_path,
            f"SPEED-EXP-006B transfer — {video}",
            times,
            [
                ("006B raw segment speed", raw, (180, 180, 180)),
                ("006B moving average speed", ma, (25, 25, 25)),
            ],
            secondary=("bbox height", heights, (90, 90, 90)),
        )
        videos.append(
            {
                "video": video,
                "speed_005a_kmh": round_or_none(parse_float(old_summary.get(video, {}).get("speed_kmh"))),
                "speed_005a_confidence": old_summary.get(video, {}).get("confidence"),
                "speed_006b_transfer_kmh": round_or_none(result.get("estimated_raw_transfer_kmh")),
                "speed_006b_median_kmh": round_or_none(result.get("moving_average_median_kmh")),
                "speed_006b_range_kmh": [round_or_none(result.get("p25_kmh")), round_or_none(result.get("p75_kmh"))],
                "speed_006b_p90_kmh": round_or_none(result.get("p90_kmh")),
                "confidence": result.get("confidence"),
                "observation_count": result.get("observation_count"),
                "valid_segment_count": result.get("valid_segment_count"),
                "selected_candidate_row_count": result.get("selected_candidate_row_count"),
                "candidate_valid_ratio": round_or_none(result.get("candidate_valid_ratio")),
                "speed_cv": round_or_none(result.get("speed_cv")),
                "mean_detection_confidence": round_or_none(result.get("mean_detection_confidence")),
                "invalid_segment_reasons": result.get("invalid_segment_reasons"),
                "plot_uri": rel(plot_path),
            }
        )

    summary_plot = args.runs_dir / "plots" / "speed_006b_demo_transfer_comparison.png"
    draw_bar_chart(summary_plot, videos)
    timeseries_csv = args.output_dir / "speed_exp_006b_demo_transfer_timeseries.csv"
    write_transfer_csv(timeseries_csv, output_rows_by_video)
    summary_json = args.output_dir / "speed_exp_006b_demo_transfer_summary.json"
    summary = {
        "experiment_id": "SPEED-EXP-006B-demo-transfer",
        "stage": "local_demo_transfer_smoke_test",
        "created_at": now_utc(),
        "source_timeseries": rel(args.timeseries),
        "source_005a_summary": rel(args.summary_005a),
        "best_006b_reference_metrics": BEST_006B_METRICS,
        "best_006b_geometry_params": BEST_006B_PARAMS,
        "model_artifact_note": "The final huber_features sklearn model was not exported from Colab; this run applies the 006B best geometry parameters only.",
        "summary_json": rel(summary_json),
        "timeseries_csv": rel(timeseries_csv),
        "summary_plot": rel(summary_plot),
        "videos": videos,
        "limitations": [
            "No ground-truth speed exists for the three local demo videos.",
            "This is not the persisted huber_features model inference; it is a best-parameter transfer smoke test.",
            "Outputs are approximate support evidence, not legal speed measurements.",
        ],
    }
    write_json(summary_json, summary)
    write_report(args.report, summary)
    print(json.dumps({"summary": rel(summary_json), "report": rel(args.report), "videos": videos}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
