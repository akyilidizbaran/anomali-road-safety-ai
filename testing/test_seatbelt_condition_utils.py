import numpy as np

from scripts.benchmarks.seatbelt_condition_utils import (
    driver_context_roi,
    enhance_for_condition,
    local_condition_profile,
    normalized_class_probabilities,
    select_driver_face,
    translate_held_roi,
)


def record_with_face(x=100, y=80, width=40, height=60):
    return {
        "cabin_bbox_xyxy": [200, 300, 1000, 900],
        "driver_face_index": 0,
        "faces": [{"bbox": [x, y, width, height], "confidence": 0.9}],
    }


def test_driver_context_contains_face_and_extends_to_torso():
    roi = driver_context_roi(
        [300, 380, 340, 440],
        [200, 300, 1000, 900],
        "side_driver_window",
        1200,
        1000,
    )
    assert roi is not None
    assert roi[0] < 300
    assert roi[1] <= 380
    assert roi[2] > 340
    assert roi[3] > 560


def test_temporal_face_rejects_large_jump():
    record = record_with_face(x=650)
    face, status = select_driver_face(record, [300, 380, 340, 440])
    assert face is None
    assert status == "face_jump_rejected"


def test_held_roi_translates_with_cabin_motion():
    roi = translate_held_roi(
        [300, 400, 600, 800],
        [100, 200, 1000, 900],
        [80, 210, 980, 910],
        1200,
        1000,
    )
    assert roi == [280, 410, 580, 810]


def test_low_light_routes_to_gamma_clahe_and_brightens():
    image = np.full((120, 160, 3), 18, dtype=np.uint8)
    profile = local_condition_profile(image)
    enhanced = enhance_for_condition(image, profile["preprocessing"])
    assert profile["lighting"] == "night_or_severe_low_light"
    assert float(enhanced.mean()) > float(image.mean())


def test_class_label_normalization():
    result = normalized_class_probabilities(
        {0: "no seatbelt", 1: "seat_belt"},
        [0.2, 0.8],
    )
    assert result == {"belted": 0.8, "unbelted": 0.2}
