from scripts.benchmarks.prepare_phone_call_segment_review import (
    build_candidate_proposals,
    build_neutral_proposal,
)


def arm_record(frame: int, candidate: bool) -> dict:
    return {
        "frame": frame,
        "decision_evaluable": True,
        "state": "hand_near_face" if candidate else "hands_on_wheel_candidate",
        "side_states": {
            "left": {"complete": True, "near_ear": candidate},
            "right": {"complete": False, "near_ear": False},
        },
    }


def test_candidate_proposals_merge_overlapping_padded_runs():
    records = [
        arm_record(10, True),
        arm_record(11, True),
        arm_record(12, True),
        arm_record(20, True),
        arm_record(21, True),
        arm_record(22, True),
    ]
    proposals = build_candidate_proposals(
        "video_1.mp4",
        records,
        fps=10.0,
        max_frame=100,
        min_candidate_frames=3,
        max_gap=1,
        pad_seconds=0.5,
        merge_gap_seconds=0.5,
    )
    assert len(proposals) == 1
    assert proposals[0].start_frame == 5
    assert proposals[0].end_frame == 27
    assert proposals[0].candidate_frame_count == 6
    assert proposals[0].proposed_label == "unknown"


def test_video_2_candidate_gets_phone_call_proposal():
    records = [arm_record(frame, True) for frame in range(1, 8)]
    proposals = build_candidate_proposals(
        "video_2.mp4",
        records,
        fps=25.0,
        max_frame=50,
        min_candidate_frames=5,
        max_gap=2,
        pad_seconds=0.0,
        merge_gap_seconds=0.0,
    )
    assert proposals[0].proposed_label == "phone_call"


def test_neutral_proposal_uses_longest_non_candidate_run():
    records = [arm_record(frame, False) for frame in range(1, 20)]
    records += [arm_record(frame, True) for frame in range(30, 36)]
    proposal = build_neutral_proposal(
        "video_3.mp4",
        records,
        fps=5.0,
        max_frame=50,
        seconds=2.0,
    )
    assert proposal is not None
    assert proposal.start_frame == 1
    assert proposal.end_frame == 10
    assert proposal.segment_type == "neutral_context"


def test_neutral_proposal_excludes_blocked_candidate_ranges():
    records = [arm_record(frame, False) for frame in range(1, 30)]
    proposal = build_neutral_proposal(
        "video_3.mp4",
        records,
        fps=5.0,
        max_frame=50,
        seconds=2.0,
        blocked_ranges=[(1, 20)],
    )
    assert proposal is not None
    assert proposal.start_frame == 21
    assert proposal.end_frame == 29
