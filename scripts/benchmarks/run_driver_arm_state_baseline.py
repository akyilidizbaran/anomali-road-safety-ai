#!/usr/bin/env python3
"""Benchmark continuous driver arm-state evidence from pose and optical flow."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

try:
    from driver_arm_state_utils import (
        HybridArmTracker,
        TemporalStateVoter,
        arm_temporal_summary,
        classify_arm_state,
        driver_identity_consistent,
        global_pose_keypoints,
    )
except ImportError:
    from scripts.benchmarks.driver_arm_state_utils import (
        HybridArmTracker,
        TemporalStateVoter,
        arm_temporal_summary,
        classify_arm_state,
        driver_identity_consistent,
        global_pose_keypoints,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POSE_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "POSE-EXP-010-vitpose_b_arm_focus_observations_v1-summary.json"
)
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_PROFILES = (
    ROOT / "architecture" / "contracts" / "driver_arm_profiles.example.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "driver_arm_state"
EXPERIMENT_ID = "ARM-EXP-001"
MODEL_KEY = "vitpose_b_lk_arm_tracker_v1"
TRACKER_KEY = "lk_arm_tracker_v1"
SUPPORTED_POSE_EXPERIMENTS = {"POSE-EXP-010", "POSE-EXP-011"}

ARM_EDGES = (
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
)
SOURCE_COLORS = {
    "observed": (0, 255, 0),
    "tracked_low_confidence": (0, 165, 255),
    "optical_flow": (255, 180, 0),
}
STATE_COLORS = {
    "hand_near_face": (255, 0, 255),
    "arm_raised": (0, 0, 255),
    "hands_on_wheel_candidate": (0, 255, 0),
    "hand_off_wheel_candidate": (0, 165, 255),
    "arms_visible_other": (255, 255, 0),
    "unknown": (160, 160, 160),
    "not_evaluable": (100, 100, 100),
}


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


def draw_arm_overlay(
    frame: Any,
    tracked: dict[str, Any],
    state: dict[str, Any],
) -> None:
    points = tracked.get("points") or {}
    for first_name, second_name in ARM_EDGES:
        first = points.get(first_name)
        second = points.get(second_name)
        if not first or not second:
            continue
        color = SOURCE_COLORS.get(
            str(second.get("source")),
            (255, 255, 255),
        )
        cv2.line(
            frame,
            (int(first["x"]), int(first["y"])),
            (int(second["x"]), int(second["y"])),
            color,
            3,
            cv2.LINE_AA,
        )
    for name, point in points.items():
        color = SOURCE_COLORS.get(str(point.get("source")), (255, 255, 255))
        radius = 5 if name.endswith("wrist") else 4
        cv2.circle(
            frame,
            (int(point["x"]), int(point["y"])),
            radius,
            color,
            -1,
            cv2.LINE_AA,
        )
    zone = state.get("wheel_zone_bbox")
    if zone:
        x1, y1, x2, y2 = [int(value) for value in zone]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 80), 1)
    for ear_zone in (state.get("ear_zone_bboxes") or {}).values():
        x1, y1, x2, y2 = [int(value) for value in ear_zone]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 1)
    color = STATE_COLORS.get(str(state["state"]), (255, 255, 255))
    cv2.putText(
        frame,
        f"arm-state: {state['state']} ({state.get('confidence')})",
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        color,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "green=observed orange=low-conf blue=optical-flow",
        (24, 64),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )


def process_video(
    video_path: Path,
    pose_video: dict[str, Any],
    cabin_video: dict[str, Any],
    profiles: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    pose_records = {
        int(item["frame"]): item
        for item in pose_video.get("per_frame", [])
    }
    cabin_records = {
        int(item["frame"]): item
        for item in cabin_video.get("per_frame", [])
    }
    view_profile = str(
        pose_video.get("view_profile")
        or cabin_video.get("view_profile")
        or "unknown"
    )
    profile = (profiles.get("profiles") or {}).get(view_profile)
    tracker = HybridArmTracker(
        observation_confidence=args.observation_confidence,
        continuation_confidence=args.continuation_confidence,
        max_flow_hold_frames=args.max_flow_hold_frames,
        max_face_hold_frames=args.max_face_hold_frames,
    )
    voter = TemporalStateVoter(
        window_size=args.vote_window,
        minimum_votes=args.minimum_votes,
    )
    run_dir = args.runs_root / "arm_exp_001"
    overlay_dir = run_dir / "annotated"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    overlay_key = getattr(args, "output_model_key", MODEL_KEY)
    overlay_path = overlay_dir / f"{video_path.stem}_{overlay_key}.mp4"
    writer = cv2.VideoWriter(
        str(overlay_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create overlay: {overlay_path}")

    records: list[dict[str, Any]] = []
    latencies: list[float] = []
    frame_number = 0
    previous_face = None
    previous_cabin = None
    identity_reset_count = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            pose_record = pose_records.get(frame_number)
            cabin_record = cabin_records.get(frame_number)
            if pose_record is None or cabin_record is None:
                writer.write(frame)
                continue
            face = pose_record.get("driver_face_bbox")
            cabin_bbox = cabin_record.get("cabin_bbox_xyxy")
            identity_ok = driver_identity_consistent(
                previous_face,
                previous_cabin,
                face,
                cabin_bbox,
                max_normalized_jump=args.max_identity_jump,
            )
            if not identity_ok:
                tracker.reset()
                voter = TemporalStateVoter(
                    window_size=args.vote_window,
                    minimum_votes=args.minimum_votes,
                )
                identity_reset_count += 1
            observations = global_pose_keypoints(pose_record)
            started = time.perf_counter()
            tracked = tracker.update(
                frame,
                observations,
                face,
                cabin_bbox,
                frame_number,
            )
            raw_state = classify_arm_state(tracked, profile)
            voted_state = voter.update(str(raw_state["state"]))
            latency = (time.perf_counter() - started) * 1000.0
            latencies.append(latency)
            state = {
                **raw_state,
                "raw_state": raw_state["state"],
                "state": voted_state,
            }
            decision_evaluable = bool(
                pose_record.get("visibility") in {"good", "limited"}
                and tracked.get("face_source") == "observed"
            )
            record = {
                "frame": frame_number,
                "visibility": pose_record.get("visibility"),
                "decision_evaluable": decision_evaluable,
                "driver_identity_consistent": identity_ok,
                "identity_reset": not identity_ok,
                "face_source": tracked.get("face_source"),
                "face_bbox": tracked.get("face_bbox"),
                "state": state["state"],
                "raw_state": state["raw_state"],
                "state_confidence": state.get("confidence"),
                "state_reasons": state.get("reasons"),
                "side_states": state.get("side_states"),
                "wheel_zone_bbox": state.get("wheel_zone_bbox"),
                "ear_zone_bboxes": state.get("ear_zone_bboxes"),
                "points": tracked.get("points"),
                "complete_arm_count": tracked.get("complete_arm_count"),
                "optical_flow_point_count": tracked.get(
                    "optical_flow_point_count"
                ),
                "low_confidence_point_count": tracked.get(
                    "low_confidence_point_count"
                ),
                "rejected_observation_count": tracked.get(
                    "rejected_observation_count"
                ),
                "latency_ms": round(latency, 3),
                "risk_enabled": False,
            }
            draw_arm_overlay(frame, tracked, state)
            writer.write(frame)
            records.append(record)
            if face is not None:
                previous_face = face
                previous_cabin = cabin_bbox
    finally:
        cap.release()
        writer.release()
    temporal = arm_temporal_summary(records, fps)
    temporal["identity_reset_count"] = identity_reset_count
    return {
        "video": video_path.name,
        "status": "completed",
        "view_profile": view_profile,
        "mean_arm_latency_ms": mean(latencies),
        "p95_arm_latency_ms": p95(latencies),
        "temporal": temporal,
        "annotated_video": rel(overlay_path),
        "per_frame": records,
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = []
    for video in summary["videos"]:
        temporal = video["temporal"]
        rows.append(
            f"| {video['video']} | {temporal['evaluable_frame_count']} | "
            f"{temporal['available_state_rate']} | "
            f"{temporal['optical_flow_recovered_frame_count']} | "
            f"{temporal['longest_unavailable_seconds']} | "
            f"{temporal['state_transition_count']} | "
            f"{temporal['identity_reset_count']} | "
            f"{video['mean_arm_latency_ms']} | {video['p95_arm_latency_ms']} |"
        )
    return "\n".join(
        [
            "# ARM-EXP-001 Driver Arm-State Baseline",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            "`ViTPose-B observations -> forward/backward LK optical flow -> "
            "anatomical gate -> temporal arm-state voting`",
            "",
            "Bu deney nesne tespit etmez ve risk üretmez. "
            "`hands_on_wheel_candidate` yalnız beklenen wheel zone geometrisidir; "
            "direksiyon teması değildir.",
            "",
            "| Video | Evaluable | Available Rate | Flow-Recovered | Longest Miss s | Transitions | Identity Reset | Mean ms | P95 ms |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            *rows,
            "",
            "Manuel review: `testing/templates/manual_driver_arm_state_review.csv`",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run driver arm-state baseline.")
    parser.add_argument("--pose-summary", type=Path, default=DEFAULT_POSE_SUMMARY)
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--observation-confidence", type=float, default=0.30)
    parser.add_argument("--continuation-confidence", type=float, default=0.10)
    parser.add_argument("--max-flow-hold-frames", type=int, default=12)
    parser.add_argument("--max-face-hold-frames", type=int, default=25)
    parser.add_argument("--max-identity-jump", type=float, default=0.18)
    parser.add_argument("--vote-window", type=int, default=9)
    parser.add_argument("--minimum-votes", type=int, default=4)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pose_path = args.pose_summary.resolve()
    cabin_path = args.cabin_summary.resolve()
    pose_summary = json.loads(pose_path.read_text(encoding="utf-8"))
    cabin_summary = json.loads(cabin_path.read_text(encoding="utf-8"))
    profiles = json.loads(args.profiles.resolve().read_text(encoding="utf-8"))
    pose_experiment_id = str(pose_summary.get("experiment_id"))
    pose_model_key = str(pose_summary.get("model_key") or "unknown_pose")
    if pose_experiment_id not in SUPPORTED_POSE_EXPERIMENTS:
        raise SystemExit(
            "ARM-EXP-001 requires arm-focus POSE-EXP-010 or POSE-EXP-011 "
            "observations."
        )
    if cabin_summary.get("experiment_id") != "CABIN-EXP-004":
        raise SystemExit("ARM-EXP-001 requires selected CABIN-EXP-004 identity input.")
    args.output_model_key = (
        MODEL_KEY
        if pose_experiment_id == "POSE-EXP-010"
        else f"{pose_model_key}_{TRACKER_KEY}"
    )
    cabin_index = {
        item["video"]: item for item in cabin_summary.get("videos", [])
    }
    selected = (
        {path.name for path in args.videos}
        if args.videos
        else {item["video"] for item in pose_summary.get("videos", [])}
    )
    videos = []
    for pose_video in pose_summary.get("videos", []):
        name = pose_video.get("video")
        if name not in selected or name not in cabin_index:
            continue
        video_path = (args.videos_dir / name).resolve()
        print(f"\n=== {name}: continuous driver arm-state ===")
        videos.append(
            process_video(
                video_path,
                pose_video,
                cabin_index[name],
                profiles,
                args,
            )
        )
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "stage": "driver_arm_state_baseline",
        "created_at_utc": now_utc(),
        "model_key": (
            args.output_model_key
        ),
        "tracker_key": TRACKER_KEY,
        "observation_model_key": pose_model_key,
        "input_pose_summary": rel(pose_path),
        "input_pose_experiment_id": pose_experiment_id,
        "input_cabin_summary": rel(cabin_path),
        "input_cabin_experiment_id": cabin_summary.get("experiment_id"),
        "profiles": rel(args.profiles),
        "decision": "candidate_not_selected_pending_manual_review",
        "risk_enabled": False,
        "videos": videos,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    if pose_experiment_id == "POSE-EXP-010":
        summary_path = args.artifact_dir / f"{EXPERIMENT_ID}-{MODEL_KEY}-summary.json"
        report_path = args.report_dir / "arm_exp_001_summary.md"
    else:
        summary_path = (
            args.artifact_dir
            / f"{EXPERIMENT_ID}-{pose_model_key}-{TRACKER_KEY}-summary.json"
        )
        report_path = (
            args.report_dir
            / f"arm_exp_001_{pose_model_key}_summary.md"
        )
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
