#!/usr/bin/env python3
"""Hybrid pose/optical-flow helpers for continuous driver arm-state evidence."""

from __future__ import annotations

import math
import statistics
from collections import Counter, deque
from typing import Any

import cv2
import numpy as np


ARM_POINTS = (
    "left_shoulder",
    "left_elbow",
    "left_wrist",
    "right_shoulder",
    "right_elbow",
    "right_wrist",
)


def point_distance(first: dict[str, Any], second: dict[str, Any]) -> float:
    return math.hypot(
        float(first["x"]) - float(second["x"]),
        float(first["y"]) - float(second["y"]),
    )


def global_pose_keypoints(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pose_index = record.get("driver_pose_index")
    poses = record.get("poses") or []
    roi = record.get("upper_body_roi_bbox")
    if (
        pose_index is None
        or roi is None
        or not 0 <= int(pose_index) < len(poses)
    ):
        return {}
    local = poses[int(pose_index)].get("keypoints") or {}
    return {
        name: {
            "x": round(float(point["x"]) + float(roi[0]), 2),
            "y": round(float(point["y"]) + float(roi[1]), 2),
            "confidence": round(float(point.get("confidence") or 0.0), 4),
            "source": "pose",
        }
        for name, point in local.items()
        if name in ARM_POINTS and "x" in point and "y" in point
    }


def point_in_bbox(point: dict[str, Any], bbox: list[float]) -> bool:
    return bool(
        float(bbox[0]) <= float(point["x"]) <= float(bbox[2])
        and float(bbox[1]) <= float(point["y"]) <= float(bbox[3])
    )


def distance_to_bbox(point: dict[str, Any], bbox: list[float]) -> float:
    x = float(point["x"])
    y = float(point["y"])
    dx = max(float(bbox[0]) - x, 0.0, x - float(bbox[2]))
    dy = max(float(bbox[1]) - y, 0.0, y - float(bbox[3]))
    return math.hypot(dx, dy)


class HybridArmTracker:
    """Fuse ViTPose observations with forward/backward sparse optical flow."""

    def __init__(
        self,
        observation_confidence: float = 0.30,
        continuation_confidence: float = 0.10,
        max_observation_flow_distance_face_units: float = 0.80,
        max_flow_error_pixels: float = 3.0,
        max_flow_hold_frames: int = 12,
        max_face_hold_frames: int = 25,
    ):
        self.observation_confidence = observation_confidence
        self.continuation_confidence = continuation_confidence
        self.max_observation_flow_distance_face_units = (
            max_observation_flow_distance_face_units
        )
        self.max_flow_error_pixels = max_flow_error_pixels
        self.max_flow_hold_frames = max(0, max_flow_hold_frames)
        self.max_face_hold_frames = max_face_hold_frames
        self.points: dict[str, dict[str, Any]] = {}
        self.previous_gray: np.ndarray | None = None
        self.last_face: list[float] | None = None
        self.last_face_frame: int | None = None
        self.reference_bones: dict[str, tuple[float, float]] = {}

    def reset(self) -> None:
        self.points = {}
        self.previous_gray = None
        self.last_face = None
        self.last_face_frame = None
        self.reference_bones = {}

    def _flow_points(
        self,
        gray: np.ndarray,
    ) -> dict[str, dict[str, Any]]:
        if self.previous_gray is None or not self.points:
            return {}
        names = list(self.points)
        previous = np.array(
            [
                [
                    float(self.points[name]["x"]),
                    float(self.points[name]["y"]),
                ]
                for name in names
            ],
            dtype=np.float32,
        ).reshape(-1, 1, 2)
        current, status_forward, _ = cv2.calcOpticalFlowPyrLK(
            self.previous_gray,
            gray,
            previous,
            None,
            winSize=(31, 31),
            maxLevel=3,
            criteria=(
                cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                30,
                0.01,
            ),
        )
        if current is None or status_forward is None:
            return {}
        backward, status_backward, _ = cv2.calcOpticalFlowPyrLK(
            gray,
            self.previous_gray,
            current,
            None,
            winSize=(31, 31),
            maxLevel=3,
            criteria=(
                cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                30,
                0.01,
            ),
        )
        if backward is None or status_backward is None:
            return {}
        flow: dict[str, dict[str, Any]] = {}
        for index, name in enumerate(names):
            if not status_forward[index, 0] or not status_backward[index, 0]:
                continue
            previous_flow_age = int(self.points[name].get("flow_age") or 0)
            if previous_flow_age >= self.max_flow_hold_frames:
                continue
            error = float(np.linalg.norm(previous[index, 0] - backward[index, 0]))
            if error > self.max_flow_error_pixels:
                continue
            flow[name] = {
                "x": round(float(current[index, 0, 0]), 2),
                "y": round(float(current[index, 0, 1]), 2),
                "confidence": round(
                    max(0.10, float(self.points[name].get("confidence") or 0.0) * 0.96),
                    4,
                ),
                "source": "optical_flow",
                "flow_error": round(error, 3),
                "flow_age": previous_flow_age + 1,
            }
        return flow

    @staticmethod
    def _chain_in_driver_region(
        side: str,
        points: dict[str, dict[str, Any]],
        face_bbox: list[float],
    ) -> bool:
        face_width = max(1.0, float(face_bbox[2]) - float(face_bbox[0]))
        face_center_x = (float(face_bbox[0]) + float(face_bbox[2])) / 2.0
        min_x = face_center_x - 5.0 * face_width
        max_x = face_center_x + 5.0 * face_width
        shoulder_min_y = float(face_bbox[1]) + 0.20 * face_width
        shoulder_max_y = float(face_bbox[3]) + 2.00 * face_width
        chain_max_y = float(face_bbox[3]) + 4.50 * face_width
        shoulder = points.get(f"{side}_shoulder")
        elbow = points.get(f"{side}_elbow")
        wrist = points.get(f"{side}_wrist")
        if not shoulder or not elbow or not wrist:
            return False
        return bool(
            min_x <= float(shoulder["x"]) <= max_x
            and shoulder_min_y <= float(shoulder["y"]) <= shoulder_max_y
            and all(
                min_x <= float(point["x"]) <= max_x
                and float(point["y"]) <= chain_max_y
                for point in (elbow, wrist)
            )
        )

    def _anatomical_chain_valid(
        self,
        side: str,
        points: dict[str, dict[str, Any]],
        face_width: float,
    ) -> bool:
        shoulder = points.get(f"{side}_shoulder")
        elbow = points.get(f"{side}_elbow")
        wrist = points.get(f"{side}_wrist")
        if not shoulder or not elbow or not wrist:
            return False
        upper = point_distance(shoulder, elbow)
        lower = point_distance(elbow, wrist)
        if not (
            face_width * 0.25 <= upper <= face_width * 5.5
            and face_width * 0.20 <= lower <= face_width * 5.5
        ):
            return False
        reference = self.reference_bones.get(side)
        if reference is not None:
            if not (
                reference[0] * 0.45 <= upper <= reference[0] * 2.20
                and reference[1] * 0.45 <= lower <= reference[1] * 2.20
            ):
                return False
            self.reference_bones[side] = (
                0.85 * reference[0] + 0.15 * upper,
                0.85 * reference[1] + 0.15 * lower,
            )
        else:
            self.reference_bones[side] = (upper, lower)
        return True

    def update(
        self,
        frame_bgr: np.ndarray,
        observations: dict[str, dict[str, Any]],
        face_bbox: list[float] | None,
        cabin_bbox: list[float] | None,
        frame_number: int,
    ) -> dict[str, Any]:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        if face_bbox is not None:
            self.last_face = [float(value) for value in face_bbox]
            self.last_face_frame = frame_number
        elif (
            self.last_face_frame is None
            or frame_number - self.last_face_frame > self.max_face_hold_frames
        ):
            self.last_face = None
        active_face = self.last_face
        face_width = (
            max(1.0, active_face[2] - active_face[0])
            if active_face is not None
            else 1.0
        )
        flow = self._flow_points(gray)
        fused: dict[str, dict[str, Any]] = {}
        rejected_observations = 0
        for name in ARM_POINTS:
            observation = observations.get(name)
            tracked = flow.get(name)
            confidence = float((observation or {}).get("confidence") or 0.0)
            accept_observation = confidence >= self.observation_confidence
            low_confidence_continuation = bool(
                observation is not None
                and confidence >= self.continuation_confidence
                and tracked is not None
                and point_distance(observation, tracked)
                <= face_width * self.max_observation_flow_distance_face_units
            )
            if accept_observation and tracked is not None:
                if (
                    point_distance(observation, tracked)
                    > face_width * 1.35
                ):
                    accept_observation = False
                    rejected_observations += 1
            if accept_observation:
                fused[name] = {
                    **observation,
                    "source": "observed",
                    "flow_age": 0,
                }
            elif low_confidence_continuation:
                fused[name] = {
                    "x": round(
                        0.65 * float(tracked["x"])
                        + 0.35 * float(observation["x"]),
                        2,
                    ),
                    "y": round(
                        0.65 * float(tracked["y"])
                        + 0.35 * float(observation["y"]),
                        2,
                    ),
                    "confidence": round(
                        max(self.continuation_confidence, confidence),
                        4,
                    ),
                    "source": "tracked_low_confidence",
                    "flow_age": int(tracked.get("flow_age") or 0),
                }
            elif tracked is not None:
                fused[name] = tracked
        if cabin_bbox is not None:
            fused = {
                name: point
                for name, point in fused.items()
                if point_in_bbox(point, cabin_bbox)
            }
        chain_valid = {
            side: bool(
                active_face is not None
                and self._chain_in_driver_region(side, fused, active_face)
                and self._anatomical_chain_valid(side, fused, face_width)
            )
            for side in ("left", "right")
        }
        self.points = fused
        self.previous_gray = gray
        return {
            "points": fused,
            "face_bbox": active_face,
            "face_source": (
                "observed"
                if face_bbox is not None
                else ("held" if active_face is not None else "unavailable")
            ),
            "chain_valid": chain_valid,
            "complete_arm_count": sum(chain_valid.values()),
            "optical_flow_point_count": sum(
                point.get("source") == "optical_flow"
                for point in fused.values()
            ),
            "low_confidence_point_count": sum(
                point.get("source") == "tracked_low_confidence"
                for point in fused.values()
            ),
            "rejected_observation_count": rejected_observations,
        }


def driver_identity_consistent(
    previous_face: list[float] | None,
    previous_cabin: list[float] | None,
    current_face: list[float] | None,
    current_cabin: list[float] | None,
    max_normalized_jump: float = 0.18,
) -> bool:
    if (
        previous_face is None
        or previous_cabin is None
        or current_face is None
        or current_cabin is None
    ):
        return True

    def normalized_center(
        face: list[float],
        cabin: list[float],
    ) -> tuple[float, float]:
        width = max(1.0, float(cabin[2]) - float(cabin[0]))
        height = max(1.0, float(cabin[3]) - float(cabin[1]))
        return (
            (
                (float(face[0]) + float(face[2])) / 2.0
                - float(cabin[0])
            )
            / width,
            (
                (float(face[1]) + float(face[3])) / 2.0
                - float(cabin[1])
            )
            / height,
        )

    previous = normalized_center(previous_face, previous_cabin)
    current = normalized_center(current_face, current_cabin)
    return math.hypot(current[0] - previous[0], current[1] - previous[1]) <= (
        max_normalized_jump
    )


def wheel_zone_bbox(
    face_bbox: list[float],
    profile: dict[str, Any] | None,
) -> list[float] | None:
    zone = (profile or {}).get("wheel_zone_face_units")
    if not zone:
        return None
    face_width = max(1.0, float(face_bbox[2]) - float(face_bbox[0]))
    center_x = (float(face_bbox[0]) + float(face_bbox[2])) / 2.0
    center_y = (float(face_bbox[1]) + float(face_bbox[3])) / 2.0
    return [
        center_x + float(zone["left"]) * face_width,
        center_y + float(zone["top"]) * face_width,
        center_x + float(zone["right"]) * face_width,
        center_y + float(zone["bottom"]) * face_width,
    ]


def ear_zone_bboxes(face_bbox: list[float]) -> dict[str, list[float]]:
    """Approximate image-left/right ear interaction zones from a face box."""
    x1, y1, x2, y2 = [float(value) for value in face_bbox]
    width = max(1.0, x2 - x1)
    height = max(1.0, y2 - y1)
    return {
        "image_left": [
            x1 - 0.75 * width,
            y1 - 0.15 * height,
            x1 + 0.25 * width,
            y2 + 0.65 * height,
        ],
        "image_right": [
            x2 - 0.25 * width,
            y1 - 0.15 * height,
            x2 + 0.75 * width,
            y2 + 0.65 * height,
        ],
    }


def classify_arm_state(
    tracked: dict[str, Any],
    profile: dict[str, Any] | None,
) -> dict[str, Any]:
    points = tracked.get("points") or {}
    face = tracked.get("face_bbox")
    chain_valid = tracked.get("chain_valid") or {}
    if face is None:
        return {
            "state": "not_evaluable",
            "confidence": None,
            "reasons": ["driver_face_unavailable"],
            "side_states": {},
            "wheel_zone_bbox": None,
        }
    face_width = max(1.0, float(face[2]) - float(face[0]))
    zone = wheel_zone_bbox(face, profile)
    ear_zones = ear_zone_bboxes(face)
    side_states: dict[str, Any] = {}
    near_face_sides = []
    raised_sides = []
    wheel_sides = []
    visible_off_wheel_sides = []
    for side in ("left", "right"):
        shoulder = points.get(f"{side}_shoulder")
        elbow = points.get(f"{side}_elbow")
        wrist = points.get(f"{side}_wrist")
        complete = bool(chain_valid.get(side) and shoulder and elbow and wrist)
        near_face = bool(
            complete and distance_to_bbox(wrist, face) <= face_width * 1.35
        )
        near_ear_zone = next(
            (
                name
                for name, ear_zone in ear_zones.items()
                if complete and point_in_bbox(wrist, ear_zone)
            ),
            None,
        )
        raised = bool(
            complete
            and (
                float(wrist["y"]) <= float(shoulder["y"]) + face_width * 0.35
                or (
                    float(elbow["y"]) <= float(shoulder["y"]) + face_width * 0.25
                    and float(wrist["y"]) < float(elbow["y"]) + face_width * 0.40
                )
            )
        )
        in_wheel_zone = bool(complete and zone and point_in_bbox(wrist, zone))
        if near_face:
            near_face_sides.append(side)
        if raised:
            raised_sides.append(side)
        if in_wheel_zone:
            wheel_sides.append(side)
        if complete and zone and not in_wheel_zone:
            visible_off_wheel_sides.append(side)
        side_states[side] = {
            "complete": complete,
            "near_face": near_face,
            "near_ear": near_ear_zone is not None,
            "near_ear_zone": near_ear_zone,
            "raised": raised,
            "in_expected_wheel_zone": in_wheel_zone,
            "wrist_source": (wrist or {}).get("source"),
        }
    complete_count = sum(item["complete"] for item in side_states.values())
    reasons = []
    if near_face_sides:
        state = "hand_near_face"
        reasons.append(f"near_face={','.join(near_face_sides)}")
    elif raised_sides:
        state = "arm_raised"
        reasons.append(f"raised={','.join(raised_sides)}")
    elif wheel_sides:
        state = "hands_on_wheel_candidate"
        reasons.append(f"expected_wheel_zone={','.join(wheel_sides)}")
    elif visible_off_wheel_sides:
        state = "hand_off_wheel_candidate"
        reasons.append(f"outside_expected_wheel_zone={','.join(visible_off_wheel_sides)}")
    elif complete_count:
        state = "arms_visible_other"
        reasons.append("complete_arm_without_special_state")
    else:
        state = "unknown"
        reasons.append("no_anatomically_valid_arm_chain")
    source_scores = {
        "observed": 1.0,
        "tracked_low_confidence": 0.72,
        "optical_flow": 0.58,
    }
    relevant_sources = [
        source_scores.get(str(point.get("source")), 0.0)
        for name, point in points.items()
        if name.endswith(("elbow", "wrist"))
    ]
    confidence = (
        statistics.fmean(relevant_sources) * min(1.0, complete_count / 1.0)
        if relevant_sources and complete_count
        else None
    )
    return {
        "state": state,
        "confidence": round(float(confidence), 4)
        if confidence is not None
        else None,
        "reasons": reasons,
        "side_states": side_states,
        "wheel_zone_bbox": [round(value, 2) for value in zone] if zone else None,
        "ear_zone_bboxes": {
            name: [round(value, 2) for value in ear_zone]
            for name, ear_zone in ear_zones.items()
        },
    }


class TemporalStateVoter:
    def __init__(
        self,
        window_size: int = 9,
        minimum_votes: int = 4,
    ):
        self.window = deque(maxlen=max(1, window_size))
        self.minimum_votes = max(1, minimum_votes)

    def update(self, state: str) -> str:
        self.window.append(state)
        usable = [
            item
            for item in self.window
            if item not in {"unknown", "not_evaluable"}
        ]
        if not usable:
            return state
        winner, count = Counter(usable).most_common(1)[0]
        return winner if count >= self.minimum_votes else state


def arm_temporal_summary(
    records: list[dict[str, Any]],
    fps: float,
) -> dict[str, Any]:
    evaluable = [
        item
        for item in records
        if item.get("decision_evaluable")
        and item.get("state") != "not_evaluable"
    ]
    available = [
        item
        for item in evaluable
        if item.get("state") not in {"unknown", "not_evaluable"}
    ]
    state_counts = Counter(item.get("state") for item in evaluable)
    longest_unavailable = 0
    current = 0
    transitions = 0
    previous = None
    for item in evaluable:
        state = item.get("state")
        if state in {"unknown", "not_evaluable"}:
            current += 1
            longest_unavailable = max(longest_unavailable, current)
        else:
            current = 0
            if previous is not None and state != previous:
                transitions += 1
            previous = state
    return {
        "processed_frame_count": len(records),
        "evaluable_frame_count": len(evaluable),
        "available_state_frame_count": len(available),
        "available_state_rate": round(
            len(available) / len(evaluable) if evaluable else 0.0,
            4,
        ),
        "state_rates": {
            state: round(count / len(evaluable), 4) if evaluable else 0.0
            for state, count in sorted(state_counts.items())
        },
        "optical_flow_recovered_frame_count": sum(
            int(item.get("optical_flow_point_count") or 0) > 0
            for item in records
        ),
        "longest_unavailable_frames": longest_unavailable,
        "longest_unavailable_seconds": round(
            longest_unavailable / max(fps, 1.0),
            3,
        ),
        "state_transition_count": transitions,
        "risk_enabled": False,
    }
