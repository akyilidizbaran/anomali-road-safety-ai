#!/usr/bin/env python3
"""CABIN-EXP-012 - cabin/driver runtime foundation smoke pipeline.

This script does not make phone, smoking, seatbelt or violation decisions.
It turns the existing target-vehicle event skeletons into deterministic cabin
runtime inputs:

  target vehicle event -> vehicle ROI -> cabin ROI -> visibility metrics
  -> face/occupant candidates -> driver/torso ROI candidates -> JSON/report

Heavy annotated images are written under runs/ and should not be committed.
Small JSON/Markdown artifacts are kept for review and FTR planning.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed005d.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "cabin" / "CABIN-EXP-012-runtime-foundation"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "cabin_exp_012_runtime_foundation.md"
DEFAULT_SUMMARY_NAME = "CABIN-EXP-012-runtime-foundation-summary.json"
DEFAULT_ENRICHED_EVENTS_NAME = "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-cabin012.json"

EXPERIMENT_ID = "CABIN-EXP-012-runtime-foundation"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def round_or_none(value: float | None, digits: int = 4) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), digits)


def mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(round((len(ordered) - 1) * 0.95))]


def clamp_bbox(bbox: list[float], width: int, height: int, padding_ratio: float = 0.0) -> list[int]:
    x1, y1, x2, y2 = [float(v) for v in bbox]
    pad_x = max(0.0, x2 - x1) * padding_ratio
    pad_y = max(0.0, y2 - y1) * padding_ratio
    x1 -= pad_x
    y1 -= pad_y
    x2 += pad_x
    y2 += pad_y
    return [
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(0, min(width, int(round(x2)))),
        max(0, min(height, int(round(y2)))),
    ]


def bbox_area(bbox: list[int]) -> int:
    return max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])


def infer_view_profile(event: dict[str, Any]) -> str:
    source_video = str(event.get("source", {}).get("source_video", ""))
    if "video_3" in source_video:
        return "front_lhd"
    return "side_driver_window"


def cabin_roi_from_vehicle(vehicle_bbox: list[int], view_profile: str) -> list[int]:
    x1, y1, x2, y2 = vehicle_bbox
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)
    if view_profile == "front_lhd":
        # Front view: windshield/driver cabin is usually upper-middle area.
        return [
            int(round(x1 + 0.18 * w)),
            int(round(y1 + 0.05 * h)),
            int(round(x1 + 0.82 * w)),
            int(round(y1 + 0.55 * h)),
        ]
    # Side driver window view: keep broader upper window/cabin strip.
    return [
        int(round(x1 + 0.03 * w)),
        int(round(y1 + 0.02 * h)),
        int(round(x1 + 0.72 * w)),
        int(round(y1 + 0.58 * h)),
    ]


def analyze_visibility(crop_bgr: Any) -> dict[str, Any]:
    if crop_bgr is None or crop_bgr.size == 0:
        return {
            "status": "not_visible",
            "quality_score": 0.0,
            "brightness_mean": None,
            "contrast_std": None,
            "laplacian_var": None,
            "edge_density": None,
            "failure_reason": "empty_cabin_roi",
        }

    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    contrast = float(gray.std())
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    edges = cv2.Canny(gray, 60, 160)
    edge_density = float((edges > 0).mean())

    brightness_score = min(max(brightness / 90.0, 0.0), 1.0)
    contrast_score = min(max(contrast / 45.0, 0.0), 1.0)
    sharpness_score = min(max(math.log1p(lap_var) / 7.0, 0.0), 1.0)
    edge_score = min(max(edge_density / 0.08, 0.0), 1.0)
    quality = (0.30 * brightness_score) + (0.30 * contrast_score) + (0.25 * sharpness_score) + (0.15 * edge_score)

    if quality >= 0.58:
        status = "good"
        failure_reason = None
    elif quality >= 0.38:
        status = "limited"
        failure_reason = None
    elif quality >= 0.22:
        status = "poor"
        failure_reason = "low_cabin_visibility_quality"
    else:
        status = "not_visible"
        failure_reason = "cabin_not_reliably_visible"

    return {
        "status": status,
        "quality_score": round(quality, 4),
        "brightness_mean": round(brightness, 3),
        "contrast_std": round(contrast, 3),
        "laplacian_var": round(lap_var, 3),
        "edge_density": round(edge_density, 5),
        "failure_reason": failure_reason,
    }


class FaceDetector:
    def __init__(self, yunet_model: Path | None = None) -> None:
        self.mode = "opencv_haar_fallback"
        self.yunet = None
        if yunet_model and yunet_model.exists() and hasattr(cv2, "FaceDetectorYN_create"):
            self.mode = "opencv_yunet"
            self.yunet = cv2.FaceDetectorYN_create(str(yunet_model), "", (320, 320))
        cascade_root = Path(cv2.data.haarcascades)
        self.frontal = cv2.CascadeClassifier(str(cascade_root / "haarcascade_frontalface_default.xml"))
        self.profile = cv2.CascadeClassifier(str(cascade_root / "haarcascade_profileface.xml"))

    def detect(self, crop_bgr: Any) -> tuple[list[dict[str, Any]], float]:
        started = time.perf_counter()
        if crop_bgr is None or crop_bgr.size == 0:
            return [], 0.0
        if self.yunet is not None:
            h, w = crop_bgr.shape[:2]
            self.yunet.setInputSize((w, h))
            _, faces = self.yunet.detect(crop_bgr)
            out = []
            if faces is not None:
                for face in faces:
                    x, y, bw, bh = [float(v) for v in face[:4]]
                    score = float(face[-1])
                    out.append(
                        {
                            "bbox_xyxy": [round(x, 2), round(y, 2), round(x + bw, 2), round(y + bh, 2)],
                            "confidence": round(score, 4),
                            "detector": "opencv_yunet",
                        }
                    )
            return out, (time.perf_counter() - started) * 1000.0

        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces_raw: list[tuple[int, int, int, int, str]] = []
        for cascade, label in [(self.frontal, "haar_frontal"), (self.profile, "haar_profile")]:
            if cascade.empty():
                continue
            detected = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(24, 24))
            for x, y, w, h in detected:
                faces_raw.append((int(x), int(y), int(w), int(h), label))

        deduped: list[dict[str, Any]] = []
        for x, y, w, h, label in sorted(faces_raw, key=lambda item: item[2] * item[3], reverse=True):
            bbox = [float(x), float(y), float(x + w), float(y + h)]
            if any(iou_float(bbox, other["bbox_xyxy"]) > 0.35 for other in deduped):
                continue
            conf = min(0.85, 0.35 + ((w * h) / max(1, crop_bgr.shape[0] * crop_bgr.shape[1])) * 12.0)
            deduped.append(
                {
                    "bbox_xyxy": [round(v, 2) for v in bbox],
                    "confidence": round(conf, 4),
                    "detector": label,
                }
            )
        return deduped, (time.perf_counter() - started) * 1000.0


def iou_float(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def select_driver_face(faces: list[dict[str, Any]], view_profile: str, cabin_width: int) -> dict[str, Any] | None:
    if not faces:
        return None
    if view_profile == "front_lhd":
        # Left-hand-drive assumption. In a front-facing camera, driver usually
        # appears on image-right; keep confidence low because this is geometry-only.
        target_x = 0.68 * cabin_width
        return min(
            faces,
            key=lambda face: abs(((face["bbox_xyxy"][0] + face["bbox_xyxy"][2]) / 2.0) - target_x),
        )
    return max(faces, key=lambda face: (face["bbox_xyxy"][2] - face["bbox_xyxy"][0]) * (face["bbox_xyxy"][3] - face["bbox_xyxy"][1]))


def torso_roi_from_face(face: dict[str, Any] | None, cabin_bbox_global: list[int], vehicle_bbox: list[int]) -> tuple[list[int], str]:
    cx1, cy1, cx2, cy2 = cabin_bbox_global
    vx1, vy1, vx2, vy2 = vehicle_bbox
    if face is None:
        w = vx2 - vx1
        h = vy2 - vy1
        return [
            int(round(vx1 + 0.20 * w)),
            int(round(vy1 + 0.30 * h)),
            int(round(vx1 + 0.78 * w)),
            int(round(vy1 + 0.82 * h)),
        ], "heuristic_no_face"

    fx1, fy1, fx2, fy2 = face["bbox_xyxy"]
    fx1 += cx1
    fx2 += cx1
    fy1 += cy1
    fy2 += cy1
    fw = max(1.0, fx2 - fx1)
    fh = max(1.0, fy2 - fy1)
    center_x = (fx1 + fx2) / 2.0
    return [
        int(round(max(vx1, center_x - 1.65 * fw))),
        int(round(max(cy1, fy2 - 0.15 * fh))),
        int(round(min(vx2, center_x + 1.65 * fw))),
        int(round(min(vy2, fy2 + 3.20 * fh))),
    ], "face_anchored"


def globalize_faces(faces: list[dict[str, Any]], cabin_bbox: list[int]) -> list[dict[str, Any]]:
    xoff, yoff = cabin_bbox[0], cabin_bbox[1]
    out = []
    for face in faces:
        x1, y1, x2, y2 = face["bbox_xyxy"]
        item = dict(face)
        item["bbox_xyxy_global"] = [round(x1 + xoff, 2), round(y1 + yoff, 2), round(x2 + xoff, 2), round(y2 + yoff, 2)]
        out.append(item)
    return out


def sample_frames(first_frame: int, last_frame: int, best_frame: int, step: int, max_frames: int) -> list[int]:
    frames = set(range(first_frame, last_frame + 1, max(1, step)))
    frames.add(best_frame)
    frames.add(first_frame)
    frames.add(last_frame)
    ordered = sorted(frames)
    if max_frames > 0 and len(ordered) > max_frames:
        must_keep = {first_frame, best_frame, last_frame}
        remaining = [f for f in ordered if f not in must_keep]
        stride = max(1, math.ceil(len(remaining) / max(1, max_frames - len(must_keep))))
        ordered = sorted(must_keep | set(remaining[::stride]))
        ordered = ordered[:max_frames]
        if best_frame not in ordered:
            ordered[-1] = best_frame
            ordered = sorted(set(ordered))
    return ordered


def seek_frame(cap: Any, frame_idx: int) -> Any | None:
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(frame_idx)))
    ok, frame = cap.read()
    return frame if ok else None


def draw_overlay(
    frame: Any,
    vehicle_bbox: list[int],
    cabin_bbox: list[int],
    torso_bbox: list[int],
    faces: list[dict[str, Any]],
    label_lines: list[str],
) -> Any:
    out = frame.copy()
    cv2.rectangle(out, (vehicle_bbox[0], vehicle_bbox[1]), (vehicle_bbox[2], vehicle_bbox[3]), (230, 230, 230), 3)
    cv2.rectangle(out, (cabin_bbox[0], cabin_bbox[1]), (cabin_bbox[2], cabin_bbox[3]), (0, 0, 0), 3)
    cv2.rectangle(out, (torso_bbox[0], torso_bbox[1]), (torso_bbox[2], torso_bbox[3]), (80, 80, 80), 2)
    for face in faces:
        x1, y1, x2, y2 = [int(round(v)) for v in face["bbox_xyxy_global"]]
        cv2.rectangle(out, (x1, y1), (x2, y2), (30, 30, 30), 2)

    x, y = 32, 48
    for line in label_lines:
        cv2.putText(out, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 5, cv2.LINE_AA)
        cv2.putText(out, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
        y += 42
    return out


def process_event(
    event: dict[str, Any],
    videos_dir: Path,
    runs_dir: Path,
    face_detector: FaceDetector,
    sample_step: int,
    max_frames_per_event: int,
    padding_ratio: float,
) -> dict[str, Any]:
    source = event.get("source", {})
    target = event.get("target_vehicle", {})
    frame_window = target.get("frame_window", {})
    source_video = source.get("source_video")
    if not source_video:
        return {"event_id": event.get("event_id"), "status": "failed", "failure_reason": "missing_source_video"}

    video_path = videos_dir / str(source_video)
    if not video_path.exists():
        return {
            "event_id": event.get("event_id"),
            "video": source_video,
            "status": "failed",
            "failure_reason": f"video_not_found:{rel(video_path)}",
        }

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"event_id": event.get("event_id"), "video": source_video, "status": "failed", "failure_reason": "video_open_failed"}

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or source.get("fps") or 0.0)
    first_frame = int(frame_window.get("first_frame") or 0)
    last_frame = int(frame_window.get("last_frame") or first_frame)
    best_frame = int(frame_window.get("best_frame") or first_frame)
    frames = sample_frames(first_frame, last_frame, best_frame, sample_step, max_frames_per_event)
    view_profile = infer_view_profile(event)

    event_run_dir = runs_dir / str(Path(str(source_video)).stem)
    event_run_dir.mkdir(parents=True, exist_ok=True)

    frame_results: list[dict[str, Any]] = []
    face_latencies: list[float] = []
    visibility_scores: list[float] = []
    statuses: list[str] = []
    face_detected_count = 0
    occupant_counts: list[int] = []

    for frame_idx in frames:
        frame = seek_frame(cap, frame_idx)
        if frame is None:
            frame_results.append({"frame": frame_idx, "status": "failed", "failure_reason": "frame_read_failed"})
            continue

        vehicle_bbox = clamp_bbox(target.get("bbox_xyxy") or target.get("bbox") or [0, 0, width, height], width, height, padding_ratio)
        cabin_bbox = cabin_roi_from_vehicle(vehicle_bbox, view_profile)
        cabin_bbox = clamp_bbox(cabin_bbox, width, height, 0.0)
        cabin_crop = frame[cabin_bbox[1] : cabin_bbox[3], cabin_bbox[0] : cabin_bbox[2]]

        visibility = analyze_visibility(cabin_crop)
        visibility_scores.append(float(visibility["quality_score"]))
        statuses.append(str(visibility["status"]))

        faces: list[dict[str, Any]] = []
        face_latency_ms = 0.0
        if visibility["status"] in {"good", "limited"}:
            faces, face_latency_ms = face_detector.detect(cabin_crop)
            face_latencies.append(face_latency_ms)
        faces_global = globalize_faces(faces, cabin_bbox)
        if faces:
            face_detected_count += 1
        occupant_counts.append(len(faces))

        driver_face = select_driver_face(faces, view_profile, max(1, cabin_bbox[2] - cabin_bbox[0]))
        torso_bbox, torso_source = torso_roi_from_face(driver_face, cabin_bbox, vehicle_bbox)
        torso_bbox = clamp_bbox(torso_bbox, width, height, 0.0)
        risk_enabled = visibility["status"] in {"good", "limited"} and bool(faces)

        overlay = draw_overlay(
            frame,
            vehicle_bbox,
            cabin_bbox,
            torso_bbox,
            faces_global,
            [
                f"{EXPERIMENT_ID}",
                f"{source_video} frame={frame_idx}",
                f"visibility={visibility['status']} q={visibility['quality_score']}",
                f"faces={len(faces)} risk_enabled={str(risk_enabled).lower()}",
            ],
        )
        overlay_path = event_run_dir / f"frame_{frame_idx:06d}_cabin_overlay.jpg"
        cv2.imwrite(str(overlay_path), overlay, [int(cv2.IMWRITE_JPEG_QUALITY), 88])

        frame_results.append(
            {
                "frame": frame_idx,
                "time_s": round(frame_idx / fps, 3) if fps > 0 else None,
                "status": "ok",
                "view_profile": view_profile,
                "vehicle_bbox_xyxy": vehicle_bbox,
                "cabin_bbox_xyxy": cabin_bbox,
                "torso_bbox_xyxy": torso_bbox,
                "torso_source": torso_source,
                "visibility": visibility,
                "face_detector": face_detector.mode,
                "face_latency_ms": round(face_latency_ms, 3),
                "faces": faces_global,
                "occupant_count_candidate": len(faces),
                "driver_candidate": {
                    "available": driver_face is not None,
                    "source": "largest_or_lhd_geometry_face_candidate" if driver_face else "none",
                    "confidence": round(driver_face["confidence"] * 0.75, 4) if driver_face else None,
                    "bbox_xyxy_global": (
                        globalize_faces([driver_face], cabin_bbox)[0]["bbox_xyxy_global"] if driver_face else None
                    ),
                },
                "risk_gate": {
                    "enabled": risk_enabled,
                    "reason": "visibility_and_face_candidate_available" if risk_enabled else "cabin_foundation_only_or_visibility_insufficient",
                },
                "overlay_uri": rel(overlay_path),
            }
        )

    cap.release()

    ok_frames = [item for item in frame_results if item.get("status") == "ok"]
    visibility_distribution = {status: statuses.count(status) for status in ["good", "limited", "poor", "not_visible"]}
    analysis_ready = visibility_distribution["good"] + visibility_distribution["limited"]
    best_frame_result = min(
        ok_frames,
        key=lambda item: abs(int(item["frame"]) - best_frame),
        default=None,
    )

    return {
        "event_id": event.get("event_id"),
        "video": source_video,
        "status": "ok" if ok_frames else "failed",
        "failure_reason": None if ok_frames else "no_frames_processed",
        "track_id": target.get("track_id"),
        "source_resolution": f"{width}x{height}",
        "fps": round(fps, 3),
        "view_profile": view_profile,
        "frame_window": frame_window,
        "sampled_frames": len(ok_frames),
        "sample_step": sample_step,
        "visibility_distribution": visibility_distribution,
        "analysis_ready_frame_rate": round(analysis_ready / max(1, len(ok_frames)), 4),
        "mean_visibility_quality": round_or_none(mean(visibility_scores)),
        "face_frame_rate": round(face_detected_count / max(1, len(ok_frames)), 4),
        "max_occupant_count_candidate": max(occupant_counts) if occupant_counts else 0,
        "mean_face_latency_ms": round_or_none(mean(face_latencies), 3),
        "p95_face_latency_ms": round_or_none(p95(face_latencies), 3),
        "best_frame_foundation": best_frame_result,
        "frame_results": frame_results,
    }


def enriched_driver_cabin_block(event_summary: dict[str, Any]) -> dict[str, Any]:
    if event_summary.get("status") != "ok":
        return {
            "status": "failed",
            "visibility": "not_visible",
            "driver_detected": None,
            "passenger_count": None,
            "phone_risk": None,
            "seatbelt_status": "unknown",
            "confidence": 0.0,
            "failure_reason": event_summary.get("failure_reason"),
        }

    visibility_distribution = event_summary.get("visibility_distribution") or {}
    best = event_summary.get("best_frame_foundation") or {}
    best_visibility = (best.get("visibility") or {}).get("status")
    max_occupants = int(event_summary.get("max_occupant_count_candidate") or 0)
    face_rate = float(event_summary.get("face_frame_rate") or 0.0)
    ready_rate = float(event_summary.get("analysis_ready_frame_rate") or 0.0)
    confidence = max(0.0, min(1.0, (0.55 * ready_rate) + (0.45 * face_rate)))
    return {
        "status": "foundation_ready",
        "visibility": best_visibility or max(visibility_distribution, key=visibility_distribution.get, default="not_visible"),
        "driver_detected": bool(max_occupants > 0),
        "passenger_count": max(0, max_occupants - 1) if max_occupants else 0,
        "phone_risk": None,
        "seatbelt_status": "unknown",
        "confidence": round(confidence, 4),
        "failure_reason": None,
        "experiment_id": EXPERIMENT_ID,
        "risk_policy": "no_phone_smoking_seatbelt_decision_in_foundation_stage",
        "visibility_distribution": visibility_distribution,
        "analysis_ready_frame_rate": event_summary.get("analysis_ready_frame_rate"),
        "face_frame_rate": event_summary.get("face_frame_rate"),
        "max_occupant_count_candidate": max_occupants,
        "best_frame_foundation": {
            "frame": best.get("frame"),
            "time_s": best.get("time_s"),
            "cabin_bbox_xyxy": best.get("cabin_bbox_xyxy"),
            "torso_bbox_xyxy": best.get("torso_bbox_xyxy"),
            "driver_candidate": best.get("driver_candidate"),
            "overlay_uri": best.get("overlay_uri"),
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    rows = []
    for event in summary["events"]:
        rows.append(
            "| {event_id} | `{video}` | `{view}` | {frames} | {ready} | {face_rate} | {occ} | `{status}` |".format(
                event_id=event["event_id"],
                video=event["video"],
                view=event["view_profile"],
                frames=event["sampled_frames"],
                ready=event["analysis_ready_frame_rate"],
                face_rate=event["face_frame_rate"],
                occ=event["max_occupant_count_candidate"],
                status=event["status"],
            )
        )

    lines = [
        "# CABIN-EXP-012 Runtime Foundation",
        "",
        "Bu rapor cabin/driver hattinin ilk calisir foundation smoke test sonucudur. Bu asama telefon, sigara, kemer veya ihlal karari uretmez; yalniz sonraki specialist modeller icin cabin ROI, visibility, face/occupant ve torso ROI adaylarini uretir.",
        "",
        "## Kapsam",
        "",
        "* Input: mevcut ByteTrack target vehicle event skeleton.",
        "* Videolar: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`.",
        "* Agir overlay ciktilari: `runs/cabin/CABIN-EXP-012-runtime-foundation/`.",
        "* JSON summary: `models/benchmarks/artifacts/CABIN-EXP-012-runtime-foundation-summary.json`.",
        "* Enriched event skeleton: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-cabin012.json`.",
        "",
        "## Sonuc Tablosu",
        "",
        "| Event | Video | View | Sampled frame | Analysis-ready rate | Face frame rate | Max occupant candidate | Status |",
        "|---|---|---|---:|---:|---:|---:|---|",
        *rows,
        "",
        "## Karar",
        "",
        "* `CABIN-EXP-012` arac/cabin ROI, visibility ve torso ROI uretimi icin calisir runtime foundation olarak kabul edilir.",
        "* Mevcut kosuda face/occupant tespiti zayiftir; YuNet checkpoint repo icinde olmadigi icin Haar fallback kullanilmistir.",
        "* `poor` veya `not_visible` kareler risk kararina katilmaz.",
        "* Face/occupant ve torso ROI ciktisi ihlal karari degildir; yalniz specialist ROI ve evidence metadata girdisidir.",
        "* Seatbelt bu asamada `unknown`, phone ise `null` kalir.",
        "",
        "## Sinirlar",
        "",
        "* YuNet checkpoint repo icinde bulunmadigi icin bu kosuda OpenCV Haar fallback kullanilabilir; YuNet checkpoint eklendiginde ayni script `--yunet-model` ile tekrar kosulmalidir.",
        "* Static event bbox, full per-frame target bbox yerine foundation smoke icin kullanilir. Phone/smoking fine-tune oncesi gerekirse per-frame track bbox baglantisi guclendirilmelidir.",
        "* Lokal 3 video benchmark degil; manuel review ve runtime input dogrulama materyalidir.",
        "",
        "## Sonraki Adim",
        "",
        "1. Overlay'ler manuel kontrol edilir.",
        "2. Cabin/torso ROI yeterliyse phone ROI export adimina gecilir.",
        "3. Face/occupant bilgisi phone kararinda zorunlu olacaksa once YuNet checkpoint aktarimi tamamlanir.",
        "4. `PHONE-EXP-003/004` phone specialist baseline/fine-tune planina bu foundation uzerinden gecilir.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--sample-step", type=int, default=20)
    parser.add_argument("--max-frames-per-event", type=int, default=24)
    parser.add_argument("--padding-ratio", type=float, default=0.02)
    parser.add_argument("--yunet-model", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    event_payload = read_json(args.events)
    events = event_payload.get("events", [])
    if not events:
        raise ValueError(f"No events found in {args.events}")

    face_detector = FaceDetector(args.yunet_model)
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    event_summaries = [
        process_event(
            event=event,
            videos_dir=args.videos_dir,
            runs_dir=args.runs_dir,
            face_detector=face_detector,
            sample_step=args.sample_step,
            max_frames_per_event=args.max_frames_per_event,
            padding_ratio=args.padding_ratio,
        )
        for event in events
    ]

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": now_utc(),
        "source_events": rel(args.events),
        "videos_dir": rel(args.videos_dir),
        "runs_dir": rel(args.runs_dir),
        "face_detector_mode": face_detector.mode,
        "policy": {
            "risk_decision_enabled": False,
            "phone_risk": None,
            "seatbelt_status": "unknown",
            "smoking_status": "not_run",
            "poor_or_not_visible_frames": "evidence_only_no_risk",
        },
        "aggregate": {
            "event_count": len(event_summaries),
            "ok_event_count": sum(1 for item in event_summaries if item.get("status") == "ok"),
            "total_sampled_frames": sum(int(item.get("sampled_frames") or 0) for item in event_summaries),
            "mean_analysis_ready_frame_rate": round_or_none(
                mean([float(item.get("analysis_ready_frame_rate") or 0.0) for item in event_summaries if item.get("status") == "ok"])
            ),
            "mean_face_frame_rate": round_or_none(
                mean([float(item.get("face_frame_rate") or 0.0) for item in event_summaries if item.get("status") == "ok"])
            ),
        },
        "events": event_summaries,
    }

    summary_path = args.artifact_dir / DEFAULT_SUMMARY_NAME
    write_json(summary_path, summary)

    enriched = deepcopy(event_payload)
    enriched["generated_at_utc"] = now_utc()
    enriched["source_event_stage"] = event_payload.get("event_stage")
    enriched["event_stage"] = "cabin_driver_runtime_foundation"
    enriched["cabin_experiment_id"] = EXPERIMENT_ID
    by_event = {item.get("event_id"): item for item in event_summaries}
    for event in enriched.get("events", []):
        event_summary = by_event.get(event.get("event_id"), {})
        event["driver_cabin"] = enriched_driver_cabin_block(event_summary)
        event.setdefault("routing_decision", {}).setdefault("experts_called", [])
        if "Cabin Runtime Foundation" not in event["routing_decision"]["experts_called"]:
            event["routing_decision"]["experts_called"].append("Cabin Runtime Foundation")
        event.setdefault("models", {})["cabin_runtime_foundation"] = EXPERIMENT_ID
        event.setdefault("evidence", {})["cabin_overlay_dir"] = rel(args.runs_dir / str(Path(str(event.get("source", {}).get("source_video", "unknown"))).stem))

    enriched_path = args.artifact_dir / DEFAULT_ENRICHED_EVENTS_NAME
    write_json(enriched_path, enriched)

    summary["summary_uri"] = rel(summary_path)
    summary["enriched_events_uri"] = rel(enriched_path)
    write_json(summary_path, summary)
    write_report(args.report, summary)

    print("CABIN-EXP-012 complete")
    print("summary:", rel(summary_path))
    print("enriched_events:", rel(enriched_path))
    print("report:", rel(args.report))
    print("runs:", rel(args.runs_dir))


if __name__ == "__main__":
    main()
