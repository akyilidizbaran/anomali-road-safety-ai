import cv2
import numpy as np

from scripts.benchmarks.seatbelt_utils import (
    clamp_bbox,
    detect_diagonal_belt_evidence,
    temporal_seatbelt_decision,
    torso_quality,
)


def test_clamp_bbox_rejects_empty_crop():
    assert clamp_bbox([20, 20, 20, 40], 100, 100) is None
    assert clamp_bbox([-10, 5, 80, 120], 100, 100) == [0, 5, 80, 100]


def test_torso_quality_rejects_tiny_dark_crop():
    crop = np.zeros((20, 20, 3), dtype=np.uint8)
    quality = torso_quality(crop)
    assert quality["status"] == "not_usable"
    assert "torso_resolution_too_small" in quality["reasons"]


def test_diagonal_line_produces_positive_belt_evidence():
    crop = np.zeros((160, 120, 3), dtype=np.uint8)
    cv2.line(crop, (15, 15), (100, 145), (255, 255, 255), 5)
    result = detect_diagonal_belt_evidence(crop)
    assert result["candidate_status"] == "belted"
    assert result["evidence_score"] >= 0.58


def test_horizontal_line_is_not_belt_evidence():
    crop = np.zeros((160, 120, 3), dtype=np.uint8)
    cv2.line(crop, (10, 80), (110, 80), (255, 255, 255), 5)
    result = detect_diagonal_belt_evidence(crop)
    assert result["candidate_status"] == "unknown"


def test_temporal_decision_never_infers_unbelted_from_absence():
    frames = [
        {
            "frame": frame,
            "decision_evaluable": True,
            "evidence_only": False,
            "quality_status": "usable",
            "candidate_status": "unknown",
            "evidence_score": 0.0,
        }
        for frame in range(1, 11)
    ]
    result = temporal_seatbelt_decision(frames)
    assert result["status"] == "unknown"
    assert result["unbelted_inference_enabled"] is False


def test_temporal_decision_requires_repeated_positive_evidence():
    frames = [
        {
            "frame": frame,
            "decision_evaluable": True,
            "evidence_only": False,
            "quality_status": "usable",
            "candidate_status": "belted" if frame <= 4 else "unknown",
            "evidence_score": 0.8 if frame <= 4 else 0.0,
            "torso_roi_uri": f"frame_{frame}.jpg",
        }
        for frame in range(1, 9)
    ]
    result = temporal_seatbelt_decision(frames)
    assert result["status"] == "belted"
    assert result["belted_evidence_rate"] == 0.5


def test_evidence_only_frames_do_not_vote():
    result = temporal_seatbelt_decision(
        [
            {
                "frame": frame,
                "decision_evaluable": False,
                "evidence_only": True,
                "quality_status": "usable",
                "candidate_status": "belted",
                "evidence_score": 0.9,
            }
            for frame in range(1, 10)
        ]
    )
    assert result["status"] == "not_evaluable"
    assert result["evidence_only_frame_count"] == 9
