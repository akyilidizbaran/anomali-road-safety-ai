# TYPE-EXP-003 Run Review

## Reviewed Artifact

Output notebook:

```text
notebooks/TYPE_EXP_003_Focus_Sedan_SUV_Hatchback_Minibus_Colab_outsaved.ipynb
```

Drive checkpoint reported by notebook:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-003-efficientnet_b0-best.pth
```

Local checkpoint used for smoke tests:

```text
runs/vehicle_type/TYPE-EXP-003-local-smoke/artifacts/TYPE-EXP-003-efficientnet_b0-best.pth
```

## Purpose

`TYPE-EXP-003` was opened as a focused refinement run after `TYPE-EXP-002`.
The goal was to improve the weak or moderate FTR vehicle-type classes:

- `sedan`
- `suv`
- `hatchback`
- `minibus`

The run continued from the `TYPE-EXP-002` EfficientNet-B0 checkpoint instead of
training a new model from scratch.

## Dataset Coverage

The notebook successfully prepared all configured data sources.

| Source | Images / records used | Role |
|---|---:|---|
| Stanford Cars | 5,045 records | Conservative model-name to FTR type mapping |
| Car Body Type | 5,366 records | Body-shape support for `sedan`, `suv`, `hatchback`, `pickup`, `panelvan` |
| MIO-TCD classification subset | 8,800 records | Commercial/heavy vehicle support |
| VTID2 | 4,193 records | Focus support for `sedan`, `suv`, `hatchback`, `pickup` |
| Vehicle-10 | 1,477 records | Focus support for `minibus` |

Raw mapped distribution:

| FTR type | Raw rows |
|---|---:|
| `sedan` | 4,094 |
| `suv` | 3,363 |
| `hatchback` | 2,175 |
| `pickup` | 5,655 |
| `minibus` | 1,686 |
| `panelvan` | 3,508 |
| `kamyon` | 4,400 |

Used distribution after capping:

| FTR type | Used rows |
|---|---:|
| `sedan` | 4,094 |
| `suv` | 3,363 |
| `hatchback` | 2,175 |
| `pickup` | 5,200 |
| `minibus` | 1,686 |
| `panelvan` | 3,508 |
| `kamyon` | 4,400 |

Train / validation / test split:

```text
17097 / 3665 / 3664
```

## Dataset-Level Metrics

The dataset-level result is a clear improvement over the parent checkpoint when
both are evaluated on the `TYPE-EXP-003` split.

| Metric | Parent `TYPE-EXP-002` on EXP-003 split | `TYPE-EXP-003` | Delta |
|---|---:|---:|---:|
| Test macro-F1 | 0.6881 | 0.8763 | +0.1882 |
| Test focus macro-F1 | 0.5628 | 0.8466 | +0.2838 |
| Test accuracy | 0.7555 | 0.8742 | +0.1187 |
| Test selection score | 0.6192 | 0.8600 | +0.2408 |

Per-class test result:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `sedan` | 0.7273 | 0.8730 | 0.7935 | 614 |
| `suv` | 0.7791 | 0.7960 | 0.7875 | 505 |
| `hatchback` | 0.8601 | 0.9049 | 0.8819 | 326 |
| `pickup` | 0.9612 | 0.8577 | 0.9065 | 780 |
| `minibus` | 0.9147 | 0.9328 | 0.9237 | 253 |
| `panelvan` | 0.9598 | 0.8175 | 0.8830 | 526 |
| `kamyon` | 0.9535 | 0.9621 | 0.9578 | 660 |

Dataset-level interpretation:

- The focused data sources fixed the `TYPE-EXP-002` minibus weakness on the
  held-out split.
- `sedan`, `suv`, and `hatchback` improved materially.
- The run is technically healthy and the checkpoint is valid.
- Dataset-level performance alone is not enough for runtime promotion, because
  our active target ROI distribution is narrower and darker than the training
  split.

## Local Target ROI Crop Smoke

Input:

```text
runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames
```

Output:

```text
runs/vehicle_type/TYPE-EXP-003-local-smoke/type-exp-003_local_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-003-local-smoke/type-exp-003_local_smoke_summary.json
runs/vehicle_type/TYPE-EXP-003-local-smoke/type-exp-003_local_smoke_contact_sheet.jpg
```

Summary:

| Video | Frames | Top-1 counts | Gate-pass frames | Gated top-1 counts | Mean confidence | Mean margin |
|---|---:|---|---:|---|---:|---:|
| `video_1` | 13 | `suv=5`, `sedan=1`, `minibus=6`, `hatchback=1` | 6 | `suv=3`, `minibus=3` | 0.6069 | 0.4107 |
| `video_2` | 13 | `suv=5`, `sedan=2`, `minibus=6` | 4 | `suv=1`, `minibus=3` | 0.5788 | 0.3822 |
| `video_3` | 13 | `minibus=7`, `sedan=1`, `suv=5` | 9 | `minibus=4`, `sedan=1`, `suv=4` | 0.7644 | 0.6379 |

Overall crop smoke:

```text
suv=15, minibus=19, sedan=4, hatchback=1
```

This is a regression for the active demo target vehicle. `TYPE-EXP-002` produced
a stable `suv` majority on the same 39 crop images.

## Local Target ROI Video Overlay Smoke

Input:

```text
runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/clips
```

Output:

```text
runs/vehicle_type/TYPE-EXP-003-local-video-smoke/type-exp-003_local_video_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-003-local-video-smoke/type-exp-003_local_video_smoke_summary.json
runs/vehicle_type/TYPE-EXP-003-local-video-smoke/video_1_type-exp-003_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-003-local-video-smoke/video_2_type-exp-003_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-003-local-video-smoke/video_3_type-exp-003_type_overlay.mp4
```

Summary:

| Video | Sampled frames | Top-1 counts | Gate-pass frames | Gated top-1 counts | Mean confidence | Mean margin |
|---|---:|---|---:|---|---:|---:|
| `video_1` | 344 | `suv=206`, `sedan=12`, `minibus=97`, `pickup=12`, `hatchback=17` | 230 | `suv=169`, `sedan=5`, `minibus=56` | 0.6809 | 0.5249 |
| `video_2` | 344 | `suv=187`, `sedan=40`, `minibus=115`, `hatchback=2` | 146 | `suv=62`, `sedan=4`, `minibus=80` | 0.5954 | 0.4080 |
| `video_3` | 287 | `minibus=170`, `suv=111`, `sedan=6` | 188 | `minibus=109`, `suv=79` | 0.6892 | 0.5094 |

Overall video smoke:

```text
suv=504, minibus=382, sedan=58, pickup=12, hatchback=19
gate_pass_frames=564
```

`TYPE-EXP-003` keeps a raw `suv` plurality overall, but the gated track-level
majority fails on `video_2` and `video_3`, where `minibus` becomes the dominant
gated label. This makes the checkpoint unsafe for the current 3-video runtime
pipeline.

## Comparison With TYPE-EXP-002 Local Smoke

| Test | `TYPE-EXP-002` | `TYPE-EXP-003` | Interpretation |
|---|---:|---:|---|
| Crop overall `suv` count | 32 / 39 | 15 / 39 | EXP-003 regressed on active crops |
| Crop overall `minibus` count | 1 / 39 | 19 / 39 | EXP-003 over-predicts `minibus` |
| Video raw `suv` count | 808 / 975 | 504 / 975 | EXP-003 is less stable |
| Video raw `minibus` count | 9 / 975 | 382 / 975 | EXP-003 introduces a major false `minibus` mode |
| Video gated `suv` frames | 651 / 729 | 310 / 564 | EXP-003 loses gated stability |
| Video gated majority on `video_1` | `suv` | `suv` | OK |
| Video gated majority on `video_2` | `suv` | `minibus` | Regression |
| Video gated majority on `video_3` | `suv` | `minibus` | Regression |

## Freeze Decision

`TYPE-EXP-003` should **not** be frozen as the active runtime vehicle-type model
for the current project phase.

Recommended active model:

```text
TYPE-EXP-002-efficientnet_b0-best.pth
```

Reason:

- `TYPE-EXP-003` is better on the broader validation/test split.
- It is worse on the actual local target ROI clips that represent the current
  demo/evidence pipeline.
- The likely cause is domain shift and over-correction from the added minibus
  sources. Vehicle-10 appears to improve minibus benchmark behavior but pushes
  our dark target SUV crops toward `minibus`.

## What To Freeze

Freeze the decision, not the `TYPE-EXP-003` checkpoint:

- Keep `TYPE-EXP-003` as a documented dataset-level refinement experiment.
- Keep `TYPE-EXP-002` as the active demo/runtime baseline for FTR `tip`.
- Runtime output must still use track-level temporal/gated majority:
  - `min_confidence >= 0.60`
  - `top1_top2_margin >= 0.15`
  - final exposed label from track-level majority, not single-frame top-1.

## Next Action

Proceed with `TYPE-EXP-002` integration into the vehicle-info / FTR adapter.

If a later `TYPE-EXP-004` is opened, it should not simply add more minibus data.
It should add a domain-aware validation gate:

1. Keep `TYPE-EXP-002` local demo clips as a fixed holdout smoke set.
2. Add dark/low-light SUV-like crops to the validation objective.
3. Use source-balanced sampling or lower minibus oversampling weight.
4. Promote a checkpoint only if both dataset-level metrics and local ROI smoke
   improve together.
