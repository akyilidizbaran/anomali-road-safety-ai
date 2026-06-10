#!/usr/bin/env python3
"""Extract target vehicle ROI crops for the Plate/OCR MVP.

This script consumes `target_vehicle_selected` event skeletons, opens the raw
test videos, crops the selected target vehicle at its best frame, writes
sample ROI crops across the track window, and creates target ROI clips for
manual plate visibility review before the next detector/OCR stage.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "plate_ocr" / "POCR-EXP-001-target-roi-crops"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "pocr_exp_001_target_roi_crops_summary.md"
DEFAULT_SUMMARY_NAME = "POCR-EXP-001-target-roi-crops-summary.json"
DEFAULT_CLIP_SIZE = (960, 540)


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_events(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("events")
    if not isinstance(events, list):
        raise ValueError(f"Expected an `events` list in {path}")
    return events


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)


def padded_clamped_bbox(bbox: list[float], width: int, height: int, padding_ratio: float) -> tuple[list[int], list[int]]:
    if len(bbox) != 4:
        raise ValueError(f"Expected bbox with 4 values, got: {bbox}")
    x1, y1, x2, y2 = [float(v) for v in bbox]
    box_w = max(0.0, x2 - x1)
    box_h = max(0.0, y2 - y1)
    pad_x = box_w * padding_ratio
    pad_y = box_h * padding_ratio

    padded = [
        int(round(x1 - pad_x)),
        int(round(y1 - pad_y)),
        int(round(x2 + pad_x)),
        int(round(y2 + pad_y)),
    ]
    clamped = [
        max(0, min(width, padded[0])),
        max(0, min(height, padded[1])),
        max(0, min(width, padded[2])),
        max(0, min(height, padded[3])),
    ]
    return padded, clamped


def sample_frame_numbers(first_frame: int, last_frame: int, best_frame: int, count: int) -> list[int]:
    first = max(1, int(first_frame))
    last = max(first, int(last_frame))
    count = max(1, int(count))
    if count == 1 or first == last:
        return [max(first, min(last, int(best_frame)))]
    indexes = {round(first + idx * (last - first) / (count - 1)) for idx in range(count)}
    indexes.add(max(first, min(last, int(best_frame))))
    return sorted(indexes)


def bbox_for_frame(event: dict[str, Any], frame_number: int) -> list[float] | None:
    target = event.get("target_vehicle") or {}
    frame_window = target.get("frame_window") or {}
    first = int(frame_window.get("first_frame") or frame_window.get("best_frame") or frame_number)
    last = int(frame_window.get("last_frame") or frame_window.get("best_frame") or frame_number)
    fallback = target.get("bbox_xyxy")
    history = (
        ((event.get("evidence") or {}).get("track_history") or {}).get("bbox_history_sample")
        or []
    )
    if not history:
        return fallback
    if last <= first:
        return history[-1] if history else fallback
    ratio = (int(frame_number) - first) / max(last - first, 1)
    idx = round(max(0.0, min(1.0, ratio)) * (len(history) - 1))
    return history[idx]


def read_frame(video_path: Path, frame_number_1_based: int) -> tuple[Any | None, dict[str, Any]]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None, {"opened": False, "failure_reason": "video_open_failed"}

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    frame_number_1_based = max(1, int(frame_number_1_based))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number_1_based - 1)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None, {
            "opened": True,
            "failure_reason": "frame_read_failed",
            "source_width": width,
            "source_height": height,
            "fps": fps,
            "frame_count": frame_count,
        }
    return frame, {
        "opened": True,
        "failure_reason": None,
        "source_width": width,
        "source_height": height,
        "fps": fps,
        "frame_count": frame_count,
    }


def write_crop_from_frame(
    frame: Any,
    bbox: list[float],
    output_path: Path,
    padding_ratio: float,
) -> dict[str, Any]:
    height, width = frame.shape[:2]
    padded, clamped = padded_clamped_bbox(bbox, width, height, padding_ratio)
    x1, y1, x2, y2 = clamped
    if x2 <= x1 or y2 <= y1:
        return {
            "status": "failed",
            "failure_reason": "invalid_clamped_bbox",
            "padded_bbox": padded,
            "clamped_bbox": clamped,
            "crop_width": 0,
            "crop_height": 0,
            "crop_area_px": 0,
            "uri": None,
        }
    crop = frame[y1:y2, x1:x2]
    crop_h, crop_w = crop.shape[:2]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(output_path), crop, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        return {
            "status": "failed",
            "failure_reason": "crop_write_failed",
            "padded_bbox": padded,
            "clamped_bbox": clamped,
            "crop_width": 0,
            "crop_height": 0,
            "crop_area_px": 0,
            "uri": None,
        }
    return {
        "status": "created",
        "failure_reason": None,
        "padded_bbox": padded,
        "clamped_bbox": clamped,
        "crop_width": int(crop_w),
        "crop_height": int(crop_h),
        "crop_area_px": int(crop_w * crop_h),
        "uri": rel(output_path),
    }


def write_sample_crops(
    event: dict[str, Any],
    video_path: Path,
    runs_dir: Path,
    padding_ratio: float,
    sample_count: int,
) -> list[dict[str, Any]]:
    event_id = event.get("event_id", "unknown_event")
    target = event.get("target_vehicle") or {}
    track_id = target.get("track_id")
    frame_window = target.get("frame_window") or {}
    best_frame = int(frame_window.get("best_frame") or 1)
    first_frame = int(frame_window.get("first_frame") or best_frame)
    last_frame = int(frame_window.get("last_frame") or best_frame)
    samples = []
    for frame_number in sample_frame_numbers(first_frame, last_frame, best_frame, sample_count):
        frame, meta = read_frame(video_path, frame_number)
        if frame is None:
            samples.append(
                {
                    "frame": frame_number,
                    "status": "failed",
                    "failure_reason": meta.get("failure_reason", "frame_unavailable"),
                    "vehicle_crop_uri": None,
                }
            )
            continue
        bbox = bbox_for_frame(event, frame_number)
        if not bbox:
            samples.append(
                {
                    "frame": frame_number,
                    "status": "failed",
                    "failure_reason": "missing_bbox_for_sample_frame",
                    "vehicle_crop_uri": None,
                }
            )
            continue
        output_path = (
            runs_dir
            / "sample_frames"
            / f"{safe_name(event_id)}_{track_id}_frame_{frame_number:06d}_target_roi.jpg"
        )
        result = write_crop_from_frame(frame, bbox, output_path, padding_ratio)
        samples.append(
            {
                "frame": frame_number,
                "status": result["status"],
                "failure_reason": result["failure_reason"],
                "vehicle_bbox_xyxy": [round(float(v), 2) for v in bbox],
                "vehicle_bbox_xyxy_clamped": result["clamped_bbox"],
                "vehicle_crop_uri": result["uri"],
                "crop_width": result["crop_width"],
                "crop_height": result["crop_height"],
                "crop_area_px": result["crop_area_px"],
            }
        )
    return samples


def write_roi_clip(
    event: dict[str, Any],
    video_path: Path,
    runs_dir: Path,
    padding_ratio: float,
    clip_fps: float,
    clip_size: tuple[int, int] = DEFAULT_CLIP_SIZE,
) -> dict[str, Any]:
    event_id = event.get("event_id", "unknown_event")
    target = event.get("target_vehicle") or {}
    track_id = target.get("track_id")
    frame_window = target.get("frame_window") or {}
    first_frame = int(frame_window.get("first_frame") or frame_window.get("best_frame") or 1)
    last_frame = int(frame_window.get("last_frame") or frame_window.get("best_frame") or first_frame)
    first_frame = max(1, first_frame)
    last_frame = max(first_frame, last_frame)
    output_path = runs_dir / "clips" / f"{safe_name(event_id)}_{track_id}_target_roi_clip.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"status": "failed", "failure_reason": "video_open_failed", "target_roi_clip_uri": None, "clip_frame_count": 0}

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(clip_fps),
        clip_size,
    )
    if not writer.isOpened():
        cap.release()
        return {"status": "failed", "failure_reason": "clip_writer_open_failed", "target_roi_clip_uri": None, "clip_frame_count": 0}

    written = 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, first_frame - 1)
    current_frame = first_frame
    while current_frame <= last_frame:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        bbox = bbox_for_frame(event, current_frame)
        if bbox:
            height, width = frame.shape[:2]
            _, clamped = padded_clamped_bbox(bbox, width, height, padding_ratio)
            x1, y1, x2, y2 = clamped
            if x2 > x1 and y2 > y1:
                crop = frame[y1:y2, x1:x2]
                resized = cv2.resize(crop, clip_size, interpolation=cv2.INTER_AREA)
                writer.write(resized)
                written += 1
        current_frame += 1

    cap.release()
    writer.release()
    if written == 0:
        return {"status": "failed", "failure_reason": "no_clip_frames_written", "target_roi_clip_uri": None, "clip_frame_count": 0}
    return {
        "status": "created",
        "failure_reason": None,
        "target_roi_clip_uri": rel(output_path),
        "clip_frame_count": written,
        "clip_fps": float(clip_fps),
        "clip_output_size": f"{clip_size[0]}x{clip_size[1]}",
        "clip_frame_window": {"first_frame": first_frame, "last_frame": last_frame},
    }


def crop_for_event(
    event: dict[str, Any],
    videos_dir: Path,
    runs_dir: Path,
    padding_ratio: float,
    sample_count: int,
    clip_fps: float,
    make_clips: bool,
) -> dict[str, Any]:
    event_id = event.get("event_id", "unknown_event")
    source = event.get("source") or {}
    target = event.get("target_vehicle") or {}
    routing = event.get("routing_decision") or {}
    source_video = source.get("source_video")
    track_id = target.get("track_id")
    frame_window = target.get("frame_window") or {}
    best_frame = frame_window.get("best_frame")
    bbox = target.get("bbox_xyxy")

    base_record = {
        "event_id": event_id,
        "video": source_video,
        "track_id": track_id,
        "best_frame": best_frame,
        "source_resolution": source.get("resolution"),
        "vehicle_bbox_xyxy": bbox,
        "vehicle_bbox_xyxy_padded": None,
        "vehicle_bbox_xyxy_clamped": None,
        "vehicle_crop_uri": None,
        "target_roi_clip_uri": None,
        "clip_frame_count": 0,
        "clip_fps": None,
        "clip_output_size": None,
        "sample_frame_count": 0,
        "sample_crop_count": 0,
        "sample_crops": [],
        "crop_width": 0,
        "crop_height": 0,
        "crop_area_px": 0,
        "track_stability": target.get("track_stability"),
        "selection_score": target.get("selection_score"),
        "condition_profile": routing.get("condition_profile"),
        "status": "failed",
        "failure_reason": None,
    }

    if not source_video:
        base_record["failure_reason"] = "missing_source_video"
        return base_record
    if best_frame is None:
        base_record["failure_reason"] = "missing_best_frame"
        return base_record
    if not bbox:
        base_record["failure_reason"] = "missing_vehicle_bbox"
        return base_record

    video_path = videos_dir / source_video
    if not video_path.exists():
        base_record["failure_reason"] = "video_file_not_found"
        return base_record

    frame, meta = read_frame(video_path, int(best_frame))
    if frame is None:
        base_record["failure_reason"] = meta.get("failure_reason", "frame_unavailable")
        return base_record

    height, width = frame.shape[:2]
    base_record["source_resolution"] = f"{width}x{height}"
    safe_event_id = safe_name(event_id)
    output_path = runs_dir / f"{safe_event_id}_{track_id}_frame_{int(best_frame):06d}_target_roi.jpg"
    result = write_crop_from_frame(frame, bbox, output_path, padding_ratio)
    if result["status"] != "created":
        base_record["vehicle_bbox_xyxy_padded"] = result["padded_bbox"]
        base_record["vehicle_bbox_xyxy_clamped"] = result["clamped_bbox"]
        base_record["failure_reason"] = result["failure_reason"]
        return base_record

    sample_crops = write_sample_crops(event, video_path, runs_dir, padding_ratio, sample_count)
    created_samples = [sample for sample in sample_crops if sample["status"] == "created"]
    clip_record = (
        write_roi_clip(event, video_path, runs_dir, padding_ratio, clip_fps)
        if make_clips
        else {"status": "skipped", "failure_reason": "clip_generation_skipped", "target_roi_clip_uri": None, "clip_frame_count": 0}
    )

    base_record.update(
        {
            "vehicle_bbox_xyxy_padded": result["padded_bbox"],
            "vehicle_bbox_xyxy_clamped": result["clamped_bbox"],
            "vehicle_crop_uri": result["uri"],
            "target_roi_clip_uri": clip_record.get("target_roi_clip_uri"),
            "clip_frame_count": clip_record.get("clip_frame_count", 0),
            "clip_fps": clip_record.get("clip_fps"),
            "clip_output_size": clip_record.get("clip_output_size"),
            "sample_frame_count": len(sample_crops),
            "sample_crop_count": len(created_samples),
            "sample_crops": sample_crops,
            "crop_width": result["crop_width"],
            "crop_height": result["crop_height"],
            "crop_area_px": result["crop_area_px"],
            "status": "created",
            "failure_reason": None,
        }
    )
    return base_record


def build_report(summary: dict[str, Any]) -> str:
    rows = [
        "| Event ID | Video | Track | Best Frame | Status | Best Crop | Samples | Clip Frames | Clip URI |",
        "|---|---|---|---:|---|---:|---:|---:|---|",
    ]
    for crop in summary["crops"]:
        crop_size = f"{crop['crop_width']}x{crop['crop_height']}" if crop["status"] == "created" else "-"
        rows.append(
            "| {event_id} | {video} | {track_id} | {best_frame} | {status} | {crop_size} | {samples} | {clip_frames} | `{clip_uri}` |".format(
                event_id=crop["event_id"],
                video=crop["video"],
                track_id=crop["track_id"],
                best_frame=crop["best_frame"],
                status=crop["status"],
                crop_size=crop_size,
                samples=crop["sample_crop_count"],
                clip_frames=crop["clip_frame_count"],
                clip_uri=crop["target_roi_clip_uri"] or crop["failure_reason"],
            )
        )

    return f"""# POCR-EXP-001 Target ROI Crop Extraction Smoke Test

Tarih: 2026-06-11

## Amaç

Bu çalışma Plate Detection + OCR değildir. Amaç, ByteTrack ile seçilmiş `target_vehicle_selected` event skeleton'larından raw video üzerindeki hedef araç ROI crop'larını üretmek ve sonraki plate detector/OCR modülüne sağlam giriş verisi hazırlamaktır.

## Girdi

* Event skeleton: `{summary['input_events']}`
* Video dizini: `{summary['videos_dir']}`
* Padding ratio: `{summary['padding_ratio']}`

## Çıktı

* Crop dizini: `{summary['runs_dir']}`
* Summary JSON: `{summary['summary_json']}`
* Manual review şablonu: `testing/templates/manual_plate_ocr_review.csv`

## Sonuç

* Event sayısı: `{summary['event_count']}`
* Üretilen crop sayısı: `{summary['created_crop_count']}`
* Üretilen sample crop sayısı: `{summary['created_sample_crop_count']}`
* Üretilen target ROI clip sayısı: `{summary['created_clip_count']}`
* Başarısız crop sayısı: `{summary['failed_crop_count']}`

## Crop Listesi

{chr(10).join(rows)}

## Notlar

* Crop görselleri `runs/` altında kaldığı için Git'e eklenmez.
* Target ROI clip videoları `runs/` altında kaldığı için Git'e eklenmez.
* Bu aşama final plaka okuma doğruluğu iddiası kurmaz.
* Plate visibility ve OCR başarısı bu script tarafından değerlendirilmez; bunlar manual review ve sonraki plate detector/OCR koşularında işaretlenecektir.
* Sonraki adım `POCR-EXP-001` plate detector smoke test'idir.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--padding-ratio", type=float, default=0.08)
    parser.add_argument("--sample-count", type=int, default=12)
    parser.add_argument("--clip-fps", type=float, default=12.0)
    parser.add_argument("--skip-clips", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events_path = args.events.resolve()
    videos_dir = args.videos_dir.resolve()
    runs_dir = args.runs_dir.resolve()
    artifact_dir = args.artifact_dir.resolve()
    report_path = args.report.resolve()

    events = load_events(events_path)
    crops = [
        crop_for_event(
            event=event,
            videos_dir=videos_dir,
            runs_dir=runs_dir,
            padding_ratio=args.padding_ratio,
            sample_count=args.sample_count,
            clip_fps=args.clip_fps,
            make_clips=not args.skip_clips,
        )
        for event in events
    ]
    created = [crop for crop in crops if crop["status"] == "created"]
    failed = [crop for crop in crops if crop["status"] != "created"]
    created_sample_count = sum(crop.get("sample_crop_count", 0) for crop in crops)
    created_clip_count = sum(1 for crop in crops if crop.get("target_roi_clip_uri"))

    summary_path = artifact_dir / DEFAULT_SUMMARY_NAME
    summary = {
        "experiment_id": "POCR-EXP-001",
        "stage": "target_vehicle_roi_crop_extraction",
        "generated_at_utc": now_utc(),
        "input_events": rel(events_path),
        "videos_dir": rel(videos_dir),
        "runs_dir": rel(runs_dir),
        "summary_json": rel(summary_path),
        "padding_ratio": args.padding_ratio,
        "sample_count": args.sample_count,
        "clip_fps": args.clip_fps,
        "event_count": len(events),
        "created_crop_count": len(created),
        "created_sample_crop_count": created_sample_count,
        "created_clip_count": created_clip_count,
        "failed_crop_count": len(failed),
        "crops": crops,
        "manual_review_template": "testing/templates/manual_plate_ocr_review.csv",
        "notes": [
            "This is not plate detection or OCR.",
            "Crop images and ROI clips are stored under ignored runs/ paths and must not be committed.",
            "The output prepares target vehicle ROI inputs for the next plate detector smoke test.",
        ],
    }

    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(summary), encoding="utf-8")

    print(
        json.dumps(
            {
                "summary": rel(summary_path),
                "report": rel(report_path),
                "runs_dir": rel(runs_dir),
                "event_count": len(events),
                "created_crop_count": len(created),
                "created_sample_crop_count": created_sample_count,
                "created_clip_count": created_clip_count,
                "failed_crop_count": len(failed),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
