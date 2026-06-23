#!/usr/bin/env python3
"""Pure helpers for face-anchored deterministic driver torso ROIs."""

from __future__ import annotations

import statistics
from typing import Any


def clamp_bbox(bbox: list[float], width: int, height: int) -> list[int]:
    x1, y1, x2, y2 = bbox
    return [
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(1, min(width, int(round(x2)))),
        max(1, min(height, int(round(y2)))),
    ]


def bbox_area(bbox: list[float]) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def intersection_area(a: list[float], b: list[float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(
        0.0, min(a[3], b[3]) - max(a[1], b[1])
    )


def driver_face_global_bbox(frame_record: dict[str, Any]) -> list[int] | None:
    index = frame_record.get("driver_face_index")
    faces = frame_record.get("faces") or []
    cabin_bbox = frame_record.get("cabin_bbox_xyxy")
    if index is None or not cabin_bbox or not (0 <= int(index) < len(faces)):
        return None
    face_bbox = faces[int(index)].get("bbox")
    if not face_bbox or len(face_bbox) != 4:
        return None
    cx1, cy1, _, _ = cabin_bbox
    x, y, width, height = face_bbox
    return [
        int(round(cx1 + x)),
        int(round(cy1 + y)),
        int(round(cx1 + x + width)),
        int(round(cy1 + y + height)),
    ]


def deterministic_torso_bbox(
    face_bbox: list[float],
    vehicle_bbox: list[float],
    cabin_bbox: list[float],
    frame_width: int,
    frame_height: int,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Create a chest/seatbelt ROI below the driver face without pose inference."""
    fx1, fy1, fx2, fy2 = [float(value) for value in face_bbox]
    vx1, vy1, vx2, vy2 = [float(value) for value in vehicle_bbox]
    cx1, cy1, cx2, cy2 = [float(value) for value in cabin_bbox]
    face_width = max(1.0, fx2 - fx1)
    face_height = max(1.0, fy2 - fy1)
    center_x = (fx1 + fx2) / 2.0
    torso = profile.get("torso") or {}
    left_scale = float(torso.get("left_face_widths", 2.0))
    right_scale = float(torso.get("right_face_widths", 2.0))
    top_scale = float(torso.get("top_face_heights_from_bottom", -0.10))
    bottom_scale = float(torso.get("bottom_face_heights_from_bottom", 4.0))
    max_below_cabin_scale = float(
        torso.get("max_bottom_below_cabin_face_heights", 0.75)
    )

    raw_bbox = [
        center_x - face_width * left_scale,
        fy2 + face_height * top_scale,
        center_x + face_width * right_scale,
        fy2 + face_height * bottom_scale,
    ]
    bounded_bbox = [
        max(vx1, cx1 - face_width * 0.5, raw_bbox[0]),
        max(vy1, raw_bbox[1]),
        min(vx2, cx2 + face_width * 0.5, raw_bbox[2]),
        min(vy2, cy2 + face_height * max_below_cabin_scale, raw_bbox[3]),
    ]
    torso_bbox = clamp_bbox(bounded_bbox, frame_width, frame_height)
    raw_area = bbox_area(raw_bbox)
    retained_ratio = bbox_area(torso_bbox) / raw_area if raw_area > 0 else 0.0
    vehicle_area = bbox_area(vehicle_bbox)
    vehicle_coverage = (
        intersection_area(torso_bbox, vehicle_bbox) / vehicle_area
        if vehicle_area > 0
        else 0.0
    )
    torso_height = max(1.0, torso_bbox[3] - torso_bbox[1])
    below_cabin_height = max(0.0, torso_bbox[3] - cy2)
    return {
        "bbox": torso_bbox,
        "raw_bbox": [round(value, 2) for value in raw_bbox],
        "face_width": round(face_width, 2),
        "face_height": round(face_height, 2),
        "retained_area_ratio": round(retained_ratio, 4),
        "vehicle_coverage_ratio": round(vehicle_coverage, 4),
        "below_cabin_vertical_ratio": round(
            below_cabin_height / torso_height,
            4,
        ),
    }


def torso_quality_decision(
    geometry: dict[str, Any],
    face_confidence: float,
    min_face_dimension: float = 20.0,
    min_torso_width: float = 56.0,
    min_torso_height: float = 72.0,
    min_retained_ratio: float = 0.62,
    max_below_cabin_ratio: float = 0.45,
) -> tuple[float, str, list[str]]:
    bbox = geometry["bbox"]
    width = float(bbox[2] - bbox[0])
    height = float(bbox[3] - bbox[1])
    face_dimension = min(
        float(geometry.get("face_width") or 0.0),
        float(geometry.get("face_height") or 0.0),
    )
    retained = float(geometry.get("retained_area_ratio") or 0.0)
    below_cabin_ratio = float(
        geometry.get("below_cabin_vertical_ratio") or 0.0
    )
    confidence = max(0.0, min(1.0, float(face_confidence)))

    face_score = max(0.0, min(1.0, face_dimension / 48.0))
    width_score = max(0.0, min(1.0, width / 180.0))
    height_score = max(0.0, min(1.0, height / 240.0))
    retained_score = max(0.0, min(1.0, retained))
    score = (
        0.25 * confidence
        + 0.20 * face_score
        + 0.20 * width_score
        + 0.20 * height_score
        + 0.15 * retained_score
    )

    reasons = []
    if face_dimension < min_face_dimension:
        reasons.append("driver_face_too_small")
    if width < min_torso_width:
        reasons.append("torso_roi_too_narrow")
    if height < min_torso_height:
        reasons.append("torso_roi_too_short")
    if retained < min_retained_ratio:
        reasons.append("torso_roi_excessively_clipped")
    if below_cabin_ratio > max_below_cabin_ratio:
        reasons.append("torso_roi_exterior_contamination")
    if confidence < 0.60:
        reasons.append("driver_face_low_confidence")

    if any(
        reason
        in {
            "driver_face_too_small",
            "torso_roi_too_narrow",
            "torso_roi_too_short",
            "torso_roi_excessively_clipped",
            "torso_roi_exterior_contamination",
        }
        for reason in reasons
    ):
        status = "not_usable"
    elif score < 0.62:
        status = "limited"
    else:
        status = "usable"
    if not reasons:
        reasons.append("deterministic_torso_roi_usable")
    return round(score, 4), status, reasons


def smooth_bbox(
    previous: list[float] | None,
    current: list[float],
    alpha: float = 0.35,
) -> list[int]:
    if previous is None:
        return [int(round(value)) for value in current]
    return [
        int(round(alpha * float(new) + (1.0 - alpha) * float(old)))
        for old, new in zip(previous, current)
    ]


def temporal_torso_summary(
    frame_results: list[dict[str, Any]],
    min_usable_frames: int = 3,
    min_usable_rate: float = 0.30,
) -> dict[str, Any]:
    evaluable = [
        item
        for item in frame_results
        if item.get("visibility") in {"good", "limited"}
        and item.get("driver_face_bbox") is not None
    ]
    usable = [item for item in evaluable if item.get("torso_status") == "usable"]
    limited = [item for item in evaluable if item.get("torso_status") == "limited"]
    usable_rate = len(usable) / len(evaluable) if evaluable else 0.0
    available_rate = (
        (len(usable) + len(limited)) / len(evaluable) if evaluable else 0.0
    )

    longest_miss = 0
    current_miss = 0
    for item in evaluable:
        if item.get("torso_status") in {"usable", "limited"}:
            current_miss = 0
        else:
            current_miss += 1
            longest_miss = max(longest_miss, current_miss)

    best = None
    if frame_results:
        best = max(
            frame_results,
            key=lambda item: (
                item.get("torso_status") == "usable",
                item.get("torso_status") == "limited",
                float(item.get("torso_quality_score") or 0.0),
                float(item.get("face_confidence") or 0.0),
            ),
        )
    detected: bool | None = None
    if evaluable:
        detected = (
            len(usable) >= min_usable_frames and usable_rate >= min_usable_rate
        )
    return {
        "processed_frame_count": len(frame_results),
        "evaluable_driver_frame_count": len(evaluable),
        "usable_torso_frame_count": len(usable),
        "usable_torso_rate": round(usable_rate, 4),
        "available_torso_frame_count": len(usable) + len(limited),
        "available_torso_rate": round(available_rate, 4),
        "torso_baseline_ready": detected,
        "longest_torso_miss_run": longest_miss,
        "mean_torso_quality_score": round(
            float(
                statistics.fmean(
                    float(item.get("torso_quality_score") or 0.0)
                    for item in evaluable
                )
            ),
            4,
        )
        if evaluable
        else None,
        "best_frame": best.get("frame") if best else None,
        "best_torso_bbox": best.get("torso_bbox") if best else None,
        "best_torso_roi_uri": best.get("torso_roi_uri") if best else None,
        "best_torso_quality_score": (
            best.get("torso_quality_score") if best else None
        ),
    }
