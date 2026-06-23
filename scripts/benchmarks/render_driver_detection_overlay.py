#!/usr/bin/env python3
"""Render visual driver detection overlays from CABIN-EXP-004 frame metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ID = "DRIVER-EXP-001"
EXPERIMENT_NAME = "yunet_view_policy_driver_presence_v1"
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_DRIVER_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "driver_detection"
    / f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"
    / "driver_exp_001_driver_detection_summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "driver_detection" / f"{EXPERIMENT_ID}-{EXPERIMENT_NAME}"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render DRIVER-EXP-001 visual overlay MP4 files."
    )
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--driver-summary", type=Path, default=DEFAULT_DRIVER_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--output-width", type=int, default=1280)
    return parser.parse_args()


def draw_label(
    image: np.ndarray,
    text: str,
    origin: tuple[int, int],
    color: tuple[int, int, int],
    scale: float = 0.58,
) -> None:
    x, y = origin
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
    pad = 6
    cv2.rectangle(
        image,
        (x, y - text_h - baseline - pad),
        (x + text_w + pad * 2, y + baseline + pad),
        (0, 0, 0),
        -1,
    )
    cv2.putText(
        image,
        text,
        (x + pad, y),
        font,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def clamp_box(box: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    return (
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(0, min(width - 1, int(round(x2)))),
        max(0, min(height - 1, int(round(y2)))),
    )


def scale_frame_and_meta(
    frame: np.ndarray,
    frame_meta: dict[str, Any],
    output_width: int,
) -> tuple[np.ndarray, float]:
    if not output_width or output_width >= frame.shape[1]:
        return frame, 1.0
    scale = output_width / float(frame.shape[1])
    output_height = int(round(frame.shape[0] * scale))
    if output_height % 2:
        output_height += 1
    resized = cv2.resize(frame, (output_width, output_height), interpolation=cv2.INTER_AREA)
    return resized, scale


def scaled_box(box: list[float], scale: float) -> list[float]:
    return [float(value) * scale for value in box]


def face_box_to_global(
    cabin_box: list[float],
    face: dict[str, Any],
) -> list[float]:
    x1, y1, _, _ = cabin_box
    fx, fy, fw, fh = [float(value) for value in face.get("bbox", [0, 0, 0, 0])]
    return [x1 + fx, y1 + fy, x1 + fx + fw, y1 + fy + fh]


def keypoint_to_global(
    cabin_box: list[float],
    point: dict[str, Any],
) -> tuple[float, float]:
    x1, y1, x2, y2 = [float(value) for value in cabin_box]
    width = max(1.0, x2 - x1)
    height = max(1.0, y2 - y1)
    return x1 + float(point.get("x", 0.0)) * width, y1 + float(point.get("y", 0.0)) * height


def draw_panel(
    frame: np.ndarray,
    video: str,
    driver_info: dict[str, Any],
    frame_idx: int,
    timestamp: float,
) -> None:
    panel_w = min(frame.shape[1] - 28, 760)
    panel_h = 142
    x0, y0 = 18, 18
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.62, frame, 0.38, 0, dst=frame)

    lines = [
        f"{EXPERIMENT_ID} driver detection",
        f"{video}  frame={frame_idx}  t={timestamp:.2f}s",
        (
            f"status={driver_info.get('status')}  driver={driver_info.get('driver_present')}  "
            f"conf={driver_info.get('confidence')}"
        ),
        (
            f"view={driver_info.get('view_profile')}  occupants={driver_info.get('occupant_count_estimate')}  "
            f"passengers={driver_info.get('passenger_count')}"
        ),
        "action/risk disabled: presence gate only",
    ]
    for i, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (x0 + 14, y0 + 28 + i * 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255) if i != 0 else (210, 255, 210),
            2 if i == 0 else 1,
            cv2.LINE_AA,
        )
    cv2.rectangle(frame, (x0, y0), (x0 + panel_w, y0 + panel_h), (255, 255, 255), 1)


def annotate_frame(
    frame: np.ndarray,
    per_frame: dict[str, Any],
    driver_info: dict[str, Any],
    video: str,
    frame_idx: int,
    timestamp: float,
    scale: float,
) -> np.ndarray:
    out = frame.copy()
    height, width = out.shape[:2]

    vehicle_box = scaled_box(per_frame.get("vehicle_bbox_xyxy") or [], scale)
    cabin_box = scaled_box(per_frame.get("cabin_bbox_xyxy") or [], scale)

    if len(vehicle_box) == 4:
        x1, y1, x2, y2 = clamp_box(vehicle_box, width, height)
        cv2.rectangle(out, (x1, y1), (x2, y2), (180, 180, 180), 2)
        draw_label(out, "target vehicle", (x1 + 6, max(26, y1 + 24)), (220, 220, 220))

    if len(cabin_box) == 4:
        x1, y1, x2, y2 = clamp_box(cabin_box, width, height)
        cv2.rectangle(out, (x1, y1), (x2, y2), (255, 210, 80), 2)
        draw_label(out, "cabin ROI", (x1 + 6, max(26, y1 + 24)), (255, 230, 120))

    cabin_unscaled = per_frame.get("cabin_bbox_xyxy") or []
    driver_idx = per_frame.get("driver_face_index")
    faces = per_frame.get("faces") or []
    for idx, face in enumerate(faces):
        face_global = face_box_to_global(cabin_unscaled, face)
        face_global = scaled_box(face_global, scale)
        x1, y1, x2, y2 = clamp_box(face_global, width, height)
        is_driver = idx == driver_idx and per_frame.get("driver_candidate_detected") is True
        color = (90, 255, 120) if is_driver else (190, 190, 190)
        thickness = 3 if is_driver else 1
        cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)
        label = (
            f"DRIVER conf={float(face.get('confidence', 0.0)):.2f}"
            if is_driver
            else f"occupant conf={float(face.get('confidence', 0.0)):.2f}"
        )
        draw_label(out, label, (x1 + 4, max(26, y1 - 4)), color)
        for point in face.get("keypoints") or []:
            px, py = keypoint_to_global(cabin_unscaled, point)
            cv2.circle(out, (int(round(px * scale)), int(round(py * scale))), 2, color, -1)

    status_text = (
        f"frame_status={per_frame.get('visibility')} "
        f"driver_frame={per_frame.get('driver_candidate_detected')} "
        f"role={per_frame.get('role_assignment_status')}"
    )
    draw_label(out, status_text, (18, out.shape[0] - 24), (255, 255, 255), scale=0.52)
    draw_panel(out, video, driver_info, frame_idx, timestamp)
    return out


def render_video(
    video_summary: dict[str, Any],
    driver_info: dict[str, Any],
    video_path: Path,
    output_path: Path,
    output_width: int,
) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    writer: cv2.VideoWriter | None = None
    frame_lookup = {int(item["frame"]): item for item in video_summary.get("per_frame", [])}
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frame_idx = 0
    rendered = 0
    annotated = 0
    last_meta: dict[str, Any] | None = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        frame, scale = scale_frame_and_meta(frame, video_summary.get("frame_meta") or {}, output_width)
        if writer is None:
            writer = cv2.VideoWriter(
                str(output_path),
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (frame.shape[1], frame.shape[0]),
            )
            if not writer.isOpened():
                raise RuntimeError(f"Could not create output video: {output_path}")
        meta = frame_lookup.get(frame_idx)
        if meta is not None:
            last_meta = meta
        if last_meta is not None:
            frame = annotate_frame(
                frame,
                last_meta,
                driver_info,
                video_path.name,
                frame_idx,
                frame_idx / fps if fps else 0.0,
                scale,
            )
            annotated += 1
        writer.write(frame)
        rendered += 1

    cap.release()
    if writer is not None:
        writer.release()
    return {
        "video": video_path.name,
        "output_video": rel(output_path),
        "source_resolution": f"{source_width}x{source_height}",
        "fps": round(fps, 3),
        "rendered_frames": rendered,
        "annotated_frames": annotated,
    }


def main() -> None:
    args = parse_args()
    cabin_summary = load_json(args.cabin_summary.resolve())
    driver_summary = load_json(args.driver_summary.resolve())
    driver_by_video = {
        str(item["video"]): item["driver_detection"]
        for item in driver_summary.get("videos", [])
        if item.get("video")
    }

    outputs = []
    for video_summary in cabin_summary.get("videos", []):
        video = str(video_summary.get("video") or "")
        if not video:
            continue
        video_path = args.videos_dir / video
        if not video_path.exists():
            print(f"Skipping missing video: {video_path}")
            continue
        output_path = args.runs_dir / "annotated" / f"{Path(video).stem}_driver_detection.mp4"
        outputs.append(
            render_video(
                video_summary,
                driver_by_video.get(video, {}),
                video_path,
                output_path,
                args.output_width,
            )
        )

    manifest_path = args.runs_dir / "driver_detection_overlay_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "experiment_name": EXPERIMENT_NAME,
        "source_cabin_summary": rel(args.cabin_summary.resolve()),
        "source_driver_summary": rel(args.driver_summary.resolve()),
        "outputs": outputs,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest: {manifest_path}")
    for item in outputs:
        print(f"Wrote video: {ROOT / item['output_video']}")


if __name__ == "__main__":
    main()
