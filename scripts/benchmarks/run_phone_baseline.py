#!/usr/bin/env python3
"""Benchmark object-first phone detection on driver-focused cabin ROIs."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO

try:
    from phone_utils import (
        classify_phone_detection,
        driver_face_global_bbox,
        local_to_global_bbox,
        phone_inference_roi_bbox,
        temporal_phone_summary,
    )
except ImportError:
    from scripts.benchmarks.phone_utils import (
        classify_phone_detection,
        driver_face_global_bbox,
        local_to_global_bbox,
        phone_inference_roi_bbox,
        temporal_phone_summary,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_YOLO_MODEL = ROOT / "yolo11n.pt"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "phone"
EXPERIMENT_ID = "PHONE-EXP-001"
MODEL_KEY = "yolo11n_coco_cell_phone_driver_roi_v1"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[int(round((len(ordered) - 1) * 0.95))], 3)


def phone_class_id(model: YOLO, class_name: str) -> int:
    for class_id, name in model.names.items():
        if str(name).lower() == class_name.lower():
            return int(class_id)
    raise RuntimeError(f"Phone class '{class_name}' not found in YOLO model names.")


def draw_label(
    frame: Any,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        color,
        2,
        cv2.LINE_AA,
    )


def process_video(
    video_path: Path,
    cabin_video: dict[str, Any],
    model: YOLO,
    target_class_id: int,
    args: argparse.Namespace,
) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    records = {
        int(item["frame"]): item
        for item in cabin_video.get("per_frame", [])[:: max(1, args.frame_stride)]
    }
    run_dir = args.runs_root / args.run_name
    crop_dir = run_dir / "rois" / video_path.stem
    overlay_dir = run_dir / "annotated"
    crop_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = overlay_dir / f"{video_path.stem}_{args.model_key}.mp4"
    writer = cv2.VideoWriter(
        str(overlay_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create overlay: {overlay_path}")

    results = []
    latencies = []
    frame_number = 0
    view_profile = str(cabin_video.get("view_profile") or "unknown")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            record = records.get(frame_number)
            if record is None:
                writer.write(frame)
                continue
            roi_bbox = phone_inference_roi_bbox(
                record,
                width,
                height,
                view_profile,
                args.roi_mode,
            )
            face_bbox = driver_face_global_bbox(record)
            decision_evaluable = bool(record.get("visibility") in {"good", "limited"})
            result = {
                "frame": frame_number,
                "visibility": record.get("visibility"),
                "decision_evaluable": decision_evaluable,
                "phone_detected": False,
                "phone_confidence": None,
                "phone_bbox": None,
                "phone_area": None,
                "object_near_face": False,
                "face_distance_units": None,
                "candidate_reasons": [],
                "phone_roi_bbox": roi_bbox,
                "phone_roi_mode": args.roi_mode,
                "phone_roi_uri": None,
                "latency_ms": 0.0,
                "phone_risk": None,
            }
            if roi_bbox is not None:
                x1, y1, x2, y2 = roi_bbox
                crop = frame[y1:y2, x1:x2].copy()
                crop_path = crop_dir / f"frame_{frame_number:06d}_phone_roi.jpg"
                cv2.imwrite(
                    str(crop_path),
                    crop,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 94],
                )
                started = time.perf_counter()
                predictions = model.predict(
                    crop,
                    classes=[target_class_id],
                    conf=args.confidence,
                    imgsz=args.imgsz,
                    device=args.device,
                    verbose=False,
                )[0]
                latency = (time.perf_counter() - started) * 1000.0
                latencies.append(latency)
                candidates = []
                for box in predictions.boxes:
                    local_bbox = [float(value) for value in box.xyxy[0].tolist()]
                    global_bbox = local_to_global_bbox(local_bbox, roi_bbox)
                    classification = classify_phone_detection(
                        global_bbox,
                        roi_bbox,
                        face_bbox,
                    )
                    if not classification["accepted"]:
                        continue
                    candidates.append(
                        {
                            "bbox": global_bbox,
                            "confidence": float(box.conf[0]),
                            **classification,
                        }
                    )
                if candidates:
                    best = max(candidates, key=lambda item: item["confidence"])
                    result.update(
                        {
                            "phone_detected": True,
                            "phone_confidence": round(best["confidence"], 4),
                            "phone_bbox": best["bbox"],
                            "phone_area": round(
                                max(0.0, best["bbox"][2] - best["bbox"][0])
                                * max(0.0, best["bbox"][3] - best["bbox"][1]),
                                2,
                            ),
                            "object_near_face": best["near_face"],
                            "face_distance_units": best["face_distance_units"],
                            "candidate_reasons": best["reasons"],
                        }
                    )
                result.update(
                    {
                        "phone_roi_uri": rel(crop_path),
                        "latency_ms": round(latency, 3),
                    }
                )
                cv2.rectangle(frame, (x1, y1), (x2, y2), (120, 120, 120), 1)
                if face_bbox is not None:
                    fx1, fy1, fx2, fy2 = [int(value) for value in face_bbox]
                    cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (255, 0, 255), 2)
                if result["phone_bbox"] is not None:
                    px1, py1, px2, py2 = [int(value) for value in result["phone_bbox"]]
                    cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 255, 255), 3)
                    draw_label(
                        frame,
                        f"phone {result['phone_confidence']}",
                        (px1, max(20, py1 - 8)),
                        (0, 255, 255),
                    )
            label = "phone: candidate" if result["phone_detected"] else "phone: none"
            draw_label(frame, label, (24, 36), (255, 255, 255))
            writer.write(frame)
            results.append(result)
    finally:
        cap.release()
        writer.release()

    temporal = temporal_phone_summary(
        results,
        min_evaluable_frames=args.min_evaluable_frames,
        min_positive_frames=args.min_positive_frames,
        min_positive_rate=args.min_positive_rate,
    )
    return {
        "video": video_path.name,
        "status": "completed",
        "view_profile": view_profile,
        "roi_mode": args.roi_mode,
        "processed_frame_count": len(results),
        "frame_stride": args.frame_stride,
        "mean_phone_latency_ms": mean(latencies),
        "p95_phone_latency_ms": p95(latencies),
        "temporal": temporal,
        "annotated_video": rel(overlay_path),
        "roi_dir": rel(crop_dir),
        "per_frame": results,
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = []
    for video in summary["videos"]:
        temporal = video["temporal"]
        rows.append(
            f"| {video['video']} | {video['view_profile']} | "
            f"{temporal['evaluable_frame_count']} | "
            f"{temporal['positive_frame_count']} | "
            f"{temporal['detection_rate']} | "
            f"{temporal['object_near_face_rate']} | {temporal['status']} | "
            f"{video['mean_phone_latency_ms']} | {video['p95_phone_latency_ms']} |"
        )
    return "\n".join(
        [
            f"# {summary['experiment_id']} Phone Summary",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            f"`YuNet cabin/driver ROI -> {summary['model_key']} -> temporal candidate metadata`",
            "",
            "Bu deney telefon nesnesi arar; tek başına ihlal veya `phone_risk` üretmez.",
            "",
            "| Video | Profil | Evaluable | Positive | Detection Rate | Near Face Rate | Status | Mean ms | P95 ms |",
            "|---|---|---:|---:|---:|---:|---|---:|---:|",
            *rows,
            "",
            "Manuel review: `testing/templates/manual_phone_review.csv`",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run phone object baseline.")
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--model", type=Path, default=DEFAULT_YOLO_MODEL)
    parser.add_argument("--experiment-id", default=EXPERIMENT_ID)
    parser.add_argument("--model-key", default=MODEL_KEY)
    parser.add_argument("--class-name", default="cell phone")
    parser.add_argument("--run-name", default="phone_exp_001")
    parser.add_argument("--report-name", default="phone_exp_001_summary.md")
    parser.add_argument(
        "--roi-mode",
        choices=("driver_phone", "face_near"),
        default="driver_phone",
    )
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--min-evaluable-frames", type=int, default=5)
    parser.add_argument("--min-positive-frames", type=int, default=2)
    parser.add_argument("--min-positive-rate", type=float, default=0.10)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.model.exists():
        raise SystemExit(f"YOLO model not found: {args.model}")
    cabin_summary = json.loads(args.cabin_summary.resolve().read_text(encoding="utf-8"))
    model = YOLO(str(args.model.resolve()))
    target_class_id = phone_class_id(model, args.class_name)
    selected = (
        {path.name for path in args.videos}
        if args.videos
        else {item.get("video") for item in cabin_summary.get("videos", [])}
    )
    videos = []
    for cabin_video in cabin_summary.get("videos", []):
        name = cabin_video.get("video")
        if name not in selected or cabin_video.get("status") != "completed":
            continue
        print(f"\n=== {name}: phone object baseline ===")
        videos.append(
            process_video(
                (args.videos_dir / str(name)).resolve(),
                cabin_video,
                model,
                target_class_id,
                args,
            )
        )
    summary = {
        "experiment_id": args.experiment_id,
        "stage": "phone_object_baseline",
        "created_at_utc": now_utc(),
        "decision": "candidate_not_selected_pending_manual_review",
        "model_key": args.model_key,
        "backend": "ultralytics_yolo",
        "model_path": rel(args.model.resolve()),
        "phone_class": args.class_name,
        "roi_mode": args.roi_mode,
        "input_cabin_summary": rel(args.cabin_summary.resolve()),
        "input_cabin_experiment_id": cabin_summary.get("experiment_id"),
        "phone_risk_enabled": False,
        "videos": videos,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.artifact_dir / f"{args.experiment_id}-{args.model_key}-summary.json"
    report_path = args.report_dir / args.report_name
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(build_report(summary) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": rel(summary_path),
                "report": rel(report_path),
                "completed_videos": len(videos),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
