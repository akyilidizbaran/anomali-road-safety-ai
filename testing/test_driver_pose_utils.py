import numpy as np

from scripts.benchmarks.run_driver_pose_baseline import (
    EXPERIMENTS,
    RTMPoseONNXDetector,
    WHOLEBODY_NAMES,
    build_report,
)
from scripts.benchmarks.driver_pose_utils import (
    TemporalKeypointStabilizer,
    associate_driver_pose,
    driver_arm_focus_roi_bbox,
    driver_face_global_bbox,
    hand_anchor_summary,
    intersect_bbox,
    pose_inference_gate,
    temporal_pose_summary,
    torso_from_keypoints,
    upper_body_cabin_roi_bbox,
    upper_body_roi_bbox,
)


def test_final_pose_baseline_is_torso_only_and_disables_arm_decisions():
    experiment = EXPERIMENTS["POSE-EXP-009"]
    assert experiment["decision"] == "selected_upperbody_torso_baseline"
    assert experiment["render_policy"] == "torso_only"
    assert experiment["enable_arm_anchors"] is False
    assert "temporal_continuation_confidence" not in experiment


def test_pose_inference_gate_runs_poor_frame_as_evidence_only():
    assert pose_inference_gate("poor", 0.92, True, 0.80) == (True, True)


def test_pose_inference_gate_does_not_bypass_poor_visibility_without_face():
    assert pose_inference_gate("poor", None, True, 0.80) == (False, False)
    assert pose_inference_gate("poor", 0.70, True, 0.80) == (False, False)


def test_pose_inference_gate_keeps_limited_frame_decision_evaluable():
    assert pose_inference_gate("limited", 0.40, True, 0.80) == (True, False)


def test_driver_arm_focus_roi_is_tighter_than_vehicle_and_contains_face():
    roi = driver_arm_focus_roi_bbox(
        [500, 300, 550, 370],
        [100, 200, 1200, 1000],
        [200, 220, 1100, 800],
        "front_lhd",
        1280,
        1080,
    )
    assert roi[0] <= 500
    assert roi[1] <= 300
    assert roi[2] >= 550
    assert roi[3] > 500
    assert roi[3] <= 800


def test_temporal_stabilizer_smooths_face_relative_motion():
    stabilizer = TemporalKeypointStabilizer(smoothing_alpha=0.5)
    first, _ = stabilizer.update(
        {"left_wrist": {"x": 30, "y": 30, "confidence": 0.9}},
        [10, 10, 30, 30],
        1,
    )
    second, _ = stabilizer.update(
        {"left_wrist": {"x": 36, "y": 30, "confidence": 0.9}},
        [10, 10, 30, 30],
        2,
    )
    assert first["left_wrist"]["x"] == 30
    assert second["left_wrist"]["x"] == 33
    assert second["left_wrist"]["temporal_source"] == "observed"


def test_temporal_stabilizer_tracks_a_moving_face_coordinate_system():
    stabilizer = TemporalKeypointStabilizer(smoothing_alpha=0.5)
    stabilizer.update(
        {"left_shoulder": {"x": 30, "y": 40, "confidence": 0.9}},
        [10, 10, 30, 30],
        1,
    )
    moved, _ = stabilizer.update(
        {"left_shoulder": {"x": 50, "y": 40, "confidence": 0.9}},
        [30, 10, 50, 30],
        2,
    )
    assert moved["left_shoulder"]["x"] == 50


def test_temporal_stabilizer_holds_short_confidence_dropout():
    stabilizer = TemporalKeypointStabilizer(
        min_confidence=0.3,
        hold_frames=3,
    )
    stabilizer.update(
        {"right_elbow": {"x": 40, "y": 50, "confidence": 0.9}},
        [10, 10, 30, 30],
        1,
    )
    held, stats = stabilizer.update({}, [10, 10, 30, 30], 3)
    expired, _ = stabilizer.update({}, [10, 10, 30, 30], 5)
    assert held["right_elbow"]["temporal_source"] == "held"
    assert held["right_elbow"]["confidence"] >= 0.3
    assert stats["held_keypoint_count"] == 1
    assert "right_elbow" not in expired


def test_temporal_stabilizer_rejects_implausible_jump_and_holds_anchor():
    stabilizer = TemporalKeypointStabilizer(
        hold_frames=3,
        max_jump_face_units=0.5,
    )
    stabilizer.update(
        {"left_wrist": {"x": 30, "y": 30, "confidence": 0.9}},
        [10, 10, 30, 30],
        1,
    )
    result, stats = stabilizer.update(
        {"left_wrist": {"x": 100, "y": 100, "confidence": 0.9}},
        [10, 10, 30, 30],
        2,
    )
    assert result["left_wrist"]["x"] == 30
    assert result["left_wrist"]["temporal_source"] == "held"
    assert stats["rejected_jump_count"] == 1


def test_temporal_stabilizer_tracks_low_confidence_continuation():
    stabilizer = TemporalKeypointStabilizer(
        min_confidence=0.3,
        continuation_confidence=0.1,
        max_continuation_frames=3,
        smoothing_alpha=1.0,
    )
    stabilizer.update(
        {"right_wrist": {"x": 30, "y": 30, "confidence": 0.8}},
        [10, 10, 30, 30],
        1,
    )
    tracked, _ = stabilizer.update(
        {"right_wrist": {"x": 32, "y": 31, "confidence": 0.15}},
        [10, 10, 30, 30],
        2,
    )
    assert tracked["right_wrist"]["x"] == 32
    assert tracked["right_wrist"]["confidence"] == 0.3
    assert (
        tracked["right_wrist"]["temporal_source"]
        == "tracked_low_confidence"
    )


def test_temporal_stabilizer_limits_low_confidence_continuation():
    stabilizer = TemporalKeypointStabilizer(
        min_confidence=0.3,
        hold_frames=0,
        continuation_confidence=0.1,
        max_continuation_frames=2,
        smoothing_alpha=1.0,
    )
    stabilizer.update(
        {"left_wrist": {"x": 30, "y": 30, "confidence": 0.8}},
        [10, 10, 30, 30],
        1,
    )
    for frame in (2, 3):
        result, _ = stabilizer.update(
            {"left_wrist": {"x": 30 + frame, "y": 30, "confidence": 0.15}},
            [10, 10, 30, 30],
            frame,
        )
        assert "left_wrist" in result
    expired, _ = stabilizer.update(
        {"left_wrist": {"x": 34, "y": 30, "confidence": 0.15}},
        [10, 10, 30, 30],
        4,
    )
    assert "left_wrist" not in expired


def test_rtmpose_simcc_decode_maps_center_back_to_roi():
    simcc_x = np.zeros((1, 17, 576), dtype=np.float32)
    simcc_y = np.zeros((1, 17, 768), dtype=np.float32)
    simcc_x[:, :, 288] = 0.9
    simcc_y[:, :, 384] = 0.8
    keypoints, scores = RTMPoseONNXDetector._decode(
        [simcc_x, simcc_y],
        input_size=(288, 384),
        center=np.array([144.0, 192.0], dtype=np.float32),
        scale=np.array([288.0, 384.0], dtype=np.float32),
    )
    assert keypoints.shape == (1, 17, 2)
    assert np.allclose(keypoints[0, 0], [144.0, 192.0])
    assert scores[0, 0] == np.float32(0.8)


def test_wholebody_contract_has_133_unique_keypoint_names():
    assert len(WHOLEBODY_NAMES) == 133
    assert len(set(WHOLEBODY_NAMES)) == 133
    assert WHOLEBODY_NAMES[91] == "left_hand_0"
    assert WHOLEBODY_NAMES[112] == "right_hand_0"


def test_pose_report_includes_wholebody_hand_metrics():
    report = build_report(
        {
            "experiment_id": "POSE-EXP-004",
            "created_at_utc": "2026-06-13T00:00:00Z",
            "model_key": "rtmw",
            "backend": "rtmpose_onnx",
            "model_path": "model.onnx",
            "input_cabin_summary": "cabin.json",
            "frame_stride": 1,
            "pose_confidence": 0.25,
            "keypoint_confidence": 0.35,
            "videos": [
                {
                    "video": "video_1.mp4",
                    "view_profile": "side_driver_window",
                    "mean_pose_latency_ms": 1.0,
                    "p95_pose_latency_ms": 2.0,
                    "temporal": {
                        "hand_anchor_rate": 0.8,
                        "hand_near_face_rate": 0.5,
                    },
                }
            ],
        }
    )
    assert "Hand Near Face" in report
    assert "| 0.8 | 0.5 |" in report


def test_driver_face_bbox_is_mapped_from_cabin_to_frame():
    record = {
        "cabin_bbox_xyxy": [100, 50, 300, 200],
        "driver_face_index": 0,
        "faces": [{"bbox": [20, 30, 40, 50]}],
    }
    assert driver_face_global_bbox(record) == [120, 80, 160, 130]


def test_upper_body_roi_expands_down_and_stays_inside_vehicle():
    roi = upper_body_roi_bbox(
        face_bbox=[220, 100, 260, 150],
        vehicle_bbox=[100, 80, 400, 360],
        frame_width=500,
        frame_height=400,
    )
    assert roi[0] >= 100
    assert roi[1] >= 80
    assert roi[2] <= 400
    assert roi[3] <= 360
    assert roi[1] < 100
    assert roi[3] > 250


def test_cabin_clamped_upper_body_roi_excludes_vehicle_hood():
    roi = upper_body_cabin_roi_bbox(
        face_bbox=[220, 100, 260, 150],
        vehicle_bbox=[100, 80, 400, 360],
        cabin_bbox=[140, 90, 360, 210],
        frame_width=500,
        frame_height=400,
    )
    assert roi[0] >= 110
    assert roi[2] <= 390
    assert roi[3] <= 228


def test_pose_association_uses_driver_face_geometry():
    poses = [
        {"bbox": [0, 10, 90, 220], "confidence": 0.9},
        {"bbox": [100, 5, 230, 250], "confidence": 0.8},
    ]
    index, status, score = associate_driver_pose(
        poses,
        face_bbox=[145, 25, 185, 70],
    )
    assert index == 1
    assert status == "driver_face_pose_matched"
    assert score is not None and score > 0.5


def test_torso_uses_shoulders_when_hips_are_not_visible():
    torso = torso_from_keypoints(
        {
            "left_shoulder": {"x": 50, "y": 60, "confidence": 0.9},
            "right_shoulder": {"x": 110, "y": 62, "confidence": 0.8},
            "left_hip": {"x": 60, "y": 180, "confidence": 0.1},
            "right_hip": {"x": 100, "y": 180, "confidence": 0.1},
        },
        roi_width=180,
        roi_height=220,
        face_bbox=[60, 10, 100, 50],
    )
    assert torso["status"] == "torso_shoulders_extrapolated"
    assert torso["shoulders_visible"] is True
    assert torso["hips_visible"] is False
    assert torso["torso_bbox"] is not None
    assert torso["seatbelt_anchor_ready"] is True
    assert torso["phone_anchor_ready"] is False


def test_torso_rejects_single_visible_shoulder():
    torso = torso_from_keypoints(
        {
            "left_shoulder": {"x": 50, "y": 60, "confidence": 0.9},
            "right_shoulder": {"x": 110, "y": 62, "confidence": 0.1},
        },
        roi_width=180,
        roi_height=220,
    )
    assert torso["status"] == "shoulders_not_visible"
    assert torso["torso_bbox"] is None


def test_torso_ignores_keypoints_outside_visible_cabin_bounds():
    torso = torso_from_keypoints(
        {
            "left_shoulder": {"x": 50, "y": 60, "confidence": 0.9},
            "right_shoulder": {"x": 110, "y": 62, "confidence": 0.9},
            "left_hip": {"x": 60, "y": 180, "confidence": 0.9},
            "right_hip": {"x": 100, "y": 180, "confidence": 0.9},
        },
        roi_width=180,
        roi_height=220,
        face_bbox=[60, 10, 100, 50],
        keypoint_bounds=[0, 0, 180, 130],
    )
    assert torso["status"] == "torso_shoulders_extrapolated"
    assert torso["hips_visible"] is False


def test_torso_bbox_is_clamped_to_visible_cabin():
    assert intersect_bbox(
        [20, 30, 180, 220],
        [40, 50, 160, 140],
    ) == [40, 50, 160, 140]
    assert intersect_bbox([0, 0, 5, 5], [10, 10, 20, 20]) is None


def test_hand_anchor_summary_detects_reliable_hand_near_face():
    keypoints = {
        "right_wrist": {"x": 79, "y": 49, "confidence": 0.9},
        **{
        f"right_hand_{index}": {
            "x": 80 + index,
            "y": 50 + index,
            "confidence": 0.8,
        }
        for index in range(6)
        },
    }
    result = hand_anchor_summary(
        keypoints,
        face_bbox=[60, 30, 100, 70],
        minimum_points=4,
        max_face_distance=3.0,
    )
    assert result["hand_anchor_count"] == 1
    assert result["hand_near_face_count"] == 1
    assert result["hands"]["right"]["ready"] is True


def test_hand_anchor_summary_rejects_sparse_landmarks():
    result = hand_anchor_summary(
        {
            "left_hand_0": {"x": 80, "y": 50, "confidence": 0.9},
            "left_hand_1": {"x": 82, "y": 52, "confidence": 0.9},
        },
        face_bbox=[60, 30, 100, 70],
        minimum_points=4,
    )
    assert result["hand_anchor_count"] == 0
    assert result["hand_near_face_count"] == 0


def test_hand_anchor_summary_rejects_hand_not_attached_to_wrist():
    keypoints = {
        "left_wrist": {"x": 20, "y": 20, "confidence": 2.0},
        **{
            f"left_hand_{index}": {
                "x": 100 + index,
                "y": 100 + index,
                "confidence": 5.0,
            }
            for index in range(6)
        },
    }
    result = hand_anchor_summary(
        keypoints,
        face_bbox=[60, 30, 100, 70],
        min_confidence=4.5,
        minimum_points=4,
        max_root_wrist_distance=0.75,
    )
    assert result["hand_anchor_count"] == 0
    assert result["hands"]["left"]["wrist_associated"] is False


def test_torso_requires_anatomically_plausible_face_shoulder_geometry():
    torso = torso_from_keypoints(
        {
            "left_shoulder": {"x": 78, "y": 62, "confidence": 0.9},
            "right_shoulder": {"x": 84, "y": 63, "confidence": 0.9},
        },
        roi_width=180,
        roi_height=220,
        face_bbox=[60, 10, 100, 50],
    )
    assert torso["status"] == "face_shoulder_geometry_invalid"
    assert torso["seatbelt_anchor_ready"] is False


def test_phone_anchor_requires_shoulder_elbow_wrist_chain():
    torso = torso_from_keypoints(
        {
            "left_shoulder": {"x": 50, "y": 70, "confidence": 0.9},
            "right_shoulder": {"x": 110, "y": 72, "confidence": 0.9},
            "left_elbow": {"x": 35, "y": 110, "confidence": 0.8},
            "left_wrist": {"x": 30, "y": 145, "confidence": 0.8},
        },
        roi_width=180,
        roi_height=220,
        face_bbox=[60, 10, 100, 50],
    )
    assert torso["seatbelt_anchor_ready"] is True
    assert torso["phone_anchor_ready"] is True
    assert torso["arm_chain_count"] == 1


def test_temporal_pose_summary_requires_repeated_ready_frames():
    frames = [
        {
            "frame": frame,
            "visibility": "limited",
            "driver_face_bbox": [10, 10, 30, 30],
            "driver_pose_detected": frame <= 3,
            "driver_analysis_ready": frame <= 3,
            "upper_body_analysis_ready": frame <= 3,
            "seatbelt_anchor_ready": frame <= 3,
            "phone_anchor_ready": frame <= 3,
            "anchor_confidence": 0.8 if frame <= 3 else None,
            "pose_confidence": 0.9 if frame <= 3 else None,
            "upper_body_roi_uri": f"frame_{frame}.jpg",
            "torso_bbox_global": [10, 20, 80, 140] if frame <= 3 else None,
            "driver_pose_index": 0 if frame <= 3 else None,
            "upper_body_roi_bbox": [0, 0, 100, 180],
            "poses": [
                {
                    "keypoints": {
                        "left_shoulder": {
                            "x": 40 + frame,
                            "y": 70,
                            "confidence": 0.9,
                        },
                        "right_shoulder": {
                            "x": 70 + frame,
                            "y": 70,
                            "confidence": 0.9,
                        },
                    }
                }
            ]
            if frame <= 3
            else [],
        }
        for frame in range(1, 6)
    ]
    summary = temporal_pose_summary(
        frames,
        min_ready_frames=3,
        min_ready_rate=0.5,
        fps=10.0,
    )
    assert summary["upper_body_detected"] is True
    assert summary["pose_detection_rate"] == 0.6
    assert summary["analysis_ready_rate"] == 0.6
    assert summary["seatbelt_anchor_rate"] == 0.6
    assert summary["phone_anchor_rate"] == 0.6
    assert summary["longest_analysis_miss_run"] == 2
    assert summary["longest_analysis_miss_seconds"] == 0.2
    assert summary["p95_shoulder_jitter_face_units"] == 0.05


def test_temporal_pose_summary_is_unknown_without_driver_face():
    summary = temporal_pose_summary(
        [
            {
                "frame": 1,
                "visibility": "good",
                "driver_face_bbox": None,
                "driver_pose_detected": None,
                "driver_analysis_ready": None,
            }
        ]
    )
    assert summary["evaluable_driver_frame_count"] == 0
    assert summary["upper_body_detected"] is None


def test_shoulder_jitter_is_relative_to_moving_face():
    frames = []
    for frame in (1, 2):
        shift = (frame - 1) * 20
        frames.append(
            {
                "frame": frame,
                "visibility": "good",
                "driver_face_bbox": [10 + shift, 10, 30 + shift, 30],
                "driver_pose_detected": True,
                "upper_body_analysis_ready": True,
                "seatbelt_anchor_ready": True,
                "phone_anchor_ready": False,
                "driver_pose_index": 0,
                "upper_body_roi_bbox": [shift, 0, 100 + shift, 180],
                "poses": [
                    {
                        "keypoints": {
                            "left_shoulder": {
                                "x": 40,
                                "y": 70,
                                "confidence": 0.9,
                            },
                            "right_shoulder": {
                                "x": 70,
                                "y": 70,
                                "confidence": 0.9,
                            },
                        }
                    }
                ],
            }
        )
    summary = temporal_pose_summary(frames)
    assert summary["p95_shoulder_jitter_face_units"] == 0.0


def test_upper_body_temporal_decision_does_not_require_phone_arm_chain():
    frames = [
        {
            "frame": frame,
            "visibility": "limited",
            "driver_face_bbox": [10, 10, 30, 30],
            "driver_pose_detected": True,
            "seatbelt_anchor_ready": True,
            "phone_anchor_ready": False,
            "upper_body_analysis_ready": True,
            "driver_analysis_ready": True,
            "driver_pose_index": None,
            "poses": [],
        }
        for frame in range(1, 5)
    ]
    summary = temporal_pose_summary(
        frames,
        min_ready_frames=3,
        min_ready_rate=0.5,
        fps=50.0,
    )
    assert summary["upper_body_detected"] is True
    assert summary["analysis_ready_rate"] == 1.0
    assert summary["phone_anchor_rate"] == 0.0
    assert summary["longest_analysis_miss_seconds"] == 0.0
