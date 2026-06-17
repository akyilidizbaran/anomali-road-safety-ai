#!/usr/bin/env python3
"""Generate black-and-white academic figures for the road safety AI paper.

The script is deterministic and exports each figure as PNG, PDF, and SVG.
PNG outputs are 3000x1800 px at 300 DPI.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.patches import FancyArrowPatch
import numpy as np


FIG_W, FIG_H, DPI = 10.0, 6.0, 300
BG = "white"
BOX_FACE = "#f2f2f2"
BOX_FACE_LIGHT = "#f7f7f7"
BOX_EDGE = "#111111"
TEXT = "#111111"
MID = "#666666"
GRID = "#dddddd"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def make_canvas() -> tuple[plt.Figure, plt.Axes]:
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    return fig, ax


def save_all(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(
            output_dir / f"{stem}.{ext}",
            dpi=DPI,
            facecolor=BG,
            edgecolor=BG,
            metadata={"Creator": "Anomali Road Safety AI academic figure generator"},
        )
    plt.close(fig)


def wrapped(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def add_title(ax: plt.Axes, title: str) -> None:
    ax.text(
        5,
        5.72,
        title,
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=TEXT,
    )
    ax.plot([0.7, 9.3], [5.48, 5.48], color=BOX_EDGE, lw=0.9)


def box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    sublabel: str | None = None,
    fontsize: float = 11.5,
    subfontsize: float = 9.5,
    facecolor: str = BOX_FACE,
    lw: float = 1.1,
    linestyle: str = "-",
    radius: float = 0.0,
) -> patches.Rectangle:
    if radius > 0:
        patch = patches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle=f"round,pad=0.012,rounding_size={radius}",
            facecolor=facecolor,
            edgecolor=BOX_EDGE,
            lw=lw,
            linestyle=linestyle,
        )
    else:
        patch = patches.Rectangle(
            (x, y), w, h, facecolor=facecolor, edgecolor=BOX_EDGE, lw=lw, linestyle=linestyle
        )
    ax.add_patch(patch)
    if sublabel:
        ax.text(
            x + w / 2,
            y + h * 0.59,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color=TEXT,
        )
        ax.text(
            x + w / 2,
            y + h * 0.30,
            sublabel,
            ha="center",
            va="center",
            fontsize=subfontsize,
            color=TEXT,
        )
    else:
        ax.text(
            x + w / 2,
            y + h / 2,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color=TEXT,
        )
    return patch


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    lw: float = 1.0,
    mutation_scale: float = 12,
    linestyle: str = "-",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            lw=lw,
            color=BOX_EDGE,
            linestyle=linestyle,
            shrinkA=2,
            shrinkB=2,
        )
    )


def figure1(output_dir: Path) -> None:
    fig, ax = make_canvas()
    add_title(ax, "Şekil 1. Tek Kameralı Araç İzleme ve Kanıt Üretim Sistemi Genel Mimarisi")

    labels = [
        ("Mobil / Sabit Kamera", "tek kamera görüntüsü"),
        ("5G / Ağ Aktarımı", "canlı frame aktarımı"),
        ("Edge / Backend Çıkarım Sunucusu", "yerel veya uç çıkarım"),
        ("Modüler AI Servisleri", "Tespit · Takip · OCR · Hız · Risk"),
        ("Event + Evidence Layer", "izlenebilir karar kaydı"),
        ("Dashboard / Karar Destek", "operatör ve rapor arayüzü"),
    ]
    x, w, h = 2.2, 4.6, 0.54
    ys = [4.75, 4.05, 3.35, 2.65, 1.95, 1.25]
    for idx, ((label, sub), y) in enumerate(zip(labels, ys)):
        box(ax, x, y, w, h, label, sublabel=sub, fontsize=12.2, subfontsize=9.7)
        if idx < len(ys) - 1:
            arrow(ax, (x + w / 2, y), (x + w / 2, ys[idx + 1] + h))

    ax.text(
        7.72,
        3.0,
        "Evidence-based\nDecision Support",
        rotation=90,
        ha="center",
        va="center",
        fontsize=11.5,
        color=TEXT,
        fontweight="bold",
    )
    ax.plot([7.35, 7.35], [1.2, 4.95], color=MID, lw=0.8)
    ax.text(
        5,
        0.56,
        "Sistem, model çıktısını tek başına karar olarak değil, denetlenebilir event ve kanıt yapısı olarak üretir.",
        ha="center",
        va="center",
        fontsize=10.4,
        color=TEXT,
    )
    save_all(fig, output_dir, "figure1_system_architecture_bw")


def figure2(output_dir: Path) -> None:
    fig, ax = make_canvas()
    add_title(ax, "Şekil 2. Tek Kamera Tabanlı Algoritmik İşlem Akışı")

    main = [
        "Video\nKaresi",
        "Ön\nİşleme",
        "Araç Tespiti\n(YOLO11n)",
        "Araç Takibi\n(ByteTrack)",
        "Hedef Araç\nSeçimi",
        "Kanıt\nÇıkarımı",
        "Risk / Kanıt\nBirleştirme",
        "Event JSON +\nGörsel Overlay",
    ]
    y, h, w = 4.18, 0.62, 1.05
    xs = [0.35, 1.55, 2.75, 3.95, 5.15, 6.35, 7.55, 8.75]
    for i, (x, label) in enumerate(zip(xs, main)):
        box(ax, x, y, w, h, label, fontsize=9.4, facecolor=BOX_FACE)
        if i < len(xs) - 1:
            arrow(ax, (x + w, y + h / 2), (xs[i + 1], y + h / 2), lw=0.9, mutation_scale=10)

    evidence_center = (6.35 + w / 2, y)
    group_x, group_y, group_w, group_h = 2.95, 1.66, 5.92, 1.90
    ax.add_patch(
        patches.Rectangle(
            (group_x, group_y),
            group_w,
            group_h,
            fill=False,
            edgecolor=MID,
            lw=0.9,
            linestyle="--",
        )
    )
    ax.text(
        group_x + group_w / 2,
        group_y + group_h - 0.23,
        "Hedef araçtan çıkarılan kanıt kaynakları",
        ha="center",
        va="center",
        fontsize=10.1,
        fontweight="bold",
    )
    arrow(ax, evidence_center, (group_x + group_w / 2, group_y + group_h), lw=0.9, mutation_scale=10)
    evidence_boxes = [
        (3.20, 2.62, "Plaka + OCR"),
        (4.62, 2.62, "Track\nGeçmişi"),
        (6.04, 2.62, "Homografi /\nKalibrasyon"),
        (3.92, 1.86, "Plaka BBox\nGeçmişi"),
        (5.50, 1.86, "Araç BBox\nGeçmişi"),
    ]
    for x, yb, label in evidence_boxes:
        box(ax, x, yb, 1.22, 0.50, label, fontsize=8.8, facecolor=BOX_FACE_LIGHT, lw=0.85)
    arrow(ax, (group_x + group_w, group_y + group_h / 2), (8.07, 4.18), lw=0.9, mutation_scale=10)
    ax.text(5.75, 1.34, "Kanıt kaynakları hedef araç izi üzerinden hesaplanır.", ha="center", va="center", fontsize=10)
    ax.text(
        0.55,
        0.72,
        "Not: Hız kestirimi, kalibrasyon varsa mutlak; yoksa göreli hareket sinyali olarak raporlanır.",
        ha="left",
        va="center",
        fontsize=10,
        color=TEXT,
    )
    save_all(fig, output_dir, "figure2_algorithmic_pipeline_bw")


def figure3(output_dir: Path) -> None:
    fig, ax = make_canvas()
    add_title(ax, "Şekil 3. Event ve Evidence JSON Üretim Akışı")

    ax.text(1.75, 5.05, "Kanıt Kaynakları", ha="center", va="center", fontsize=12.2, fontweight="bold")
    sources = ["Kare Bilgisi", "Araç Tespiti", "Araç Takibi", "Plaka ve OCR", "Hız / Risk Sinyali"]
    source_y = [4.45, 3.82, 3.19, 2.56, 1.93]
    for s, y in zip(sources, source_y):
        box(ax, 0.55, y, 2.4, 0.44, s, fontsize=10.6, facecolor=BOX_FACE_LIGHT)
        arrow(ax, (2.95, y + 0.22), (4.03, 3.21), lw=0.8, mutation_scale=9)

    box(
        ax,
        4.05,
        2.15,
        2.1,
        2.12,
        "Evidence\nFusion Layer",
        sublabel="Güven skoru\nUyarılar\nKaynak izlenebilirliği\nZaman damgası",
        fontsize=12,
        subfontsize=9.5,
        facecolor=BOX_FACE,
        lw=1.2,
    )
    arrow(ax, (6.15, 3.21), (7.0, 3.21), lw=1.0, mutation_scale=12)

    ax.text(8.28, 5.05, "Event JSON", ha="center", va="center", fontsize=12.2, fontweight="bold")
    ax.add_patch(patches.Rectangle((7.05, 1.35), 2.65, 3.35, facecolor=BOX_FACE_LIGHT, edgecolor=BOX_EDGE, lw=1.1))
    json_lines = [
        "{",
        "  frame_id / timestamp",
        "  vehicle_id",
        "  detection_bbox",
        "  plate_ocr_result",
        "  speed_mode",
        "  risk_score",
        "  confidence",
        "  warnings",
        "  evidence_refs",
        "}",
    ]
    ax.text(
        7.28,
        4.42,
        "\n".join(json_lines),
        ha="left",
        va="top",
        fontsize=9.8,
        family="DejaVu Sans Mono",
        color=TEXT,
        linespacing=1.33,
    )

    ax.text(
        5,
        0.60,
        "Her event, görsel kanıt ve modül çıktılarıyla ilişkilendirilir.",
        ha="center",
        va="center",
        fontsize=10.6,
    )
    save_all(fig, output_dir, "figure3_event_evidence_json_bw")


def load_event(root: Path) -> dict | None:
    candidates = [
        root / "models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json",
        root / "models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        events = data.get("events", [])
        for event in events:
            if event.get("source", {}).get("source_video") == "video_3.mp4":
                return event
        if events:
            return events[0]
    return None


def read_video_frame(video_path: Path, frame_index: int) -> np.ndarray | None:
    try:
        import cv2
    except Exception:
        return None
    if not video_path.exists():
        return None
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame


def synthetic_frame() -> np.ndarray:
    h, w = 1080, 1920
    img = np.full((h, w), 230, dtype=np.uint8)
    # Perspective road surface.
    yy = np.linspace(0, 1, h)[:, None]
    img = (img * (0.92 - 0.18 * yy)).astype(np.uint8)
    for x1, x2 in [(650, 450), (1270, 1470)]:
        for t in range(-3, 4):
            rr = np.arange(h)
            cc = (x1 + (x2 - x1) * rr / h + t).astype(int)
            valid = (cc >= 0) & (cc < w)
            img[rr[valid], cc[valid]] = 80
    # Vehicle silhouette.
    img[360:690, 1180:1540] = 90
    img[430:540, 1230:1490] = 55
    img[620:670, 1305:1425] = 200
    return np.dstack([img, img, img])


def grayscale_rgb(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        gray = frame.astype(np.float32)
    else:
        gray = 0.299 * frame[:, :, 0] + 0.587 * frame[:, :, 1] + 0.114 * frame[:, :, 2]
    # Mild contrast stretch for publication print.
    lo, hi = np.percentile(gray, [1, 99])
    gray = np.clip((gray - lo) / max(hi - lo, 1) * 255, 0, 255).astype(np.uint8)
    return np.dstack([gray, gray, gray])


def figure5(output_dir: Path) -> None:
    root = repo_root()
    event = load_event(root)
    video = root / "Test/video_3.mp4"
    frame_idx = 101
    if event:
        plate = event.get("plate", {})
        frame_idx = int(plate.get("best_frame") or event.get("target_vehicle", {}).get("frame_window", {}).get("best_frame") or 101)
        video = root / "Test" / event.get("source", {}).get("source_video", "video_3.mp4")

    frame = read_video_frame(video, frame_idx)
    source_note = f"source: {video.name}, frame: {frame_idx}" if frame is not None else "source: schematic fallback"
    if frame is None:
        frame = synthetic_frame()
    frame = grayscale_rgb(frame)
    height, width = frame.shape[:2]

    fig, ax = make_canvas()
    add_title(ax, "Şekil 5. Demo Karesi Üzerinde Kanıt Tabanlı Overlay Örneği")

    # Image frame area.
    img_x, img_y, img_w, img_h = 0.55, 0.78, 6.85, 4.35
    ax.imshow(frame, extent=(img_x, img_x + img_w, img_y, img_y + img_h), cmap="gray", aspect="auto", zorder=0)
    ax.add_patch(patches.Rectangle((img_x, img_y), img_w, img_h, fill=False, edgecolor=BOX_EDGE, lw=1.0))

    def px_to_axes(x: float, y: float) -> tuple[float, float]:
        return img_x + (x / width) * img_w, img_y + img_h - (y / height) * img_h

    # Manual, deterministic annotation for video_3 frame 101; fallback scales naturally.
    vehicle_px = (2235, 560, 3065, 1265) if frame.shape[1] >= 3000 else (1180, 360, 1540, 690)
    plate_px = (2490, 855, 2935, 1048) if frame.shape[1] >= 3000 else (1290, 600, 1450, 690)
    x1, y1 = px_to_axes(vehicle_px[0], vehicle_px[1])
    x2, y2 = px_to_axes(vehicle_px[2], vehicle_px[3])
    vx, vy, vw, vh = min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
    ax.add_patch(patches.Rectangle((vx, vy), vw, vh, fill=False, edgecolor="black", lw=1.55))
    ax.text(
        vx,
        vy + vh + 0.08,
        "track_id: 12 | vehicle_bbox",
        ha="left",
        va="bottom",
        fontsize=9.7,
        color="black",
        bbox=dict(facecolor="white", edgecolor="black", lw=0.7, pad=2),
    )

    p1x, p1y = px_to_axes(plate_px[0], plate_px[1])
    p2x, p2y = px_to_axes(plate_px[2], plate_px[3])
    px0, py0, pw, ph = min(p1x, p2x), min(p1y, p2y), abs(p2x - p1x), abs(p2y - p1y)
    ax.add_patch(patches.Rectangle((px0, py0), pw, ph, facecolor="#d9d9d9", edgecolor="black", lw=1.1, linestyle="--"))
    ax.text(px0 + pw / 2, py0 + ph / 2, "masked", ha="center", va="center", fontsize=8.2, color="black")
    ax.text(
        px0,
        py0 - 0.08,
        "plate/OCR: XX-***",
        ha="left",
        va="top",
        fontsize=8.8,
        color="black",
        bbox=dict(facecolor="white", edgecolor="black", lw=0.6, pad=1.8),
    )

    # Academic evidence panel.
    panel_x, panel_y, panel_w, panel_h = 7.68, 0.78, 1.78, 4.35
    ax.add_patch(patches.Rectangle((panel_x, panel_y), panel_w, panel_h, facecolor=BOX_FACE_LIGHT, edgecolor=BOX_EDGE, lw=1.0))
    ax.text(panel_x + panel_w / 2, panel_y + panel_h - 0.34, "Evidence Panel", ha="center", va="center", fontsize=12, fontweight="bold")
    rows = [
        ("Track ID", "12"),
        ("OCR Confidence", "0.87"),
        ("Speed Mode", "relative"),
        ("Risk Score", "medium"),
        ("Warnings", "calibration\nunavailable"),
    ]
    y = panel_y + panel_h - 0.78
    for key, value in rows:
        ax.text(panel_x + 0.15, y, key, ha="left", va="center", fontsize=9.5, fontweight="bold")
        ax.text(panel_x + 0.15, y - 0.21, value, ha="left", va="top", fontsize=9.2)
        ax.plot([panel_x + 0.12, panel_x + panel_w - 0.12], [y - 0.43, y - 0.43], color=GRID, lw=0.8)
        y -= 0.70
    ax.text(0.58, 0.43, source_note, ha="left", va="center", fontsize=8.7, color=TEXT)
    ax.text(5.95, 0.43, "Not: OCR çıktısı gizlilik amacıyla maskelenmiştir.", ha="left", va="center", fontsize=8.7, color=TEXT)
    save_all(fig, output_dir, "figure5_demo_overlay_bw")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/academic_figures_bw")
    args = parser.parse_args()
    output_dir = (repo_root() / args.output_dir).resolve()

    figure1(output_dir)
    figure2(output_dir)
    figure3(output_dir)
    figure5(output_dir)

    print("Generated academic black-and-white figures:")
    for path in sorted(output_dir.glob("*")):
        print(" -", path)


if __name__ == "__main__":
    main()
