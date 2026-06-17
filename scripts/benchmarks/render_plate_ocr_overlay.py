#!/usr/bin/env python3
"""Render OCR overlays onto existing plate-detection annotated videos.

Input:
  * POCR-EXP-002/003/004 summary JSON
  * POCR-EXP-001 detection summary JSON

Output:
  * runs/plate_ocr/POCR-EXP-002-004-ocr/overlay/<engine>/<video>_ocr_overlay.mp4

Bu script OCR'i yeniden calistirmaz. Var olan OCR summary'deki kare bazli sonuclari,
POCR-EXP-001 annotated videolari uzerine overlay olarak yazar.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OCR_SUMMARY = ROOT / "models" / "benchmarks" / "artifacts" / "POCR-EXP-002-paddleocr-summary.json"
DEFAULT_DETECTION_SUMMARY = ROOT / "models" / "benchmarks" / "artifacts" / "POCR-EXP-001-plate-detection-yolo-summary.json"
DEFAULT_OUTPUT_DIR = ROOT / "runs" / "plate_ocr" / "POCR-EXP-002-004-ocr" / "overlay"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_rootish(value: str | Path | None) -> Path:
    if not value:
        return ROOT
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def frame_result_map(video_summary: dict[str, Any]) -> dict[int, dict[str, Any]]:
    per_crop = video_summary.get("per_crop")
    if isinstance(per_crop, list):
        return {int(item["frame"]): item for item in per_crop if item.get("frame") is not None}

    fallback_items: list[dict[str, Any]] = []
    highest = video_summary.get("highest_confidence_result")
    best = video_summary.get("best_frame_result")
    sample_results = video_summary.get("sample_results") or []
    if isinstance(highest, dict) and highest.get("frame") is not None:
        fallback_items.append(highest)
    if isinstance(best, dict) and best.get("frame") is not None:
        fallback_items.append(best)
    for item in sample_results:
        if isinstance(item, dict) and item.get("frame") is not None:
            fallback_items.append(item)
    dedup: dict[int, dict[str, Any]] = {}
    for item in fallback_items:
        dedup[int(item["frame"])] = item
    return dedup


def put_label(frame: Any, text: str, xy: tuple[int, int], color: tuple[int, int, int], scale: float = 0.8) -> None:
    x, y = xy
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
    cv2.rectangle(frame, (x - 8, y - th - 10), (x + tw + 8, y + 8), (0, 0, 0), -1)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2, cv2.LINE_AA)


def render_video(
    video_summary: dict[str, Any],
    detection_video: dict[str, Any],
    engine_key: str,
    output_dir: Path,
) -> dict[str, Any]:
    source_video = resolve_rootish(detection_video.get("annotated_video"))
    if not source_video.exists():
        parent = source_video.parent
        stem = source_video.stem
        candidates = sorted(parent.glob(f"{stem}_*.mp4"))
        if candidates:
            source_video = candidates[0]
        else:
            raise FileNotFoundError(f"Annotated video bulunamadi: {source_video}")

    cap = cv2.VideoCapture(str(source_video))
    if not cap.isOpened():
        raise RuntimeError(f"Video acilamadi: {source_video}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    out_dir = output_dir / engine_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(video_summary['video']).stem}_ocr_overlay.mp4"
    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    by_frame = frame_result_map(video_summary)
    temporal_vote = video_summary.get("temporal_vote") or {}
    current_result: dict[str, Any] | None = None
    frame_num = 0

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        frame_num += 1
        if frame_num in by_frame:
            current_result = by_frame[frame_num]

        vote_text = temporal_vote.get("plate_text") or "N/A"
        vote_conf = temporal_vote.get("vote_confidence")
        put_label(frame, f"{engine_key.upper()} vote: {vote_text}", (24, 40), (0, 255, 255), 0.9)
        if vote_conf is not None:
            put_label(frame, f"vote_conf: {vote_conf}", (24, 76), (0, 255, 255), 0.7)

        if current_result:
            active = frame_num in by_frame
            status_color = (0, 220, 0) if active else (180, 180, 180)
            model_text = current_result.get("normalized_text") or current_result.get("raw_text") or "not_read"
            conf_text = current_result.get("ocr_confidence")
            variant = current_result.get("variant") or "-"
            put_label(frame, f"frame {frame_num} OCR: {model_text}", (24, height - 86), status_color, 0.9)
            put_label(frame, f"conf: {conf_text} | variant: {variant}", (24, height - 50), status_color, 0.7)
        else:
            put_label(frame, f"frame {frame_num} OCR: not_read_yet", (24, height - 50), (0, 120, 255), 0.8)

        writer.write(frame)

    cap.release()
    writer.release()

    return {
        "video": video_summary["video"],
        "source_annotated_video": rel(source_video),
        "output_video": rel(out_path),
        "frames": total_frames,
        "ocr_frames": len(by_frame),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render OCR overlay videos from OCR summary.")
    parser.add_argument("--ocr-summary", type=Path, default=DEFAULT_OCR_SUMMARY)
    parser.add_argument("--detection-summary", type=Path, default=DEFAULT_DETECTION_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ocr_summary = load_json(args.ocr_summary.resolve())
    detection_summary = load_json(args.detection_summary.resolve())

    detection_by_video = {item["video"]: item for item in detection_summary.get("videos", []) if item.get("video")}
    engine_key = ocr_summary.get("ocr_engine") or "ocr"
    rendered = []
    for video_summary in ocr_summary.get("videos", []):
        name = video_summary.get("video")
        detection_video = detection_by_video.get(name)
        if not detection_video:
            continue
        rendered.append(render_video(video_summary, detection_video, engine_key, args.output_dir.resolve()))

    meta = {
        "generated_at_utc": now_utc(),
        "ocr_summary": rel(args.ocr_summary.resolve()),
        "detection_summary": rel(args.detection_summary.resolve()),
        "engine": engine_key,
        "rendered_videos": rendered,
    }
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
