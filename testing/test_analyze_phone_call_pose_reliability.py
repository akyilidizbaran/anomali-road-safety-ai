from scripts.benchmarks.analyze_phone_call_pose_reliability import (
    longest_boolean_run,
    summarize_video,
)


def record(evaluable=True, complete_arm_count=2, confidence=0.8, flow_points=0):
    return {
        "decision_evaluable": evaluable,
        "complete_arm_count": complete_arm_count,
        "optical_flow_point_count": flow_points,
        "low_confidence_point_count": 0,
        "visibility": "good" if evaluable else "poor",
        "points": {
            "left_wrist": {"confidence": confidence},
            "right_wrist": {"confidence": confidence},
        } if evaluable else {},
        "side_states": {
            "left": {"wrist_source": "observed"},
            "right": {"wrist_source": "observed"},
        } if evaluable else {},
    }


def test_longest_boolean_run_counts_target_runs():
    assert longest_boolean_run([False, True, True, False, True], target=True) == 2
    assert longest_boolean_run([False, False, True], target=False) == 2


def test_summarize_video_marks_reliable_pose_usable():
    item = {
        "video": "ok.mp4",
        "view_profile": "side",
        "per_frame": [record() for _ in range(10)],
    }
    summary = summarize_video(item)
    assert summary["reliability"] == "decision_usable"
    assert summary["evaluable_rate"] == 1.0
    assert summary["complete_arm_rate"] == 1.0


def test_summarize_video_marks_low_coverage_pose_limited():
    item = {
        "video": "bad.mp4",
        "view_profile": "side",
        "per_frame": [record(evaluable=True)] + [record(evaluable=False) for _ in range(9)],
    }
    summary = summarize_video(item)
    assert summary["reliability"] == "pose_limited"
    assert "evaluable_rate=0.1<0.45" in summary["pose_reliability_blockers"]
    assert summary["decision_policy"].startswith("prefer_not_evaluable")


def test_summarize_video_marks_borderline_without_blocking():
    item = {
        "video": "borderline.mp4",
        "view_profile": "side",
        "per_frame": [record(evaluable=True) for _ in range(5)]
        + [record(evaluable=False) for _ in range(5)],
    }
    summary = summarize_video(item)
    assert summary["reliability"] == "decision_usable"
    assert summary["reliability_detail"] == "usable_borderline"
    assert "evaluable_rate=0.5<0.55" in summary["borderline_flags"]
    assert summary["decision_policy"] == "allow_pose_temporal_decision_but_require_temporal_consistency"
