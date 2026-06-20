#!/usr/bin/env python3
"""Create confidence and candidate-speed audit plots for the speed layer.

This audit intentionally separates "signal confidence" from "absolute km/h
accuracy". The demo videos have no ground-truth speed, so the plots are meant
to explain why a layer received a high support score, not to claim that the
reported km/h is correct.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_004A = ROOT / "models/benchmarks/artifacts/speed/SPEED-EXP-004A-relative-track-bbox/speed_exp_004a_relative_track_speed_summary.json"
DEFAULT_002 = ROOT / "models/benchmarks/artifacts/speed/SPEED-EXP-002-plate-bbox-xyz/speed_exp_002_plate_bbox_xyz_summary.json"
DEFAULT_005A = ROOT / "models/benchmarks/artifacts/speed/SPEED-EXP-005A-bbox-geometry-auto/speed_exp_005a_bbox_geometry_summary.json"
DEFAULT_005A_TS = ROOT / "models/benchmarks/artifacts/speed/SPEED-EXP-005A-bbox-geometry-auto/speed_exp_005a_bbox_geometry_timeseries.csv"
DEFAULT_005D = ROOT / "models/benchmarks/artifacts/speed/SPEED-EXP-005D-candidate-fusion/speed_exp_005d_candidate_fusion_summary.json"
DEFAULT_RUNS = ROOT / "runs/speed/SPEED-EXP-005D-candidate-fusion/plots"
DEFAULT_ARTIFACT = ROOT / "models/benchmarks/artifacts/speed/SPEED-EXP-005D-candidate-fusion/speed_exp_005d_confidence_audit.json"
DEFAULT_REPORT = ROOT / "testing/reports/speed_exp_005d_confidence_audit.md"

CANVAS_W = 1800
CANVAS_H = 1080
BG = "white"
BLACK = (20, 20, 20)
GREY = (100, 100, 100)
LIGHT = (235, 235, 235)
MID = (190, 190, 190)
DARK = (65, 65, 65)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fnum(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def round_or_none(value: Any, digits: int = 4) -> float | None:
    number = fnum(value)
    return round(number, digits) if number is not None else None


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


F_TITLE = font(42, bold=True)
F_SUB = font(25)
F_AXIS = font(24)
F_SMALL = font(21)
F_TINY = font(18)
F_BOLD = font(24, bold=True)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, fill=BLACK, font_obj=None, anchor=None) -> None:
    draw.text(xy, value, fill=fill, font=font_obj or F_SMALL, anchor=anchor)


def safe_video_stem(video: str) -> str:
    return Path(video).stem


def index_004a(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for event in data.get("events", []):
        block = event.get("speed_exp_004a") or {}
        out[event["video"]] = {
            "relative_speed_score": block.get("relative_speed_score"),
            "relative_speed_label": block.get("relative_speed_label"),
            "relative_confidence": block.get("fusion_confidence"),
            "jitter": block.get("bbox_motion_jitter_score"),
        }
    return out


def index_002(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for video in data.get("videos", []):
        variants = video.get("variants") or {}
        geomean = variants.get("geomean") or {}
        summary = geomean.get("summary") or {}
        note = str(summary.get("confidence_note") or "")
        out[video["video"]] = {
            "plate_speed_kmh": summary.get("median_speed_kmh"),
            "plate_confidence": 0.28 if "low_" in note else 0.45,
            "confidence_note": note,
            "aspect_ratio_median": video.get("plate_aspect_ratio_median"),
            "usable_measurement_count": video.get("usable_measurement_count"),
        }
    return out


def index_005a(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for video in data.get("videos", []):
        candidate = video.get("bbox_geometry_candidate") or {}
        diagnostics = candidate.get("diagnostics") or {}
        out[video["video"]] = {
            "bbox_speed_kmh": candidate.get("estimated_kmh"),
            "bbox_confidence": candidate.get("confidence"),
            "speed_range_kmh": candidate.get("speed_range_kmh"),
            "observation_count": diagnostics.get("observation_count"),
            "usable_segment_count": diagnostics.get("usable_segment_count"),
            "speed_cv": diagnostics.get("speed_cv"),
            "invalid_reason_counts": diagnostics.get("invalid_reason_counts"),
        }
    return out


def index_005d(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for event in data.get("events", []):
        block = event.get("speed_exp_005d") or {}
        out[event["video"]] = {
            "fused_speed_kmh": block.get("estimated_kmh"),
            "fusion_confidence": block.get("fusion_confidence"),
            "decision": block.get("decision"),
            "speed_mode": block.get("speed_mode"),
            "agreement": (block.get("candidate_agreement") or {}).get("bbox_vs_plate_relative_diff_ratio"),
            "relative_support": (block.get("candidate_agreement") or {}).get("relative_label_supports_candidate"),
        }
    return out


def read_timeseries(path: Path) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            video = row["video"]
            out.setdefault(video, []).append(row)
    return out


def collect_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    d004a = index_004a(load_json(args.summary_004a))
    d002 = index_002(load_json(args.summary_002))
    d005a = index_005a(load_json(args.summary_005a))
    d005d = index_005d(load_json(args.summary_005d))
    videos = sorted(set(d004a) | set(d002) | set(d005a) | set(d005d))
    rows = []
    for video in videos:
        row = {"video": video}
        row.update(d004a.get(video, {}))
        row.update(d002.get(video, {}))
        row.update(d005a.get(video, {}))
        row.update(d005d.get(video, {}))
        row["confidence_breakdown"] = confidence_breakdown(row)
        row["interpretation"] = interpret_row(row)
        rows.append(row)
    return rows, read_timeseries(args.timeseries_005a)


def confidence_breakdown(row: dict[str, Any]) -> dict[str, float]:
    bbox_conf = fnum(row.get("bbox_confidence"), 0.0) or 0.0
    plate_conf = fnum(row.get("plate_confidence"), 0.0) or 0.0
    relative_conf = fnum(row.get("relative_confidence"), 0.0) or 0.0
    agreement = fnum(row.get("agreement"))
    relative_ok = bool(row.get("relative_support"))
    parts = {
        "base": 0.20,
        "bbox_quality": 0.38 * max(0.0, min(1.0, bbox_conf)),
        "plate_support": 0.12 * max(0.0, min(1.0, plate_conf)),
        "relative_track_support": 0.10 * max(0.0, min(1.0, relative_conf)),
        "agreement_support": 0.0,
        "relative_label_support": 0.07 if relative_ok else 0.0,
    }
    if agreement is not None:
        parts["agreement_support"] = 0.13 * max(0.0, min(1.0, 1.0 - agreement / 0.45))
    raw_total = sum(parts.values())
    capped = min(0.72, raw_total)
    parts["raw_total"] = raw_total
    parts["cap_penalty"] = raw_total - capped
    parts["fused_confidence"] = capped
    return {k: round(v, 4) for k, v in parts.items()}


def interpret_row(row: dict[str, Any]) -> str:
    label = row.get("relative_speed_label")
    bbox_conf = fnum(row.get("bbox_confidence"), 0.0) or 0.0
    fusion_conf = fnum(row.get("fusion_confidence"), 0.0) or 0.0
    agreement = fnum(row.get("agreement"))
    if fusion_conf >= 0.70 and agreement is not None and agreement <= 0.45:
        return "High support for approximate candidate; not ground-truth km/h."
    if bbox_conf >= 0.70:
        return "Bbox signal is internally stable, but final support is limited."
    if label == "fast":
        return "Relative motion marks fast behavior; absolute km/h remains approximate."
    return "Support signal only."


def draw_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], ymax: float, ylabel: str) -> None:
    x0, y0, x1, y1 = box
    draw.line((x0, y0, x0, y1), fill=BLACK, width=3)
    draw.line((x0, y1, x1, y1), fill=BLACK, width=3)
    for i in range(6):
        value = ymax * i / 5
        y = y1 - int((y1 - y0) * i / 5)
        draw.line((x0 - 8, y, x0, y), fill=BLACK, width=2)
        if i:
            draw.line((x0, y, x1, y), fill=(228, 228, 228), width=1)
        text(draw, (x0 - 14, y), f"{value:.1f}", font_obj=F_TINY, fill=GREY, anchor="rm")
    text(draw, (x0, y0 - 44), ylabel, font_obj=F_AXIS, fill=BLACK)


def draw_grouped_bars(
    rows: list[dict[str, Any]],
    series: list[tuple[str, str, tuple[int, int, int]]],
    title: str,
    subtitle: str,
    ylabel: str,
    ymax: float,
    path: Path,
) -> None:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    draw = ImageDraw.Draw(img)
    text(draw, (70, 54), title, font_obj=F_TITLE)
    text(draw, (70, 110), subtitle, font_obj=F_SUB, fill=GREY)
    chart = (150, 220, 1680, 850)
    draw_axes(draw, chart, ymax, ylabel)
    x0, y0, x1, y1 = chart
    group_w = (x1 - x0) / max(1, len(rows))
    bar_gap = 12
    bar_w = int((group_w - 70) / len(series)) - bar_gap
    for idx, row in enumerate(rows):
        gx = x0 + idx * group_w + 42
        for si, (label, key, color) in enumerate(series):
            value = fnum(row.get(key), 0.0) or 0.0
            h = int((y1 - y0) * min(value, ymax) / ymax)
            bx0 = int(gx + si * (bar_w + bar_gap))
            bx1 = bx0 + bar_w
            by0 = y1 - h
            draw.rectangle((bx0, by0, bx1, y1), fill=color, outline=BLACK, width=2)
            text(draw, ((bx0 + bx1) // 2, by0 - 28), f"{value:.2f}", font_obj=F_TINY, anchor="mm")
        video = safe_video_stem(row["video"])
        text(draw, (int(gx + (len(series) * (bar_w + bar_gap)) / 2 - bar_gap), y1 + 30), video, font_obj=F_AXIS, anchor="mm")
        note = str(row.get("relative_speed_label") or "")
        text(draw, (int(gx + (len(series) * (bar_w + bar_gap)) / 2 - bar_gap), y1 + 62), f"relative: {note}", font_obj=F_TINY, fill=GREY, anchor="mm")
    lx, ly = 1280, 130
    for label, _key, color in series:
        draw.rectangle((lx, ly, lx + 34, ly + 22), fill=color, outline=BLACK, width=2)
        text(draw, (lx + 48, ly - 2), label, font_obj=F_SMALL)
        ly += 34
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def draw_confidence_breakdown(rows: list[dict[str, Any]], path: Path) -> None:
    parts = [
        ("base", "Base", (230, 230, 230)),
        ("bbox_quality", "BBox quality", (180, 180, 180)),
        ("plate_support", "Plate support", (145, 145, 145)),
        ("relative_track_support", "Relative track", (105, 105, 105)),
        ("agreement_support", "Agreement", (75, 75, 75)),
        ("relative_label_support", "Label support", (40, 40, 40)),
    ]
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    draw = ImageDraw.Draw(img)
    text(draw, (70, 54), "SPEED-EXP-005D Fusion Confidence Breakdown", font_obj=F_TITLE)
    text(draw, (70, 110), "Stacked components; total is capped at 0.72 and does not represent ground-truth km/h accuracy.", font_obj=F_SUB, fill=GREY)
    chart = (150, 220, 1680, 850)
    draw_axes(draw, chart, 0.8, "Confidence contribution")
    x0, y0, x1, y1 = chart
    group_w = (x1 - x0) / max(1, len(rows))
    bar_w = int(group_w * 0.42)
    for idx, row in enumerate(rows):
        gx = int(x0 + idx * group_w + group_w * 0.29)
        y_cursor = y1
        breakdown = row["confidence_breakdown"]
        for key, _label, color in parts:
            value = breakdown[key]
            h = int((y1 - y0) * value / 0.8)
            draw.rectangle((gx, y_cursor - h, gx + bar_w, y_cursor), fill=color, outline=BLACK, width=2)
            y_cursor -= h
        fused = fnum(row.get("fusion_confidence"), 0.0) or 0.0
        text(draw, (gx + bar_w // 2, y_cursor - 30), f"{fused:.3f}", font_obj=F_SMALL, anchor="mm")
        if breakdown.get("cap_penalty", 0) > 0:
            text(draw, (gx + bar_w // 2, y_cursor - 58), "capped", font_obj=F_TINY, fill=GREY, anchor="mm")
        text(draw, (gx + bar_w // 2, y1 + 30), safe_video_stem(row["video"]), font_obj=F_AXIS, anchor="mm")
        text(draw, (gx + bar_w // 2, y1 + 62), str(row.get("decision")), font_obj=F_TINY, fill=GREY, anchor="mm")
    lx, ly = 1180, 130
    for _key, label, color in parts:
        draw.rectangle((lx, ly, lx + 34, ly + 22), fill=color, outline=BLACK, width=2)
        text(draw, (lx + 48, ly - 2), label, font_obj=F_SMALL)
        ly += 34
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def draw_timeseries(rows: list[dict[str, Any]], timeseries: dict[str, list[dict[str, Any]]], path: Path) -> None:
    img = Image.new("RGB", (CANVAS_W, 1380), BG)
    draw = ImageDraw.Draw(img)
    text(draw, (70, 54), "High-Confidence Speed Candidate Time Series", font_obj=F_TITLE)
    text(draw, (70, 110), "SPEED-EXP-005A moving average curves. Peaks are filtered; values remain approximate without ground truth.", font_obj=F_SUB, fill=GREY)
    panel_h = 300
    panel_gap = 78
    start_y = 210
    for idx, row in enumerate(rows):
        video = row["video"]
        panel = (145, start_y + idx * (panel_h + panel_gap), 1680, start_y + idx * (panel_h + panel_gap) + panel_h)
        x0, y0, x1, y1 = panel
        values = []
        raw_values = []
        for item in timeseries.get(video, []):
            t = fnum(item.get("time_s"))
            moving = fnum(item.get("segment_speed_kmh_moving_avg"))
            raw = fnum(item.get("segment_speed_kmh_raw"))
            if t is not None and moving is not None:
                values.append((t, moving))
            if t is not None and raw is not None:
                raw_values.append((t, raw))
        ymax = max([v for _t, v in raw_values + values] or [1.0])
        ymax = max(5.0, min(35.0, ymax * 1.1))
        draw.rectangle(panel, outline=BLACK, width=2)
        for i in range(1, 5):
            y = y1 - int((y1 - y0) * i / 5)
            draw.line((x0, y, x1, y), fill=(230, 230, 230), width=1)
        def pt(t: float, v: float) -> tuple[int, int]:
            max_t = max([p[0] for p in values] or [1.0])
            x = x0 + int((x1 - x0) * t / max_t)
            y = y1 - int((y1 - y0) * min(v, ymax) / ymax)
            return x, y
        if len(raw_values) > 1:
            raw_pts = [pt(t, v) for t, v in raw_values]
            draw.line(raw_pts, fill=(190, 190, 190), width=2)
        if len(values) > 1:
            pts = [pt(t, v) for t, v in values]
            draw.line(pts, fill=BLACK, width=4)
        fused = row.get("fused_speed_kmh")
        if fused is not None:
            fy = y1 - int((y1 - y0) * min(float(fused), ymax) / ymax)
            draw.line((x0, fy, x1, fy), fill=(70, 70, 70), width=2)
            text(draw, (x1 - 10, fy - 28), f"fused {float(fused):.2f} km/h", font_obj=F_TINY, anchor="ra")
        title = (
            f"{safe_video_stem(video)} | 005A conf={row.get('bbox_confidence')} | "
            f"005D conf={row.get('fusion_confidence')} | relative={row.get('relative_speed_label')}"
        )
        text(draw, (x0, y0 - 32), title, font_obj=F_BOLD)
        text(draw, (x0 - 16, y0), f"{ymax:.1f}", font_obj=F_TINY, fill=GREY, anchor="rt")
        text(draw, (x0 - 16, y1), "0", font_obj=F_TINY, fill=GREY, anchor="rb")
        text(draw, (x1, y1 + 10), "time (s)", font_obj=F_TINY, fill=GREY, anchor="ra")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def write_report(rows: list[dict[str, Any]], report: Path, plots_dir: Path) -> None:
    lines = [
        "# SPEED-EXP-005D Confidence Audit",
        "",
        "Bu rapor, hız katmanlarındaki confidence skorlarının ne anlama geldiğini ayırmak için oluşturuldu.",
        "Mevcut üç demo videoda ground-truth hız bulunmadığı için hiçbir confidence değeri mutlak km/s doğruluğu olarak yorumlanmamalıdır.",
        "",
        "## Kısa Sonuç",
        "",
        "* `SPEED-EXP-004A`: Track/bbox göreli hareket sinyalidir; km/s üretmez. Confidence, track kararlılığı ve bbox geçmiş kalitesidir.",
        "* `SPEED-EXP-002`: Plaka ölçeği destek sinyalidir. Mevcut aspect-ratio sapmaları nedeniyle düşük confidence ile tutulur.",
        "* `SPEED-EXP-005A`: Bbox geometry otomatik yaklaşık km/s adayıdır. Confidence, uzun/stabil track ve filtrelenmiş segment kalitesidir.",
        "* `SPEED-EXP-005D`: 004A + 002 + 005A sinyallerini birleştirir. Fusion confidence, adayların birbirini destekleme düzeyidir; ground-truth accuracy değildir.",
        "",
        "## Üretilen Grafikler",
        "",
        f"* `{plots_dir / 'speed_candidate_comparison.png'}`",
        f"* `{plots_dir / 'confidence_comparison.png'}`",
        f"* `{plots_dir / 'fusion_confidence_breakdown.png'}`",
        f"* `{plots_dir / 'speed_candidate_timeseries_grid.png'}`",
        "",
        "## Katman Sonuçları",
        "",
        "| Video | 004A relative | 004A conf | 002 plate km/h | 002 conf | 005A bbox km/h | 005A conf | 005D final km/h | 005D conf | Yorum |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {video} | {rel} | {rel_conf} | {plate_speed} | {plate_conf} | {bbox_speed} | {bbox_conf} | {fused_speed} | {fusion_conf} | {interp} |".format(
                video=row["video"],
                rel=row.get("relative_speed_label"),
                rel_conf=row.get("relative_confidence"),
                plate_speed=row.get("plate_speed_kmh"),
                plate_conf=row.get("plate_confidence"),
                bbox_speed=row.get("bbox_speed_kmh"),
                bbox_conf=row.get("bbox_confidence"),
                fused_speed=row.get("fused_speed_kmh"),
                fusion_conf=row.get("fusion_confidence"),
                interp=row.get("interpretation"),
            )
        )
    lines += [
        "",
        "## Confidence Formülleri",
        "",
        "### 004A Relative Track/BBox",
        "",
        "```text",
        "confidence = 0.35",
        "           + 0.45 * track_stability",
        "           + 0.10 * min(history_count / 30, 1)",
        "           + 0.05 if median_bbox_height >= 80",
        "           - 0.12 * min(bbox_jitter_score / 1.25, 1)",
        "           - 0.25 if id_switch_suspected",
        "cap: 0.95",
        "```",
        "",
        "Bu skor track kalitesidir; km/s doğruluğu değildir.",
        "",
        "### 005A BBox Geometry",
        "",
        "```text",
        "confidence = 0.20",
        "           + 0.22 * min(observation_count / 240, 1)",
        "           + 0.18 * min(median_bbox_height / 300, 1)",
        "           + 0.15 if moving_average_speed exists",
        "           + 0.12 * (1 - speed_cv / 1.2)",
        "           - invalid/outlier penalties",
        "cap: 0.72",
        "```",
        "",
        "Bu skor otomatik monocular aday sinyalinin iç stabilitesidir. Ölçülü referans veya ground truth yoksa nihai hız doğruluğu anlamına gelmez.",
        "",
        "### 005D Candidate Fusion",
        "",
        "```text",
        "fusion_confidence = 0.20",
        "                  + 0.38 * bbox_confidence",
        "                  + 0.12 * plate_confidence",
        "                  + 0.10 * relative_confidence",
        "                  + 0.13 * agreement_support",
        "                  + 0.07 if relative_label supports candidate",
        "cap: 0.72",
        "```",
        "",
        "Bu skor aday hızların birbirini destekleme skorudur. En doğru yorum: `support/evidence confidence`.",
        "",
        "## Kapanış Kararı",
        "",
        "Hız modülü mevcut FTR fazı için `support evidence only` olarak yeterlidir. 005D grafikleri, üç videoda göreli sinyal + bbox geometry + plaka ölçeği arasında tutarlı bir destek olduğunu gösterir. Ancak bu, gerçek hız ground-truth'u olmadığı için mutlak hız modelinin tamamlandığı anlamına gelmez. Hız konusu FTR geliştirmesini bloklamamalı; future scope'ta kontrollü ground-truth video veya kalibrasyonlu sahne ile doğrulanmalıdır.",
        "",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-004a", type=Path, default=DEFAULT_004A)
    parser.add_argument("--summary-002", type=Path, default=DEFAULT_002)
    parser.add_argument("--summary-005a", type=Path, default=DEFAULT_005A)
    parser.add_argument("--timeseries-005a", type=Path, default=DEFAULT_005A_TS)
    parser.add_argument("--summary-005d", type=Path, default=DEFAULT_005D)
    parser.add_argument("--plots-dir", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    rows, timeseries = collect_rows(args)
    args.plots_dir.mkdir(parents=True, exist_ok=True)

    draw_grouped_bars(
        rows,
        [
            ("Plate scale", "plate_speed_kmh", (215, 215, 215)),
            ("BBox geometry", "bbox_speed_kmh", (125, 125, 125)),
            ("Fusion final", "fused_speed_kmh", (35, 35, 35)),
        ],
        "Speed Candidate Comparison",
        "Plate-scale, bbox-geometry and fusion outputs. Values are approximate support evidence, not legal speed.",
        "km/h",
        max(20.0, max((fnum(r.get("plate_speed_kmh"), 0) or 0) for r in rows) * 1.25, max((fnum(r.get("bbox_speed_kmh"), 0) or 0) for r in rows) * 1.25),
        args.plots_dir / "speed_candidate_comparison.png",
    )
    draw_grouped_bars(
        rows,
        [
            ("004A relative", "relative_confidence", (220, 220, 220)),
            ("002 plate", "plate_confidence", (170, 170, 170)),
            ("005A bbox", "bbox_confidence", (105, 105, 105)),
            ("005D fusion", "fusion_confidence", (35, 35, 35)),
        ],
        "Speed Layer Confidence Comparison",
        "Confidence is signal/support quality. No ground-truth speed is available for these videos.",
        "confidence",
        1.0,
        args.plots_dir / "confidence_comparison.png",
    )
    draw_confidence_breakdown(rows, args.plots_dir / "fusion_confidence_breakdown.png")
    draw_timeseries(rows, timeseries, args.plots_dir / "speed_candidate_timeseries_grid.png")

    audit = {
        "experiment_id": "SPEED-EXP-005D-confidence-audit",
        "purpose": "Explain speed-layer confidence scores and generate high-confidence candidate plots.",
        "ground_truth_speed_available": False,
        "rows": rows,
        "plots": {
            "speed_candidate_comparison": str(args.plots_dir / "speed_candidate_comparison.png"),
            "confidence_comparison": str(args.plots_dir / "confidence_comparison.png"),
            "fusion_confidence_breakdown": str(args.plots_dir / "fusion_confidence_breakdown.png"),
            "speed_candidate_timeseries_grid": str(args.plots_dir / "speed_candidate_timeseries_grid.png"),
        },
        "interpretation": {
            "high_confidence_means": "internal signal quality and candidate agreement",
            "high_confidence_does_not_mean": "verified ground-truth absolute km/h accuracy",
            "closure": "sufficient as support/evidence signal for FTR phase; not a legal speed estimator",
        },
    }
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.artifact.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(rows, args.report, args.plots_dir)
    print(f"Wrote audit artifact: {args.artifact}")
    print(f"Wrote report: {args.report}")
    for name, path in audit["plots"].items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
