#!/usr/bin/env python3
"""Compare phone-call action scores on driver-focused ROI strategies.

DACT-EXP-020B was trained on in-cabin State Farm images. The project demo videos
are exterior road-facing videos, so this script does not emit a final driver
action. It only measures whether a tighter driver/head-shoulder crop gives a
more usable ``telefonla_konusma`` signal than the earlier broad vehicle/cabin
crop.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch

try:
    from run_dact_020b_external_video_smoke import (
        cabin_candidate_bbox,
        clamp_bbox,
        crop_bbox,
        infer_crop,
        load_events,
        load_model,
        make_transform,
        pick_device,
        prepare_writer,
    )
except ImportError:
    from scripts.benchmarks.run_dact_020b_external_video_smoke import (
        cabin_candidate_bbox,
        clamp_bbox,
        crop_bbox,
        infer_crop,
        load_events,
        load_model,
        make_transform,
        pick_device,
        prepare_writer,
    )


ROOT = Path(__file__).resolve().parents[2]

EXPERIMENT_ID = "DACT-EXP-021"
EXPERIMENT_NAME = "phone_call_driver_roi_head_shoulder_smoke_v1"
SOURCE_MODEL_EXPERIMENT_ID = "DACT-EXP-020B"

DEFAULT_CHECKPOINT = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin_driver"
    / "DACT-EXP-020B"
    / "DACT-EXP-020B-efficientnet_b0-best.pth"
)
DEFAULT_LABEL_MAP = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin_driver"
    / "DACT-EXP-020B"
    / "DACT-EXP-020B-label-map.json"
)
DEFAULT_EVENTS = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-driver-detection.json"
)
DEFAULT_PHONE_ROI_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-EXP-004-yolo26s_phone_windshield_seed_smoke-summary.json"
)
DEFAULT_POSE_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "POSE-EXP-010-vitpose_b_arm_focus_observations_v1-summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "driver_action" / f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"
DEFAULT_ARTIFACT_DIR = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "cabin_driver"
    / f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"
)
DEFAULT_REPORT = (
    ROOT
    / "testing"
    / "reports"
    / "dact_exp_021_phone_call_driver_roi_head_shoulder_smoke.md"
)

PHONE_CALL_LABEL = "telefonla_konusma"
FTR_ACTION_LABELS = {
    "telefonla_konusma",
    "phone_use_non_call",
    "su_icme",
    "arkaya_bakma_candidate",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run DACT-EXP-020B on target/driver/head-shoulder ROIs for phone-call smoke testing."
    )
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--label-map", type=Path, default=DEFAULT_LABEL_MAP)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--phone-roi-summary", type=Path, default=DEFAULT_PHONE_ROI_SUMMARY)
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["target_vehicle", "driver_roi", "head_shoulder_roi"],
        choices=["target_vehicle", "cabin_candidate", "driver_roi", "head_shoulder_roi", "face_near_roi"],
    )
    parser.add_argument("--sample-every", type=int, default=1)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--output-width", type=int, default=1280)
    parser.add_argument("--temporal-threshold", type=float, default=0.65)
    parser.add_argument("--min-positive-rate", type=float, default=0.20)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    return parser.parse_args()


def load_video_frame_index(summary_path: Path) -> dict[str, dict[int, dict[str, Any]]]:
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    index: dict[str, dict[int, dict[str, Any]]] = {}
    for video in data.get("videos", []):
        per_frame = video.get("per_frame") or []
        index[str(video.get("video"))] = {
            int(item.get("frame") or -1): item
            for item in per_frame
            if item.get("frame") is not None
        }
    return index


def expand_face_bbox(
    face_bbox: list[float] | None,
    width: int,
    height: int,
) -> tuple[int, int, int, int] | None:
    if not face_bbox or len(face_bbox) != 4:
        return None
    fx1, fy1, fx2, fy2 = [float(v) for v in face_bbox]
    fw = max(1.0, fx2 - fx1)
    fh = max(1.0, fy2 - fy1)
    return clamp_bbox(
        [
            fx1 - 3.0 * fw,
            fy1 - 1.1 * fh,
            fx2 + 3.2 * fw,
            fy2 + 3.9 * fh,
        ],
        width,
        height,
    )


def mode_bbox(
    frame: np.ndarray,
    event: dict[str, Any],
    mode: str,
    frame_number: int,
    phone_index: dict[str, dict[int, dict[str, Any]]],
    pose_index: dict[str, dict[int, dict[str, Any]]],
) -> tuple[int, int, int, int] | None:
    h, w = frame.shape[:2]
    video_name = str(event["source"]["source_video"])
    target_bbox = clamp_bbox(
        event.get("target_vehicle", {}).get("bbox_xyxy") or [],
        w,
        h,
    )
    if mode == "target_vehicle":
        return target_bbox
    if mode == "cabin_candidate":
        if target_bbox is None:
            return None
        view_profile = (event.get("driver_detection") or {}).get("view_profile")
        return cabin_candidate_bbox(target_bbox, w, h, view_profile)
    if mode == "driver_roi":
        record = phone_index.get(video_name, {}).get(frame_number) or {}
        bbox = record.get("phone_roi_bbox")
        if bbox:
            return clamp_bbox(bbox, w, h)
        if target_bbox is None:
            return None
        view_profile = (event.get("driver_detection") or {}).get("view_profile")
        return cabin_candidate_bbox(target_bbox, w, h, view_profile)
    if mode == "head_shoulder_roi":
        record = pose_index.get(video_name, {}).get(frame_number) or {}
        bbox = record.get("upper_body_roi_bbox")
        if bbox:
            return clamp_bbox(bbox, w, h)
        return expand_face_bbox(record.get("driver_face_bbox"), w, h)
    if mode == "face_near_roi":
        record = pose_index.get(video_name, {}).get(frame_number) or {}
        return expand_face_bbox(record.get("driver_face_bbox"), w, h)
    raise ValueError(mode)


def draw_label(
    frame: np.ndarray,
    text: str,
    xy: tuple[int, int],
    color: tuple[int, int, int],
    scale: float = 0.58,
    thickness: int = 1,
) -> None:
    cv2.putText(frame, text, xy, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def render_combined_overlay(
    frame: np.ndarray,
    event: dict[str, Any],
    frame_idx: int,
    timestamp_sec: float,
    predictions: dict[str, dict[str, Any]],
    bboxes: dict[str, tuple[int, int, int, int] | None],
) -> np.ndarray:
    out = frame.copy()
    palette = {
        "target_vehicle": (255, 255, 255),
        "cabin_candidate": (180, 180, 180),
        "driver_roi": (0, 255, 255),
        "head_shoulder_roi": (0, 180, 255),
        "face_near_roi": (120, 255, 120),
    }
    for mode, bbox in bboxes.items():
        if bbox is None:
            continue
        color = palette.get(mode, (255, 255, 255))
        cv2.rectangle(out, bbox[:2], bbox[2:], color, 2)
        draw_label(out, mode, (bbox[0] + 6, max(20, bbox[1] - 8)), color, 0.55, 2)

    panel_w = min(out.shape[1] - 24, 980)
    panel_h = 48 + 26 * max(1, len(predictions))
    x0, y0 = 14, 14
    overlay = out.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
    out = cv2.addWeighted(overlay, 0.68, out, 0.32, 0)
    draw_label(
        out,
        f"{EXPERIMENT_ID} phone-call ROI smoke | {event['source']['source_video']} | frame={frame_idx} t={timestamp_sec:.2f}s",
        (x0 + 12, y0 + 26),
        (255, 255, 255),
        0.58,
        2,
    )
    for row_idx, (mode, prediction) in enumerate(predictions.items()):
        phone_prob = prediction.get("probabilities", {}).get(PHONE_CALL_LABEL, 0.0)
        top3 = " / ".join(f"{item['label']} {item['probability']:.2f}" for item in prediction["top3"])
        draw_label(
            out,
            f"{mode}: phone_prob={phone_prob:.3f} top1={prediction['label']} {prediction['confidence']:.3f} | {top3}",
            (x0 + 12, y0 + 54 + row_idx * 26),
            palette.get(mode, (255, 255, 255)),
            0.52,
            1,
        )
    cv2.rectangle(out, (x0, y0), (x0 + panel_w, y0 + panel_h), (255, 255, 255), 1)
    return out


def aggregate_rows(
    event: dict[str, Any],
    mode: str,
    rows: list[dict[str, Any]],
    labels: list[str],
    temporal_threshold: float,
    min_positive_rate: float,
) -> dict[str, Any]:
    if not rows:
        return {
            "video": event["source"]["source_video"],
            "event_id": event["event_id"],
            "mode": mode,
            "status": "no_samples",
            "sample_count": 0,
            "should_emit_driver_action": False,
        }
    counts = Counter(str(row["pred_label"]) for row in rows)
    phone_probs = [float(row.get(f"prob_{PHONE_CALL_LABEL}") or 0.0) for row in rows]
    pred_conf = [float(row.get("pred_confidence") or 0.0) for row in rows]
    phone_positive_rows = [
        row for row in rows
        if float(row.get(f"prob_{PHONE_CALL_LABEL}") or 0.0) >= temporal_threshold
    ]
    top1_phone_rows = [
        row for row in rows
        if row.get("pred_label") == PHONE_CALL_LABEL
        and float(row.get("pred_confidence") or 0.0) >= temporal_threshold
    ]
    top1_label, top1_count = counts.most_common(1)[0]
    positive_rate = len(phone_positive_rows) / len(rows)
    top1_phone_rate = len(top1_phone_rows) / len(rows)
    ftr_action_rates = {
        label: round(
            sum(1 for row in rows if row.get("pred_label") == label) / len(rows),
            4,
        )
        for label in labels
        if label in FTR_ACTION_LABELS
    }
    return {
        "video": event["source"]["source_video"],
        "event_id": event["event_id"],
        "track_id": event.get("target_vehicle", {}).get("track_id"),
        "mode": mode,
        "status": "roi_crop_strategy_smoke_only",
        "sample_count": len(rows),
        "bbox_available_rate": round(
            sum(1 for row in rows if row.get("crop_bbox_xyxy")) / len(rows),
            4,
        ),
        "temporal_vote_label": top1_label,
        "temporal_vote_rate": round(top1_count / len(rows), 4),
        "mean_top1_confidence": round(float(np.mean(pred_conf)), 4),
        "phone_call_probability_mean": round(float(np.mean(phone_probs)), 4),
        "phone_call_probability_p95": round(float(np.percentile(phone_probs, 95)), 4),
        "phone_call_probability_max": round(float(max(phone_probs)), 4),
        "phone_call_prob_positive_count": len(phone_positive_rows),
        "phone_call_prob_positive_rate": round(positive_rate, 4),
        "phone_call_top1_positive_count": len(top1_phone_rows),
        "phone_call_top1_positive_rate": round(top1_phone_rate, 4),
        "top1_counts": dict(counts),
        "ftr_action_top1_rates": ftr_action_rates,
        "candidate_if_temporal_gate": bool(positive_rate >= min_positive_rate),
        "should_emit_driver_action": False,
        "failure_reason": "exterior_roi_smoke_test_no_final_action",
        "view_profile": (event.get("driver_detection") or {}).get("view_profile"),
    }


def process_event(
    event: dict[str, Any],
    args: argparse.Namespace,
    model: torch.nn.Module,
    labels: list[str],
    transform: Any,
    device: torch.device,
    phone_index: dict[str, dict[int, dict[str, Any]]],
    pose_index: dict[str, dict[int, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    video_name = str(event["source"]["source_video"])
    video_path = args.videos_dir / video_name
    if not video_path.exists():
        raise FileNotFoundError(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    rendered_fps = max(1.0, fps / max(1, args.sample_every))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    window = event.get("target_vehicle", {}).get("frame_window") or {}
    first_frame = int(window.get("first_frame") or 1)
    last_frame = int(window.get("last_frame") or total_frames)
    if args.max_frames > 0:
        last_frame = min(last_frame, first_frame + args.max_frames - 1)

    render_path = args.runs_dir / "annotated" / f"{Path(video_name).stem}_dact021_phone_roi_compare.mp4"
    writer, writer_size = prepare_writer(
        frame_width,
        frame_height,
        rendered_fps,
        args.output_width,
        render_path,
    )

    rows_by_mode: dict[str, list[dict[str, Any]]] = {mode: [] for mode in args.modes}
    frame_rows: list[dict[str, Any]] = []
    frame_number = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            if frame_number < first_frame:
                continue
            if frame_number > last_frame:
                break
            if (frame_number - first_frame) % max(1, args.sample_every) != 0:
                continue

            timestamp_sec = frame_number / fps if fps else 0.0
            predictions: dict[str, dict[str, Any]] = {}
            bboxes: dict[str, tuple[int, int, int, int] | None] = {}
            for mode in args.modes:
                bbox = mode_bbox(
                    frame,
                    event,
                    mode,
                    frame_number,
                    phone_index,
                    pose_index,
                )
                bboxes[mode] = bbox
                crop = crop_bbox(frame, bbox) if bbox else frame
                prediction = infer_crop(model, labels, transform, device, crop)
                predictions[mode] = prediction
                row = {
                    "video": video_name,
                    "event_id": event["event_id"],
                    "track_id": event.get("target_vehicle", {}).get("track_id"),
                    "frame": frame_number,
                    "timestamp_sec": round(timestamp_sec, 4),
                    "mode": mode,
                    "pred_label": prediction["label"],
                    "pred_confidence": round(float(prediction["confidence"]), 6),
                    "crop_bbox_xyxy": list(bbox) if bbox else None,
                    "crop_width": int(bbox[2] - bbox[0]) if bbox else frame_width,
                    "crop_height": int(bbox[3] - bbox[1]) if bbox else frame_height,
                }
                row.update(
                    {
                        f"prob_{label}": round(float(prediction["probabilities"].get(label, 0.0)), 6)
                        for label in labels
                    }
                )
                rows_by_mode[mode].append(row)
                frame_rows.append(row)

            rendered = render_combined_overlay(
                frame,
                event,
                frame_number,
                timestamp_sec,
                predictions,
                bboxes,
            )
            out_w, out_h = writer_size
            if (rendered.shape[1], rendered.shape[0]) != (out_w, out_h):
                rendered = cv2.resize(rendered, (out_w, out_h), interpolation=cv2.INTER_AREA)
            writer.write(rendered)
    finally:
        cap.release()
        writer.release()

    summaries = [
        aggregate_rows(
            event,
            mode,
            rows_by_mode[mode],
            labels,
            args.temporal_threshold,
            args.min_positive_rate,
        )
        for mode in args.modes
    ]
    return summaries, frame_rows, rel(render_path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    summary: dict[str, Any],
    summary_json: Path,
    summary_csv: Path,
    frame_csv: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DACT-EXP-021 Phone-Call Driver ROI / Head-Shoulder Smoke Test",
        "",
        f"Tarih: {summary['created_at_utc']}",
        "",
        "## Amaç",
        "",
        (
            "Bu deney `DACT-EXP-020B` driver-action classifier'ını dış kamera "
            "videolarında daha sıkı crop stratejileriyle dener: hedef araç, "
            "driver ROI ve head-shoulder ROI. Amaç final `telefonla_konusma` "
            "kararı üretmek değil, crop stratejisinin sinyal taşıyıp taşımadığını "
            "manuel videolarla kontrol etmektir."
        ),
        "",
        "## Karar",
        "",
        f"* Genel karar: `{summary['overall_decision']}`",
        f"* Gerekçe: {summary['overall_reason']}",
        "* `should_emit_driver_action=false` tüm modlar için sabittir.",
        "",
        "## Özet Tablo",
        "",
        "| Video | Mode | Samples | Vote | Vote rate | phone mean | phone p95 | phone >= threshold | Top-1 phone | Candidate gate |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["mode_summaries"]:
        lines.append(
            "| {video} | {mode} | {sample_count} | {temporal_vote_label} | "
            "{temporal_vote_rate} | {phone_call_probability_mean} | "
            "{phone_call_probability_p95} | {phone_call_prob_positive_rate} | "
            "{phone_call_top1_positive_rate} | {gate} |".format(
                gate=row.get("candidate_if_temporal_gate"),
                **row,
            )
        )
    lines.extend(
        [
            "",
            "## Annotated Video Çıktıları",
            "",
        ]
    )
    for video, uri in summary.get("rendered_videos", {}).items():
        lines.append(f"* `{video}`: `{uri}`")
    lines.extend(
        [
            "",
            "## Artefactler",
            "",
            f"* Summary JSON: `{summary_json.relative_to(ROOT)}`",
            f"* Summary CSV: `{summary_csv.relative_to(ROOT)}`",
            f"* Frame CSV: `{frame_csv.relative_to(ROOT)}`",
            "",
            "## Yorum",
            "",
            (
                "Eger head-shoulder ROI'da `telefonla_konusma` skoru stabil "
                "artmiyorsa, mevcut State Farm classifier dis-kamera domain'i icin "
                "yeterli sayilmaz. Bu durumda sonraki adim, gorunur driver ROI "
                "crop'lari uzerinden yeni/focused bir model veya daha uygun dis "
                "kamera/driver dataset'i ile fine-tune calismasidir."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    device = pick_device(args.device)
    model, labels, img_size, checkpoint = load_model(args.checkpoint, args.label_map, device)
    if PHONE_CALL_LABEL not in labels:
        raise RuntimeError(f"{PHONE_CALL_LABEL!r} not found in labels: {labels}")
    transform = make_transform(img_size)
    events = load_events(args.events)
    phone_index = load_video_frame_index(args.phone_roi_summary)
    pose_index = load_video_frame_index(args.pose_summary)

    all_summaries: list[dict[str, Any]] = []
    all_frame_rows: list[dict[str, Any]] = []
    rendered: dict[str, str] = {}
    for event in events:
        mode_summaries, frame_rows, rendered_uri = process_event(
            event,
            args,
            model,
            labels,
            transform,
            device,
            phone_index,
            pose_index,
        )
        all_summaries.extend(mode_summaries)
        all_frame_rows.extend(frame_rows)
        rendered[str(event["source"]["source_video"])] = rendered_uri

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "experiment_name": EXPERIMENT_NAME,
        "source_model_experiment_id": SOURCE_MODEL_EXPERIMENT_ID,
        "created_at_utc": now_utc(),
        "checkpoint": rel(args.checkpoint),
        "label_map": rel(args.label_map),
        "phone_roi_summary": rel(args.phone_roi_summary),
        "pose_summary": rel(args.pose_summary),
        "backbone": checkpoint.get("backbone", "efficientnet_b0"),
        "img_size": img_size,
        "labels": labels,
        "modes": args.modes,
        "sample_every": args.sample_every,
        "temporal_threshold": args.temporal_threshold,
        "min_positive_rate": args.min_positive_rate,
        "overall_decision": "roi_smoke_only_do_not_emit_driver_action",
        "overall_reason": (
            "Telefonla konusma dis-kamera acisinda gorunurluk ve domain gap nedeniyle "
            "dogrudan aksiyon karari olarak kullanilamaz; bu kosu yalniz crop "
            "stratejisi karsilastirmasi ve manuel review icindir."
        ),
        "mode_summaries": all_summaries,
        "rendered_videos": rendered,
    }

    summary_json = args.artifact_dir / "dact_exp_021_phone_call_roi_smoke_summary.json"
    summary_csv = args.artifact_dir / "dact_exp_021_phone_call_roi_smoke_summary.csv"
    frame_csv = args.artifact_dir / "dact_exp_021_phone_call_roi_smoke_frames.csv"
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(summary_csv, all_summaries)
    write_csv(frame_csv, all_frame_rows)
    write_report(args.report, summary, summary_json, summary_csv, frame_csv)

    print("summary:", summary_json)
    print("summary_csv:", summary_csv)
    print("frame_csv:", frame_csv)
    print("report:", args.report)
    print("rendered:", json.dumps(rendered, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
