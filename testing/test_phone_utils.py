from scripts.benchmarks.phone_utils import (
    classify_phone_detection,
    driver_face_global_bbox,
    face_near_crop_bbox,
    phone_inference_roi_bbox,
    phone_search_roi_bbox,
    temporal_phone_call_summary,
    temporal_phone_call_timeline,
    temporal_phone_summary,
)


def frame_record():
    return {
        "vehicle_bbox_xyxy": [100, 100, 900, 700],
        "cabin_bbox_xyxy": [220, 140, 760, 390],
        "driver_face_index": 0,
        "faces": [{"bbox": [360, 70, 50, 60], "confidence": 0.9}],
    }


def test_driver_face_global_bbox_maps_cabin_coordinates():
    assert driver_face_global_bbox(frame_record()) == [580, 210, 630, 270]


def test_phone_search_roi_clamps_to_vehicle_and_contains_face():
    roi = phone_search_roi_bbox(frame_record(), 1000, 800, "front_lhd")
    assert roi is not None
    face = driver_face_global_bbox(frame_record())
    assert roi[0] <= face[0] <= roi[2]
    assert roi[1] <= face[1] <= roi[3]
    assert roi[0] >= 100
    assert roi[2] <= 900


def test_face_near_crop_contains_driver_face():
    face = driver_face_global_bbox(frame_record())
    roi = face_near_crop_bbox(face, 1000, 800)
    assert roi is not None
    assert roi[0] <= face[0] < face[2] <= roi[2]
    assert roi[1] <= face[1] < face[3] <= roi[3]


def test_phone_inference_roi_selects_face_near_mode():
    face = driver_face_global_bbox(frame_record())
    assert phone_inference_roi_bbox(
        frame_record(), 1000, 800, "front_lhd", "face_near"
    ) == face_near_crop_bbox(face, 1000, 800)


def test_classify_phone_detection_rejects_huge_box():
    result = classify_phone_detection(
        [100, 100, 500, 500],
        [100, 100, 600, 600],
        [300, 150, 350, 210],
    )
    assert result["accepted"] is False
    assert "phone_box_too_large" in result["reasons"]


def test_classify_phone_detection_rejects_face_scale_false_positive():
    result = classify_phone_detection(
        [100, 100, 260, 230],
        [0, 0, 500, 500],
        [300, 150, 350, 210],
    )
    assert result["accepted"] is False
    assert "phone_box_too_wide_for_face_scale" in result["reasons"]


def test_temporal_phone_summary_keeps_risk_null():
    summary = temporal_phone_summary(
        [
            {"decision_evaluable": True, "phone_detected": True, "phone_confidence": 0.7, "phone_area": 30, "frame": 1, "phone_bbox": [1, 2, 3, 4]},
            {"decision_evaluable": True, "phone_detected": True, "phone_confidence": 0.8, "phone_area": 25, "frame": 2, "phone_bbox": [2, 3, 4, 5], "object_near_face": True},
            {"decision_evaluable": True, "phone_detected": False},
        ],
        min_evaluable_frames=3,
        min_positive_frames=2,
        min_positive_rate=0.5,
    )
    assert summary["status"] == "detected"
    assert summary["detection_rate"] == 0.6667
    assert summary["object_near_face_rate"] == 0.5
    assert summary["phone_risk"] is None


def arm_record(frame, state="hand_near_face", side="left", confidence=0.9):
    return {
        "frame": frame,
        "decision_evaluable": True,
        "state": state,
        "state_confidence": confidence,
        "side_states": {
            "left": {
                "complete": side == "left",
                "near_face": state == "hand_near_face" and side == "left",
                "near_ear": state == "hand_near_face" and side == "left",
            },
            "right": {
                "complete": side == "right",
                "near_face": state == "hand_near_face" and side == "right",
                "near_ear": state == "hand_near_face" and side == "right",
            },
        },
    }


def test_pose_only_sustained_hand_near_ear_can_mark_call_likely():
    summary = temporal_phone_call_summary(
        [arm_record(frame) for frame in range(1, 26)],
        fps=25.0,
        phone_object_detected=False,
    )
    assert summary["phone_call_status"] == "handheld_call_likely"
    assert summary["phone_call_evidence_source"] == "pose_temporal"
    assert summary["phone_object_detected"] is False
    assert summary["phone_risk"] is None


def test_pose_only_call_respects_dominant_side_threshold():
    records = [arm_record(frame, side="left") for frame in range(1, 16)]
    records.extend(arm_record(frame, side="right") for frame in range(16, 26))
    summary = temporal_phone_call_summary(
        records,
        fps=25.0,
        phone_object_detected=False,
        min_dominant_side_rate=0.70,
    )
    assert summary["phone_call_status"] == "candidate"
    assert summary["dominant_hand_side_rate"] == 0.6


def test_brief_face_touch_stays_candidate():
    records = [arm_record(frame, state="arms_visible_other") for frame in range(1, 31)]
    records[9:14] = [arm_record(frame) for frame in range(10, 15)]
    summary = temporal_phone_call_summary(records, fps=25.0)
    assert summary["phone_call_status"] == "candidate"
    assert summary["longest_hand_near_ear_seconds"] == 0.2


def test_phone_call_behavior_requires_evaluable_window():
    records = [arm_record(frame) for frame in range(1, 6)]
    summary = temporal_phone_call_summary(records, fps=25.0)
    assert summary["phone_call_status"] == "not_evaluable"


def test_phone_call_timeline_is_causal_and_activates_after_duration():
    timeline = temporal_phone_call_timeline(
        [arm_record(frame) for frame in range(1, 31)],
        fps=25.0,
        window_seconds=2.0,
    )
    assert timeline[5]["phone_call_status"] == "not_evaluable"
    assert timeline[10]["phone_call_status"] == "candidate"
    assert timeline[20]["phone_call_status"] == "handheld_call_likely"


def test_phone_call_timeline_hysteresis_holds_then_releases():
    records = [arm_record(frame) for frame in range(1, 26)]
    records.extend(
        arm_record(frame, state="arms_visible_other") for frame in range(26, 76)
    )
    timeline = temporal_phone_call_timeline(
        records,
        fps=25.0,
        window_seconds=2.0,
        exit_hand_near_ear_rate=0.20,
    )
    assert timeline[25]["phone_call_status"] == "handheld_call_likely"
    assert timeline[35]["phone_call_status"] == "handheld_call_likely"
    assert timeline[75]["phone_call_status"] == "not_detected"
