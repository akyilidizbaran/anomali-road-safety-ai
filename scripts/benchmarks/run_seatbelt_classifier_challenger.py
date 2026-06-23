#!/usr/bin/env python3
"""Run a condition-aware seatbelt classifier challenger on driver context ROIs."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

try:
    from seatbelt_condition_utils import (
        driver_context_roi,
        enhance_for_condition,
        local_condition_profile,
        normalized_class_probabilities,
        select_driver_face,
        translate_held_roi,
    )
except ImportError:
    from scripts.benchmarks.seatbelt_condition_utils import (
        driver_context_roi,
        enhance_for_condition,
        local_condition_profile,
        normalized_class_probabilities,
        select_driver_face,
        translate_held_roi,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "seatbelt"
DEFAULT_MODEL_DIR = ROOT / "models" / "checkpoints" / "seatbelt"
EXPERIMENT_ID = "SEATBELT-EXP-002"
MODEL_REPO = "RISEF/yolov11s-seatbelt"
MODEL_FILE = "weights/best.pt"
MODEL_KEY = "risef_yolo11s_seatbelt_cls"


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


def load_model(model_path: Path | None) -> tuple[Any, Path]:
    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO

    if model_path is None:
        downloaded = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir=DEFAULT_MODEL_DIR,
        )
        model_path = Path(downloaded)
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    return YOLO(str(model_path)), model_path


def classifier_result(model: Any, image: Any) -> dict[str, Any]:
    started = time.perf_counter()
    result = model.predict(image, verbose=False)[0]
    latency_ms = (time.perf_counter() - started) * 1000.0
    if result.probs is None:
        raise RuntimeError("Seatbelt challenger is not an image classifier.")
    probabilities = result.probs.data.detach().cpu().tolist()
    normalized = normalized_class_probabilities(result.names, probabilities)
    return {
        **normalized,
        "top1": str(result.names[int(result.probs.top1)]),
        "top1_confidence": round(float(result.probs.top1conf), 6),
        "latency_ms": round(latency_ms, 3),
    }


def temporal_candidate(records: list[dict[str, Any]]) -> dict[str, Any]:
    routed = [
        item["classification"]["routed"]
        for item in records
        if (item.get("classification") or {}).get("routed")
        and item.get("roi_source") == "direct_face"
    ]
    if not routed:
        return {
            "status": "not_evaluable",
            "confidence": None,
            "direct_frame_count": 0,
            "belted_frame_rate": 0.0,
            "unbelted_frame_rate": 0.0,
        }
    belted = [float(item["belted"]) for item in routed]
    unbelted = [float(item["unbelted"]) for item in routed]
    belted_rate = sum(value >= 0.70 for value in belted) / len(belted)
    unbelted_rate = sum(value >= 0.70 for value in unbelted) / len(unbelted)
    status = "unknown"
    confidence = None
    if len(routed) >= 5 and belted_rate >= 0.35:
        status = "belted_candidate"
        confidence = statistics.median(belted)
    elif len(routed) >= 5 and unbelted_rate >= 0.35:
        status = "unbelted_candidate"
        confidence = statistics.median(unbelted)
    return {
        "status": status,
        "confidence": round(float(confidence), 4) if confidence is not None else None,
        "direct_frame_count": len(routed),
        "belted_frame_rate": round(belted_rate, 4),
        "unbelted_frame_rate": round(unbelted_rate, 4),
        "decision_accepted": False,
    }


def process_video(
    video_path: Path,
    cabin_video: dict[str, Any],
    args: argparse.Namespace,
    model: Any | None,
) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    records_by_frame = {
        int(item["frame"]): item
        for item in cabin_video.get("per_frame", [])[:: max(1, args.frame_stride)]
    }
    run_dir = args.runs_root / "seatbelt_exp_002"
    crop_dir = run_dir / "rois" / video_path.stem
    overlay_dir = run_dir / "annotated"
    crop_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = overlay_dir / f"{video_path.stem}_{MODEL_KEY}.mp4"
    writer = cv2.VideoWriter(
        str(overlay_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create overlay: {overlay_path}")

    results: list[dict[str, Any]] = []
    latencies: list[float] = []
    frame_number = 0
    previous_face: list[float] | None = None
    previous_roi: list[int] | None = None
    previous_cabin: list[float] | None = None
    last_direct_frame: int | None = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            record = records_by_frame.get(frame_number)
            if record is None:
                writer.write(frame)
                continue
            cabin_bbox = record.get("cabin_bbox_xyxy")
            face_bbox, face_status = select_driver_face(record, previous_face)
            roi = None
            roi_source = "not_evaluable"
            if face_bbox is not None and cabin_bbox is not None:
                roi = driver_context_roi(
                    face_bbox,
                    cabin_bbox,
                    str(record.get("view_profile") or "unknown"),
                    width,
                    height,
                )
                if roi is not None:
                    previous_face = face_bbox
                    previous_roi = roi
                    previous_cabin = list(cabin_bbox)
                    last_direct_frame = frame_number
                    roi_source = "direct_face"
            if (
                roi is None
                and previous_roi is not None
                and previous_cabin is not None
                and cabin_bbox is not None
                and last_direct_frame is not None
                and frame_number - last_direct_frame <= args.max_hold_frames
            ):
                roi = translate_held_roi(
                    previous_roi,
                    previous_cabin,
                    cabin_bbox,
                    width,
                    height,
                )
                if roi is not None:
                    roi_source = "temporal_hold"

            output: dict[str, Any] = {
                "frame": frame_number,
                "visibility": record.get("visibility"),
                "visibility_score": record.get("visibility_score"),
                "face_status": face_status,
                "roi_source": roi_source,
                "driver_context_bbox": roi,
                "condition": None,
                "classification": None,
                "raw_roi_uri": None,
                "routed_roi_uri": None,
            }
            if roi is not None:
                x1, y1, x2, y2 = roi
                raw = frame[y1:y2, x1:x2].copy()
                condition = local_condition_profile(raw)
                routed = enhance_for_condition(raw, condition["preprocessing"])
                raw_path = crop_dir / f"frame_{frame_number:06d}_raw.jpg"
                routed_path = crop_dir / f"frame_{frame_number:06d}_routed.jpg"
                cv2.imwrite(str(raw_path), raw, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                cv2.imwrite(
                    str(routed_path),
                    routed,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 95],
                )
                output.update(
                    {
                        "condition": condition,
                        "raw_roi_uri": rel(raw_path),
                        "routed_roi_uri": rel(routed_path),
                    }
                )
                if model is not None:
                    raw_result = classifier_result(model, raw)
                    routed_result = classifier_result(model, routed)
                    latencies.extend(
                        [raw_result["latency_ms"], routed_result["latency_ms"]]
                    )
                    output["classification"] = {
                        "raw": raw_result,
                        "routed": routed_result,
                    }
                color = (0, 255, 0) if roi_source == "direct_face" else (0, 165, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"seatbelt ROI: {roi_source} / {condition['lighting']}"
                if output["classification"]:
                    routed_result = output["classification"]["routed"]
                    label += (
                        f" / {routed_result['top1']} "
                        f"{routed_result['top1_confidence']:.2f}"
                    )
                cv2.putText(
                    frame,
                    label,
                    (24, 36),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
            results.append(output)
            writer.write(frame)
    finally:
        cap.release()
        writer.release()

    return {
        "video": video_path.name,
        "status": "completed",
        "view_profile": cabin_video.get("view_profile"),
        "processed_frame_count": len(results),
        "direct_roi_frame_count": sum(
            item["roi_source"] == "direct_face" for item in results
        ),
        "held_roi_frame_count": sum(
            item["roi_source"] == "temporal_hold" for item in results
        ),
        "severe_low_light_frame_count": sum(
            (item.get("condition") or {}).get("lighting")
            == "night_or_severe_low_light"
            for item in results
        ),
        "mean_classifier_latency_ms": mean(latencies),
        "p95_classifier_latency_ms": p95(latencies),
        "temporal_candidate": temporal_candidate(results) if model else None,
        "annotated_video": rel(overlay_path),
        "roi_dir": rel(crop_dir),
        "per_frame": results,
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = []
    for video in summary["videos"]:
        candidate = video.get("temporal_candidate") or {}
        rows.append(
            f"| {video['video']} | {video['direct_roi_frame_count']} | "
            f"{video['held_roi_frame_count']} | "
            f"{video['severe_low_light_frame_count']} | "
            f"{candidate.get('status', 'extract_only')} | "
            f"{video['mean_classifier_latency_ms']} | "
            f"{video['p95_classifier_latency_ms']} |"
        )
    return "\n".join(
        [
            "# SEATBELT-EXP-002 Condition-Aware Classifier Challenger",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            "Bu deney seçilmiş baseline değildir. Raw ve lokal condition-routed "
            "driver-context ROI çıktıları karşılaştırılır. Candidate kararlar "
            "event riskine yazılmaz.",
            "",
            "| Video | Direct ROI | Held ROI | Severe Low Light | Candidate | Mean ms | P95 ms |",
            "|---|---:|---:|---:|---|---:|---:|",
            *rows,
            "",
            "Model kartı gece/tinted glass/glare verisinin az ve eğitim verisinin "
            "dengesiz olduğunu belirtir. Sonuçlar manuel review ve kontrollü veri "
            "olmadan kabul edilmeyecektir.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run condition-aware seatbelt classifier challenger."
    )
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--max-hold-frames", type=int, default=25)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cabin_path = args.cabin_summary.resolve()
    cabin_summary = json.loads(cabin_path.read_text(encoding="utf-8"))
    if cabin_summary.get("experiment_id") != "CABIN-EXP-004":
        raise SystemExit("SEATBELT-EXP-002 requires selected CABIN-EXP-004 input.")
    model = None
    resolved_model_path = None
    if not args.extract_only:
        model, resolved_model_path = load_model(
            args.model_path.resolve() if args.model_path else None
        )
    selected = (
        {path.name for path in args.videos}
        if args.videos
        else {item["video"] for item in cabin_summary.get("videos", [])}
    )
    videos = []
    for cabin_video in cabin_summary.get("videos", []):
        if cabin_video.get("video") not in selected:
            continue
        video_path = (args.videos_dir / cabin_video["video"]).resolve()
        print(f"\n=== {video_path.name}: condition-aware seatbelt challenger ===")
        videos.append(process_video(video_path, cabin_video, args, model))
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "stage": "seatbelt_classifier_challenger",
        "created_at_utc": now_utc(),
        "input_cabin_summary": rel(cabin_path),
        "input_cabin_experiment_id": cabin_summary.get("experiment_id"),
        "model_key": MODEL_KEY if model else "extract_only",
        "model_repo": MODEL_REPO,
        "model_path": rel(resolved_model_path) if resolved_model_path else None,
        "license": "AGPL-3.0",
        "decision_accepted": False,
        "frame_stride": args.frame_stride,
        "max_hold_frames": args.max_hold_frames,
        "videos": videos,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    suffix = MODEL_KEY if model else "condition_roi_extract"
    summary_path = args.artifact_dir / f"{EXPERIMENT_ID}-{suffix}-summary.json"
    report_path = args.report_dir / "seatbelt_exp_002_summary.md"
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
                "extract_only": args.extract_only,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
