#!/usr/bin/env python3
"""Pure geometry and temporal helpers for the driver pose baseline."""

from __future__ import annotations

import math
import statistics
from typing import Any


class TemporalKeypointStabilizer:
    """Causally stabilize face-relative keypoints and bridge short dropouts."""

    def __init__(
        self,
        min_confidence: float = 0.30,
        hold_frames: int = 10,
        smoothing_alpha: float = 0.55,
        max_jump_face_units: float = 1.25,
        continuation_confidence: float | None = None,
        max_continuation_frames: int = 0,
        continuation_max_jump_face_units: float = 0.45,
    ):
        self.min_confidence = min_confidence
        self.hold_frames = max(0, hold_frames)
        self.smoothing_alpha = smoothing_alpha
        self.max_jump_face_units = max_jump_face_units
        self.continuation_confidence = continuation_confidence
        self.max_continuation_frames = max(0, max_continuation_frames)
        self.continuation_max_jump_face_units = (
            continuation_max_jump_face_units
        )
        self._state: dict[str, dict[str, float | int]] = {}

    def update(
        self,
        keypoints: dict[str, dict[str, float]],
        face_bbox: list[float],
        frame_number: int,
    ) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
        face_center_x = (float(face_bbox[0]) + float(face_bbox[2])) / 2.0
        face_center_y = (float(face_bbox[1]) + float(face_bbox[3])) / 2.0
        face_width = max(1.0, float(face_bbox[2]) - float(face_bbox[0]))
        names = set(keypoints) | set(self._state)
        stabilized: dict[str, dict[str, float]] = {}
        accepted = 0
        held = 0
        rejected = 0

        for name in names:
            point = keypoints.get(name) or {}
            confidence = float(point.get("confidence") or 0.0)
            state = self._state.get(name)
            valid = confidence >= self.min_confidence
            continuation = bool(
                not valid
                and state is not None
                and self.continuation_confidence is not None
                and confidence >= self.continuation_confidence
                and int(state.get("continuation_frames") or 0)
                < self.max_continuation_frames
            )
            relative_x = (
                (float(point.get("x") or 0.0) - face_center_x) / face_width
                if valid or continuation
                else 0.0
            )
            relative_y = (
                (float(point.get("y") or 0.0) - face_center_y) / face_width
                if valid or continuation
                else 0.0
            )
            if (valid or continuation) and state is not None:
                frame_delta = max(1, frame_number - int(state["frame"]))
                jump = math.hypot(
                    relative_x - float(state["x"]),
                    relative_y - float(state["y"]),
                ) / frame_delta
                jump_limit = (
                    self.continuation_max_jump_face_units
                    if continuation
                    else self.max_jump_face_units
                )
                if jump > jump_limit:
                    valid = False
                    continuation = False
                    rejected += 1

            if valid or continuation:
                if state is not None:
                    alpha = self.smoothing_alpha
                    relative_x = (
                        alpha * relative_x + (1.0 - alpha) * float(state["x"])
                    )
                    relative_y = (
                        alpha * relative_y + (1.0 - alpha) * float(state["y"])
                    )
                self._state[name] = {
                    "x": relative_x,
                    "y": relative_y,
                    "confidence": confidence,
                    "frame": frame_number,
                    "continuation_frames": (
                        int(state.get("continuation_frames") or 0) + 1
                        if continuation and state is not None
                        else 0
                    ),
                }
                stabilized[name] = {
                    "x": round(face_center_x + relative_x * face_width, 2),
                    "y": round(face_center_y + relative_y * face_width, 2),
                    "confidence": round(
                        max(self.min_confidence, confidence),
                        4,
                    ),
                    "temporal_source": (
                        "tracked_low_confidence"
                        if continuation
                        else "observed"
                    ),
                }
                accepted += 1
                continue

            if (
                state is not None
                and frame_number - int(state["frame"]) <= self.hold_frames
            ):
                age = max(1, frame_number - int(state["frame"]))
                decay = max(0.35, 1.0 - age / max(1, self.hold_frames + 1))
                stabilized[name] = {
                    "x": round(
                        face_center_x + float(state["x"]) * face_width,
                        2,
                    ),
                    "y": round(
                        face_center_y + float(state["y"]) * face_width,
                        2,
                    ),
                    "confidence": round(
                        max(self.min_confidence, float(state["confidence"]) * decay),
                        4,
                    ),
                    "temporal_source": "held",
                }
                held += 1

        expired = [
            name
            for name, state in self._state.items()
            if frame_number - int(state["frame"]) > self.hold_frames
        ]
        for name in expired:
            del self._state[name]
        return stabilized, {
            "observed_keypoint_count": accepted,
            "held_keypoint_count": held,
            "rejected_jump_count": rejected,
        }


def pose_inference_gate(
    visibility: str,
    driver_face_confidence: float | None,
    has_required_geometry: bool,
    poor_face_confidence_threshold: float | None = None,
) -> tuple[bool, bool]:
    """Separate pose evidence generation from visibility-gated risk decisions."""
    decision_evaluable = visibility in {"good", "limited"}
    evidence_only = bool(
        visibility == "poor"
        and poor_face_confidence_threshold is not None
        and driver_face_confidence is not None
        and driver_face_confidence >= poor_face_confidence_threshold
    )
    return (
        bool(has_required_geometry and (decision_evaluable or evidence_only)),
        bool(has_required_geometry and evidence_only and not decision_evaluable),
    )


def clamp_bbox(bbox: list[float], width: int, height: int) -> list[int]:
    x1, y1, x2, y2 = bbox
    return [
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(1, min(width, int(round(x2)))),
        max(1, min(height, int(round(y2)))),
    ]


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


def upper_body_roi_bbox(
    face_bbox: list[float],
    vehicle_bbox: list[float],
    frame_width: int,
    frame_height: int,
    horizontal_face_scale: float = 5.0,
    downward_face_scale: float = 5.5,
) -> list[int]:
    """Expand a driver face into a torso/arm ROI, bounded by the target vehicle."""
    fx1, fy1, fx2, fy2 = face_bbox
    vx1, vy1, vx2, vy2 = vehicle_bbox
    face_width = max(1.0, fx2 - fx1)
    face_height = max(1.0, fy2 - fy1)
    center_x = (fx1 + fx2) / 2.0
    roi_width = max(face_width * horizontal_face_scale, (vx2 - vx1) * 0.38)
    x1 = max(vx1, center_x - roi_width / 2.0)
    x2 = min(vx2, center_x + roi_width / 2.0)
    y1 = max(vy1, fy1 - face_height * 0.65)
    y2 = min(vy2, fy2 + face_height * downward_face_scale)
    return clamp_bbox([x1, y1, x2, y2], frame_width, frame_height)


def upper_body_cabin_roi_bbox(
    face_bbox: list[float],
    vehicle_bbox: list[float],
    cabin_bbox: list[float],
    frame_width: int,
    frame_height: int,
    below_cabin_face_scale: float = 0.35,
) -> list[int]:
    """Build a face-anchored person crop without feeding hood/bodywork as torso."""
    base = upper_body_roi_bbox(
        face_bbox,
        vehicle_bbox,
        frame_width,
        frame_height,
    )
    face_width = max(1.0, float(face_bbox[2]) - float(face_bbox[0]))
    face_height = max(1.0, float(face_bbox[3]) - float(face_bbox[1]))
    bounds = [
        max(float(vehicle_bbox[0]), float(cabin_bbox[0]) - face_width * 0.75),
        max(float(vehicle_bbox[1]), float(cabin_bbox[1]) - face_height * 0.50),
        min(float(vehicle_bbox[2]), float(cabin_bbox[2]) + face_width * 0.75),
        min(
            float(vehicle_bbox[3]),
            float(cabin_bbox[3]) + face_height * below_cabin_face_scale,
        ),
    ]
    bounded = intersect_bbox(base, bounds, min_width=24, min_height=32)
    return bounded if bounded is not None else base


def driver_arm_focus_roi_bbox(
    face_bbox: list[float],
    vehicle_bbox: list[float],
    cabin_bbox: list[float],
    view_profile: str,
    frame_width: int,
    frame_height: int,
) -> list[int]:
    """Crop driver head, shoulders and arms while excluding most bodywork."""
    fx1, fy1, fx2, fy2 = [float(value) for value in face_bbox]
    face_width = max(1.0, fx2 - fx1)
    face_height = max(1.0, fy2 - fy1)
    if view_profile == "front_lhd":
        left_scale, right_scale = 4.5, 2.4
    else:
        left_scale, right_scale = 4.7, 3.2
    proposed = [
        fx1 - face_width * left_scale,
        fy1 - face_height * 0.55,
        fx2 + face_width * right_scale,
        fy2 + face_height * 4.2,
    ]
    bounds = [
        max(float(vehicle_bbox[0]), float(cabin_bbox[0]) - face_width * 0.40),
        max(float(vehicle_bbox[1]), float(cabin_bbox[1]) - face_height * 0.20),
        min(float(vehicle_bbox[2]), float(cabin_bbox[2]) + face_width * 0.40),
        min(float(vehicle_bbox[3]), float(cabin_bbox[3])),
    ]
    bounded = intersect_bbox(proposed, bounds, min_width=48, min_height=64)
    return (
        bounded
        if bounded is not None
        else upper_body_cabin_roi_bbox(
            face_bbox,
            vehicle_bbox,
            cabin_bbox,
            frame_width,
            frame_height,
        )
    )


def xyxy_to_local(
    bbox: list[float],
    roi_bbox: list[float],
) -> list[float]:
    rx1, ry1, _, _ = roi_bbox
    x1, y1, x2, y2 = bbox
    return [x1 - rx1, y1 - ry1, x2 - rx1, y2 - ry1]


def _center(bbox: list[float]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def associate_driver_pose(
    poses: list[dict[str, Any]],
    face_bbox: list[float],
) -> tuple[int | None, str, float | None]:
    """Match a pose instance to the already assigned driver face."""
    if not poses:
        return None, "no_pose_detected", None
    face_center_x, face_center_y = _center(face_bbox)
    candidates: list[tuple[float, int]] = []
    for index, pose in enumerate(poses):
        bbox = pose.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [float(value) for value in bbox]
        width = max(1.0, x2 - x1)
        height = max(1.0, y2 - y1)
        margin_x = width * 0.18
        margin_y = height * 0.12
        if not (
            x1 - margin_x <= face_center_x <= x2 + margin_x
            and y1 - margin_y <= face_center_y <= y1 + height * 0.60
        ):
            continue
        pose_center_x = (x1 + x2) / 2.0
        expected_head_y = y1 + height * 0.16
        distance = math.hypot(
            (face_center_x - pose_center_x) / width,
            (face_center_y - expected_head_y) / height,
        )
        confidence = float(pose.get("confidence") or 0.0)
        score = max(0.0, 1.0 - distance) * 0.8 + confidence * 0.2
        candidates.append((score, index))
    if not candidates:
        return None, "driver_face_pose_not_matched", None
    score, index = max(candidates)
    return index, "driver_face_pose_matched", round(score, 4)


def torso_from_keypoints(
    keypoints: dict[str, dict[str, float]],
    roi_width: int,
    roi_height: int,
    min_confidence: float = 0.35,
    face_bbox: list[float] | None = None,
    keypoint_bounds: list[float] | None = None,
) -> dict[str, Any]:
    """Build a torso ROI from shoulders and optional hips."""

    def visible(name: str) -> bool:
        point = keypoints.get(name) or {}
        x = float(point.get("x") or 0.0)
        y = float(point.get("y") or 0.0)
        inside_bounds = True
        if keypoint_bounds is not None:
            bx1, by1, bx2, by2 = keypoint_bounds
            inside_bounds = bx1 <= x <= bx2 and by1 <= y <= by2
        return (
            float(point.get("confidence") or 0.0) >= min_confidence
            and 0 <= x < roi_width
            and 0 <= y < roi_height
            and inside_bounds
        )

    shoulders_ready = visible("left_shoulder") and visible("right_shoulder")
    hips_ready = visible("left_hip") and visible("right_hip")
    if not shoulders_ready:
        return {
            "status": "shoulders_not_visible",
            "shoulders_visible": False,
            "hips_visible": hips_ready,
            "torso_bbox": None,
            "mean_anchor_confidence": None,
        }

    left_shoulder = keypoints["left_shoulder"]
    right_shoulder = keypoints["right_shoulder"]
    shoulder_span = math.hypot(
        float(left_shoulder["x"]) - float(right_shoulder["x"]),
        float(left_shoulder["y"]) - float(right_shoulder["y"]),
    )
    if shoulder_span < 6.0:
        return {
            "status": "shoulder_span_too_small",
            "shoulders_visible": True,
            "hips_visible": hips_ready,
            "torso_bbox": None,
            "mean_anchor_confidence": None,
        }

    if face_bbox:
        face_width = max(1.0, float(face_bbox[2]) - float(face_bbox[0]))
        face_height = max(1.0, float(face_bbox[3]) - float(face_bbox[1]))
        face_bottom = float(face_bbox[3])
        shoulder_mid_y = (
            float(left_shoulder["y"]) + float(right_shoulder["y"])
        ) / 2.0
        geometry_valid = (
            face_width * 0.75 <= shoulder_span <= face_width * 4.5
            and face_bottom - face_height * 0.20
            <= shoulder_mid_y
            <= face_bottom + face_height * 3.5
        )
        if not geometry_valid:
            return {
                "status": "face_shoulder_geometry_invalid",
                "shoulders_visible": True,
                "hips_visible": hips_ready,
                "torso_bbox": None,
                "mean_anchor_confidence": None,
                "arm_chain_count": 0,
                "seatbelt_anchor_ready": False,
                "phone_anchor_ready": False,
            }

    shoulder_x = [float(left_shoulder["x"]), float(right_shoulder["x"])]
    shoulder_y = [float(left_shoulder["y"]), float(right_shoulder["y"])]
    x1 = min(shoulder_x) - shoulder_span * 0.45
    x2 = max(shoulder_x) + shoulder_span * 0.45
    y1 = min(shoulder_y) - shoulder_span * 0.25
    anchor_confidences = [
        float(left_shoulder["confidence"]),
        float(right_shoulder["confidence"]),
    ]

    if hips_ready:
        left_hip = keypoints["left_hip"]
        right_hip = keypoints["right_hip"]
        hip_x = [float(left_hip["x"]), float(right_hip["x"])]
        hip_y = [float(left_hip["y"]), float(right_hip["y"])]
        x1 = min(x1, min(hip_x) - shoulder_span * 0.25)
        x2 = max(x2, max(hip_x) + shoulder_span * 0.25)
        y2 = max(hip_y) + shoulder_span * 0.30
        anchor_confidences.extend(
            [float(left_hip["confidence"]), float(right_hip["confidence"])]
        )
        status = "torso_with_hips"
    else:
        y2 = max(shoulder_y) + shoulder_span * 2.25
        status = "torso_shoulders_extrapolated"

    torso_bbox = clamp_bbox([x1, y1, x2, y2], roi_width, roi_height)
    if torso_bbox[2] - torso_bbox[0] < 12 or torso_bbox[3] - torso_bbox[1] < 16:
        return {
            "status": "torso_roi_too_small",
            "shoulders_visible": True,
            "hips_visible": hips_ready,
            "torso_bbox": None,
            "mean_anchor_confidence": None,
            "arm_chain_count": 0,
            "seatbelt_anchor_ready": False,
            "phone_anchor_ready": False,
        }
    arm_chain_count = 0
    for side in ("left", "right"):
        if all(
            visible(f"{side}_{joint}")
            for joint in ("shoulder", "elbow", "wrist")
        ):
            arm_chain_count += 1
    return {
        "status": status,
        "shoulders_visible": True,
        "hips_visible": hips_ready,
        "torso_bbox": torso_bbox,
        "mean_anchor_confidence": round(
            float(statistics.fmean(anchor_confidences)),
            4,
        ),
        "arm_chain_count": arm_chain_count,
        "seatbelt_anchor_ready": True,
        "phone_anchor_ready": arm_chain_count >= 1,
    }


def intersect_bbox(
    bbox: list[float],
    bounds: list[float],
    min_width: int = 12,
    min_height: int = 16,
) -> list[int] | None:
    x1 = max(float(bbox[0]), float(bounds[0]))
    y1 = max(float(bbox[1]), float(bounds[1]))
    x2 = min(float(bbox[2]), float(bounds[2]))
    y2 = min(float(bbox[3]), float(bounds[3]))
    if x2 - x1 < min_width or y2 - y1 < min_height:
        return None
    return [int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))]


def hand_anchor_summary(
    keypoints: dict[str, dict[str, float]],
    face_bbox: list[float],
    min_confidence: float = 0.35,
    minimum_points: int = 4,
    max_face_distance: float = 1.6,
    max_root_wrist_distance: float = 0.75,
) -> dict[str, Any]:
    face_center_x = (float(face_bbox[0]) + float(face_bbox[2])) / 2.0
    face_center_y = (float(face_bbox[1]) + float(face_bbox[3])) / 2.0
    face_width = max(1.0, float(face_bbox[2]) - float(face_bbox[0]))
    anchor_count = 0
    near_face_count = 0
    sides: dict[str, Any] = {}
    for side in ("left", "right"):
        wrist = keypoints.get(f"{side}_wrist") or {}
        points = [
            point
            for index in range(21)
            if (
                point := keypoints.get(f"{side}_hand_{index}")
            )
            and float(point.get("confidence") or 0.0) >= min_confidence
        ]
        root = keypoints.get(f"{side}_hand_0") or {}
        root_wrist_distance = None
        wrist_associated = False
        if root and wrist:
            root_wrist_distance = math.hypot(
                float(root.get("x") or 0.0) - float(wrist.get("x") or 0.0),
                float(root.get("y") or 0.0) - float(wrist.get("y") or 0.0),
            ) / face_width
            wrist_associated = root_wrist_distance <= max_root_wrist_distance
        ready = len(points) >= minimum_points and wrist_associated
        centroid = None
        distance_face_units = None
        near_face = False
        if ready:
            anchor_count += 1
            centroid = [
                round(float(statistics.fmean(float(p["x"]) for p in points)), 2),
                round(float(statistics.fmean(float(p["y"]) for p in points)), 2),
            ]
            distance_face_units = math.hypot(
                centroid[0] - face_center_x,
                centroid[1] - face_center_y,
            ) / face_width
            near_face = distance_face_units <= max_face_distance
            if near_face:
                near_face_count += 1
        sides[side] = {
            "visible_point_count": len(points),
            "ready": ready,
            "centroid": centroid,
            "distance_to_face_units": (
                round(distance_face_units, 4)
                if distance_face_units is not None
                else None
            ),
            "root_wrist_distance_units": (
                round(root_wrist_distance, 4)
                if root_wrist_distance is not None
                else None
            ),
            "wrist_associated": wrist_associated,
            "near_face": near_face,
        }
    return {
        "hand_anchor_count": anchor_count,
        "hand_near_face_count": near_face_count,
        "hands": sides,
    }


def temporal_pose_summary(
    frame_results: list[dict[str, Any]],
    min_ready_frames: int = 3,
    min_ready_rate: float = 0.30,
    fps: float = 25.0,
    frame_stride: int = 1,
) -> dict[str, Any]:
    evaluable = [
        item
        for item in frame_results
        if item.get("visibility") in {"good", "limited"}
        and item.get("driver_face_bbox") is not None
    ]
    evidence_only_pose_frames = [
        item
        for item in frame_results
        if item.get("pose_evidence_only") is True
        and item.get("driver_pose_detected") is True
    ]
    pose_frames = [
        item for item in evaluable if item.get("driver_pose_detected") is True
    ]
    raw_pose_frames = [
        item for item in evaluable if item.get("raw_driver_pose_detected") is True
    ]
    temporally_recovered_frames = [
        item
        for item in evaluable
        if int(item.get("temporal_held_keypoint_count") or 0) > 0
    ]
    seatbelt_frames = [
        item for item in evaluable if item.get("seatbelt_anchor_ready") is True
    ]
    phone_frames = [
        item for item in evaluable if item.get("phone_anchor_ready") is True
    ]
    hand_frames = [
        item for item in evaluable if int(item.get("hand_anchor_count") or 0) > 0
    ]
    hand_near_face_frames = [
        item
        for item in evaluable
        if int(item.get("hand_near_face_count") or 0) > 0
    ]
    ready_frames = [
        item
        for item in evaluable
        if item.get(
            "upper_body_analysis_ready",
            item.get("driver_analysis_ready"),
        )
        is True
    ]
    pose_rate = len(pose_frames) / len(evaluable) if evaluable else 0.0
    seatbelt_rate = len(seatbelt_frames) / len(evaluable) if evaluable else 0.0
    phone_rate = len(phone_frames) / len(evaluable) if evaluable else 0.0
    hand_rate = len(hand_frames) / len(evaluable) if evaluable else 0.0
    hand_near_face_rate = (
        len(hand_near_face_frames) / len(evaluable) if evaluable else 0.0
    )
    ready_rate = len(ready_frames) / len(evaluable) if evaluable else 0.0
    longest_miss_run = 0
    current_miss_run = 0
    for item in evaluable:
        if item.get(
            "upper_body_analysis_ready",
            item.get("driver_analysis_ready"),
        ) is True:
            current_miss_run = 0
        else:
            current_miss_run += 1
            longest_miss_run = max(longest_miss_run, current_miss_run)
    shoulder_jitter = []
    previous_relative_midpoint = None
    previous_frame = None
    for item in evaluable:
        pose_index = item.get("driver_pose_index")
        poses = item.get("poses") or []
        roi = item.get("upper_body_roi_bbox")
        face = item.get("driver_face_bbox")
        if (
            pose_index is None
            or not (0 <= int(pose_index) < len(poses))
            or not roi
            or not face
        ):
            previous_relative_midpoint = None
            previous_frame = None
            continue
        keypoints = poses[int(pose_index)].get("keypoints") or {}
        left = keypoints.get("left_shoulder") or {}
        right = keypoints.get("right_shoulder") or {}
        if min(
            float(left.get("confidence") or 0.0),
            float(right.get("confidence") or 0.0),
        ) < 0.35:
            previous_relative_midpoint = None
            previous_frame = None
            continue
        midpoint = (
            float(roi[0]) + (float(left["x"]) + float(right["x"])) / 2.0,
            float(roi[1]) + (float(left["y"]) + float(right["y"])) / 2.0,
        )
        face_width = max(1.0, float(face[2]) - float(face[0]))
        face_center = (
            (float(face[0]) + float(face[2])) / 2.0,
            (float(face[1]) + float(face[3])) / 2.0,
        )
        relative_midpoint = (
            (midpoint[0] - face_center[0]) / face_width,
            (midpoint[1] - face_center[1]) / face_width,
        )
        frame_number = int(item.get("frame") or 0)
        if (
            previous_relative_midpoint is not None
            and previous_frame is not None
            and frame_number - previous_frame <= max(1, frame_stride)
        ):
            shoulder_jitter.append(
                math.hypot(
                    relative_midpoint[0] - previous_relative_midpoint[0],
                    relative_midpoint[1] - previous_relative_midpoint[1],
                )
            )
        previous_relative_midpoint = relative_midpoint
        previous_frame = frame_number

    best = None
    if frame_results:
        best = max(
            frame_results,
            key=lambda item: (
                item.get(
                    "upper_body_analysis_ready",
                    item.get("driver_analysis_ready"),
                )
                is True,
                item.get("driver_pose_detected") is True,
                float(item.get("anchor_confidence") or 0.0),
                float(item.get("pose_confidence") or 0.0),
                float(item.get("visibility_score") or 0.0),
            ),
        )

    detected: bool | None = None
    if evaluable:
        detected = (
            len(ready_frames) >= min_ready_frames and ready_rate >= min_ready_rate
        )
    return {
        "processed_frame_count": len(frame_results),
        "evidence_only_pose_frame_count": len(evidence_only_pose_frames),
        "evaluable_driver_frame_count": len(evaluable),
        "driver_pose_frame_count": len(pose_frames),
        "pose_detection_rate": round(pose_rate, 4),
        "raw_driver_pose_frame_count": len(raw_pose_frames),
        "raw_pose_detection_rate": round(
            len(raw_pose_frames) / len(evaluable) if evaluable else 0.0,
            4,
        ),
        "temporally_recovered_frame_count": len(temporally_recovered_frames),
        "temporally_recovered_frame_rate": round(
            len(temporally_recovered_frames) / len(evaluable)
            if evaluable
            else 0.0,
            4,
        ),
        "temporal_rejected_jump_count": sum(
            int(item.get("temporal_rejected_jump_count") or 0)
            for item in evaluable
        ),
        "seatbelt_anchor_frame_count": len(seatbelt_frames),
        "seatbelt_anchor_rate": round(seatbelt_rate, 4),
        "phone_anchor_frame_count": len(phone_frames),
        "phone_anchor_rate": round(phone_rate, 4),
        "hand_anchor_frame_count": len(hand_frames),
        "hand_anchor_rate": round(hand_rate, 4),
        "hand_near_face_frame_count": len(hand_near_face_frames),
        "hand_near_face_rate": round(hand_near_face_rate, 4),
        "analysis_ready_frame_count": len(ready_frames),
        "analysis_ready_rate": round(ready_rate, 4),
        "upper_body_detected": detected,
        "longest_analysis_miss_run": longest_miss_run,
        "longest_analysis_miss_seconds": round(
            longest_miss_run * max(1, frame_stride) / max(fps, 1.0),
            3,
        ),
        "mean_shoulder_jitter_face_units": (
            round(float(statistics.fmean(shoulder_jitter)), 4)
            if shoulder_jitter
            else None
        ),
        "p95_shoulder_jitter_face_units": (
            round(
                sorted(shoulder_jitter)[
                    int(round((len(shoulder_jitter) - 1) * 0.95))
                ],
                4,
            )
            if shoulder_jitter
            else None
        ),
        "best_frame": best.get("frame") if best else None,
        "best_upper_body_roi_uri": best.get("upper_body_roi_uri") if best else None,
        "best_torso_bbox": best.get("torso_bbox_global") if best else None,
        "best_anchor_confidence": best.get("anchor_confidence") if best else None,
    }
