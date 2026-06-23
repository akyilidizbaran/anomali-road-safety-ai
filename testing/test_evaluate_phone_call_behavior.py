from scripts.benchmarks.evaluate_phone_call_behavior import evaluate_rows


def test_evaluation_counts_confusion_matrix_and_accepts_quality():
    rows = [
        {"video": "p1", "session_id": "sp1", "ground_truth": "positive", "phone_visibility": "not_visible"},
        {"video": "p2", "session_id": "sp2", "ground_truth": "positive", "phone_visibility": "visible"},
        {"video": "n1", "session_id": "sn1", "ground_truth": "negative", "negative_subtype": "cheek_rest"},
        {"video": "n2", "session_id": "sn2", "ground_truth": "negative", "negative_subtype": "face_scratch"},
    ]
    predictions = {
        "p1": "handheld_call_likely",
        "p2": "handheld_call_likely",
        "n1": "candidate",
        "n2": "not_detected",
    }
    result = evaluate_rows(
        rows,
        predictions,
        min_positive_sessions=2,
        min_negative_sessions=2,
        min_hard_negative_sessions=2,
        min_occluded_positive_sessions=1,
    )
    assert result["counts"] == {"tp": 2, "fp": 0, "tn": 2, "fn": 0}
    assert result["hard_negative_specificity"] == 1.0
    assert result["baseline_accepted"] is True


def test_evaluation_rejects_insufficient_label_coverage():
    rows = [
        {"video": "p1", "ground_truth": "positive"},
        {"video": "n1", "ground_truth": "unknown"},
    ]
    result = evaluate_rows(rows, {"p1": "handheld_call_likely"})
    assert result["recall"] == 1.0
    assert result["coverage_gate_passed"] is False
    assert result["baseline_accepted"] is False
    assert result["pending_review_videos"] == ["n1"]


def test_evaluation_rejects_easy_negative_trap():
    rows = [
        {"video": "p1", "session_id": "sp1", "ground_truth": "positive", "phone_visibility": "not_visible"},
        {"video": "p2", "session_id": "sp2", "ground_truth": "positive", "phone_visibility": "visible"},
        {"video": "p3", "session_id": "sp3", "ground_truth": "positive", "phone_visibility": "visible"},
        {"video": "n1", "session_id": "sn1", "ground_truth": "negative"},
        {"video": "n2", "session_id": "sn2", "ground_truth": "negative"},
        {"video": "n3", "session_id": "sn3", "ground_truth": "negative"},
        {"video": "n4", "session_id": "sn4", "ground_truth": "negative"},
        {"video": "n5", "session_id": "sn5", "ground_truth": "negative"},
    ]
    predictions = {row["video"]: "handheld_call_likely" if row["ground_truth"] == "positive" else "not_detected" for row in rows}
    result = evaluate_rows(rows, predictions)
    assert result["specificity"] == 1.0
    assert result["baseline_accepted"] is False
    assert "hard_negative_sessions=0<2" in result["coverage_blockers"]
    assert "hard_negative_specificity=None<0.9" in result["quality_blockers"]


def test_evaluation_rejects_session_leakage():
    rows = [
        {"video": "p1a", "session_id": "sp1", "ground_truth": "positive", "phone_visibility": "not_visible"},
        {"video": "p1b", "session_id": "sp1", "ground_truth": "positive", "phone_visibility": "not_visible"},
        {"video": "n1a", "session_id": "sn1", "ground_truth": "negative", "negative_subtype": "cheek_rest"},
        {"video": "n1b", "session_id": "sn1", "ground_truth": "negative", "negative_subtype": "face_scratch"},
    ]
    predictions = {row["video"]: "handheld_call_likely" if row["ground_truth"] == "positive" else "not_detected" for row in rows}
    result = evaluate_rows(
        rows,
        predictions,
        min_positive_sessions=2,
        min_negative_sessions=2,
        min_hard_negative_sessions=1,
    )
    assert result["counts"] == {"tp": 2, "fp": 0, "tn": 2, "fn": 0}
    assert result["positive_session_count"] == 1
    assert result["negative_session_count"] == 1
    assert result["baseline_accepted"] is False
