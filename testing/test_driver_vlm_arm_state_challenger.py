from scripts.benchmarks.run_driver_vlm_arm_state_challenger import (
    extract_first_json_object,
    normalize_response,
    select_records,
)


def test_extract_first_json_object_from_markdown():
    result = extract_first_json_object(
        '```json\n{"arm_state":"hand_near_face","confidence":0.7}\n```'
    )
    assert result["arm_state"] == "hand_near_face"


def test_extract_first_json_object_from_extra_text():
    result = extract_first_json_object(
        'answer: {"arm_state":"unknown","reasons":["dark"]} done'
    )
    assert result["reasons"] == ["dark"]


def test_normalize_response_clamps_state_and_confidence():
    result = normalize_response(
        {"arm_state": "bad", "confidence": 2, "reasons": ["x"]}
    )
    assert result["arm_state"] == "unknown"
    assert result["confidence"] == 1.0


def test_select_records_respects_visibility_and_stride():
    records = [
        {"frame": 1, "visibility": "limited"},
        {"frame": 2, "visibility": "poor"},
        {"frame": 4, "visibility": "good"},
    ]
    assert [r["frame"] for r in select_records(records, None, 2, False)] == [4]
    assert [r["frame"] for r in select_records(records, {2}, 2, True)] == [2]
