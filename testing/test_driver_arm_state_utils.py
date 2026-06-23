import cv2
import numpy as np

from scripts.benchmarks.driver_arm_state_utils import (
    HybridArmTracker,
    TemporalStateVoter,
    arm_temporal_summary,
    classify_arm_state,
    driver_identity_consistent,
    ear_zone_bboxes,
    global_pose_keypoints,
    point_in_bbox,
)


PROFILE = {
    "wheel_zone_face_units": {
        "left": -4.0,
        "top": 1.0,
        "right": 1.0,
        "bottom": 5.0,
    }
}


def tracked_arm(wrist=(95, 95), elbow=(90, 110), shoulder=(100, 140)):
    points = {}
    for side in ("left", "right"):
        points[f"{side}_shoulder"] = {
            "x": shoulder[0],
            "y": shoulder[1],
            "source": "observed",
        }
        points[f"{side}_elbow"] = {
            "x": elbow[0],
            "y": elbow[1],
            "source": "observed",
        }
        points[f"{side}_wrist"] = {
            "x": wrist[0],
            "y": wrist[1],
            "source": "observed",
        }
    return {
        "points": points,
        "face_bbox": [80, 60, 120, 100],
        "chain_valid": {"left": True, "right": True},
    }


def test_global_pose_keypoints_maps_roi_coordinates():
    record = {
        "driver_pose_index": 0,
        "upper_body_roi_bbox": [100, 200, 400, 600],
        "poses": [
            {
                "keypoints": {
                    "left_wrist": {"x": 20, "y": 30, "confidence": 0.8},
                    "nose": {"x": 10, "y": 10, "confidence": 0.9},
                }
            }
        ],
    }
    result = global_pose_keypoints(record)
    assert result["left_wrist"]["x"] == 120
    assert result["left_wrist"]["y"] == 230
    assert "nose" not in result


def test_classifies_hand_near_face_before_raised():
    result = classify_arm_state(tracked_arm(), PROFILE)
    assert result["state"] == "hand_near_face"


def test_ear_zones_exclude_face_center_and_include_side_bands():
    zones = ear_zone_bboxes([80, 60, 120, 100])
    assert not point_in_bbox({"x": 100, "y": 90}, zones["image_left"])
    assert not point_in_bbox({"x": 100, "y": 90}, zones["image_right"])
    assert point_in_bbox({"x": 75, "y": 95}, zones["image_left"])
    assert point_in_bbox({"x": 125, "y": 95}, zones["image_right"])


def test_arm_state_exposes_near_ear_separately_from_near_face():
    result = classify_arm_state(
        tracked_arm(wrist=(75, 95), elbow=(85, 110), shoulder=(100, 140)),
        PROFILE,
    )
    assert result["side_states"]["left"]["near_face"] is True
    assert result["side_states"]["left"]["near_ear"] is True


def test_classifies_wheel_zone_candidate():
    result = classify_arm_state(
        tracked_arm(wrist=(70, 175), elbow=(85, 155), shoulder=(100, 130)),
        PROFILE,
    )
    assert result["state"] == "hands_on_wheel_candidate"


def test_unknown_without_complete_chain():
    result = classify_arm_state(
        {
            "points": {},
            "face_bbox": [80, 60, 120, 100],
            "chain_valid": {"left": False, "right": False},
        },
        PROFILE,
    )
    assert result["state"] == "unknown"


def test_state_voter_requires_persistence():
    voter = TemporalStateVoter(window_size=5, minimum_votes=3)
    assert voter.update("arm_raised") == "arm_raised"
    voter.update("unknown")
    voter.update("arm_raised")
    assert voter.update("arm_raised") == "arm_raised"


def test_driver_identity_uses_cabin_normalized_motion():
    assert driver_identity_consistent(
        [300, 300, 340, 360],
        [100, 100, 900, 800],
        [320, 310, 360, 370],
        [120, 110, 920, 810],
    )
    assert not driver_identity_consistent(
        [300, 300, 340, 360],
        [100, 100, 900, 800],
        [700, 300, 740, 360],
        [100, 100, 900, 800],
    )


def test_optical_flow_recovers_translated_points():
    first = np.zeros((160, 160, 3), dtype=np.uint8)
    second = np.zeros_like(first)
    observations = {
        "left_shoulder": {"x": 60, "y": 60, "confidence": 0.9},
        "left_elbow": {"x": 70, "y": 85, "confidence": 0.9},
        "left_wrist": {"x": 80, "y": 110, "confidence": 0.9},
    }
    for point in observations.values():
        cv2.circle(first, (point["x"], point["y"]), 5, (255, 255, 255), -1)
        cv2.circle(second, (point["x"] + 3, point["y"] + 2), 5, (255, 255, 255), -1)
    tracker = HybridArmTracker()
    tracker.update(first, observations, [50, 30, 90, 70], [0, 0, 160, 160], 1)
    result = tracker.update(second, {}, [53, 32, 93, 72], [0, 0, 160, 160], 2)
    assert result["optical_flow_point_count"] >= 2


def test_summary_never_enables_risk():
    summary = arm_temporal_summary(
        [
            {
                "state": "unknown",
                "decision_evaluable": True,
                "optical_flow_point_count": 0,
            },
            {
                "state": "arm_raised",
                "decision_evaluable": True,
                "optical_flow_point_count": 2,
            },
        ],
        fps=50.0,
    )
    assert summary["risk_enabled"] is False
    assert summary["optical_flow_recovered_frame_count"] == 1


def test_arm_chain_outside_driver_region_is_rejected():
    tracker = HybridArmTracker()
    points = {
        "left_shoulder": {"x": 100, "y": 400},
        "left_elbow": {"x": 120, "y": 430},
        "left_wrist": {"x": 140, "y": 460},
    }
    assert not tracker._chain_in_driver_region(
        "left",
        points,
        [90, 90, 130, 140],
    )


def test_temporal_summary_excludes_evidence_only_frames():
    summary = arm_temporal_summary(
        [
            {
                "state": "hand_near_face",
                "decision_evaluable": False,
                "optical_flow_point_count": 0,
            },
            {
                "state": "hands_on_wheel_candidate",
                "decision_evaluable": True,
                "optical_flow_point_count": 0,
            },
        ],
        fps=25.0,
    )
    assert summary["evaluable_frame_count"] == 1
    assert summary["state_rates"] == {"hands_on_wheel_candidate": 1.0}
