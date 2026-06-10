#!/usr/bin/env python3
"""Extract target vehicle ROI crops for the Plate/OCR MVP.

This script consumes `target_vehicle_selected` event skeletons, opens the raw
test videos, crops the selected target vehicle at its best frame, and writes
small metadata artifacts for the next plate detection/OCR stage.
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


def crop_for_event(
    event: dict[str, Any],
    videos_dir: Path,
    runs_dir: Path,
    padding_ratio: float,
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
    padded, clamped = padded_clamped_bbox(bbox, width, height, padding_ratio)
    x1, y1, x2, y2 = clamped
    if x2 <= x1 or y2 <= y1:
        base_record["vehicle_bbox_xyxy_padded"] = padded
        base_record["vehicle_bbox_xyxy_clamped"] = clamped
        base_record["failure_reason"] = "invalid_clamped_bbox"
        return base_record

    crop = frame[y1:y2, x1:x2]
    crop_h, crop_w = crop.shape[:2]
    safe_event_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in event_id)
    output_path = runs_dir / f"{safe_event_id}_{track_id}_frame_{int(best_frame):06d}_target_roi.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(output_path), crop, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        base_record["failure_reason"] = "crop_write_failed"
        return base_record

    base_record.update(
        {
            "vehicle_bbox_xyxy_padded": padded,
            "vehicle_bbox_xyxy_clamped": clamped,
            "vehicle_crop_uri": rel(output_path),
            "crop_width": int(crop_w),
            "crop_height": int(crop_h),
            "crop_area_px": int(crop_w * crop_h),
            "status": "created",
            "failure_reason": None,
        }
    )
    return base_record


def build_report(summary: dict[str, Any]) -> str:
    rows = [
        "| Event ID | Video | Track | Best Frame | Status | Crop Size | Crop URI |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for crop in summary["crops"]:
        crop_size = f"{crop['crop_width']}x{crop['crop_height']}" if crop["status"] == "created" else "-"
        rows.append(
            "| {event_id} | {video} | {track_id} | {best_frame} | {status} | {crop_size} | `{uri}` |".format(
                event_id=crop["event_id"],
                video=crop["video"],
                track_id=crop["track_id"],
                best_frame=crop["best_frame"],
                status=crop["status"],
                crop_size=crop_size,
                uri=crop["vehicle_crop_uri"] or crop["failure_reason"],
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
* Başarısız crop sayısı: `{summary['failed_crop_count']}`

## Crop Listesi

{chr(10).join(rows)}

## Notlar

* Crop görselleri `runs/` altında kaldığı için Git'e eklenmez.
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
        )
        for event in events
    ]
    created = [crop for crop in crops if crop["status"] == "created"]
    failed = [crop for crop in crops if crop["status"] != "created"]

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
        "event_count": len(events),
        "created_crop_count": len(created),
        "failed_crop_count": len(failed),
        "crops": crops,
        "manual_review_template": "testing/templates/manual_plate_ocr_review.csv",
        "notes": [
            "This is not plate detection or OCR.",
            "Crop images are stored under ignored runs/ paths and must not be committed.",
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
                "failed_crop_count": len(failed),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
