#!/usr/bin/env python3
"""Pure helpers for cabin visibility and temporal driver decisions."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any


VISIBILITY_ORDER = {
    "not_visible": 0,
    "poor": 1,
    "limited": 2,
    "good": 3,
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * 0.95))
    return round(float(ordered[index]), 3)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(statistics.fmean(values)), 3)


def iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


def clamp_bbox(bbox: list[float], width: int, height: int) -> list[int]:
    x1, y1, x2, y2 = bbox
    return [
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(1, min(width, int(round(x2)))),
        max(1, min(height, int(round(y2)))),
    ]


def cabin_roi_bbox(
    vehicle_bbox: list[float],
    frame_width: int,
    frame_height: int,
    profile: dict[str, Any],
) -> list[int]:
    """Return a configurable cabin crop inside a vehicle bbox."""
    x1, y1, x2, y2 = vehicle_bbox
    width = max(1.0, x2 - x1)
    height = max(1.0, y2 - y1)
    roi = profile.get("roi") or {}
    left = float(roi.get("left", 0.05))
    top = float(roi.get("top", 0.02))
    right = float(roi.get("right", 0.95))
    bottom = float(roi.get("bottom", 0.70))
    return clamp_bbox(
        [
            x1 + width * left,
            y1 + height * top,
            x1 + width * right,
            y1 + height * bottom,
        ],
        frame_width,
        frame_height,
    )


def visibility_decision(metrics: dict[str, float]) -> tuple[float, str, list[str]]:
    """Convert cheap image metrics into an auditable visibility gate."""
    brightness = float(metrics.get("brightness", 0.0))
    contrast = float(metrics.get("contrast", 0.0))
    sharpness = float(metrics.get("sharpness", 0.0))
    dark_ratio = float(metrics.get("dark_ratio", 1.0))
    glare_ratio = float(metrics.get("glare_ratio", 0.0))
    min_dimension = float(metrics.get("min_dimension", 0.0))

    # External cabin views often contain a dark windshield while still
    # preserving enough contrast and edge detail for face detection. Treat
    # darkness as a quality penalty instead of an automatic rejection.
    brightness_score = clamp((brightness - 12.0) / 58.0)
    contrast_score = clamp(contrast / 45.0)
    sharpness_score = clamp(sharpness / 130.0)
    resolution_score = clamp(min_dimension / 180.0)
    exposure_score = clamp(1.0 - 0.65 * dark_ratio - 0.50 * glare_ratio)

    score = clamp(
        0.16 * brightness_score
        + 0.23 * contrast_score
        + 0.24 * sharpness_score
        + 0.20 * resolution_score
        + 0.17 * exposure_score
    )

    reasons: list[str] = []
    if min_dimension < 80:
        reasons.append("cabin_roi_too_small")
    if brightness < 35:
        reasons.append("low_brightness")
    if contrast < 25:
        reasons.append("low_contrast")
    if sharpness < 45:
        reasons.append("blur_or_soft_focus")
    if dark_ratio > 0.55:
        reasons.append("high_dark_pixel_ratio")
    if glare_ratio > 0.25:
        reasons.append("high_glare_ratio")
    if not reasons:
        reasons.append("cabin_roi_quality_usable")

    if min_dimension < 48 or score < 0.20:
        visibility = "not_visible"
    elif score < 0.44:
        visibility = "poor"
    elif score < 0.70:
        visibility = "limited"
    else:
        visibility = "good"
    return round(score, 4), visibility, reasons


def assign_driver_candidate(
    faces: list[dict[str, Any]],
    profile_name: str,
    roi_width: int,
) -> tuple[int | None, str]:
    """Select a driver candidate using an explicit camera-view policy."""
    if not faces:
        return None, "no_face_detected"
    if profile_name == "side_driver_window":
        if len(faces) > 1:
            return None, "side_view_multiple_faces_role_ambiguous"
        index = max(
            range(len(faces)),
            key=lambda idx: (
                float(faces[idx].get("bbox", [0, 0, 0, 0])[2])
                * float(faces[idx].get("bbox", [0, 0, 0, 0])[3]),
                float(faces[idx].get("confidence", 0.0)),
            ),
        )
        return index, "assigned_side_driver_largest_face"
    if profile_name == "front_lhd":
        right_half = []
        for idx, face in enumerate(faces):
            x, _, width, _ = face.get("bbox", [0, 0, 0, 0])
            center_x = float(x) + float(width) / 2.0
            if center_x >= roi_width * 0.50:
                right_half.append(idx)
        if not right_half:
            return None, "front_lhd_driver_side_face_missing"
        index = max(
            right_half,
            key=lambda idx: (
                float(faces[idx].get("bbox", [0, 0, 0, 0])[2])
                * float(faces[idx].get("bbox", [0, 0, 0, 0])[3]),
                float(faces[idx].get("confidence", 0.0)),
            ),
        )
        return index, "assigned_front_lhd_right_side_face"
    return None, "profile_unknown_role_not_assigned"


def temporal_cabin_summary(
    frame_results: list[dict[str, Any]],
    min_driver_frames: int = 3,
    min_driver_rate: float = 0.30,
) -> dict[str, Any]:
    processed = len(frame_results)
    eligible = [
        item
        for item in frame_results
        if item.get("visibility") in {"good", "limited"}
    ]
    face_frames = [item for item in eligible if int(item.get("face_count") or 0) > 0]
    raw_face_frames = [
        item for item in frame_results if int(item.get("face_count") or 0) > 0
    ]
    driver_frames = [
        item for item in eligible if item.get("driver_candidate_detected") is True
    ]

    visible_rate = len(eligible) / processed if processed else 0.0
    face_rate = len(face_frames) / len(eligible) if eligible else 0.0
    driver_rate = len(driver_frames) / len(eligible) if eligible else 0.0
    longest_face_miss_run = 0
    current_face_miss_run = 0
    for item in eligible:
        if int(item.get("face_count") or 0) > 0:
            current_face_miss_run = 0
        else:
            current_face_miss_run += 1
            longest_face_miss_run = max(
                longest_face_miss_run,
                current_face_miss_run,
            )

    # Zero-face frames indicate a detector miss or temporary occlusion, not proof
    # that the vehicle has zero occupants. Estimate occupants only from frames
    # where at least one face is detected.
    occupant_votes = Counter(int(item.get("face_count") or 0) for item in face_frames)
    occupant_count = None
    if occupant_votes:
        # Rear occupants may be visible only during a short camera-angle window.
        # Keep the highest count that has repeated temporal support instead of
        # letting the dominant single-face view erase valid passenger evidence.
        min_occupant_support = max(2, int(len(face_frames) * 0.02 + 0.999))
        supported_counts = [
            count
            for count, support in occupant_votes.items()
            if support >= min_occupant_support
        ]
        occupant_count = (
            max(supported_counts)
            if supported_counts
            else occupant_votes.most_common(1)[0][0]
        )

    role_statuses = Counter(
        str(item.get("role_assignment_status") or "unknown") for item in eligible
    )
    assigned_statuses = Counter(
        {
            status: count
            for status, count in role_statuses.items()
            if status.startswith("assigned_")
        }
    )
    role_status = (
        assigned_statuses.most_common(1)[0][0]
        if assigned_statuses
        else role_statuses.most_common(1)[0][0]
        if role_statuses
        else "not_assigned"
    )
    role_assignable = bool(assigned_statuses)
    driver_detected = None
    if role_assignable:
        driver_detected = (
            len(driver_frames) >= min_driver_frames and driver_rate >= min_driver_rate
        )

    best = None
    if frame_results:
        best = max(
            frame_results,
            key=lambda item: (
                VISIBILITY_ORDER.get(str(item.get("visibility")), -1),
                int(item.get("face_count") or 0),
                float(item.get("max_face_confidence") or 0.0),
                float(item.get("visibility_score") or 0.0),
            ),
        )

    visibility_votes = Counter(str(item.get("visibility")) for item in frame_results)
    temporal_visibility = (
        visibility_votes.most_common(1)[0][0] if visibility_votes else "not_visible"
    )
    if eligible and temporal_visibility in {"poor", "not_visible"}:
        temporal_visibility = "limited"

    return {
        "processed_frame_count": processed,
        "eligible_visibility_frame_count": len(eligible),
        "visible_frame_rate": round(visible_rate, 4),
        "face_detection_frame_count": len(face_frames),
        "temporal_detection_rate": round(face_rate, 4),
        "raw_face_detection_frame_count": len(raw_face_frames),
        "raw_face_detection_rate": round(
            len(raw_face_frames) / processed if processed else 0.0,
            4,
        ),
        "longest_eligible_face_miss_run": longest_face_miss_run,
        "driver_candidate_frame_count": len(driver_frames),
        "driver_candidate_rate": round(driver_rate, 4),
        "driver_candidate_detected": driver_detected,
        "occupant_count_estimate": occupant_count,
        "role_assignment_status": role_status,
        "visibility": temporal_visibility,
        "best_frame": best.get("frame") if best else None,
        "best_visibility_score": best.get("visibility_score") if best else None,
        "best_roi_uri": best.get("roi_file") if best else None,
        "mean_visibility_score": mean(
            [float(item.get("visibility_score") or 0.0) for item in frame_results]
        ),
    }
