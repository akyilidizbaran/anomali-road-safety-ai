#!/usr/bin/env python3
"""Pure quality, geometry and temporal helpers for the seatbelt baseline."""

from __future__ import annotations

import math
import statistics
from typing import Any

import cv2
import numpy as np


def clamp_bbox(
    bbox: list[float],
    frame_width: int,
    frame_height: int,
) -> list[int] | None:
    x1, y1, x2, y2 = bbox
    result = [
        max(0, min(frame_width - 1, int(round(x1)))),
        max(0, min(frame_height - 1, int(round(y1)))),
        max(1, min(frame_width, int(round(x2)))),
        max(1, min(frame_height, int(round(y2)))),
    ]
    if result[2] - result[0] < 2 or result[3] - result[1] < 2:
        return None
    return result


def torso_quality(
    image_bgr: np.ndarray,
    min_width: int = 56,
    min_height: int = 64,
) -> dict[str, Any]:
    height, width = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    reasons = []
    if width < min_width or height < min_height:
        reasons.append("torso_resolution_too_small")
    if brightness < 22:
        reasons.append("torso_too_dark")
    if contrast < 12:
        reasons.append("torso_low_contrast")
    if sharpness < 18:
        reasons.append("torso_blur_or_soft")
    status = "usable" if not reasons else "limited"
    if width < min_width or height < min_height or brightness < 12:
        status = "not_usable"
    score = (
        min(1.0, width / max(min_width, 1))
        * 0.25
        + min(1.0, height / max(min_height, 1)) * 0.25
        + min(1.0, brightness / 55.0) * 0.15
        + min(1.0, contrast / 38.0) * 0.20
        + min(1.0, sharpness / 90.0) * 0.15
    )
    return {
        "status": status,
        "score": round(float(score), 4),
        "reasons": reasons,
        "width": width,
        "height": height,
        "brightness": round(brightness, 3),
        "contrast": round(contrast, 3),
        "sharpness": round(sharpness, 3),
    }


def _segment_score(
    line: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[float, dict[str, Any]] | None:
    x1, y1, x2, y2 = line
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    diagonal = math.hypot(width, height)
    if length < diagonal * 0.20:
        return None
    angle = abs(math.degrees(math.atan2(dy, dx)))
    if angle > 90:
        angle = 180 - angle
    if not 22 <= angle <= 72:
        return None
    midpoint_x = (x1 + x2) / 2.0
    midpoint_y = (y1 + y2) / 2.0
    if not (
        width * 0.12 <= midpoint_x <= width * 0.88
        and height * 0.08 <= midpoint_y <= height * 0.92
    ):
        return None
    length_score = min(1.0, length / max(diagonal * 0.62, 1.0))
    angle_score = max(0.0, 1.0 - abs(angle - 45.0) / 30.0)
    center_score = max(
        0.0,
        1.0
        - math.hypot(
            (midpoint_x - width / 2.0) / max(width, 1),
            (midpoint_y - height / 2.0) / max(height, 1),
        ),
    )
    score = length_score * 0.50 + angle_score * 0.30 + center_score * 0.20
    return score, {
        "xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
        "length": round(length, 3),
        "angle_degrees": round(angle, 3),
        "score": round(score, 4),
    }


def detect_diagonal_belt_evidence(image_bgr: np.ndarray) -> dict[str, Any]:
    """Find long diagonal line evidence without treating absence as unbelted."""
    height, width = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(gray)
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
    detector = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    detected = detector.detect(enhanced)[0]
    candidates = []
    if detected is not None:
        for raw in detected.reshape(-1, 4):
            scored = _segment_score(tuple(float(value) for value in raw), width, height)
            if scored is not None:
                candidates.append(scored)
    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score = candidates[0][0] if candidates else 0.0
    return {
        "evidence_score": round(float(best_score), 4),
        "candidate_status": "belted" if best_score >= 0.58 else "unknown",
        "best_line": candidates[0][1] if candidates else None,
        "candidate_count": len(candidates),
        "top_candidates": [item[1] for item in candidates[:5]],
    }


def temporal_seatbelt_decision(
    frame_results: list[dict[str, Any]],
    min_evaluable_frames: int = 5,
    min_positive_frames: int = 3,
    min_positive_rate: float = 0.35,
) -> dict[str, Any]:
    evaluable = [
        item
        for item in frame_results
        if item.get("decision_evaluable") is True
        and item.get("quality_status") in {"usable", "limited"}
    ]
    evidence_only = [
        item for item in frame_results if item.get("evidence_only") is True
    ]
    positive = [
        item for item in evaluable if item.get("candidate_status") == "belted"
    ]
    rate = len(positive) / len(evaluable) if evaluable else 0.0
    scores = [float(item.get("evidence_score") or 0.0) for item in positive]
    final_status = "not_evaluable"
    confidence = None
    if len(evaluable) >= min_evaluable_frames:
        final_status = "unknown"
        if len(positive) >= min_positive_frames and rate >= min_positive_rate:
            final_status = "belted"
            confidence = float(statistics.median(scores)) if scores else None
    best = max(
        frame_results,
        key=lambda item: float(item.get("evidence_score") or 0.0),
        default=None,
    )
    return {
        "status": final_status,
        "confidence": round(confidence, 4) if confidence is not None else None,
        "processed_frame_count": len(frame_results),
        "evaluable_frame_count": len(evaluable),
        "evidence_only_frame_count": len(evidence_only),
        "belted_evidence_frame_count": len(positive),
        "belted_evidence_rate": round(rate, 4),
        "best_frame": best.get("frame") if best else None,
        "best_evidence_score": best.get("evidence_score") if best else None,
        "best_torso_roi_uri": best.get("torso_roi_uri") if best else None,
        "unbelted_inference_enabled": False,
        "incorrect_usage_inference_enabled": False,
    }
