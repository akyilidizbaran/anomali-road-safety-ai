import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.benchmarks.enrich_event_skeleton_with_cabin import enrich_event


ROOT = Path(__file__).resolve().parents[1]


def test_cabin_enrichment_preserves_plate_and_risk():
    source = json.loads(
        (
            ROOT
            / "models"
            / "benchmarks"
            / "artifacts"
            / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json"
        ).read_text(encoding="utf-8")
    )["events"][0]
    original_plate = json.loads(json.dumps(source["plate"]))
    original_risk = json.loads(json.dumps(source["risk"]))
    cabin_summary = {
        "model_key": "blazeface_full_range",
    }
    video_summary = {
        "status": "completed",
        "view_profile": "side_driver_window",
        "annotated_video": "runs/cabin/example.mp4",
        "visibility_reason_counts": {"cabin_roi_quality_usable": 10},
        "temporal": {
            "visibility": "limited",
            "mean_visibility_score": 0.58,
            "occupant_count_estimate": 1,
            "driver_candidate_detected": True,
            "role_assignment_status": "assigned_side_driver_largest_face",
            "temporal_detection_rate": 0.75,
            "best_frame": 42,
            "best_roi_uri": "runs/cabin/frame_000042_cabin.jpg",
        },
    }

    enriched = enrich_event(
        source,
        video_summary,
        cabin_summary,
        "events-cabin.json",
    )

    assert enriched["plate"] == original_plate
    assert enriched["risk"] == original_risk
    assert enriched["driver_cabin"]["driver_detected"] is True
    assert enriched["driver_cabin"]["passenger_count"] == 0
    assert enriched["driver_cabin"]["phone_risk"] is None
    assert enriched["driver_cabin"]["seatbelt_status"] == "unknown"

    schema = json.loads(
        (ROOT / "architecture" / "contracts" / "event.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(enriched)
