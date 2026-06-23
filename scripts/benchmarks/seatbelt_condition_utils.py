#!/usr/bin/env python3
"""Condition-aware ROI and preprocessing helpers for seatbelt classifiers."""

from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np


def clamp_bbox(
    bbox: list[float],
    frame_width: int,
    frame_height: int,
    min_width: int = 24,
    min_height: int = 32,
) -> list[int] | None:
    x1, y1, x2, y2 = bbox
    result = [
        max(0, min(frame_width - 1, int(round(x1)))),
        max(0, min(frame_height - 1, int(round(y1)))),
        max(1, min(frame_width, int(round(x2)))),
        max(1, min(frame_height, int(round(y2)))),
    ]
    if result[2] - result[0] < min_width:
        return None
    if result[3] - result[1] < min_height:
        return None
    return result


def face_bbox_global(
    record: dict[str, Any],
    face_index: int,
) -> list[float] | None:
    faces = record.get("faces") or []
    cabin = record.get("cabin_bbox_xyxy")
    if cabin is None or not 0 <= face_index < len(faces):
        return None
    bbox = faces[face_index].get("bbox")
    if not bbox or len(bbox) != 4:
        return None
    x, y, width, height = [float(value) for value in bbox]
    return [
        float(cabin[0]) + x,
        float(cabin[1]) + y,
        float(cabin[0]) + x + width,
        float(cabin[1]) + y + height,
    ]


def _face_distance(candidate: list[float], previous: list[float]) -> float:
    candidate_width = max(1.0, candidate[2] - candidate[0])
    previous_width = max(1.0, previous[2] - previous[0])
    scale = max(candidate_width, previous_width)
    candidate_center = (
        (candidate[0] + candidate[2]) / 2.0,
        (candidate[1] + candidate[3]) / 2.0,
    )
    previous_center = (
        (previous[0] + previous[2]) / 2.0,
        (previous[1] + previous[3]) / 2.0,
    )
    return math.hypot(
        candidate_center[0] - previous_center[0],
        candidate_center[1] - previous_center[1],
    ) / scale


def select_driver_face(
    record: dict[str, Any],
    previous_face: list[float] | None,
    max_jump_face_units: float = 3.0,
) -> tuple[list[float] | None, str]:
    faces = record.get("faces") or []
    candidates = [
        face_bbox_global(record, index)
        for index in range(len(faces))
    ]
    candidates = [bbox for bbox in candidates if bbox is not None]
    if not candidates:
        return None, "no_face"
    if previous_face is not None:
        ranked = sorted(
            (
                (_face_distance(candidate, previous_face), candidate)
                for candidate in candidates
            ),
            key=lambda item: item[0],
        )
        if ranked[0][0] <= max_jump_face_units:
            return ranked[0][1], "temporal_face_match"
        return None, "face_jump_rejected"
    driver_index = record.get("driver_face_index")
    if driver_index is not None:
        bbox = face_bbox_global(record, int(driver_index))
        if bbox is not None:
            return bbox, "view_profile_assignment"
    return candidates[0], "first_face_fallback"


def driver_context_roi(
    face_bbox: list[float],
    cabin_bbox: list[float],
    view_profile: str,
    frame_width: int,
    frame_height: int,
) -> list[int] | None:
    fx1, fy1, fx2, fy2 = face_bbox
    face_width = max(1.0, fx2 - fx1)
    face_height = max(1.0, fy2 - fy1)
    if view_profile == "side_driver_window":
        proposed = [
            fx1 - 2.2 * face_width,
            fy1 - 0.15 * face_height,
            fx2 + 2.8 * face_width,
            fy2 + 2.8 * face_height,
        ]
    else:
        proposed = [
            fx1 - 2.0 * face_width,
            fy1 - 0.20 * face_height,
            fx2 + 2.0 * face_width,
            fy2 + 3.0 * face_height,
        ]
    bounded = [
        max(float(cabin_bbox[0]), proposed[0]),
        max(float(cabin_bbox[1]), proposed[1]),
        min(float(cabin_bbox[2]), proposed[2]),
        min(float(cabin_bbox[3]), proposed[3]),
    ]
    return clamp_bbox(bounded, frame_width, frame_height)


def translate_held_roi(
    previous_roi: list[float],
    previous_cabin: list[float],
    current_cabin: list[float],
    frame_width: int,
    frame_height: int,
) -> list[int] | None:
    previous_center = (
        (float(previous_cabin[0]) + float(previous_cabin[2])) / 2.0,
        (float(previous_cabin[1]) + float(previous_cabin[3])) / 2.0,
    )
    current_center = (
        (float(current_cabin[0]) + float(current_cabin[2])) / 2.0,
        (float(current_cabin[1]) + float(current_cabin[3])) / 2.0,
    )
    dx = current_center[0] - previous_center[0]
    dy = current_center[1] - previous_center[1]
    translated = [
        float(previous_roi[0]) + dx,
        float(previous_roi[1]) + dy,
        float(previous_roi[2]) + dx,
        float(previous_roi[3]) + dy,
    ]
    bounded = [
        max(float(current_cabin[0]), translated[0]),
        max(float(current_cabin[1]), translated[1]),
        min(float(current_cabin[2]), translated[2]),
        min(float(current_cabin[3]), translated[3]),
    ]
    return clamp_bbox(bounded, frame_width, frame_height)


def local_condition_profile(image_bgr: np.ndarray) -> dict[str, Any]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    dark_ratio = float(np.mean(gray < 35))
    glare_ratio = float(np.mean(gray > 235))
    if brightness < 32 or dark_ratio > 0.78:
        lighting = "night_or_severe_low_light"
        preprocessing = "gamma_clahe"
    elif brightness < 55 or dark_ratio > 0.58:
        lighting = "low_light"
        preprocessing = "clahe"
    else:
        lighting = "normal"
        preprocessing = "raw"
    return {
        "lighting": lighting,
        "preprocessing": preprocessing,
        "brightness": round(brightness, 3),
        "contrast": round(contrast, 3),
        "dark_ratio": round(dark_ratio, 4),
        "glare_ratio": round(glare_ratio, 4),
    }


def enhance_for_condition(
    image_bgr: np.ndarray,
    preprocessing: str,
) -> np.ndarray:
    if preprocessing == "raw":
        return image_bgr.copy()
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    lightness, channel_a, channel_b = cv2.split(lab)
    if preprocessing == "gamma_clahe":
        mean = max(1.0, float(np.mean(lightness))) / 255.0
        gamma = float(np.clip(math.log(0.40) / math.log(mean), 0.35, 0.85))
        lookup = np.array(
            [((index / 255.0) ** gamma) * 255 for index in range(256)],
            dtype=np.uint8,
        )
        lightness = cv2.LUT(lightness, lookup)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(6, 6))
    lightness = clahe.apply(lightness)
    return cv2.cvtColor(
        cv2.merge((lightness, channel_a, channel_b)),
        cv2.COLOR_LAB2BGR,
    )


def normalized_class_probabilities(
    names: dict[int, str] | list[str],
    probabilities: list[float],
) -> dict[str, float]:
    if isinstance(names, list):
        labels = {index: name for index, name in enumerate(names)}
    else:
        labels = {int(index): name for index, name in names.items()}
    result = {"belted": 0.0, "unbelted": 0.0}
    for index, probability in enumerate(probabilities):
        label = str(labels.get(index, index)).lower().replace("-", "_").replace(" ", "_")
        if any(token in label for token in ("no_seat", "without", "unbelt", "not_wear")):
            result["unbelted"] += float(probability)
        elif "seat" in label or "belt" in label:
            result["belted"] += float(probability)
    return {key: round(value, 6) for key, value in result.items()}
