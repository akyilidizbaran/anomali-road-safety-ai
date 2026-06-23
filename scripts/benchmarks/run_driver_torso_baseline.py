#!/usr/bin/env python3
"""Generate deterministic driver torso ROIs from the selected YuNet face output."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

try:
    from driver_torso_utils import (
        deterministic_torso_bbox,
        driver_face_global_bbox,
        smooth_bbox,
        temporal_torso_summary,
        torso_quality_decision,
    )
except ImportError:
    from scripts.benchmarks.driver_torso_utils import (
        deterministic_torso_bbox,
        driver_face_global_bbox,
        smooth_bbox,
        temporal_torso_summary,
        torso_quality_decision,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_PROFILES = (
    ROOT / "architecture" / "contracts" / "driver_torso_profiles.example.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "driver_torso"
EXPERIMENT_ID = "TORSO-EXP-001"
MODEL_KEY = "yunet_face_anchored_deterministic_torso_v1"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        0.62,
        color,
        2,
        cv2.LINE_AA,
    )


def face_confidence(record: dict[str, Any]) -> float:
    index = record.get("driver_face_index")
    faces = record.get("faces") or []
    if index is None or not (0 <= int(index) < len(faces)):
        return 0.0
    return float(faces[int(index)].get("confidence") or 0.0)


def process_video(
    video_path: Path,
    cabin_video: dict[str, Any],
    profiles: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    frame_meta = cabin_video.get("frame_meta") or {}
    width = int(frame_meta.get("width") or 0)
    height = int(frame_meta.get("height") or 0)
    fps = float(frame_meta.get("fps") or 25.0)
    profile_name = str(cabin_video.get("view_profile") or "unknown")
    profile = (profiles.get("profiles") or {}).get(profile_name) or {}
    selected_records = (cabin_video.get("per_frame") or [])[:: max(1, args.frame_stride)]
    by_frame = {int(item["frame"]): item for item in selected_records}
    print(
        f"\n=== {video_path.name}: deterministic driver torso ===\n"
        f"profile={profile_name}, input={len(selected_records)}, stride={args.frame_stride}"
    )

    run_dir = args.runs_root / EXPERIMENT_ID.lower().replace("-", "_")
    roi_dir = run_dir / "rois" / video_path.stem
    annotated_dir = run_dir / "annotated"
    roi_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)
    annotated_path = annotated_dir / f"{video_path.stem}_{MODEL_KEY}.mp4"

    output_width = max(1, int(width * args.video_scale))
    output_height = max(1, int(height * args.video_scale))
    writer = cv2.VideoWriter(
        str(annotated_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (output_width, output_height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not create annotated video: {annotated_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        writer.release()
        raise RuntimeError(f"Could not open video: {video_path}")

    frame_results = []
    frame_number = 0
    previous_bbox = None
    previous_frame = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            record = by_frame.get(frame_number)
            if record:
                visibility = str(record.get("visibility") or "not_visible")
                face_bbox = driver_face_global_bbox(record)
                vehicle_bbox = record.get("vehicle_bbox_xyxy")
                confidence = face_confidence(record)
                result = {
                    "frame": frame_number,
                    "view_profile": profile_name,
                    "visibility": visibility,
                    "visibility_score": record.get("visibility_score"),
                    "driver_face_bbox": face_bbox,
                    "face_confidence": round(confidence, 4),
                    "torso_bbox": None,
                    "raw_torso_bbox": None,
                    "torso_status": "not_evaluable",
                    "torso_quality_score": None,
                    "torso_quality_reasons": [],
                    "retained_area_ratio": None,
                    "vehicle_coverage_ratio": None,
                    "below_cabin_vertical_ratio": None,
                    "torso_roi_uri": None,
                }
                evaluable = (
                    visibility in {"good", "limited"}
                    and face_bbox is not None
                    and vehicle_bbox is not None
                    and record.get("cabin_bbox_xyxy") is not None
                    and bool(profile.get("torso"))
                )
                if evaluable:
                    geometry = deterministic_torso_bbox(
                        face_bbox,
                        vehicle_bbox,
                        record["cabin_bbox_xyxy"],
                        width,
                        height,
                        profile,
                    )
                    quality_score, torso_status, reasons = torso_quality_decision(
                        geometry,
                        confidence,
                        min_face_dimension=args.min_face_dimension,
                        min_torso_width=args.min_torso_width,
                        min_torso_height=args.min_torso_height,
                        min_retained_ratio=args.min_retained_ratio,
                        max_below_cabin_ratio=float(
                            (profile.get("torso") or {}).get(
                                "max_below_cabin_vertical_ratio",
                                args.max_below_cabin_ratio,
                            )
                        ),
                    )
                    if (
                        previous_bbox is not None
                        and previous_frame is not None
                        and frame_number - previous_frame <= args.max_smoothing_gap
                    ):
                        torso_bbox = smooth_bbox(
                            previous_bbox,
                            geometry["bbox"],
                            alpha=args.smoothing_alpha,
                        )
                    else:
                        torso_bbox = geometry["bbox"]
                    previous_bbox = torso_bbox
                    previous_frame = frame_number
                    tx1, ty1, tx2, ty2 = torso_bbox
                    crop = frame[ty1:ty2, tx1:tx2].copy()
                    roi_path = roi_dir / f"frame_{frame_number:06d}_torso.jpg"
                    if crop.size:
                        cv2.imwrite(
                            str(roi_path),
                            crop,
                            [int(cv2.IMWRITE_JPEG_QUALITY), 95],
                        )
                    result.update(
                        {
                            "torso_bbox": torso_bbox,
                            "raw_torso_bbox": geometry["raw_bbox"],
                            "torso_status": torso_status,
                            "torso_quality_score": quality_score,
                            "torso_quality_reasons": reasons,
                            "retained_area_ratio": geometry["retained_area_ratio"],
                            "vehicle_coverage_ratio": geometry[
                                "vehicle_coverage_ratio"
                            ],
                            "below_cabin_vertical_ratio": geometry[
                                "below_cabin_vertical_ratio"
                            ],
                            "torso_roi_uri": rel(roi_path) if crop.size else None,
                        }
                    )
                    color = {
                        "usable": (0, 220, 0),
                        "limited": (0, 200, 255),
                        "not_usable": (0, 0, 255),
                    }[torso_status]
                    cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), color, 2)
                    draw_label(
                        frame,
                        f"torso {torso_status} {quality_score:.2f}",
                        (tx1, max(24, ty1 - 8)),
                        color,
                    )
                else:
                    previous_bbox = None
                    previous_frame = None

                if face_bbox:
                    fx1, fy1, fx2, fy2 = face_bbox
                    cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (255, 0, 255), 2)
                    draw_label(
                        frame,
                        f"driver face {confidence:.2f}",
                        (fx1, max(24, fy1 - 8)),
                        (255, 0, 255),
                    )
                frame_results.append(result)

            output = (
                cv2.resize(
                    frame,
                    (output_width, output_height),
                    interpolation=cv2.INTER_AREA,
                )
                if args.video_scale != 1.0
                else frame
            )
            writer.write(output)
    finally:
        cap.release()
        writer.release()

    temporal = temporal_torso_summary(
        frame_results,
        min_usable_frames=args.min_usable_frames,
        min_usable_rate=args.min_usable_rate,
    )
    reason_counts = Counter(
        reason
        for item in frame_results
        for reason in item.get("torso_quality_reasons") or []
    )
    return {
        "video": video_path.name,
        "event_id": cabin_video.get("event_id"),
        "status": "completed",
        "view_profile": profile_name,
        "processed_frame_count": len(frame_results),
        "frame_stride": args.frame_stride,
        "temporal": temporal,
        "quality_reason_counts": dict(sorted(reason_counts.items())),
        "annotated_video": rel(annotated_path),
        "roi_dir": rel(roi_dir),
        "per_frame": frame_results,
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = []
    for video in summary.get("videos", []):
        temporal = video.get("temporal") or {}
        rows.append(
            "| {video} | {profile} | {evaluable} | {usable_rate} | "
            "{available_rate} | {ready} | {miss} | {quality} |".format(
                video=video.get("video"),
                profile=video.get("view_profile"),
                evaluable=temporal.get("evaluable_driver_frame_count"),
                usable_rate=temporal.get("usable_torso_rate"),
                available_rate=temporal.get("available_torso_rate"),
                ready=temporal.get("torso_baseline_ready"),
                miss=temporal.get("longest_torso_miss_run"),
                quality=temporal.get("mean_torso_quality_score"),
            )
        )
    return "\n".join(
        [
            "# TORSO-EXP-001 Deterministic Driver Torso Baseline",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            "## Zincir",
            "",
            "`YuNet driver face -> view-profile torso geometry -> quality gate -> temporal torso metadata`",
            "",
            "## Sonuç",
            "",
            "| Video | Profil | Evaluable | Usable Rate | Available Rate | "
            "Ready | Longest Miss | Mean Quality |",
            "|---|---|---:|---:|---:|---|---:|---:|",
            *rows,
            "",
            "## Sınırlar",
            "",
            "* Bu deney insan pozu, seatbelt veya phone sınıflandırması yapmaz.",
            "* Yeşil torso kutusu yalnız specialist model için candidate crop'tur.",
            "* Geometrik ROI doğruluğu tam overlay manuel review ile onaylanmalıdır.",
            "* Kemerli/kemersiz ayrımı kontrollü veri ve ayrı specialist benchmark ister.",
            "",
            "## Manuel Review",
            "",
            "* Şablon: `testing/templates/manual_driver_torso_review.csv`",
            "* Crop ve overlay: `runs/driver_torso/` altında Git dışındadır.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Face-anchored deterministic driver torso ROI baseline."
    )
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--video-scale", type=float, default=0.50)
    parser.add_argument("--smoothing-alpha", type=float, default=0.65)
    parser.add_argument("--max-smoothing-gap", type=int, default=3)
    parser.add_argument("--min-face-dimension", type=float, default=40.0)
    parser.add_argument("--min-torso-width", type=float, default=56.0)
    parser.add_argument("--min-torso-height", type=float, default=72.0)
    parser.add_argument("--min-retained-ratio", type=float, default=0.62)
    parser.add_argument("--max-below-cabin-ratio", type=float, default=0.45)
    parser.add_argument("--min-usable-frames", type=int, default=3)
    parser.add_argument("--min-usable-rate", type=float, default=0.30)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cabin_path = args.cabin_summary.resolve()
    profiles_path = args.profiles.resolve()
    for required in (cabin_path, profiles_path):
        if not required.exists():
            raise SystemExit(f"Required input not found: {required}")

    cabin_summary = load_json(cabin_path)
    profiles = load_json(profiles_path)
    selected_names = (
        {path.name for path in args.videos}
        if args.videos
        else {item.get("video") for item in cabin_summary.get("videos", [])}
    )
    results = []
    for cabin_video in cabin_summary.get("videos", []):
        if (
            cabin_video.get("video") not in selected_names
            or cabin_video.get("status") != "completed"
        ):
            continue
        video_path = (args.videos_dir / str(cabin_video["video"])).resolve()
        if not video_path.exists():
            results.append(
                {
                    "video": cabin_video["video"],
                    "status": "failed",
                    "failure_reason": "source_video_not_found",
                }
            )
            continue
        results.append(process_video(video_path, cabin_video, profiles, args))

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "stage": "driver_deterministic_torso_baseline",
        "created_at_utc": now_utc(),
        "model_key": MODEL_KEY,
        "input_cabin_summary": rel(cabin_path),
        "input_cabin_experiment_id": cabin_summary.get("experiment_id"),
        "torso_profiles": rel(profiles_path),
        "frame_stride": args.frame_stride,
        "smoothing_alpha": args.smoothing_alpha,
        "quality_thresholds": {
            "min_face_dimension": args.min_face_dimension,
            "min_torso_width": args.min_torso_width,
            "min_torso_height": args.min_torso_height,
            "min_retained_ratio": args.min_retained_ratio,
            "max_below_cabin_ratio": args.max_below_cabin_ratio,
        },
        "manual_review_template": "testing/templates/manual_driver_torso_review.csv",
        "videos": results,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = (
        args.artifact_dir / f"{EXPERIMENT_ID}-{MODEL_KEY}-summary.json"
    )
    report_path = args.report_dir / "torso_exp_001_summary.md"
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
                    item.get("status") == "completed" for item in results
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
