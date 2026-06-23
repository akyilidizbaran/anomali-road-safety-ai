from scripts.benchmarks.driver_torso_utils import (
    deterministic_torso_bbox,
    driver_face_global_bbox,
    smooth_bbox,
    temporal_torso_summary,
    torso_quality_decision,
)


PROFILE = {
    "torso": {
        "left_face_widths": 2.0,
        "right_face_widths": 2.0,
        "top_face_heights_from_bottom": -0.1,
        "bottom_face_heights_from_bottom": 2.7,
    }
}


def test_driver_face_bbox_maps_from_cabin_coordinates():
    assert driver_face_global_bbox(
        {
            "cabin_bbox_xyxy": [100, 50, 300, 200],
            "driver_face_index": 0,
            "faces": [{"bbox": [20, 30, 40, 50]}],
        }
    ) == [120, 80, 160, 130]


def test_deterministic_torso_starts_below_face_and_expands_to_chest():
    geometry = deterministic_torso_bbox(
        face_bbox=[200, 100, 240, 150],
        vehicle_bbox=[100, 80, 400, 360],
        cabin_bbox=[110, 85, 390, 320],
        frame_width=500,
        frame_height=400,
        profile=PROFILE,
    )
    x1, y1, x2, y2 = geometry["bbox"]
    assert x1 == 140
    assert x2 == 300
    assert 140 <= y1 <= 150
    assert y2 == 285
    assert geometry["retained_area_ratio"] == 1.0


def test_deterministic_torso_is_clamped_to_target_vehicle():
    geometry = deterministic_torso_bbox(
        face_bbox=[360, 100, 400, 150],
        vehicle_bbox=[100, 80, 390, 300],
        cabin_bbox=[120, 90, 380, 260],
        frame_width=500,
        frame_height=400,
        profile=PROFILE,
    )
    assert geometry["bbox"][2] == 390
    assert geometry["bbox"][3] == 285
    assert geometry["retained_area_ratio"] < 1.0


def test_deterministic_torso_caps_extension_below_cabin():
    geometry = deterministic_torso_bbox(
        face_bbox=[200, 100, 240, 150],
        vehicle_bbox=[100, 80, 400, 500],
        cabin_bbox=[120, 90, 380, 220],
        frame_width=500,
        frame_height=500,
        profile={
            "torso": {
                **PROFILE["torso"],
                "max_bottom_below_cabin_face_heights": 0.5,
            }
        },
    )
    assert geometry["bbox"][3] == 245
    assert geometry["below_cabin_vertical_ratio"] < 0.3


def test_quality_rejects_tiny_face_and_torso():
    score, status, reasons = torso_quality_decision(
        {
            "bbox": [10, 10, 45, 60],
            "face_width": 12,
            "face_height": 15,
            "retained_area_ratio": 1.0,
            "below_cabin_vertical_ratio": 0.0,
        },
        face_confidence=0.9,
    )
    assert score < 0.7
    assert status == "not_usable"
    assert "driver_face_too_small" in reasons
    assert "torso_roi_too_narrow" in reasons


def test_quality_accepts_large_unclipped_torso():
    score, status, reasons = torso_quality_decision(
        {
            "bbox": [10, 10, 210, 280],
            "face_width": 52,
            "face_height": 68,
            "retained_area_ratio": 0.95,
            "below_cabin_vertical_ratio": 0.1,
        },
        face_confidence=0.92,
    )
    assert score >= 0.8
    assert status == "usable"
    assert reasons == ["deterministic_torso_roi_usable"]


def test_front_profile_can_allow_expected_below_cabin_chest_region():
    _, status, reasons = torso_quality_decision(
        {
            "bbox": [10, 10, 210, 280],
            "face_width": 52,
            "face_height": 68,
            "retained_area_ratio": 0.95,
            "below_cabin_vertical_ratio": 0.7,
        },
        face_confidence=0.92,
        max_below_cabin_ratio=0.8,
    )
    assert status == "usable"
    assert "torso_roi_exterior_contamination" not in reasons


def test_smoothing_reduces_single_frame_bbox_jitter():
    assert smooth_bbox([100, 100, 200, 300], [120, 90, 220, 290], 0.25) == [
        105,
        98,
        205,
        298,
    ]


def test_temporal_summary_requires_repeated_usable_torso():
    frames = [
        {
            "frame": frame,
            "visibility": "limited",
            "driver_face_bbox": [10, 10, 40, 50],
            "torso_status": "usable" if frame <= 3 else "not_usable",
            "torso_quality_score": 0.8 if frame <= 3 else 0.4,
            "torso_bbox": [5, 40, 100, 180],
            "torso_roi_uri": f"frame_{frame}.jpg",
        }
        for frame in range(1, 6)
    ]
    summary = temporal_torso_summary(
        frames,
        min_usable_frames=3,
        min_usable_rate=0.5,
    )
    assert summary["usable_torso_rate"] == 0.6
    assert summary["torso_baseline_ready"] is True
    assert summary["longest_torso_miss_run"] == 2


def test_temporal_summary_is_unknown_without_driver_face():
    summary = temporal_torso_summary(
        [
            {
                "frame": 1,
                "visibility": "good",
                "driver_face_bbox": None,
                "torso_status": "not_evaluable",
            }
        ]
    )
    assert summary["evaluable_driver_frame_count"] == 0
    assert summary["torso_baseline_ready"] is None
