# Handoff Cabin / Phone Import Summary

Date: 2026-06-23

Source archive:

```text
handoff.zip
```

## Import Result

| Item | Result |
|---|---:|
| Zip entries | 20624 |
| Uncompressed size | ~1326.95 MB |
| Non-run tracked files imported | 199 |
| Existing conflicting files skipped | 11 |
| Phone `.pt` checkpoints promoted to checkpoint registry | 4 |
| Large `runs/` directories copied locally | 10 |

## Imported Areas

| Area | Destination | Status |
|---|---|---|
| Cabin/driver/phone research docs | `research/08_cabin_risk/` | Imported new files. |
| Benchmark and enrichment scripts | `scripts/benchmarks/` | Imported new files; existing plate/OCR scripts preserved. |
| Tests and manual review templates | `testing/` | Imported new files. |
| Cabin benchmark CSVs | `models/benchmarks/cabin/` | Imported. |
| Summary/event artifacts | `models/benchmarks/artifacts/` | Imported JSON artifacts. |
| Integration contracts | `architecture/contracts/` | Imported new example profiles; existing contracts preserved. |
| Phone specialist weights | `models/checkpoints/cabin_phone/phone/` | Copied locally, Git ignored. |
| Visual/runnable outputs | `runs/` | Copied locally, Git ignored. |

## Imported Runtime Directories

These directories are intentionally not tracked by Git:

```text
runs/cabin_pose/
runs/driver_torso/
runs/driver_arm_state/
runs/driver_vlm_arm_state/
runs/phone/
runs/phone_call/
runs/phone_call_baseline_v2/
runs/phone_call_review/
runs/seatbelt/
runs/smoking_review/
```

## Local Model Files

The following files were copied locally:

```text
models/checkpoints/cabin_phone/phone/PHONE-EXP-003-yolo26s-p2-phone-windshield-seed-smoke-best.pt
models/checkpoints/cabin_phone/phone/PHONE-EXP-003-yolo26s-p2-phone-windshield-seed-smoke-last.pt
models/checkpoints/cabin_phone/phone/PHONE-EXP-004-yolo26s-phone-windshield-seed-smoke-best.pt
models/checkpoints/cabin_phone/phone/PHONE-EXP-004-yolo26s-phone-windshield-seed-smoke-last.pt
```

They are documented in:

```text
models/checkpoint_registry_cabin_phone.md
```

## Preserved Conflicts

These handoff files differed from existing repo files and were not overwritten:

```text
research/08_cabin_risk/README.md
scripts/benchmarks/enrich_event_skeleton_with_plate_ocr.py
scripts/benchmarks/README.md
scripts/benchmarks/run_plate_detection_smoke.py
scripts/benchmarks/run_plate_ocr_baseline.py
testing/README.md
testing/reports/README.md
testing/reports/trk_exp_001_plate_ocr_event_enrichment_summary.md
architecture/contracts/model_output_contract.md
architecture/contracts/README.md
architecture/contracts/event.schema.json
```

## Baseline Interpretation

| Module | Status after import |
|---|---|
| Cabin visibility / face | Usable baseline concept; exact YuNet ONNX checkpoint is referenced but not present in the zip. |
| Driver torso / pose | Usable as ROI/context baseline; not direct risk. |
| Driver arm state | Reference/metadata only; not direct risk. |
| Seatbelt | Deferred / unknown; imported for review, not accepted as final. |
| Phone object | Smoke specialist exists; supporting evidence only. |
| Phone-call behavior | Provisional integration baseline; `phone_risk` remains disabled. |
| Smoking | Segment review seed package only; no accepted model yet. |

## Required User / Teammate Clarification

1. Provide or approve the exact YuNet ONNX checkpoint source before claiming cabin visibility is fully runnable on a clean machine.
2. Confirm whether `PHONE-EXP-004` should be wired into the next FTR adapter run as supporting evidence, or kept research-only until negative/hard-negative sessions are labeled.
3. Decide whether the large local `runs/` outputs should be kept after manual review or compressed/removed to save disk.

## Next Step

Run a lightweight verification pass:

```bash
python3 -m py_compile scripts/benchmarks/cabin_utils.py scripts/benchmarks/phone_utils.py scripts/benchmarks/seatbelt_utils.py
```

Then wire only non-risk cabin/phone evidence fields into event/evidence JSON. Do
not enable final phone-call or seatbelt risk without the required validation data.
