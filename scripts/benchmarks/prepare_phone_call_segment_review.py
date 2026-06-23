#!/usr/bin/env python3
"""Prepare phone-call segment review clips and CSV rows.

This script does not create training labels. It turns the current pose/object
evidence into reviewable segments so a human can mark:

* ``phone_call``
* ``face_touch_hard_negative``
* ``neutral``
* ``unknown``

Large media outputs stay under ``runs/`` and are ignored by Git. The compact JSON
summary is written under benchmark artifacts for traceability.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

try:
    from train_phone_call_temporal_head import is_candidate_frame
except ImportError:
    from scripts.benchmarks.train_phone_call_temporal_head import is_candidate_frame


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARM_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json"
)
DEFAULT_BEHAVIOR_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-002-phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2-summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "phone_call_review" / "segment_review_v1"
DEFAULT_ARTIFACT = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-006-segment_review_pack.json"
)
EXPERIMENT_ID = "PHONE-CALL-EXP-006"
MODEL_KEY = "phone_call_segment_review_pack_v1"


@dataclass
class SegmentProposal:
    segment_id: str
    video: str
    session_id: str
    segment_type: str
    start_frame: int
    end_frame: int
    candidate_frame_count: int
    proposed_label: str
    notes: str
    clip_path: Path | None = None
    contact_sheet_path: Path | None = None

    @property
    def frame_count(self) -> int:
        return max(0, self.end_frame - self.start_frame + 1)


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def open_video_info(path: Path) -> tuple[float, int, int, int]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return fps, width, height, frame_count
    finally:
        cap.release()


def candidate_frames(records: list[dict[str, Any]]) -> list[int]:
    frames: list[int] = []
    for record in records:
        is_candidate, _, _ = is_candidate_frame(record)
        if record.get("decision_evaluable") and is_candidate:
            frames.append(int(record.get("frame") or 0))
    return sorted(frame for frame in frames if frame > 0)


def runs_from_frames(frames: list[int], max_gap: int) -> list[list[int]]:
    runs: list[list[int]] = []
    current: list[int] = []
    previous = None
    for frame in sorted(frames):
        if previous is None or frame - previous <= max_gap:
            current.append(frame)
        else:
            if current:
                runs.append(current)
            current = [frame]
        previous = frame
    if current:
        runs.append(current)
    return runs


def merge_overlapping_segments(
    segments: list[tuple[int, int, int]],
    merge_gap_frames: int,
) -> list[tuple[int, int, int]]:
    if not segments:
        return []
    ordered = sorted(segments)
    merged: list[tuple[int, int, int]] = [ordered[0]]
    for start, end, count in ordered[1:]:
        prev_start, prev_end, prev_count = merged[-1]
        if start <= prev_end + merge_gap_frames:
            merged[-1] = (prev_start, max(prev_end, end), prev_count + count)
        else:
            merged.append((start, end, count))
    return merged


def build_candidate_proposals(
    video: str,
    records: list[dict[str, Any]],
    fps: float,
    max_frame: int,
    min_candidate_frames: int,
    max_gap: int,
    pad_seconds: float,
    merge_gap_seconds: float,
) -> list[SegmentProposal]:
    pad_frames = int(round(pad_seconds * fps))
    merge_gap_frames = int(round(merge_gap_seconds * fps))
    raw_segments = []
    for run in runs_from_frames(candidate_frames(records), max_gap=max_gap):
        if len(run) < min_candidate_frames:
            continue
        raw_segments.append(
            (
                max(1, run[0] - pad_frames),
                min(max_frame, run[-1] + pad_frames),
                len(run),
            )
        )
    merged = merge_overlapping_segments(raw_segments, merge_gap_frames=merge_gap_frames)
    proposals: list[SegmentProposal] = []
    for index, (start, end, count) in enumerate(merged, start=1):
        proposed = "phone_call" if video == "video_2.mp4" else "unknown"
        proposals.append(
            SegmentProposal(
                segment_id=f"{Path(video).stem}_candidate_{index:02d}",
                video=video,
                session_id=f"session_{Path(video).stem}",
                segment_type="hand_near_ear_candidate",
                start_frame=start,
                end_frame=end,
                candidate_frame_count=count,
                proposed_label=proposed,
                notes=(
                    "user_confirmed_positive_context"
                    if video == "video_2.mp4"
                    else "review_required_candidate"
                ),
            )
        )
    return proposals


def build_neutral_proposal(
    video: str,
    records: list[dict[str, Any]],
    fps: float,
    max_frame: int,
    seconds: float,
    blocked_ranges: list[tuple[int, int]] | None = None,
) -> SegmentProposal | None:
    candidate_set = set(candidate_frames(records))
    blocked_ranges = blocked_ranges or []

    def blocked(frame: int) -> bool:
        return any(start <= frame <= end for start, end in blocked_ranges)

    evaluable_non_candidate = [
        int(record.get("frame") or 0)
        for record in records
        if record.get("decision_evaluable")
        and int(record.get("frame") or 0) > 0
        and int(record.get("frame") or 0) not in candidate_set
        and not blocked(int(record.get("frame") or 0))
    ]
    runs = runs_from_frames(evaluable_non_candidate, max_gap=2)
    if not runs:
        return None
    target_frames = max(1, int(round(seconds * fps)))
    run = max(runs, key=len)
    start = run[0]
    end = min(run[-1], start + target_frames - 1, max_frame)
    if end <= start:
        return None
    return SegmentProposal(
        segment_id=f"{Path(video).stem}_neutral_01",
        video=video,
        session_id=f"session_{Path(video).stem}",
        segment_type="neutral_context",
        start_frame=start,
        end_frame=end,
        candidate_frame_count=0,
        proposed_label="unknown",
        notes="review_required_neutral_or_hard_negative_context",
    )


def read_frame_at(cap: cv2.VideoCapture, frame_number: int) -> np.ndarray | None:
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_number - 1))
    ok, frame = cap.read()
    return frame if ok else None


def render_contact_sheet(
    video_path: Path,
    output_path: Path,
    proposal: SegmentProposal,
    width: int = 420,
) -> None:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video for contact sheet: {video_path}")
    frames_to_sample = sorted(
        {
            proposal.start_frame,
            (proposal.start_frame + proposal.end_frame) // 2,
            proposal.end_frame,
        }
    )
    tiles: list[np.ndarray] = []
    try:
        for frame_number in frames_to_sample:
            frame = read_frame_at(cap, frame_number)
            if frame is None:
                continue
            scale = width / max(1, frame.shape[1])
            tile = cv2.resize(frame, (width, int(round(frame.shape[0] * scale))))
            cv2.rectangle(tile, (0, 0), (width, 34), (0, 0, 0), -1)
            cv2.putText(
                tile,
                f"{proposal.segment_id} frame={frame_number}",
                (8, 23),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            tiles.append(tile)
    finally:
        cap.release()
    if not tiles:
        raise RuntimeError(f"No frames rendered for {proposal.segment_id}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet = np.vstack(tiles)
    cv2.imwrite(str(output_path), sheet)


def render_clip(video_path: Path, output_path: Path, proposal: SegmentProposal) -> None:
    fps, width, height, _ = open_video_info(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video for clip: {video_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create clip: {output_path}")
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, proposal.start_frame - 1))
        current = proposal.start_frame
        while current <= proposal.end_frame:
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)
            current += 1
    finally:
        cap.release()
        writer.release()


def behavior_overlay_index(summary: dict[str, Any]) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for item in summary.get("videos", []):
        annotated = item.get("annotated_video")
        if annotated:
            index[str(item.get("video"))] = ROOT / annotated
    return index


def write_review_csv(path: Path, proposals: list[SegmentProposal], fps_by_video: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "segment_id",
        "video",
        "session_id",
        "split",
        "start_frame",
        "end_frame",
        "start_seconds",
        "end_seconds",
        "segment_type",
        "candidate_frame_count",
        "proposed_label",
        "final_label",
        "phone_visibility",
        "negative_subtype",
        "review_clip",
        "contact_sheet",
        "reviewer",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for proposal in proposals:
            fps = fps_by_video[proposal.video]
            writer.writerow(
                {
                    "segment_id": proposal.segment_id,
                    "video": proposal.video,
                    "session_id": proposal.session_id,
                    "split": "review",
                    "start_frame": proposal.start_frame,
                    "end_frame": proposal.end_frame,
                    "start_seconds": round((proposal.start_frame - 1) / fps, 3),
                    "end_seconds": round(proposal.end_frame / fps, 3),
                    "segment_type": proposal.segment_type,
                    "candidate_frame_count": proposal.candidate_frame_count,
                    "proposed_label": proposal.proposed_label,
                    "final_label": "",
                    "phone_visibility": "",
                    "negative_subtype": "",
                    "review_clip": rel(proposal.clip_path),
                    "contact_sheet": rel(proposal.contact_sheet_path),
                    "reviewer": "",
                    "notes": proposal.notes,
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare phone-call segment review media.")
    parser.add_argument("--arm-summary", type=Path, default=DEFAULT_ARM_SUMMARY)
    parser.add_argument("--behavior-summary", type=Path, default=DEFAULT_BEHAVIOR_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--min-candidate-frames", type=int, default=5)
    parser.add_argument("--max-gap", type=int, default=2)
    parser.add_argument("--pad-seconds", type=float, default=0.5)
    parser.add_argument("--merge-gap-seconds", type=float, default=0.75)
    parser.add_argument("--neutral-seconds", type=float, default=2.0)
    parser.add_argument("--skip-media", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    arm_summary = json.loads(args.arm_summary.resolve().read_text(encoding="utf-8"))
    behavior_summary = json.loads(args.behavior_summary.resolve().read_text(encoding="utf-8"))
    overlays = behavior_overlay_index(behavior_summary)
    proposals: list[SegmentProposal] = []
    fps_by_video: dict[str, float] = {}
    frame_counts: dict[str, int] = {}
    for video_item in arm_summary.get("videos", []):
        video = str(video_item.get("video"))
        source_video = args.videos_dir / video
        fps, _, _, frame_count = open_video_info(source_video)
        fps_by_video[video] = fps
        frame_counts[video] = frame_count
        records = video_item.get("per_frame") or []
        video_proposals = build_candidate_proposals(
            video=video,
            records=records,
            fps=fps,
            max_frame=frame_count,
            min_candidate_frames=args.min_candidate_frames,
            max_gap=args.max_gap,
            pad_seconds=args.pad_seconds,
            merge_gap_seconds=args.merge_gap_seconds,
        )
        neutral = build_neutral_proposal(
            video=video,
            records=records,
            fps=fps,
            max_frame=frame_count,
            seconds=args.neutral_seconds,
            blocked_ranges=[
                (proposal.start_frame, proposal.end_frame)
                for proposal in video_proposals
            ],
        )
        if neutral is not None:
            video_proposals.append(neutral)
        proposals.extend(video_proposals)

    for proposal in proposals:
        media_source = overlays.get(proposal.video)
        if media_source is None or not media_source.exists():
            media_source = args.videos_dir / proposal.video
        clip_path = args.runs_dir / "clips" / f"{proposal.segment_id}.mp4"
        sheet_path = args.runs_dir / "contact_sheets" / f"{proposal.segment_id}.jpg"
        proposal.clip_path = clip_path
        proposal.contact_sheet_path = sheet_path
        if not args.skip_media:
            render_clip(media_source, clip_path, proposal)
            render_contact_sheet(media_source, sheet_path, proposal)

    review_csv = args.runs_dir / "manual_phone_call_segments_review.csv"
    write_review_csv(review_csv, proposals, fps_by_video)
    artifact = {
        "experiment_id": EXPERIMENT_ID,
        "model_key": MODEL_KEY,
        "created_at_utc": now_utc(),
        "inputs": {
            "arm_summary": rel(args.arm_summary),
            "behavior_summary": rel(args.behavior_summary),
            "videos_dir": rel(args.videos_dir),
        },
        "outputs": {
            "review_csv": rel(review_csv),
            "runs_dir": rel(args.runs_dir),
        },
        "parameters": {
            "min_candidate_frames": args.min_candidate_frames,
            "max_gap": args.max_gap,
            "pad_seconds": args.pad_seconds,
            "merge_gap_seconds": args.merge_gap_seconds,
            "neutral_seconds": args.neutral_seconds,
            "skip_media": args.skip_media,
        },
        "video_count": len(fps_by_video),
        "segment_count": len(proposals),
        "segments_by_video": {
            video: sum(1 for proposal in proposals if proposal.video == video)
            for video in sorted(fps_by_video)
        },
        "frame_counts": frame_counts,
        "segments": [
            {
                "segment_id": proposal.segment_id,
                "video": proposal.video,
                "segment_type": proposal.segment_type,
                "start_frame": proposal.start_frame,
                "end_frame": proposal.end_frame,
                "candidate_frame_count": proposal.candidate_frame_count,
                "proposed_label": proposal.proposed_label,
                "review_clip": rel(proposal.clip_path),
                "contact_sheet": rel(proposal.contact_sheet_path),
            }
            for proposal in proposals
        ],
    }
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.artifact.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
