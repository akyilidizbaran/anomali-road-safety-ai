# Cabin / Phone Checkpoint Registry

Date: 2026-06-23

This registry records local cabin/phone model files imported from `handoff.zip`.
Binary checkpoint files are intentionally not tracked by Git because `.pt`, `.pth`
and `.onnx` artifacts are ignored project-wide.

## Local Checkpoints

| Experiment | Local path | Size | Status | Use |
|---|---|---:|---|---|
| `PHONE-EXP-003` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-003-yolo26s-p2-phone-windshield-seed-smoke-best.pt` | ~19 MB | Smoke checkpoint | Phone object supporting evidence; not accepted final baseline. |
| `PHONE-EXP-003` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-003-yolo26s-p2-phone-windshield-seed-smoke-last.pt` | ~19 MB | Training last | Debug/repro only. |
| `PHONE-EXP-004` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-004-yolo26s-phone-windshield-seed-smoke-best.pt` | ~19 MB | Smoke checkpoint | Preferred visible-phone object branch from handoff; still not final phone-call risk baseline. |
| `PHONE-EXP-004` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-004-yolo26s-phone-windshield-seed-smoke-last.pt` | ~19 MB | Training last | Debug/repro only. |

Original training context is preserved under:

```text
runs/phone/training/
```

## Current Interpretation

The imported phone object specialists are not standalone "phone-call" models.
They detect visible phone-like objects in the windshield/cabin-view domain and
should only be used as one evidence branch.

The handoff's provisional phone-call decision stack is:

```text
PHONE-CALL-PROVISIONAL-BASELINE = PHONE-CALL-EXP-002 + PHONE-CALL-EXP-007 + PHONE-EXP-004
```

Key guardrail:

```text
phone_object_detected=false does not mean phone-call=false
```

The phone-call behavior module may return `candidate` or `not_evaluable` when the
phone object is not visible but pose/ear-zone evidence is ambiguous. Risk scoring
remains disabled until session-disjoint positive, negative, hard-negative and
occluded-positive validation data is available.

## Missing / External Checkpoints

The handoff documentation references:

```text
models/checkpoints/cabin/face_detection_yunet_2026may.onnx
```

That ONNX file was not included in `handoff.zip`. If cabin visibility is enabled,
obtain the exact checkpoint or document the OpenCV Zoo download source before
claiming the baseline is runnable on a fresh machine.
