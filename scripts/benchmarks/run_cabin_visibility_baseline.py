#!/usr/bin/env python3
"""Run cabin visibility and occupant face-detection baselines.

The script reconnects each enriched event to the same target vehicle using
YOLO11n + ByteTrack, extracts a view-profile-aware cabin ROI, applies a cheap
visibility gate, and runs the selected face detector only on usable ROIs.

Large crops and annotated videos stay under ignored ``runs/`` paths. Small
JSON and Markdown summaries are written to tracked benchmark locations.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from ultralytics import YOLO

try:
    from cabin_utils import (
        assign_driver_candidate,
        cabin_roi_bbox,
        iou,
        mean,
        p95,
        temporal_cabin_summary,
        visibility_decision,
    )
except ImportError:
    from scripts.benchmarks.cabin_utils import (
        assign_driver_candidate,
        cabin_roi_bbox,
        iou,
        mean,
        p95,
        temporal_cabin_summary,
        visibility_decision,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json"
)
DEFAULT_VIEW_PROFILES = (
    ROOT / "architecture" / "contracts" / "cabin_view_profiles.example.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_VEHICLE_MODEL = ROOT / "yolo11n.pt"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "cabin"
DEFAULT_FULL_RANGE_MODEL = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin"
    / "blaze_face_full_range.tflite"
)
DEFAULT_SHORT_RANGE_MODEL = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin"
    / "blaze_face_short_range.tflite"
)
DEFAULT_YUNET_MODEL = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin"
    / "face_detection_yunet_2026may.onnx"
)

VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
EXPERIMENTS = {
    "CABIN-EXP-001": {
        "model_key": "blazeface_full_range",
        "model_path": DEFAULT_FULL_RANGE_MODEL,
        "backend": "mediapipe",
        "run_on_poor": False,
        "decision": "primary_external_camera_baseline",
    },
    "CABIN-EXP-002": {
        "model_key": "blazeface_short_range",
        "model_path": DEFAULT_SHORT_RANGE_MODEL,
        "backend": "mediapipe",
        "run_on_poor": False,
        "decision": "short_range_challenger",
    },
    "CABIN-EXP-004": {
        "model_key": "opencv_yunet_2026may",
        "model_path": DEFAULT_YUNET_MODEL,
        "backend": "yunet",
        "run_on_poor": True,
        "decision": "small_distant_multi_face_challenger",
    },
}


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_target_specs(events_path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(events_path)
    specs: dict[str, dict[str, Any]] = {}
    for event in data.get("events", []):
        source = event.get("source") or {}
        target = event.get("target_vehicle") or {}
        frame_window = target.get("frame_window") or {}
        video = source.get("source_video")
        if not video:
            continue
        specs[str(video)] = {
            "event_id": event.get("event_id"),
            "best_frame": int(frame_window.get("best_frame") or 1),
            "bbox_xyxy": target.get("bbox_xyxy") or target.get("bbox"),
            "track_id_label": target.get("track_id"),
        }
    return specs


def track_video(
    model: Any,
    video_path: Path,
    tracker: str,
    conf: float,
    imgsz: int,
    device: str,
) -> tuple[dict[int, dict[int, dict[str, Any]]], dict[str, Any]]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    tracks: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    frame = 0
    while True:
        ok, image = cap.read()
        if not ok:
            break
        frame += 1
        results = model.track(
            image,
            persist=True,
            tracker=tracker,
            classes=list(VEHICLE_CLASSES),
            conf=conf,
            imgsz=imgsz,
            device=device,
            verbose=False,
        )
        result = results[0]
        boxes = result.boxes
        if boxes is None or not getattr(boxes, "is_track", False) or boxes.id is None:
            continue
        ids = boxes.id.int().cpu().tolist()
        classes = boxes.cls.int().cpu().tolist()
        confidences = boxes.conf.cpu().tolist()
        bboxes = boxes.xyxy.cpu().tolist()
        for track_id, class_id, confidence, bbox in zip(
            ids, classes, confidences, bboxes
        ):
            tracks[int(track_id)][frame] = {
                "bbox_xyxy": [float(value) for value in bbox],
                "confidence": float(confidence),
                "class_name": VEHICLE_CLASSES.get(int(class_id), str(class_id)),
            }
    cap.release()
    return tracks, {
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "frames": frame,
    }


def select_target_track(
    tracks: dict[int, dict[int, dict[str, Any]]],
    spec: dict[str, Any],
) -> tuple[int | None, str]:
    ref_bbox = spec.get("bbox_xyxy")
    best_frame = int(spec.get("best_frame") or 1)
    if ref_bbox:
        matches = []
        for track_id, frames in tracks.items():
            observation = frames.get(best_frame)
            if observation:
                matches.append(
                    (
                        iou(
                            observation["bbox_xyxy"],
                            [float(value) for value in ref_bbox],
                        ),
                        track_id,
                    )
                )
        if matches:
            best_iou, best_track = max(matches)
            if best_iou >= 0.30:
                return best_track, f"iou_match_best_frame={best_iou:.3f}"
    if tracks:
        track_id, frames = max(tracks.items(), key=lambda item: len(item[1]))
        return track_id, f"fallback_longest_track_frames={len(frames)}"
    return None, "no_tracks"


def image_quality_metrics(crop: np.ndarray) -> dict[str, float]:
    if crop.size == 0:
        return {
            "brightness": 0.0,
            "contrast": 0.0,
            "sharpness": 0.0,
            "dark_ratio": 1.0,
            "glare_ratio": 0.0,
            "min_dimension": 0.0,
        }
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return {
        "brightness": round(float(gray.mean()), 3),
        "contrast": round(float(gray.std()), 3),
        "sharpness": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 3),
        "dark_ratio": round(float(np.mean(gray < 40)), 4),
        "glare_ratio": round(float(np.mean(gray > 235)), 4),
        "min_dimension": float(min(crop.shape[:2])),
    }


class MediaPipeFaceDetector:
    def __init__(self, model_path: Path, min_confidence: float) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe is not installed. Run the requirements install command."
            ) from exc
        self.mp = mp
        options = mp.tasks.vision.FaceDetectorOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            min_detection_confidence=min_confidence,
        )
        self.detector = mp.tasks.vision.FaceDetector.create_from_options(options)

    def close(self) -> None:
        self.detector.close()

    def detect(self, crop_bgr: np.ndarray, timestamp_ms: int) -> list[dict[str, Any]]:
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        image = self.mp.Image(
            image_format=self.mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb),
        )
        result = self.detector.detect_for_video(image, timestamp_ms)
        faces = []
        for detection in result.detections:
            bbox = detection.bounding_box
            category = detection.categories[0] if detection.categories else None
            faces.append(
                {
                    "bbox": [
                        int(bbox.origin_x),
                        int(bbox.origin_y),
                        int(bbox.width),
                        int(bbox.height),
                    ],
                    "confidence": round(float(category.score if category else 0.0), 4),
                    "keypoints": [
                        {
                            "x": round(float(point.x), 5),
                            "y": round(float(point.y), 5),
                        }
                        for point in detection.keypoints
                    ],
                }
            )
        return faces


class YuNetFaceDetector:
    def __init__(self, model_path: Path, min_confidence: float) -> None:
        if not hasattr(cv2, "FaceDetectorYN"):
            raise RuntimeError(
                "This OpenCV build does not include FaceDetectorYN support."
            )
        self.detector = cv2.FaceDetectorYN.create(
            str(model_path),
            "",
            (320, 320),
            float(min_confidence),
            0.30,
            5000,
        )

    def close(self) -> None:
        return None

    def detect(self, crop_bgr: np.ndarray, timestamp_ms: int) -> list[dict[str, Any]]:
        del timestamp_ms
        height, width = crop_bgr.shape[:2]
        self.detector.setInputSize((width, height))
        _, detections = self.detector.detect(crop_bgr)
        if detections is None:
            return []

        faces = []
        for detection in detections:
            x, y, bbox_width, bbox_height = detection[:4]
            keypoint_values = detection[4:14]
            faces.append(
                {
                    "bbox": [
                        int(round(float(x))),
                        int(round(float(y))),
                        int(round(float(bbox_width))),
                        int(round(float(bbox_height))),
                    ],
                    "confidence": round(float(detection[14]), 4),
                    "keypoints": [
                        {
                            "x": round(
                                float(keypoint_values[index]) / max(width, 1), 5
                            ),
                            "y": round(
                                float(keypoint_values[index + 1]) / max(height, 1), 5
                            ),
                        }
                        for index in range(0, 10, 2)
                    ],
                }
            )
        return faces


def create_face_detector(
    backend: str,
    model_path: Path,
    min_confidence: float,
) -> MediaPipeFaceDetector | YuNetFaceDetector:
    if backend == "mediapipe":
        return MediaPipeFaceDetector(model_path, min_confidence)
    if backend == "yunet":
        return YuNetFaceDetector(model_path, min_confidence)
    raise ValueError(f"Unsupported face detector backend: {backend}")


def draw_label(
    frame: np.ndarray,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )


def profile_for_video(
    profiles: dict[str, Any], video_name: str
) -> tuple[str, dict[str, Any]]:
    profile_name = (profiles.get("video_profiles") or {}).get(
        video_name, profiles.get("default_profile", "unknown")
    )
    profile = (profiles.get("profiles") or {}).get(profile_name)
    if not profile:
        profile_name = "unknown"
        profile = (profiles.get("profiles") or {}).get("unknown", {})
    return str(profile_name), profile


def process_video(
    video_path: Path,
    spec: dict[str, Any],
    vehicle_model: Any,
    face_model_path: Path,
    model_key: str,
    face_backend: str,
    run_on_poor: bool,
    profiles: dict[str, Any],
    args: argparse.Namespace,
    device: str,
) -> dict[str, Any]:
    print(f"\n=== {video_path.name}: target tracking ===")
    tracks, frame_meta = track_video(
        vehicle_model,
        video_path,
        args.tracker,
        args.conf,
        args.imgsz,
        device,
    )
    target_track, selection_reason = select_target_track(tracks, spec)
    if target_track is None:
        return {
            "video": video_path.name,
            "status": "failed",
            "failure_reason": "target_track_not_found",
            "frame_meta": frame_meta,
        }

    profile_name, profile = profile_for_video(profiles, video_path.name)
    all_target_frames = sorted(tracks[target_track])
    processed_frames = all_target_frames[:: max(1, args.frame_stride)]
    run_set = set(processed_frames)
    target_set = set(all_target_frames)
    print(
        f"target={target_track} ({selection_reason}), profile={profile_name}, "
        f"processed={len(processed_frames)} stride={args.frame_stride}"
    )

    experiment_runs = args.runs_root / args.experiment.lower().replace("-", "_")
    roi_dir = experiment_runs / "rois" / video_path.stem
    annotated_dir = experiment_runs / "annotated"
    roi_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)
    annotated_path = annotated_dir / f"{video_path.stem}_{model_key}.mp4"

    output_width = max(1, int(frame_meta["width"] * args.video_scale))
    output_height = max(1, int(frame_meta["height"] * args.video_scale))
    writer = cv2.VideoWriter(
        str(annotated_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(frame_meta["fps"]),
        (output_width, output_height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not create annotated video: {annotated_path}")

    face_detector = create_face_detector(
        face_backend,
        face_model_path,
        args.face_conf,
    )
    cap = cv2.VideoCapture(str(video_path))
    frame_number = 0
    frame_results: list[dict[str, Any]] = []
    latencies: list[float] = []
    last_overlay: dict[str, Any] | None = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            if frame_number in target_set:
                clean_frame = frame.copy()
                vehicle_bbox = tracks[target_track][frame_number]["bbox_xyxy"]
                vx1, vy1, vx2, vy2 = [int(round(value)) for value in vehicle_bbox]
                cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), (255, 255, 255), 2)
                draw_label(
                    frame,
                    f"target TRK-{target_track:03d}",
                    (vx1, max(24, vy1 - 8)),
                    (255, 255, 255),
                )
                if frame_number in run_set:
                    rx1, ry1, rx2, ry2 = cabin_roi_bbox(
                        vehicle_bbox,
                        frame_meta["width"],
                        frame_meta["height"],
                        profile,
                    )
                    crop = clean_frame[ry1:ry2, rx1:rx2].copy()
                    metrics = image_quality_metrics(crop)
                    visibility_score, visibility, visibility_reasons = (
                        visibility_decision(metrics)
                    )
                    faces: list[dict[str, Any]] = []
                    face_latency = 0.0
                    detector_allowed = visibility in {"good", "limited"} or (
                        run_on_poor and visibility == "poor"
                    )
                    if detector_allowed:
                        started = time.perf_counter()
                        faces = face_detector.detect(
                            crop,
                            int(frame_number / max(frame_meta["fps"], 1.0) * 1000),
                        )
                        face_latency = (time.perf_counter() - started) * 1000.0
                        latencies.append(face_latency)

                    driver_index, role_status = assign_driver_candidate(
                        faces, profile_name, max(1, rx2 - rx1)
                    )
                    driver_candidate = None
                    if role_status.startswith("assigned_"):
                        driver_candidate = driver_index is not None

                    roi_path = roi_dir / f"frame_{frame_number:06d}_cabin.jpg"
                    cv2.imwrite(
                        str(roi_path),
                        crop,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 95],
                    )
                    record = {
                        "frame": frame_number,
                        "vehicle_bbox_xyxy": [
                            round(float(value), 2) for value in vehicle_bbox
                        ],
                        "cabin_bbox_xyxy": [rx1, ry1, rx2, ry2],
                        "view_profile": profile_name,
                        "visibility": visibility,
                        "visibility_score": visibility_score,
                        "visibility_reasons": visibility_reasons,
                        "quality_metrics": metrics,
                        "face_count": len(faces),
                        "max_face_confidence": max(
                            [float(face["confidence"]) for face in faces],
                            default=None,
                        ),
                        "driver_face_index": driver_index,
                        "driver_candidate_detected": driver_candidate,
                        "role_assignment_status": role_status,
                        "face_latency_ms": round(face_latency, 3),
                        "faces": faces,
                        "roi_file": rel(roi_path),
                    }
                    frame_results.append(record)
                    last_overlay = record

                overlay = last_overlay if last_overlay and last_overlay["frame"] == frame_number else None
                if overlay:
                    rx1, ry1, rx2, ry2 = overlay["cabin_bbox_xyxy"]
                    visibility = overlay["visibility"]
                    color = {
                        "good": (0, 220, 0),
                        "limited": (0, 200, 255),
                        "poor": (0, 90, 255),
                        "not_visible": (0, 0, 255),
                    }[visibility]
                    cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), color, 2)
                    draw_label(
                        frame,
                        f"cabin {visibility} {overlay['visibility_score']:.2f}",
                        (rx1, max(24, ry1 - 8)),
                        color,
                    )
                    for index, face in enumerate(overlay["faces"]):
                        x, y, width, height = face["bbox"]
                        fx1, fy1 = rx1 + x, ry1 + y
                        fx2, fy2 = fx1 + width, fy1 + height
                        face_color = (
                            (255, 0, 255)
                            if index == overlay["driver_face_index"]
                            else (255, 180, 0)
                        )
                        cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), face_color, 2)
                        role = "driver" if index == overlay["driver_face_index"] else "face"
                        draw_label(
                            frame,
                            f"{role} {face['confidence']:.2f}",
                            (fx1, max(24, fy1 - 6)),
                            face_color,
                        )
                elif args.frame_stride > 1:
                    draw_label(
                        frame,
                        f"cabin not sampled (stride={args.frame_stride})",
                        (vx1, min(frame_meta["height"] - 12, vy2 + 28)),
                        (0, 165, 255),
                    )

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
        face_detector.close()

    temporal = temporal_cabin_summary(
        frame_results,
        min_driver_frames=args.min_driver_frames,
        min_driver_rate=args.min_driver_rate,
    )
    reason_counts: dict[str, int] = defaultdict(int)
    for item in frame_results:
        for reason in item.get("visibility_reasons") or []:
            reason_counts[str(reason)] += 1

    return {
        "video": video_path.name,
        "event_id": spec.get("event_id"),
        "status": "completed",
        "failure_reason": None,
        "target_track_id": target_track,
        "target_track_label": spec.get("track_id_label"),
        "target_selection_reason": selection_reason,
        "target_track_frame_count": len(all_target_frames),
        "processed_frame_count": len(frame_results),
        "frame_stride": args.frame_stride,
        "view_profile": profile_name,
        "frame_meta": frame_meta,
        "model_key": model_key,
        "face_backend": face_backend,
        "run_on_poor": run_on_poor,
        "model_path": rel(face_model_path),
        "mean_face_latency_ms": mean(latencies),
        "p95_face_latency_ms": p95(latencies),
        "visibility_reason_counts": dict(sorted(reason_counts.items())),
        "temporal": temporal,
        "annotated_video": rel(annotated_path),
        "roi_dir": rel(roi_dir),
        "per_frame": frame_results,
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = []
    for video in summary.get("videos", []):
        temporal = video.get("temporal") or {}
        rows.append(
            "| {video} | {profile} | {processed} | {visibility} | {visible_rate} | "
            "{face_rate} | {occupants} | {driver} | {mean_latency} | {p95_latency} |".format(
                video=video.get("video"),
                profile=video.get("view_profile"),
                processed=video.get("processed_frame_count"),
                visibility=temporal.get("visibility"),
                visible_rate=temporal.get("visible_frame_rate"),
                face_rate=temporal.get("temporal_detection_rate"),
                occupants=temporal.get("occupant_count_estimate"),
                driver=temporal.get("driver_candidate_detected"),
                mean_latency=video.get("mean_face_latency_ms"),
                p95_latency=video.get("p95_face_latency_ms"),
            )
        )
    return "\n".join(
        [
            f"# {summary['experiment_id']} Cabin Visibility + Driver Baseline",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            "## Amaç",
            "",
            "Hedef araç ROI içinde cabin görünürlüğünü ölçmek, yalnız görünürlük yeterliyse "
            "yüz/occupant tespiti çalıştırmak ve temporal driver candidate kararı üretmek.",
            "",
            "## Konfigürasyon",
            "",
            f"* Face model: `{summary['model_key']}`",
            f"* Model path: `{summary['model_path']}`",
            f"* Input events: `{summary['input_events']}`",
            f"* Frame stride: `{summary['frame_stride']}`",
            f"* Face confidence: `{summary['face_confidence']}`",
            "",
            "## Sonuç",
            "",
            "| Video | View Profile | Kare | Visibility | Görünür Kare Oranı | "
            "Yüz Tespit Oranı | Occupant | Driver | Mean ms | P95 ms |",
            "|---|---|---:|---|---:|---:|---:|---|---:|---:|",
            *rows,
            "",
            "## Sınırlar",
            "",
            "* Telefon, kemer ve sigara bu deneyde çalıştırılmaz.",
            "* Occupant varlığı risk skorunu yükseltmez.",
            "* Driver rolü yalnız açık view-profile politikasıyla atanır.",
            "* Ground truth olmadığı için sonuçlar manuel review ile doğrulanmalıdır.",
            "",
            "## Manuel Review",
            "",
            "* Şablon: `testing/templates/manual_cabin_review.csv`",
            "* Crop ve overlay videoları `runs/cabin/` altında, Git dışındadır.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cabin visibility + MediaPipe face baseline."
    )
    parser.add_argument(
        "--experiment",
        choices=sorted(EXPERIMENTS),
        default="CABIN-EXP-001",
    )
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--view-profiles", type=Path, default=DEFAULT_VIEW_PROFILES)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--vehicle-model", type=Path, default=DEFAULT_VEHICLE_MODEL)
    parser.add_argument("--face-model", type=Path)
    parser.add_argument("--tracker", default="bytetrack.yaml")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--face-conf", type=float, default=0.50)
    parser.add_argument("--min-driver-frames", type=int, default=3)
    parser.add_argument("--min-driver-rate", type=float, default=0.30)
    parser.add_argument("--video-scale", type=float, default=0.50)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    experiment = EXPERIMENTS[args.experiment]
    face_model_path = (args.face_model or experiment["model_path"]).resolve()
    if not face_model_path.exists():
        raise SystemExit(
            f"Face model not found: {face_model_path}\n"
            "Download it using research/08_cabin_risk/RUN_CABIN_BASELINE.md."
        )
    for required in (
        args.events.resolve(),
        args.view_profiles.resolve(),
        args.vehicle_model.resolve(),
    ):
        if not required.exists():
            raise SystemExit(f"Required input not found: {required}")

    device = resolve_device(args.device)
    specs = load_target_specs(args.events.resolve())
    profiles = load_json(args.view_profiles.resolve())
    video_paths = (
        [path.resolve() for path in args.videos]
        if args.videos
        else [
            (args.videos_dir / video_name).resolve()
            for video_name in specs
        ]
    )
    missing = [path for path in video_paths if not path.exists()]
    if missing:
        raise SystemExit(f"Missing videos: {', '.join(str(path) for path in missing)}")

    video_results = []
    for video_path in video_paths:
        spec = specs.get(video_path.name)
        if not spec:
            video_results.append(
                {
                    "video": video_path.name,
                    "status": "skipped",
                    "failure_reason": "event_spec_not_found",
                }
            )
            continue
        video_results.append(
            process_video(
                video_path,
                spec,
                YOLO(str(args.vehicle_model.resolve())),
                face_model_path,
                experiment["model_key"],
                experiment["backend"],
                bool(experiment.get("run_on_poor")),
                profiles,
                args,
                device,
            )
        )

    completed = [item for item in video_results if item.get("status") == "completed"]
    summary = {
        "experiment_id": args.experiment,
        "stage": "cabin_visibility_driver_baseline",
        "created_at_utc": now_utc(),
        "decision": experiment["decision"],
        "input_events": rel(args.events),
        "view_profiles": rel(args.view_profiles),
        "vehicle_model": rel(args.vehicle_model),
        "tracker": args.tracker,
        "device": device,
        "model_key": experiment["model_key"],
        "face_backend": experiment["backend"],
        "run_on_poor": bool(experiment.get("run_on_poor")),
        "model_path": rel(face_model_path),
        "frame_stride": args.frame_stride,
        "face_confidence": args.face_conf,
        "phone_risk_status": "not_run",
        "seatbelt_status": "unknown",
        "manual_review_template": "testing/templates/manual_cabin_review.csv",
        "aggregate": {
            "video_count": len(video_results),
            "completed_video_count": len(completed),
            "processed_frame_count": sum(
                int(item.get("processed_frame_count") or 0) for item in completed
            ),
            "mean_face_latency_ms": mean(
                [
                    float(item["mean_face_latency_ms"])
                    for item in completed
                    if item.get("mean_face_latency_ms") is not None
                ]
            ),
            "driver_detected_video_count": sum(
                1
                for item in completed
                if (item.get("temporal") or {}).get("driver_candidate_detected") is True
            ),
        },
        "videos": video_results,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    output_json = (
        args.artifact_dir
        / f"{args.experiment}-{experiment['model_key']}-summary.json"
    )
    output_report = (
        args.report_dir
        / f"{args.experiment.lower().replace('-', '_')}_cabin_summary.md"
    )
    output_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_report.write_text(build_report(summary) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": rel(output_json),
                "report": rel(output_report),
                "completed_videos": len(completed),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
