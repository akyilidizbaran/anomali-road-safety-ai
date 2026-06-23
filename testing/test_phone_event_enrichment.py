import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.benchmarks.enrich_event_skeleton_with_phone import enrich_event


ROOT = Path(__file__).resolve().parents[1]


def source_event():
    return json.loads(
        (
            ROOT
            / "models"
            / "benchmarks"
            / "artifacts"
            / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin.json"
        ).read_text(encoding="utf-8")
    )["events"][0]


def test_phone_enrichment_preserves_risk_and_keeps_phone_risk_null():
    event = source_event()
    risk = json.loads(json.dumps(event["risk"]))
    enriched = enrich_event(
        event,
        {
            "annotated_video": "runs/phone/video.mp4",
            "temporal": {
                "status": "detected",
                "confidence": 0.76,
                "detection_rate": 0.4,
                "object_near_face_rate": 0.5,
                "best_frame": 22,
                "best_phone_bbox": [1, 2, 3, 4],
                "best_phone_roi_uri": "runs/phone/frame.jpg",
            },
        },
        {"model_key": "yolo11n_coco_cell_phone_driver_roi_v1"},
    )
    assert enriched["risk"] == risk
    assert enriched["driver_cabin"]["phone_detected"] is True
    assert enriched["driver_cabin"]["phone_analysis_status"] == "candidate"
    assert enriched["driver_cabin"]["phone_risk"] is None
    schema = json.loads(
        (ROOT / "architecture" / "contracts" / "event.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(enriched)


def test_phone_call_behavior_can_be_likely_without_object_detection():
    event = source_event()
    enriched = enrich_event(
        event,
        {"temporal": {"status": "not_detected", "detection_rate": 0.0}},
        {"model_key": "phone_object_model"},
        {
            "annotated_video": "runs/phone_call/video.mp4",
            "behavior": {
                "phone_call_status": "handheld_call_likely",
                "phone_call_confidence": 0.96,
                "phone_call_evidence_source": "pose_temporal",
                "hand_near_ear_candidate_rate": 0.91,
                "longest_hand_near_ear_seconds": 2.4,
                "dominant_hand_side": "right",
                "pose_reliability_detail": "decision_usable",
                "pose_reliability_policy": "standard",
            },
        },
        {"model_key": "phone_call_fusion_v1"},
        {
            "baseline_id": "PHONE-CALL-PROVISIONAL-BASELINE",
            "final_baseline_accepted": False,
        },
    )
    cabin = enriched["driver_cabin"]
    assert cabin["phone_detected"] is False
    assert cabin["phone_call_status"] == "handheld_call_likely"
    assert cabin["phone_call_evidence_source"] == "pose_temporal"
    assert cabin["phone_call_baseline_id"] == "PHONE-CALL-PROVISIONAL-BASELINE"
    assert cabin["phone_call_pose_reliability"] == "decision_usable"
    assert cabin["phone_risk"] is None
    assert enriched["models"]["phone_call_behavior"] == "phone_call_fusion_v1"
    assert enriched["models"]["phone_call_provisional_baseline"] == "PHONE-CALL-PROVISIONAL-BASELINE"
    assert enriched["evidence"]["phone_call_final_baseline_accepted"] is False
    schema = json.loads(
        (ROOT / "architecture" / "contracts" / "event.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(enriched)
