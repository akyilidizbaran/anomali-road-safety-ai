from scripts.benchmarks.summarize_phone_call_events import summarize_events


def test_summarize_events_counts_status_and_keeps_risk_null():
    data = {
        "experiment_id": "PHONE-CALL-PROVISIONAL-BASELINE",
        "phone_call_baseline_id": "PHONE-CALL-PROVISIONAL-BASELINE",
        "phone_call_final_baseline_accepted": False,
        "events": [
            {
                "event_id": "e1",
                "source": {"source_video": "a.mp4"},
                "driver_cabin": {
                    "phone_analysis_status": "not_detected",
                    "phone_detected": False,
                    "phone_call_status": "candidate",
                    "phone_call_confidence": 0.5,
                    "phone_call_evidence_source": "pose_temporal",
                    "phone_call_baseline_id": "PHONE-CALL-PROVISIONAL-BASELINE",
                    "phone_call_pose_reliability": "usable_borderline",
                    "phone_risk": None,
                },
                "evidence": {"phone_call_final_baseline_accepted": False},
            },
            {
                "event_id": "e2",
                "source": {"source_video": "b.mp4"},
                "driver_cabin": {
                    "phone_call_status": "handheld_call_likely",
                    "phone_call_pose_reliability": "decision_usable",
                    "phone_risk": None,
                },
                "evidence": {"phone_call_final_baseline_accepted": False},
            },
        ],
    }
    summary = summarize_events(data)
    assert summary["status_counts"] == {
        "candidate": 1,
        "handheld_call_likely": 1,
    }
    assert summary["pose_reliability_counts"] == {
        "usable_borderline": 1,
        "decision_usable": 1,
    }
    assert summary["phone_risk_all_null"] is True
