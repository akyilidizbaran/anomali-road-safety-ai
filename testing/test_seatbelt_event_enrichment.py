import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.benchmarks.enrich_event_skeleton_with_seatbelt import enrich_event


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


def test_candidate_enrichment_keeps_unknown_until_acceptance():
    event = source_event()
    risk = json.loads(json.dumps(event["risk"]))
    enriched = enrich_event(
        event,
        {
            "annotated_video": "runs/seatbelt/video.mp4",
            "temporal": {
                "status": "belted",
                "confidence": 0.82,
                "belted_evidence_rate": 0.6,
                "best_frame": 20,
                "best_torso_roi_uri": "runs/seatbelt/frame_20.jpg",
            },
        },
        {"model_key": "opencv_diagonal_belt_evidence_v1"},
    )
    assert enriched["risk"] == risk
    assert enriched["driver_cabin"]["seatbelt_status"] == "unknown"
    assert enriched["driver_cabin"]["seatbelt_analysis_status"] == "candidate"
    assert enriched["driver_cabin"]["phone_risk"] is None
    schema = json.loads(
        (ROOT / "architecture" / "contracts" / "event.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(enriched)


def test_accepted_enrichment_can_publish_positive_belted_only():
    enriched = enrich_event(
        source_event(),
        {"temporal": {"status": "belted", "confidence": 0.8}},
        {"model_key": "model"},
        accept_decisions=True,
    )
    assert enriched["driver_cabin"]["seatbelt_status"] == "belted"
    assert enriched["driver_cabin"]["seatbelt_analysis_status"] == "accepted"
