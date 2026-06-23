#!/usr/bin/env python3
"""Helpers for driver phone object detection and temporal metadata."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


def clamp_bbox(bbox: list[float], width: int, height: int) -> list[int] | None:
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(width - 1, int(round(x1))))
    y1 = max(0, min(height - 1, int(round(y1))))
    x2 = max(1, min(width, int(round(x2))))
    y2 = max(1, min(height, int(round(y2))))
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y2]


def bbox_area(bbox: list[float]) -> float:
    return max(0.0, float(bbox[2]) - float(bbox[0])) * max(
        0.0,
        float(bbox[3]) - float(bbox[1]),
    )


def bbox_center(bbox: list[float]) -> tuple[float, float]:
    return (
        (float(bbox[0]) + float(bbox[2])) / 2.0,
        (float(bbox[1]) + float(bbox[3])) / 2.0,
    )


def point_in_bbox(point: tuple[float, float], bbox: list[float]) -> bool:
    return bool(
        float(bbox[0]) <= point[0] <= float(bbox[2])
        and float(bbox[1]) <= point[1] <= float(bbox[3])
    )


def driver_face_global_bbox(frame_record: dict[str, Any]) -> list[int] | None:
    index = frame_record.get("driver_face_index")
    faces = frame_record.get("faces") or []
    cabin_bbox = frame_record.get("cabin_bbox_xyxy")
    if index is None or not cabin_bbox or not 0 <= int(index) < len(faces):
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


def face_near_crop_bbox(
    face_bbox: list[int],
    width: int,
    height: int,
) -> list[int] | None:
    fx1, fy1, fx2, fy2 = [float(value) for value in face_bbox]
    face_width = max(1.0, fx2 - fx1)
    face_height = max(1.0, fy2 - fy1)
    return clamp_bbox(
        [
            fx1 - face_width * 2.4,
            fy1 - face_height * 1.5,
            fx2 + face_width * 2.1,
            fy2 + face_height * 3.0,
        ],
        width,
        height,
    )


def phone_search_roi_bbox(
    frame_record: dict[str, Any],
    frame_width: int,
    frame_height: int,
    profile_name: str,
) -> list[int] | None:
    """Build a driver-focused phone object search ROI."""
    cabin_bbox = frame_record.get("cabin_bbox_xyxy")
    vehicle_bbox = frame_record.get("vehicle_bbox_xyxy")
    face_bbox = driver_face_global_bbox(frame_record)
    if not cabin_bbox or not vehicle_bbox:
        return None
    if face_bbox is None:
        return clamp_bbox(cabin_bbox, frame_width, frame_height)

    fx1, fy1, fx2, fy2 = [float(value) for value in face_bbox]
    face_width = max(1.0, fx2 - fx1)
    face_height = max(1.0, fy2 - fy1)
    if profile_name == "front_lhd":
        left_scale, right_scale = 4.3, 2.6
    else:
        left_scale, right_scale = 4.8, 3.1
    proposed = [
        fx1 - face_width * left_scale,
        fy1 - face_height * 0.85,
        fx2 + face_width * right_scale,
        fy2 + face_height * 4.6,
    ]
    bounds = [
        max(float(vehicle_bbox[0]), float(cabin_bbox[0]) - face_width * 0.55),
        max(float(vehicle_bbox[1]), float(cabin_bbox[1]) - face_height * 0.35),
        min(float(vehicle_bbox[2]), float(cabin_bbox[2]) + face_width * 0.75),
        min(float(vehicle_bbox[3]), float(cabin_bbox[3]) + face_height * 0.45),
    ]
    bounded = [
        max(proposed[0], bounds[0]),
        max(proposed[1], bounds[1]),
        min(proposed[2], bounds[2]),
        min(proposed[3], bounds[3]),
    ]
    return clamp_bbox(bounded, frame_width, frame_height)


def phone_inference_roi_bbox(
    frame_record: dict[str, Any],
    frame_width: int,
    frame_height: int,
    profile_name: str,
    roi_mode: str,
) -> list[int] | None:
    if roi_mode == "driver_phone":
        return phone_search_roi_bbox(
            frame_record,
            frame_width,
            frame_height,
            profile_name,
        )
    if roi_mode == "face_near":
        face_bbox = driver_face_global_bbox(frame_record)
        if face_bbox is None:
            return None
        return face_near_crop_bbox(face_bbox, frame_width, frame_height)
    raise ValueError(f"Unsupported phone ROI mode: {roi_mode}")


def local_to_global_bbox(local_bbox: list[float], roi_bbox: list[float]) -> list[float]:
    return [
        round(float(local_bbox[0]) + float(roi_bbox[0]), 2),
        round(float(local_bbox[1]) + float(roi_bbox[1]), 2),
        round(float(local_bbox[2]) + float(roi_bbox[0]), 2),
        round(float(local_bbox[3]) + float(roi_bbox[1]), 2),
    ]


def classify_phone_detection(
    phone_bbox: list[float],
    roi_bbox: list[float],
    face_bbox: list[float] | None,
    min_box_area: float = 20.0,
    max_roi_area_fraction: float = 0.22,
    max_face_width_units: float = 1.85,
    max_face_height_units: float = 2.20,
) -> dict[str, Any]:
    area = bbox_area(phone_bbox)
    roi_area = max(1.0, bbox_area(roi_bbox))
    reasons = []
    if area < min_box_area:
        reasons.append("phone_box_too_small")
    if area / roi_area > max_roi_area_fraction:
        reasons.append("phone_box_too_large")
    center = bbox_center(phone_bbox)
    if not point_in_bbox(center, roi_bbox):
        reasons.append("phone_center_outside_driver_roi")

    near_face = False
    face_distance_units = None
    if face_bbox is not None:
        face_width = max(1.0, float(face_bbox[2]) - float(face_bbox[0]))
        box_width = max(0.0, float(phone_bbox[2]) - float(phone_bbox[0]))
        box_height = max(0.0, float(phone_bbox[3]) - float(phone_bbox[1]))
        if box_width > face_width * max_face_width_units:
            reasons.append("phone_box_too_wide_for_face_scale")
        if box_height > face_width * max_face_height_units:
            reasons.append("phone_box_too_tall_for_face_scale")
        fx, fy = bbox_center(face_bbox)
        distance = math.hypot(center[0] - fx, center[1] - fy)
        face_distance_units = round(distance / face_width, 4)
        near_face = distance <= face_width * 2.20

    accepted = not reasons
    return {
        "accepted": accepted,
        "reasons": reasons or ["phone_box_inside_driver_roi"],
        "near_face": near_face,
        "face_distance_units": face_distance_units,
    }


def temporal_phone_summary(
    records: list[dict[str, Any]],
    min_evaluable_frames: int = 5,
    min_positive_frames: int = 2,
    min_positive_rate: float = 0.10,
) -> dict[str, Any]:
    evaluable = [
        item
        for item in records
        if item.get("decision_evaluable")
    ]
    positives = [
        item
        for item in evaluable
        if item.get("phone_detected") is True
    ]
    near_face = [
        item
        for item in positives
        if item.get("object_near_face") is True
    ]
    if len(evaluable) < min_evaluable_frames:
        status = "not_evaluable"
    elif (
        len(positives) >= min_positive_frames
        and len(positives) / len(evaluable) >= min_positive_rate
    ):
        status = "detected"
    else:
        status = "not_detected"

    best = None
    if positives:
        best = max(
            positives,
            key=lambda item: (
                float(item.get("phone_confidence") or 0.0),
                int(item.get("phone_area") or 0),
            ),
        )
    state_counts = Counter(
        "detected" if item.get("phone_detected") else "not_detected"
        for item in evaluable
    )
    return {
        "status": status,
        "evaluable_frame_count": len(evaluable),
        "positive_frame_count": len(positives),
        "detection_rate": round(
            len(positives) / len(evaluable) if evaluable else 0.0,
            4,
        ),
        "near_face_frame_count": len(near_face),
        "object_near_face_rate": round(
            len(near_face) / len(positives) if positives else 0.0,
            4,
        ),
        "confidence": round(
            max((float(item.get("phone_confidence") or 0.0) for item in positives), default=0.0),
            4,
        )
        if positives
        else None,
        "best_frame": best.get("frame") if best else None,
        "best_phone_bbox": best.get("phone_bbox") if best else None,
        "best_phone_roi_uri": best.get("phone_roi_uri") if best else None,
        "state_counts": dict(state_counts),
        "phone_risk": None,
    }


def temporal_phone_call_summary(
    arm_records: list[dict[str, Any]],
    fps: float,
    phone_object_detected: bool | None = None,
    min_evaluable_frames: int = 10,
    min_hand_near_ear_rate: float = 0.45,
    min_sustained_seconds: float = 0.80,
    min_dominant_side_rate: float = 0.70,
    max_frame_gap: int = 2,
) -> dict[str, Any]:
    """Summarize a sustained hand-to-ear phone-call behavior candidate.

    Object absence does not veto a call candidate because the phone may be fully
    occluded by the hand or head. This function intentionally produces behavior
    metadata only; risk remains disabled until controlled negative review passes.
    """
    evaluable = [
        item
        for item in arm_records
        if item.get("decision_evaluable")
    ]
    candidates: list[tuple[int, str, float]] = []
    for item in evaluable:
        if item.get("state") != "hand_near_face":
            continue
        side_states = item.get("side_states") or {}
        for side in ("left", "right"):
            side_state = side_states.get(side) or {}
            if side_state.get("complete") and side_state.get("near_ear"):
                candidates.append(
                    (
                        int(item.get("frame") or 0),
                        side,
                        float(item.get("state_confidence") or 0.0),
                    )
                )

    side_counts = Counter(side for _, side, _ in candidates)
    dominant_side = side_counts.most_common(1)[0][0] if side_counts else None
    dominant = [item for item in candidates if item[1] == dominant_side]
    candidate_frame_count = len({frame for frame, _, _ in candidates})
    longest_frames = 0
    current_frames = 0
    previous_frame = None
    for frame, _, _ in dominant:
        if previous_frame is None or frame - previous_frame <= max_frame_gap:
            current_frames += 1
        else:
            current_frames = 1
        longest_frames = max(longest_frames, current_frames)
        previous_frame = frame

    evaluable_count = len(evaluable)
    candidate_rate = (
        candidate_frame_count / evaluable_count if evaluable_count else 0.0
    )
    dominant_side_rate = (
        len(dominant) / len(candidates) if candidates else 0.0
    )
    sustained_seconds = longest_frames / max(float(fps), 1.0)
    mean_confidence = (
        sum(item[2] for item in dominant) / len(dominant)
        if dominant
        else 0.0
    )

    if evaluable_count < min_evaluable_frames:
        status = "not_evaluable"
    elif (
        candidate_rate >= min_hand_near_ear_rate
        and sustained_seconds >= min_sustained_seconds
        and dominant_side_rate >= min_dominant_side_rate
    ):
        status = "handheld_call_likely"
    elif candidates:
        status = "candidate"
    else:
        status = "not_detected"

    confidence = None
    if candidates:
        confidence = min(
            1.0,
        0.45 * min(1.0, candidate_rate / max(min_hand_near_ear_rate, 0.01))
            + 0.25 * min(1.0, sustained_seconds / max(min_sustained_seconds, 0.01))
            + 0.20 * mean_confidence
            + 0.10 * min(1.0, dominant_side_rate / max(min_dominant_side_rate, 0.01))
            + (0.08 if phone_object_detected is True else 0.0),
        )

    evidence_source = (
        "object_pose_temporal"
        if phone_object_detected is True and candidates
        else "pose_temporal"
        if candidates
        else "object"
        if phone_object_detected is True
        else None
    )
    return {
        "phone_call_status": status,
        "phone_call_confidence": round(confidence, 4)
        if confidence is not None
        else None,
        "phone_call_evidence_source": evidence_source,
        "evaluable_frame_count": evaluable_count,
        "hand_near_ear_candidate_frame_count": candidate_frame_count,
        "hand_near_ear_candidate_rate": round(candidate_rate, 4),
        "dominant_hand_side": dominant_side,
        "dominant_hand_side_rate": round(dominant_side_rate, 4),
        "longest_hand_near_ear_frames": longest_frames,
        "longest_hand_near_ear_seconds": round(sustained_seconds, 3),
        "min_hand_near_ear_rate": min_hand_near_ear_rate,
        "min_sustained_seconds": min_sustained_seconds,
        "min_dominant_side_rate": min_dominant_side_rate,
        "phone_object_detected": phone_object_detected,
        "phone_risk": None,
        "risk_enabled": False,
    }


def temporal_phone_call_timeline(
    arm_records: list[dict[str, Any]],
    fps: float,
    phone_object_detected: bool | None = None,
    window_seconds: float = 2.0,
    exit_hand_near_ear_rate: float = 0.20,
    **summary_options: Any,
) -> dict[int, dict[str, Any]]:
    """Build causal per-frame behavior states from a sliding past-only window."""
    ordered = sorted(arm_records, key=lambda item: int(item.get("frame") or 0))
    window_frames = max(1, int(round(max(window_seconds, 0.1) * max(fps, 1.0))))
    timeline: dict[int, dict[str, Any]] = {}
    start = 0
    active = False
    for index, record in enumerate(ordered):
        frame = int(record.get("frame") or 0)
        minimum_frame = frame - window_frames + 1
        while (
            start <= index
            and int(ordered[start].get("frame") or 0) < minimum_frame
        ):
            start += 1
        current = temporal_phone_call_summary(
            ordered[start : index + 1],
            fps=fps,
            phone_object_detected=phone_object_detected,
            **summary_options,
        )
        raw_status = current["phone_call_status"]
        if raw_status == "handheld_call_likely":
            active = True
        elif active and (
            float(current.get("hand_near_ear_candidate_rate") or 0.0)
            >= exit_hand_near_ear_rate
        ):
            current["phone_call_status"] = "handheld_call_likely"
        else:
            active = False
        current["raw_phone_call_status"] = raw_status
        current["hysteresis_active"] = active
        timeline[frame] = current
    return timeline
