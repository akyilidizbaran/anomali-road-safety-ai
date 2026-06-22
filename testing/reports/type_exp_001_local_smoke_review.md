# TYPE-EXP-001 Local Target ROI Smoke Review

Date: 2026-06-22

## Purpose

The `TYPE-EXP-001` vehicle type classifier checkpoint was downloaded from Google Drive and tested
on the project's local target vehicle ROI sample frames.

This is a smoke/manual-review test, not a final accuracy benchmark. The local `Test/video_1-3`
clips do not contain ground-truth vehicle type labels.

## Source Artifacts

Google Drive checkpoint folder:

```text
models/checkpoints/vehicle_type/
```

Files used:

```text
TYPE-EXP-001-efficientnet_b0-best.pth
TYPE-EXP-001-label-map.json
```

Drive metadata:

| File | Drive ID |
|---|---|
| `TYPE-EXP-001-efficientnet_b0-best.pth` | `1KGV0cGkpMjN-gsd5CSkMll-pSWa4MVHi` |
| `TYPE-EXP-001-label-map.json` | `1wWbI1lqz-IbZ75lbqdE7F15hzS4sJLIa` |

Local test input:

```text
runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames/
```

Local test outputs:

```text
runs/vehicle_type/TYPE-EXP-001-local-smoke/type_exp_001_local_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-001-local-smoke/type_exp_001_local_smoke_summary.json
runs/vehicle_type/TYPE-EXP-001-local-smoke/type_exp_001_local_smoke_contact_sheet.jpg
```

## Script

```text
scripts/benchmarks/run_type_classifier_smoke.py
```

Command:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_type_classifier_smoke.py
```

Gate used for local review:

```text
min_confidence = 0.60
min_margin = 0.15
```

## Checkpoint Context

| Field | Value |
|---|---:|
| Experiment | `TYPE-EXP-001` |
| Backbone | `efficientnet_b0` |
| Best epoch | 8 |
| Validation macro-F1 | 0.5414 |
| Validation accuracy | 0.6612 |

Known blocker from dataset-level review:

```text
kamyon support = 0
```

## Local ROI Smoke Results

Total local ROI sample frames:

```text
39
```

Overall predictions:

| Predicted type | Frame count |
|---|---:|
| `suv` | 21 |
| `hatchback` | 15 |
| `sedan` | 2 |
| `panelvan` | 1 |

Gate-passing frames:

```text
31 / 39
```

## Per-Video Summary

| Video | Frames | Top-1 counts | Gate pass | Gated counts | Mean confidence | Mean margin |
|---|---:|---|---:|---|---:|---:|
| `video_1` | 13 | `suv=7`, `hatchback=5`, `sedan=1` | 11 | `suv=7`, `hatchback=4` | 0.7808 | 0.6177 |
| `video_2` | 13 | `suv=7`, `hatchback=6` | 11 | `suv=7`, `hatchback=4` | 0.7686 | 0.6159 |
| `video_3` | 13 | `suv=7`, `hatchback=4`, `sedan=1`, `panelvan=1` | 9 | `suv=7`, `hatchback=2` | 0.7608 | 0.6052 |

## Interpretation

The checkpoint gives strong `suv` predictions on frontal or near-frontal target vehicle crops.
However, it is not temporally stable enough for final runtime promotion:

- Side/rear/partial crops frequently shift to `hatchback`.
- One low-confidence frame shifts to `panelvan`.
- The same target vehicle should ideally produce a stable type label across the track.
- The model was trained before the token-aware mapping fix, so it may still carry label noise.

## Decision

Do not promote this checkpoint as the final FTR `arac_bilgisi.tip` model.

It can be kept as a diagnostic baseline, but final integration should wait for:

1. Rerun with the patched token-aware mapper.
2. Additional `kamyon` data.
3. Track-level temporal voting over ROI predictions.
4. Manual review on the local target vehicle crops.
