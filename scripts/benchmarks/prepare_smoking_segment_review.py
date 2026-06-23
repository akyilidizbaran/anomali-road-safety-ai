#!/usr/bin/env python3
"""Prepare smoking/cigarette segment review clips and CSV rows.

This is the first smoking workflow step. It does not train a model and does not
emit risk. It converts existing cabin/arm evidence into reviewable mouth/hand
segments so a human can mark:

* ``smoking``
* ``neutral``
* ``face_touch_hard_negative``
* ``drink_eat_hard_negative``
* ``phone_call_hard_negative``
* ``unknown``

Large media outputs stay under ``runs/`` and are ignored by Git. A compact JSON
summary is written under benchmark artifacts for traceability.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARM_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "smoking_review" / "segment_review_v1"
DEFAULT_ARTIFACT = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "smoking"
    / "SMOKING-EXP-000-segment_review_pack.json"
)
EXPERIMENT_ID = "SMOKING-EXP-000"
MODEL_KEY = "smoking_segment_review_pack_v1"


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
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def xyxy_from_face_bbox(face_bbox: list[float] | None) -> tuple[float, float, float, float] | None:
    if not face_bbox or len(face_bbox) != 4:
        return None
    x1, y1, x2, y2 = [float(value) for value in face_bbox]
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def mouth_zone(face_bbox: list[float] | None, expand: float = 0.65) -> tuple[int, int, int, int] | None:
    """Return an expanded lower-face/mouth zone in full-frame coordinates."""

    face = xyxy_from_face_bbox(face_bbox)
    if face is None:
        return None
    x1, y1, x2, y2 = face
    width = x2 - x1
    height = y2 - y1
    mouth_x1 = x1 + 0.12 * width
    mouth_x2 = x2 - 0.12 * width
    mouth_y1 = y1 + 0.48 * height
    mouth_y2 = y2 + 0.18 * height
    pad_x = width * expand
    pad_y = height * expand * 0.65
    return (
        int(round(mouth_x1 - pad_x)),
        int(round(mouth_y1 - pad_y)),
        int(round(mouth_x2 + pad_x)),
        int(round(mouth_y2 + pad_y)),
    )


def point_xy(record: dict[str, Any], name: str) -> tuple[float, float] | None:
    point = (record.get("points") or {}).get(name)
    if not point:
        return None
    x = point.get("x")
    y = point.get("y")
    if x is None or y is None:
        return None
    return float(x), float(y)


def point_confidence(record: dict[str, Any], name: str) -> float:
    point = (record.get("points") or {}).get(name) or {}
    return float(point.get("confidence") or 0.0)


def point_in_box(point: tuple[float, float] | None, box: tuple[int, int, int, int] | None) -> bool:
    if point is None or box is None:
        return False
    x, y = point
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2


def distance_to_box_center(point: tuple[float, float], box: tuple[int, int, int, int]) -> float:
    x, y = point
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    return math.hypot(x - cx, y - cy)


def smoking_candidate_frame(record: dict[str, Any], min_wrist_confidence: float) -> tuple[bool, list[str]]:
    if not record.get("decision_evaluable"):
        return False, ["not_decision_evaluable"]
    box = mouth_zone(record.get("face_bbox"))
    if box is None:
        return False, ["missing_face_mouth_zone"]

    reasons: list[str] = []
    side_states = record.get("side_states") or {}
    for side in ("left", "right"):
        wrist_name = f"{side}_wrist"
        wrist = point_xy(record, wrist_name)
        confidence = point_confidence(record, wrist_name)
        side_state = side_states.get(side) or {}
        if wrist is not None and confidence >= min_wrist_confidence and point_in_box(wrist, box):
            reasons.append(f"{side}_wrist_in_mouth_zone")
        elif side_state.get("near_face"):
            reasons.append(f"{side}_near_face_proxy")

    return bool(reasons), reasons


def candidate_frames(records: list[dict[str, Any]], min_wrist_confidence: float) -> list[int]:
    frames: list[int] = []
    for record in records:
        is_candidate, _ = smoking_candidate_frame(record, min_wrist_confidence)
        if is_candidate:
            frame = int(record.get("frame") or 0)
            if frame > 0:
                frames.append(frame)
    return sorted(frames)


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
    min_wrist_confidence: float,
    max_segment_seconds: float,
    max_segments_per_video: int,
) -> list[SegmentProposal]:
    pad_frames = int(round(pad_seconds * fps))
    merge_gap_frames = int(round(merge_gap_seconds * fps))
    max_segment_frames = max(1, int(round(max_segment_seconds * fps)))
    all_candidate_frames = candidate_frames(records, min_wrist_confidence=min_wrist_confidence)
    raw_segments = []
    for run in runs_from_frames(
        all_candidate_frames,
        max_gap=max_gap,
    ):
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
    candidate_set = set(all_candidate_frames)
    chunked: list[tuple[int, int, int]] = []
    for start, end, _ in merged:
        current = start
        while current <= end:
            chunk_end = min(end, current + max_segment_frames - 1)
            count = sum(1 for frame in candidate_set if current <= frame <= chunk_end)
            if count >= min_candidate_frames:
                chunked.append((current, chunk_end, count))
            current = chunk_end + 1
    chunked = sorted(
        chunked,
        key=lambda item: (item[2], -(item[1] - item[0])),
        reverse=True,
    )[:max_segments_per_video]
    chunked = sorted(chunked)
    proposals: list[SegmentProposal] = []
    for index, (start, end, count) in enumerate(chunked, start=1):
        proposals.append(
            SegmentProposal(
                segment_id=f"{Path(video).stem}_mouth_hand_candidate_{index:02d}",
                video=video,
                session_id=f"session_{Path(video).stem}",
                segment_type="mouth_hand_candidate",
                start_frame=start,
                end_frame=end,
                candidate_frame_count=count,
                proposed_label="unknown",
                notes="review_required_mouth_hand_candidate",
            )
        )
    return proposals


def build_context_proposal(
    video: str,
    records: list[dict[str, Any]],
    fps: float,
    max_frame: int,
    seconds: float,
    blocked_ranges: list[tuple[int, int]] | None = None,
) -> SegmentProposal | None:
    blocked_ranges = blocked_ranges or []

    def blocked(frame: int) -> bool:
        return any(start <= frame <= end for start, end in blocked_ranges)

    usable = [
        int(record.get("frame") or 0)
        for record in records
        if record.get("decision_evaluable")
        and int(record.get("frame") or 0) > 0
        and not blocked(int(record.get("frame") or 0))
    ]
    runs = runs_from_frames(usable, max_gap=2)
    if not runs:
        return None
    target_frames = max(1, int(round(seconds * fps)))
    run = max(runs, key=len)
    start = run[0]
    end = min(run[-1], start + target_frames - 1, max_frame)
    if end <= start:
        return None
    return SegmentProposal(
        segment_id=f"{Path(video).stem}_context_01",
        video=video,
        session_id=f"session_{Path(video).stem}",
        segment_type="context_review",
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


def draw_smoking_overlay(frame: np.ndarray, record: dict[str, Any] | None) -> np.ndarray:
    canvas = frame.copy()
    if record is None:
        return canvas
    zone = mouth_zone(record.get("face_bbox"))
    if zone is not None:
        x1, y1, x2, y2 = zone
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 180, 255), 2)
        cv2.putText(
            canvas,
            "mouth/hand ROI",
            (max(0, x1), max(18, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 180, 255),
            2,
            cv2.LINE_AA,
        )
    face = xyxy_from_face_bbox(record.get("face_bbox"))
    if face is not None:
        x1, y1, x2, y2 = [int(round(value)) for value in face]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 0, 255), 1)

    for side, color in [("left", (80, 220, 80)), ("right", (255, 120, 80))]:
        for point_name in [f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist"]:
            point = point_xy(record, point_name)
            if point is None:
                continue
            x, y = [int(round(value)) for value in point]
            cv2.circle(canvas, (x, y), 5 if point_name.endswith("wrist") else 4, color, -1)
            if point_name.endswith("wrist"):
                cv2.putText(
                    canvas,
                    f"{side} wrist",
                    (x + 6, y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    color,
                    1,
                    cv2.LINE_AA,
                )
    is_candidate, reasons = smoking_candidate_frame(record, min_wrist_confidence=0.15)
    label = "smoking candidate" if is_candidate else "context"
    cv2.rectangle(canvas, (0, 0), (min(canvas.shape[1], 760), 38), (0, 0, 0), -1)
    cv2.putText(
        canvas,
        f"{label}: {','.join(reasons[:2])}",
        (8, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return canvas


def render_contact_sheet(
    video_path: Path,
    output_path: Path,
    proposal: SegmentProposal,
    records_by_frame: dict[int, dict[str, Any]],
    width: int = 520,
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
            frame = draw_smoking_overlay(frame, records_by_frame.get(frame_number))
            scale = width / max(1, frame.shape[1])
            tile = cv2.resize(frame, (width, int(round(frame.shape[0] * scale))))
            cv2.rectangle(tile, (0, 0), (width, 30), (0, 0, 0), -1)
            cv2.putText(
                tile,
                f"{proposal.segment_id} frame={frame_number}",
                (8, 21),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
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


def render_clip(
    video_path: Path,
    output_path: Path,
    proposal: SegmentProposal,
    records_by_frame: dict[int, dict[str, Any]],
) -> None:
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
            writer.write(draw_smoking_overlay(frame, records_by_frame.get(current)))
            current += 1
    finally:
        cap.release()
        writer.release()


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
        "cigarette_visibility",
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
                    "cigarette_visibility": "",
                    "negative_subtype": "",
                    "review_clip": rel(proposal.clip_path),
                    "contact_sheet": rel(proposal.contact_sheet_path),
                    "reviewer": "",
                    "notes": proposal.notes,
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare smoking segment review media.")
    parser.add_argument("--arm-summary", type=Path, default=DEFAULT_ARM_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--min-candidate-frames", type=int, default=4)
    parser.add_argument("--max-gap", type=int, default=2)
    parser.add_argument("--pad-seconds", type=float, default=0.6)
    parser.add_argument("--merge-gap-seconds", type=float, default=0.75)
    parser.add_argument("--context-seconds", type=float, default=2.0)
    parser.add_argument("--min-wrist-confidence", type=float, default=0.15)
    parser.add_argument("--max-segment-seconds", type=float, default=4.0)
    parser.add_argument("--max-candidate-segments-per-video", type=int, default=2)
    parser.add_argument("--skip-media", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    arm_summary = json.loads(args.arm_summary.resolve().read_text(encoding="utf-8"))
    proposals: list[SegmentProposal] = []
    fps_by_video: dict[str, float] = {}
    frame_counts: dict[str, int] = {}
    candidate_frame_counts: dict[str, int] = {}
    records_by_video: dict[str, dict[int, dict[str, Any]]] = {}

    for video_item in arm_summary.get("videos", []):
        video = str(video_item.get("video"))
        source_video = args.videos_dir / video
        fps, _, _, frame_count = open_video_info(source_video)
        fps_by_video[video] = fps
        frame_counts[video] = frame_count
        records = video_item.get("per_frame") or []
        records_by_video[video] = {
            int(record.get("frame") or 0): record
            for record in records
            if int(record.get("frame") or 0) > 0
        }
        video_candidate_frames = candidate_frames(records, args.min_wrist_confidence)
        candidate_frame_counts[video] = len(video_candidate_frames)
        video_proposals = build_candidate_proposals(
            video=video,
            records=records,
            fps=fps,
            max_frame=frame_count,
            min_candidate_frames=args.min_candidate_frames,
            max_gap=args.max_gap,
            pad_seconds=args.pad_seconds,
            merge_gap_seconds=args.merge_gap_seconds,
            min_wrist_confidence=args.min_wrist_confidence,
            max_segment_seconds=args.max_segment_seconds,
            max_segments_per_video=args.max_candidate_segments_per_video,
        )
        context = build_context_proposal(
            video=video,
            records=records,
            fps=fps,
            max_frame=frame_count,
            seconds=args.context_seconds,
            blocked_ranges=[
                (proposal.start_frame, proposal.end_frame)
                for proposal in video_proposals
            ],
        )
        if context is not None:
            video_proposals.append(context)
        proposals.extend(video_proposals)

    for proposal in proposals:
        source_video = args.videos_dir / proposal.video
        clip_path = args.runs_dir / "clips" / f"{proposal.segment_id}.mp4"
        sheet_path = args.runs_dir / "contact_sheets" / f"{proposal.segment_id}.jpg"
        proposal.clip_path = clip_path
        proposal.contact_sheet_path = sheet_path
        if not args.skip_media:
            render_clip(source_video, clip_path, proposal, records_by_video[proposal.video])
            render_contact_sheet(source_video, sheet_path, proposal, records_by_video[proposal.video])

    review_csv = args.runs_dir / "manual_smoking_segments_review.csv"
    write_review_csv(review_csv, proposals, fps_by_video)
    artifact = {
        "experiment_id": EXPERIMENT_ID,
        "model_key": MODEL_KEY,
        "created_at_utc": now_utc(),
        "inputs": {
            "arm_summary": rel(args.arm_summary),
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
            "context_seconds": args.context_seconds,
            "min_wrist_confidence": args.min_wrist_confidence,
            "max_segment_seconds": args.max_segment_seconds,
            "max_candidate_segments_per_video": args.max_candidate_segments_per_video,
            "skip_media": args.skip_media,
        },
        "video_count": len(fps_by_video),
        "segment_count": len(proposals),
        "segments_by_video": {
            video: sum(1 for proposal in proposals if proposal.video == video)
            for video in sorted(fps_by_video)
        },
        "candidate_frame_counts": candidate_frame_counts,
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
