from scripts.benchmarks.cabin_utils import (
    assign_driver_candidate,
    cabin_roi_bbox,
    temporal_cabin_summary,
    visibility_decision,
)


def test_cabin_roi_bbox_is_clamped_to_frame():
    profile = {"roi": {"left": 0.0, "top": 0.0, "right": 1.0, "bottom": 0.7}}
    assert cabin_roi_bbox([-10, -20, 120, 180], 100, 100, profile) == [0, 0, 100, 100]


def test_visibility_decision_rejects_tiny_dark_roi():
    score, visibility, reasons = visibility_decision(
        {
            "brightness": 10,
            "contrast": 8,
            "sharpness": 12,
            "dark_ratio": 0.9,
            "glare_ratio": 0.0,
            "min_dimension": 40,
        }
    )
    assert score < 0.2
    assert visibility == "not_visible"
    assert "cabin_roi_too_small" in reasons


def test_visibility_decision_accepts_clear_large_roi():
    score, visibility, reasons = visibility_decision(
        {
            "brightness": 105,
            "contrast": 60,
            "sharpness": 260,
            "dark_ratio": 0.08,
            "glare_ratio": 0.04,
            "min_dimension": 320,
        }
    )
    assert score >= 0.64
    assert visibility == "good"
    assert reasons == ["cabin_roi_quality_usable"]


def test_visibility_decision_allows_dark_windshield_with_usable_detail():
    score, visibility, reasons = visibility_decision(
        {
            "brightness": 30,
            "contrast": 28,
            "sharpness": 50,
            "dark_ratio": 0.84,
            "glare_ratio": 0.01,
            "min_dimension": 300,
        }
    )
    assert score >= 0.44
    assert visibility == "limited"
    assert "high_dark_pixel_ratio" in reasons


def test_front_lhd_assigns_right_side_face():
    faces = [
        {"bbox": [10, 10, 40, 40], "confidence": 0.9},
        {"bbox": [120, 10, 35, 35], "confidence": 0.8},
    ]
    index, status = assign_driver_candidate(faces, "front_lhd", roi_width=180)
    assert index == 1
    assert status == "assigned_front_lhd_right_side_face"


def test_side_view_does_not_force_driver_role_with_multiple_faces():
    index, status = assign_driver_candidate(
        [
            {"bbox": [120, 80, 80, 100], "confidence": 0.9},
            {"bbox": [80, 40, 60, 70], "confidence": 0.8},
        ],
        "side_driver_window",
        roi_width=240,
    )
    assert index is None
    assert status == "side_view_multiple_faces_role_ambiguous"


def test_unknown_profile_does_not_assign_driver():
    index, status = assign_driver_candidate(
        [{"bbox": [10, 10, 40, 40], "confidence": 0.9}],
        "unknown",
        roi_width=180,
    )
    assert index is None
    assert status == "profile_unknown_role_not_assigned"


def test_temporal_summary_requires_multiple_driver_frames():
    frames = [
        {
            "frame": 1,
            "visibility": "good",
            "visibility_score": 0.8,
            "face_count": 1,
            "driver_candidate_detected": True,
            "role_assignment_status": "assigned_front_lhd_right_side_face",
            "max_face_confidence": 0.9,
        },
        {
            "frame": 2,
            "visibility": "limited",
            "visibility_score": 0.6,
            "face_count": 1,
            "driver_candidate_detected": False,
            "role_assignment_status": "assigned_front_lhd_right_side_face",
            "max_face_confidence": 0.7,
        },
    ]
    summary = temporal_cabin_summary(frames, min_driver_frames=3)
    assert summary["driver_candidate_detected"] is False
    assert summary["occupant_count_estimate"] == 1
    assert summary["temporal_detection_rate"] == 1.0
    assert summary["raw_face_detection_rate"] == 1.0


def test_temporal_summary_keeps_assigned_role_when_some_frames_have_no_face():
    frames = [
        {
            "frame": 1,
            "visibility": "good",
            "visibility_score": 0.8,
            "face_count": 1,
            "driver_candidate_detected": True,
            "role_assignment_status": "assigned_front_lhd_right_side_face",
        },
        {
            "frame": 2,
            "visibility": "good",
            "visibility_score": 0.7,
            "face_count": 0,
            "driver_candidate_detected": None,
            "role_assignment_status": "no_face_detected",
        },
        {
            "frame": 3,
            "visibility": "good",
            "visibility_score": 0.7,
            "face_count": 0,
            "driver_candidate_detected": None,
            "role_assignment_status": "no_face_detected",
        },
    ]
    summary = temporal_cabin_summary(frames, min_driver_frames=1)
    assert summary["role_assignment_status"] == "assigned_front_lhd_right_side_face"
    assert summary["driver_candidate_detected"] is True
    assert summary["occupant_count_estimate"] == 1
    assert summary["longest_eligible_face_miss_run"] == 2


def test_temporal_summary_keeps_repeated_higher_occupant_count():
    frames = [
        {
            "frame": frame,
            "visibility": "limited",
            "visibility_score": 0.6,
            "face_count": 2 if frame in {4, 5, 6} else 1,
            "driver_candidate_detected": None,
            "role_assignment_status": "side_view_multiple_faces_role_ambiguous",
        }
        for frame in range(1, 21)
    ]
    summary = temporal_cabin_summary(frames)
    assert summary["occupant_count_estimate"] == 2
