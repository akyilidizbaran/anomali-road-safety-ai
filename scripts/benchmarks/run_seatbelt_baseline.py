#!/usr/bin/env python3
"""Benchmark conservative seatbelt evidence on POSE-EXP-009 torso crops."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

try:
    from seatbelt_utils import (
        clamp_bbox,
        detect_diagonal_belt_evidence,
        temporal_seatbelt_decision,
        torso_quality,
    )
except ImportError:
    from scripts.benchmarks.seatbelt_utils import (
        clamp_bbox,
        detect_diagonal_belt_evidence,
        temporal_seatbelt_decision,
        torso_quality,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POSE_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "POSE-EXP-009-vitpose_b_final_torso_baseline_v1-summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "seatbelt"
EXPERIMENT_ID = "SEATBELT-EXP-001"
MODEL_KEY = "opencv_diagonal_belt_evidence_v1"


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
    values = sorted(values)
    return round(values[int(round((len(values) - 1) * 0.95))], 3)


def draw_label(
    image: Any,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    cv2.putText(
        image,
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
    pose_video: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    frame_meta = pose_video.get("frame_meta") or {}
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    source_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    fps = float(frame_meta.get("fps") or source_fps or 25.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    records = {
        int(item["frame"]): item
        for item in pose_video.get("per_frame", [])[:: max(1, args.frame_stride)]
    }
    run_dir = args.runs_root / "seatbelt_exp_001"
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

    results = []
    latencies = []
    frame_number = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            record = records.get(frame_number)
            if record is not None:
                bbox = record.get("torso_bbox_global")
                evidence_only = bool(record.get("pose_evidence_only"))
                decision_evaluable = bool(
                    not evidence_only
                    and record.get("upper_body_analysis_ready") is True
                    and record.get("visibility") in {"good", "limited"}
                )
                result = {
                    "frame": frame_number,
                    "visibility": record.get("visibility"),
                    "decision_evaluable": decision_evaluable,
                    "evidence_only": evidence_only,
                    "torso_bbox": bbox,
                    "quality_status": "not_evaluable",
                    "quality_score": None,
                    "quality_reasons": [],
                    "candidate_status": "not_evaluable",
                    "evidence_score": 0.0,
                    "best_line": None,
                    "candidate_count": 0,
                    "latency_ms": 0.0,
                    "torso_roi_uri": None,
                }
                clamped = clamp_bbox(bbox, width, height) if bbox else None
                if clamped is not None:
                    x1, y1, x2, y2 = clamped
                    crop = frame[y1:y2, x1:x2].copy()
                    crop_path = crop_dir / f"frame_{frame_number:06d}_torso.jpg"
                    cv2.imwrite(
                        str(crop_path),
                        crop,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 95],
                    )
                    quality = torso_quality(crop)
                    started = time.perf_counter()
                    evidence = (
                        detect_diagonal_belt_evidence(crop)
                        if quality["status"] != "not_usable"
                        else {
                            "evidence_score": 0.0,
                            "candidate_status": "unknown",
                            "best_line": None,
                            "candidate_count": 0,
                        }
                    )
                    latency = (time.perf_counter() - started) * 1000.0
                    latencies.append(latency)
                    result.update(
                        {
                            "torso_bbox": clamped,
                            "quality_status": quality["status"],
                            "quality_score": quality["score"],
                            "quality_reasons": quality["reasons"],
                            "candidate_status": evidence["candidate_status"],
                            "evidence_score": evidence["evidence_score"],
                            "best_line": evidence["best_line"],
                            "candidate_count": evidence["candidate_count"],
                            "latency_ms": round(latency, 3),
                            "torso_roi_uri": rel(crop_path),
                        }
                    )
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    line = evidence.get("best_line")
                    if line is not None:
                        lx1, ly1, lx2, ly2 = line["xyxy"]
                        cv2.line(
                            frame,
                            (x1 + int(lx1), y1 + int(ly1)),
                            (x1 + int(lx2), y1 + int(ly2)),
                            (0, 165, 255),
                            3,
                            cv2.LINE_AA,
                        )
                label = (
                    "seatbelt: evidence-only"
                    if evidence_only
                    else f"seatbelt: {result['candidate_status']}"
                )
                draw_label(frame, label, (24, 36), (255, 255, 255))
                results.append(result)
            writer.write(frame)
    finally:
        cap.release()
        writer.release()

    temporal = temporal_seatbelt_decision(
        results,
        min_evaluable_frames=args.min_evaluable_frames,
        min_positive_frames=args.min_positive_frames,
        min_positive_rate=args.min_positive_rate,
    )
    return {
        "video": video_path.name,
        "status": "completed",
        "view_profile": pose_video.get("view_profile"),
        "processed_frame_count": len(results),
        "frame_stride": args.frame_stride,
        "mean_latency_ms": mean(latencies),
        "p95_latency_ms": p95(latencies),
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
            f"{temporal['evidence_only_frame_count']} | "
            f"{temporal['belted_evidence_rate']} | {temporal['status']} | "
            f"{video['mean_latency_ms']} | {video['p95_latency_ms']} |"
        )
    return "\n".join(
        [
            "# SEATBELT-EXP-001 Baseline Summary",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            "## Karar Sınırı",
            "",
            "Bu heuristic yalnız tekrarlanan diyagonal kemer kanıtından `belted` "
            "adayı üretir. Çizgi yokluğu `unbelted` değildir; `incorrect` sınıfı "
            "kontrollü etiketli model olmadan kapalıdır.",
            "",
            "| Video | Profil | Evaluable | Evidence-only | Belt Evidence Rate | "
            "Temporal Status | Mean ms | P95 ms |",
            "|---|---|---:|---:|---:|---|---:|---:|",
            *rows,
            "",
            "## Çıktılar",
            "",
            "* Manual review: `testing/templates/manual_seatbelt_review.csv`",
            "* Büyük crop/overlay çıktıları: `runs/seatbelt/`",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run seatbelt evidence baseline.")
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--min-evaluable-frames", type=int, default=5)
    parser.add_argument("--min-positive-frames", type=int, default=3)
    parser.add_argument("--min-positive-rate", type=float, default=0.35)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pose_path = args.pose_summary.resolve()
    pose_summary = json.loads(pose_path.read_text(encoding="utf-8"))
    if pose_summary.get("experiment_id") != "POSE-EXP-009":
        raise SystemExit("Seatbelt baseline requires selected POSE-EXP-009 input.")
    selected = (
        {path.name for path in args.videos}
        if args.videos
        else {item["video"] for item in pose_summary.get("videos", [])}
    )
    videos = []
    for pose_video in pose_summary.get("videos", []):
        if pose_video.get("video") not in selected:
            continue
        video_path = (args.videos_dir / pose_video["video"]).resolve()
        if not video_path.exists():
            videos.append(
                {
                    "video": pose_video["video"],
                    "status": "failed",
                    "failure_reason": "source_video_not_found",
                }
            )
            continue
        print(f"\n=== {video_path.name}: seatbelt evidence baseline ===")
        videos.append(process_video(video_path, pose_video, args))
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "stage": "seatbelt_specialist_baseline",
        "created_at_utc": now_utc(),
        "input_pose_summary": rel(pose_path),
        "input_pose_experiment_id": pose_summary.get("experiment_id"),
        "model_key": MODEL_KEY,
        "decision_policy": "positive_evidence_only_no_unbelted_from_absence",
        "frame_stride": args.frame_stride,
        "minimum_evaluable_frames": args.min_evaluable_frames,
        "minimum_positive_frames": args.min_positive_frames,
        "minimum_positive_rate": args.min_positive_rate,
        "manual_review_template": "testing/templates/manual_seatbelt_review.csv",
        "videos": videos,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.artifact_dir / f"{EXPERIMENT_ID}-{MODEL_KEY}-summary.json"
    report_path = args.report_dir / "seatbelt_exp_001_summary.md"
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
                "completed_videos": sum(
                    item.get("status") == "completed" for item in videos
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
