#!/usr/bin/env python3
"""Fuse phone-object and temporal arm evidence into phone-call behavior metadata."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

try:
    from phone_utils import temporal_phone_call_summary, temporal_phone_call_timeline
except ImportError:
    from scripts.benchmarks.phone_utils import (
        temporal_phone_call_summary,
        temporal_phone_call_timeline,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_PHONE_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "PHONE-EXP-001-yolo11n_coco_cell_phone_driver_roi_v1-summary.json"
)
DEFAULT_POSE_RELIABILITY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-007-pose_reliability.json"
)
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "phone_call"
EXPERIMENT_ID = "PHONE-CALL-EXP-002"
MODEL_KEY = "phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_pose_reliability_index(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    summary = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(item.get("video")): item
        for item in summary.get("videos", [])
    }


def behavior_thresholds_for_pose_reliability(
    args: argparse.Namespace,
    pose_reliability: dict[str, Any] | None,
) -> dict[str, Any]:
    reliability_detail = str(
        (pose_reliability or {}).get("reliability_detail")
        or (pose_reliability or {}).get("reliability")
        or "unknown"
    )
    min_sustained_seconds = args.min_sustained_seconds
    min_hand_near_ear_rate = args.min_hand_near_ear_rate
    min_dominant_side_rate = args.min_dominant_side_rate
    reliability_policy = "standard"
    if reliability_detail == "usable_borderline":
        min_sustained_seconds = max(
            min_sustained_seconds,
            args.borderline_min_sustained_seconds,
        )
        reliability_policy = "borderline_requires_stronger_temporal_consistency"
    elif reliability_detail == "pose_limited":
        min_sustained_seconds = max(
            min_sustained_seconds,
            args.pose_limited_min_sustained_seconds,
        )
        min_hand_near_ear_rate = max(
            min_hand_near_ear_rate,
            args.pose_limited_min_hand_near_ear_rate,
        )
        reliability_policy = "pose_limited_prefers_not_evaluable_or_candidate"
    return {
        "min_hand_near_ear_rate": min_hand_near_ear_rate,
        "min_sustained_seconds": min_sustained_seconds,
        "min_dominant_side_rate": min_dominant_side_rate,
        "pose_reliability_detail": reliability_detail,
        "pose_reliability_policy": reliability_policy,
    }


def apply_pose_reliability_guardrail(
    behavior: dict[str, Any],
    pose_reliability: dict[str, Any] | None,
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    guarded = dict(behavior)
    reliability_detail = thresholds["pose_reliability_detail"]
    guarded["pose_reliability_detail"] = reliability_detail
    guarded["pose_reliability_policy"] = thresholds["pose_reliability_policy"]
    guarded["pose_reliability_blockers"] = (
        (pose_reliability or {}).get("pose_reliability_blockers") or []
    )
    guarded["pose_reliability_borderline_flags"] = (
        (pose_reliability or {}).get("borderline_flags") or []
    )
    if reliability_detail == "pose_limited" and guarded.get("phone_call_status") == "handheld_call_likely":
        guarded["raw_phone_call_status_before_pose_guardrail"] = "handheld_call_likely"
        guarded["phone_call_status"] = "candidate"
        guarded["phone_call_confidence"] = min(
            float(guarded.get("phone_call_confidence") or 0.0),
            0.74,
        )
    return guarded


def draw_status(
    frame: Any,
    behavior: dict[str, Any],
    arm_record: dict[str, Any] | None,
    phone_object_detected: bool | None,
) -> None:
    status = str(behavior.get("phone_call_status") or "unknown")
    color = {
        "handheld_call_likely": (0, 0, 255),
        "candidate": (0, 165, 255),
        "not_detected": (0, 200, 0),
        "not_evaluable": (140, 140, 140),
    }.get(status, (255, 255, 255))
    cv2.rectangle(frame, (12, 82), (790, 174), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"phone-object: {phone_object_detected}",
        (24, 108),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"call-behavior: {status} conf={behavior.get('phone_call_confidence')}",
        (24, 136),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        color,
        2,
        cv2.LINE_AA,
    )
    current_state = (arm_record or {}).get("state", "unavailable")
    cv2.putText(
        frame,
        f"arm-state: {current_state} source={behavior.get('phone_call_evidence_source')}",
        (24, 164),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.54,
        color,
        1,
        cv2.LINE_AA,
    )


def render_overlay(
    source_video: Path,
    output_video: Path,
    arm_records: list[dict[str, Any]],
    behavior: dict[str, Any],
    behavior_timeline: dict[int, dict[str, Any]],
    phone_object_detected: bool | None,
) -> None:
    cap = cv2.VideoCapture(str(source_video))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open overlay source: {source_video}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    output_video.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create overlay: {output_video}")
    record_index = {int(item["frame"]): item for item in arm_records}
    frame_number = 0
    current_behavior = {
        **behavior,
        "phone_call_status": "not_evaluable",
        "phone_call_confidence": None,
        "phone_call_evidence_source": None,
    }
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            current_behavior = behavior_timeline.get(frame_number, current_behavior)
            draw_status(
                frame,
                current_behavior,
                record_index.get(frame_number),
                phone_object_detected,
            )
            writer.write(frame)
    finally:
        cap.release()
        writer.release()


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# PHONE-CALL-EXP-002 Summary",
        "",
        "Telefon nesnesi ve zamansal el-kulak davranis kanitini ayri tutar.",
        "Telefon kutusunun yoklugu davranis adayini veto etmez.",
        "",
        "| Video | Object | Call status | Pose | Confidence | Hand-ear rate | Longest | Side |",
        "|---|---:|---|---|---:|---:|---:|---|",
    ]
    for video in summary.get("videos", []):
        behavior = video.get("behavior") or {}
        lines.append(
            "| {video} | {obj} | {status} | {pose} | {conf} | {rate} | {duration}s | {side} |".format(
                video=video.get("video"),
                obj=behavior.get("phone_object_detected"),
                status=behavior.get("phone_call_status"),
                pose=behavior.get("pose_reliability_detail"),
                conf=behavior.get("phone_call_confidence"),
                rate=behavior.get("hand_near_ear_candidate_rate"),
                duration=behavior.get("longest_hand_near_ear_seconds"),
                side=behavior.get("dominant_hand_side"),
            )
        )
    lines.extend(
        [
            "",
            "Risk kapali tutulmustur. Yuz kasima, gozluk/sac duzeltme, yanaga",
            "dayanma ve benzeri hard-negative review tamamlanmadan phone_risk uretilmez.",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run phone-call behavior fusion.")
    parser.add_argument("--arm-summary", type=Path, required=True)
    parser.add_argument("--phone-summary", type=Path, default=DEFAULT_PHONE_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--min-evaluable-frames", type=int, default=10)
    parser.add_argument("--min-hand-near-ear-rate", type=float, default=0.45)
    parser.add_argument("--min-sustained-seconds", type=float, default=0.80)
    parser.add_argument("--min-dominant-side-rate", type=float, default=0.70)
    parser.add_argument("--max-frame-gap", type=int, default=2)
    parser.add_argument("--window-seconds", type=float, default=2.0)
    parser.add_argument("--exit-hand-near-ear-rate", type=float, default=0.20)
    parser.add_argument("--pose-reliability", type=Path, default=DEFAULT_POSE_RELIABILITY)
    parser.add_argument("--borderline-min-sustained-seconds", type=float, default=1.50)
    parser.add_argument("--pose-limited-min-sustained-seconds", type=float, default=2.00)
    parser.add_argument("--pose-limited-min-hand-near-ear-rate", type=float, default=0.60)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    arm_path = args.arm_summary.resolve()
    phone_path = args.phone_summary.resolve()
    if not arm_path.exists():
        raise SystemExit(f"Arm summary not found: {arm_path}")
    if not phone_path.exists():
        raise SystemExit(f"Phone summary not found: {phone_path}")
    arm_summary = json.loads(arm_path.read_text(encoding="utf-8"))
    phone_summary = json.loads(phone_path.read_text(encoding="utf-8"))
    pose_reliability_path = args.pose_reliability.resolve() if args.pose_reliability else None
    pose_reliability_index = load_pose_reliability_index(pose_reliability_path)
    phone_index = {item["video"]: item for item in phone_summary.get("videos", [])}
    selected = {path.name for path in args.videos} if args.videos else None

    videos = []
    for arm_video in arm_summary.get("videos", []):
        name = str(arm_video.get("video"))
        if selected is not None and name not in selected:
            continue
        phone_video = phone_index.get(name) or {}
        phone_temporal = phone_video.get("temporal") or {}
        phone_status = phone_temporal.get("status")
        phone_object_detected = (
            True if phone_status == "detected" else False if phone_status == "not_detected" else None
        )
        source_video = (args.videos_dir / name).resolve()
        fps_cap = cv2.VideoCapture(str(source_video))
        if not fps_cap.isOpened():
            raise RuntimeError(f"Could not open source video: {source_video}")
        fps = float(fps_cap.get(cv2.CAP_PROP_FPS) or 25.0)
        fps_cap.release()
        pose_reliability = pose_reliability_index.get(name)
        reliability_thresholds = behavior_thresholds_for_pose_reliability(
            args,
            pose_reliability,
        )
        behavior = temporal_phone_call_summary(
            arm_video.get("per_frame") or [],
            fps=fps,
            phone_object_detected=phone_object_detected,
            min_evaluable_frames=args.min_evaluable_frames,
            min_hand_near_ear_rate=reliability_thresholds["min_hand_near_ear_rate"],
            min_sustained_seconds=reliability_thresholds["min_sustained_seconds"],
            min_dominant_side_rate=reliability_thresholds["min_dominant_side_rate"],
            max_frame_gap=args.max_frame_gap,
        )
        behavior = apply_pose_reliability_guardrail(
            behavior,
            pose_reliability,
            reliability_thresholds,
        )
        behavior_timeline = temporal_phone_call_timeline(
            arm_video.get("per_frame") or [],
            fps=fps,
            phone_object_detected=phone_object_detected,
            window_seconds=args.window_seconds,
            exit_hand_near_ear_rate=args.exit_hand_near_ear_rate,
            min_evaluable_frames=args.min_evaluable_frames,
            min_hand_near_ear_rate=reliability_thresholds["min_hand_near_ear_rate"],
            min_sustained_seconds=reliability_thresholds["min_sustained_seconds"],
            min_dominant_side_rate=reliability_thresholds["min_dominant_side_rate"],
            max_frame_gap=args.max_frame_gap,
        )
        behavior_timeline = {
            frame: apply_pose_reliability_guardrail(
                frame_behavior,
                pose_reliability,
                reliability_thresholds,
            )
            for frame, frame_behavior in behavior_timeline.items()
        }
        arm_overlay = arm_video.get("annotated_video")
        overlay_source = ROOT / arm_overlay if arm_overlay else source_video
        if not overlay_source.exists():
            overlay_source = source_video
        output_video = (
            args.runs_root
            / EXPERIMENT_ID.lower().replace("-", "_")
            / "annotated"
            / f"{Path(name).stem}_{MODEL_KEY}.mp4"
        )
        render_overlay(
            overlay_source,
            output_video,
            arm_video.get("per_frame") or [],
            behavior,
            behavior_timeline,
            phone_object_detected,
        )
        videos.append(
            {
                "video": name,
                "status": "completed",
                "view_profile": arm_video.get("view_profile"),
                "behavior": behavior,
                "pose_reliability_model_key": (
                    "phone_call_pose_reliability_diagnostic_v1"
                    if pose_reliability
                    else None
                ),
                "object_model_key": phone_summary.get("model_key"),
                "arm_model_key": arm_summary.get("model_key"),
                "annotated_video": rel(output_video),
            }
        )

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "stage": "phone_call_behavior_fusion",
        "created_at_utc": now_utc(),
        "model_key": MODEL_KEY,
        "input_arm_summary": rel(arm_path),
        "input_phone_summary": rel(phone_path),
        "input_pose_reliability": rel(pose_reliability_path)
        if pose_reliability_path and pose_reliability_path.exists()
        else None,
        "risk_enabled": False,
        "decision": "candidate_pending_controlled_negative_review_pose_reliability_guarded",
        "thresholds": {
            "min_evaluable_frames": args.min_evaluable_frames,
            "min_hand_near_ear_rate": args.min_hand_near_ear_rate,
            "min_sustained_seconds": args.min_sustained_seconds,
            "min_dominant_side_rate": args.min_dominant_side_rate,
            "max_frame_gap": args.max_frame_gap,
            "window_seconds": args.window_seconds,
            "exit_hand_near_ear_rate": args.exit_hand_near_ear_rate,
            "borderline_min_sustained_seconds": args.borderline_min_sustained_seconds,
            "pose_limited_min_sustained_seconds": args.pose_limited_min_sustained_seconds,
            "pose_limited_min_hand_near_ear_rate": args.pose_limited_min_hand_near_ear_rate,
        },
        "videos": videos,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.artifact_dir / f"{EXPERIMENT_ID}-{MODEL_KEY}-summary.json"
    report_path = args.report_dir / "phone_call_exp_002_summary.md"
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
