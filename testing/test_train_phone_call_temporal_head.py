import pytest

from scripts.benchmarks.train_phone_call_temporal_head import (
    auto_split_review_labels,
    load_segment_labels,
    review_label_status,
    SegmentLabel,
    validate_samples,
    window_features,
    WindowSample,
)


def test_window_features_separate_hand_near_ear_and_phone_object():
    arm_records = [
        {
            "frame": 1,
            "decision_evaluable": True,
            "state": "hand_near_face",
            "state_confidence": 0.8,
            "complete_arm_count": 1,
            "optical_flow_point_count": 0,
            "side_states": {
                "left": {"complete": True, "near_ear": True},
                "right": {"complete": False, "near_ear": False},
            },
        },
        {
            "frame": 2,
            "decision_evaluable": True,
            "state": "hands_on_wheel_candidate",
            "state_confidence": 1.0,
            "complete_arm_count": 2,
            "optical_flow_point_count": 1,
            "side_states": {},
        },
    ]
    phone_records = [
        {"frame": 1, "decision_evaluable": True, "phone_detected": False},
        {
            "frame": 2,
            "decision_evaluable": True,
            "phone_detected": True,
            "object_near_face": True,
            "phone_confidence": 0.4,
        },
    ]
    features = window_features(arm_records, phone_records, fps=25.0)
    assert features[2] == 0.5  # hand_near_ear_rate
    assert features[3] == 0.5  # left_near_ear_rate
    assert features[10] == 0.5  # phone_detected_rate
    assert features[12] == 0.4  # max_phone_confidence


def test_validate_samples_rejects_single_class_training():
    samples = [
        WindowSample(
            video="video_2.mp4",
            session_id="s1",
            split="train",
            label="phone_call",
            class_index=2,
            start_frame=1,
            end_frame=50,
            features=[0.0] * 14,
        )
    ]
    with pytest.raises(ValueError, match="At least two reviewed classes"):
        validate_samples(samples, smoke=False)


def test_validate_samples_rejects_session_leakage():
    samples = [
        WindowSample("a.mp4", "same", "train", "phone_call", 2, 1, 50, [0.0] * 14),
        WindowSample("a.mp4", "same", "val", "neutral", 0, 51, 100, [0.0] * 14),
    ]
    with pytest.raises(ValueError, match="Session split leakage"):
        validate_samples(samples, smoke=False)


def test_load_segment_labels_prefers_review_final_label(tmp_path):
    labels = tmp_path / "segments.csv"
    labels.write_text(
        "video,session_id,split,label,final_label\n"
        "video_1.mp4,s1,train,unknown,face_touch_hard_negative\n",
        encoding="utf-8",
    )
    loaded = load_segment_labels(labels)
    assert len(loaded) == 1
    assert loaded[0].label == "face_touch_hard_negative"


def test_review_label_status_counts_empty_final_labels(tmp_path):
    labels = tmp_path / "segments.csv"
    labels.write_text(
        "segment_id,video,split,final_label\n"
        "s1,video_1.mp4,review,\n"
        "s2,video_2.mp4,review,phone_call\n",
        encoding="utf-8",
    )
    status = review_label_status(labels)
    assert status["row_count"] == 2
    assert status["trainable_row_count"] == 1
    assert status["empty_label_rows"] == ["s1"]


def test_auto_split_review_labels_assigns_session_level_val():
    labels = [
        SegmentLabel("a.mp4", "s1", "review", 1, 10, None, None, "phone_call", "x"),
        SegmentLabel("b.mp4", "s2", "review", 1, 10, None, None, "neutral", "x"),
    ]
    converted, warnings = auto_split_review_labels(labels)
    assert [label.split for label in converted] == ["train", "val"]
    assert warnings == ["review_split_auto_session_split:train=1,val=1"]
