# Cabin / Driver / Phone Handoff Integration Design

Date: 2026-06-23

Source archive:

```text
handoff.zip
```

Temporary extraction path:

```text
/tmp/anomali_handoff_extract/handoff
```

## Goal

This integration imports the cabin/driver/phone work delivered by a teammate without overwriting existing project files. The handoff mostly covers cabin visibility, driver torso/pose, arm-state diagnostics, seatbelt experiments, phone object detection, phone-call behavior fusion, smoking review preparation, related contracts, benchmark summaries, tests and visual review outputs.

## Placement Rules

| Handoff content | Repo placement | Commit policy | Reason |
|---|---|---|---|
| Research and decision docs | `research/08_cabin_risk/` | Track | Human-readable model decisions and handoff rationale. |
| Benchmark/evaluation scripts | `scripts/benchmarks/` | Track | Reusable local pipelines and enrichment scripts. |
| Tests/templates/reports | `testing/` | Track | Reproducibility, manual review templates and regression checks. |
| Model output contracts | `architecture/contracts/` | Track new, do not overwrite conflicts | Shared integration contracts must be reviewable. Existing project contracts may already be newer. |
| Benchmark comparison tables | `models/benchmarks/cabin/` | Track | Small CSV summaries for model comparison. |
| Benchmark summary JSONs | `models/benchmarks/artifacts/` | Track JSON summaries | Small model/result metadata. |
| Phone specialist `.pt` weights | `models/checkpoints/cabin_phone/phone/` | Do not track binary | Binary model weights are ignored by `.gitignore`; registry records the paths. |
| Visual overlays, clips, training runs | `runs/` | Do not track | Large generated artifacts used for local/manual review. |
| Raw source archive | `handoff.zip` | Do not track | Large transfer archive, kept local only. |

## Imported Model Checkpoints

The handoff contains four phone specialist YOLO checkpoint files. They were copied to both their original run context and a cleaner checkpoint registry location.

| Experiment | Source in handoff/run context | Registry path | Role |
|---|---|---|---|
| `PHONE-EXP-003` | `runs/phone/training/phone_exp_003_yolo26s_p2_seed_smoke/weights/best.pt` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-003-yolo26s-p2-phone-windshield-seed-smoke-best.pt` | P2 phone object specialist smoke checkpoint. |
| `PHONE-EXP-003` | `runs/phone/training/phone_exp_003_yolo26s_p2_seed_smoke/weights/last.pt` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-003-yolo26s-p2-phone-windshield-seed-smoke-last.pt` | P2 training last checkpoint. |
| `PHONE-EXP-004` | `runs/phone/training/phone_exp_004_yolo26s_seed_smoke/weights/best.pt` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-004-yolo26s-phone-windshield-seed-smoke-best.pt` | Standard phone object specialist smoke checkpoint. |
| `PHONE-EXP-004` | `runs/phone/training/phone_exp_004_yolo26s_seed_smoke/weights/last.pt` | `models/checkpoints/cabin_phone/phone/PHONE-EXP-004-yolo26s-phone-windshield-seed-smoke-last.pt` | Standard training last checkpoint. |

These checkpoints are not final accepted phone-call risk models. The handoff defines them as phone-object supporting evidence only.

## Imported Runtime / Review Artifacts

The following large ignored directories were copied under `runs/` for local review and reproduction:

| Directory | Purpose |
|---|---|
| `runs/cabin_pose/` | Cabin/pose visual outputs. |
| `runs/driver_torso/` | Deterministic torso and driver ROI outputs. |
| `runs/driver_arm_state/` | Arm-state/pose diagnostic overlays. |
| `runs/driver_vlm_arm_state/` | VLM arm-state challenger metadata. |
| `runs/phone/` | Phone object training outputs, seed dataset and manual labels. |
| `runs/phone_call/` | Earlier phone-call behavior outputs. |
| `runs/phone_call_baseline_v2/` | Current provisional phone-call baseline overlays and summaries. |
| `runs/phone_call_review/` | Manual segment review clips and CSVs. |
| `runs/seatbelt/` | Seatbelt baseline/challenger outputs. |
| `runs/smoking_review/` | Smoking segment review seed package. |

## Conflict Policy

Existing repo files were not overwritten. The following handoff files had different existing counterparts and were skipped for manual review:

| Path | Action |
|---|---|
| `research/08_cabin_risk/README.md` | Skipped, existing repo README kept. |
| `scripts/benchmarks/enrich_event_skeleton_with_plate_ocr.py` | Skipped, existing repo plate/OCR script kept. |
| `scripts/benchmarks/README.md` | Skipped, existing repo README kept. |
| `scripts/benchmarks/run_plate_detection_smoke.py` | Skipped, existing repo plate detector script kept. |
| `scripts/benchmarks/run_plate_ocr_baseline.py` | Skipped, existing repo OCR script kept. |
| `testing/README.md` | Skipped, existing repo README kept. |
| `testing/reports/README.md` | Skipped, existing repo README kept. |
| `testing/reports/trk_exp_001_plate_ocr_event_enrichment_summary.md` | Skipped, existing repo report kept. |
| `architecture/contracts/model_output_contract.md` | Skipped, existing repo contract kept. |
| `architecture/contracts/README.md` | Skipped, existing repo README kept. |
| `architecture/contracts/event.schema.json` | Skipped, existing repo schema kept. |

## Integrated Baseline Interpretation

| Area | Handoff status | Project usage |
|---|---|---|
| Cabin visibility / face | Usable baseline | Use OpenCV YuNet style cabin visibility gate if checkpoint is available locally. Do not infer risk from poor visibility. |
| Driver torso / skeleton | Usable baseline | Use torso/shoulder continuity for ROI and context, not direct risk. |
| Driver arm state | Reference only | Keep as metadata/reference; do not produce final risk from arm position alone. |
| Seatbelt | Deferred / unknown | Keep reports and scripts; do not present as accepted baseline yet. |
| Phone object | Specialist smoke model | Use as supporting evidence when phone is visible; absence does not mean no phone-call. |
| Phone-call behavior | Provisional integration baseline | Can produce `handheld_call_likely`, `candidate`, `not_detected`, `not_evaluable`; risk remains disabled. |
| Smoking | Review seed only | Segment review package is present; no accepted model yet. |

## Open Questions For User / Teammate

1. Is the YuNet ONNX checkpoint (`face_detection_yunet_2026may.onnx`) available separately? It is referenced by the handoff docs but not present in `handoff.zip`.
2. Should the phone specialist checkpoints be used immediately in the FTR adapter, or only kept as research artifacts until negative/hard-negative data is labeled?
3. Does the team want the large `runs/` overlay outputs preserved on this machine long-term, or should they be reduced after manual review?
4. Are there additional held-out cabin/phone videos beyond the current three road videos for session-disjoint validation?

## Next Integration Step

Do not enable cabin/phone risk scoring yet. The safe next step is:

1. Run py-compile/unit tests for the imported cabin/phone scripts.
2. Create a small local smoke run that reads the existing event skeleton and appends cabin/phone provisional fields.
3. Keep phone risk as `null` until positive, negative, hard-negative and occluded-positive sessions are labeled.
