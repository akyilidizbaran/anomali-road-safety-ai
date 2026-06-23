# TYPE-EXP-004 Run Review

Date: 2026-06-23

Notebook:

```text
notebooks/TYPE_EXP_004_T4_Controlled_Minibus_Repair_Colab_outsaved.ipynb
```

Drive checkpoint reviewed:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-004-efficientnet_b0-best.pth
```

Local checkpoint copy:

```text
runs/vehicle_type/TYPE-EXP-004-local-smoke/artifacts/TYPE-EXP-004-efficientnet_b0-best.pth
```

## Decision

`TYPE-EXP-004` should not be promoted as the active runtime/FTR vehicle type model.

The controlled minibus repair worked on the dataset split, but it did not solve the local target ROI false-mode problem. On the same three target ROI videos used for `TYPE-EXP-002` and `TYPE-EXP-003`, `TYPE-EXP-004` still shifts `video_2` and `video_3` toward `minibus` after the confidence/margin gate.

Active runtime baseline remains:

```text
TYPE-EXP-002-efficientnet_b0-best.pth
```

with track-level gated temporal majority.

## Notebook-Level Result

The notebook completed and produced a valid checkpoint. The Colab output is technically healthy:

| Item | Result |
|---|---:|
| Raw metadata rows | 23281 |
| Controlled metadata rows | 17942 |
| Train / val / test | 12558 / 2692 / 2692 |
| Best backbone | efficientnet_b0 |
| Parent checkpoint | TYPE-EXP-002-efficientnet_b0-best.pth |
| Dataset promotion candidate | true |

Controlled class counts:

| Class | Count |
|---|---:|
| sedan | 3400 |
| suv | 3200 |
| hatchback | 2175 |
| pickup | 3400 |
| minibus | 859 |
| panelvan | 3108 |
| kamyon | 1800 |

## Dataset Metrics

Validation:

| Metric | Value |
|---|---:|
| macro_f1 | 0.8675 |
| guard_macro_f1 | 0.8486 |
| minibus_f1 | 0.8675 |
| minibus_precision | 0.9000 |
| minibus_recall | 0.8372 |
| minibus_false_positive_rate | 0.0047 |
| minibus_pred_ratio | 0.0446 |
| accuracy | 0.8607 |

Test:

| Metric | Value |
|---|---:|
| macro_f1 | 0.8880 |
| guard_macro_f1 | 0.8644 |
| minibus_f1 | 0.9106 |
| minibus_precision | 0.9573 |
| minibus_recall | 0.8682 |
| minibus_false_positive_rate | 0.0020 |
| minibus_pred_ratio | 0.0435 |
| accuracy | 0.8789 |

Test per-class F1:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| sedan | 0.7985 | 0.8549 | 0.8258 | 510 |
| suv | 0.8107 | 0.8208 | 0.8157 | 480 |
| hatchback | 0.8783 | 0.9266 | 0.9018 | 327 |
| pickup | 0.9372 | 0.8784 | 0.9069 | 510 |
| minibus | 0.9573 | 0.8682 | 0.9106 | 129 |
| panelvan | 0.9513 | 0.8798 | 0.9142 | 466 |
| kamyon | 0.9100 | 0.9741 | 0.9410 | 270 |

These metrics are much better than `TYPE-EXP-002` for minibus, and they are strong enough for dataset-level documentation. They are not enough for runtime freeze because the local target ROI holdout exposes a regression.

## Parent Comparison

On the `TYPE-EXP-004` split, the parent checkpoint had weak minibus metrics:

| Metric | Parent TYPE-EXP-002 | TYPE-EXP-004 |
|---|---:|---:|
| val_macro_f1 | 0.7014 | 0.8675 |
| val_minibus_f1 | 0.1604 | 0.8675 |
| val_minibus_precision | 0.2586 | 0.9000 |
| val_minibus_recall | 0.1163 | 0.8372 |
| test_macro_f1 | 0.7144 | 0.8880 |
| test_minibus_f1 | 0.2584 | 0.9106 |
| test_minibus_precision | 0.3375 | 0.9573 |
| test_minibus_recall | 0.2093 | 0.8682 |

This confirms the repair objective worked on the curated split.

## Local Crop Smoke

Command:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_type_classifier_smoke.py \
  --checkpoint runs/vehicle_type/TYPE-EXP-004-local-smoke/artifacts/TYPE-EXP-004-efficientnet_b0-best.pth \
  --input-dir runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames \
  --output-dir runs/vehicle_type/TYPE-EXP-004-local-smoke
```

Artifacts:

```text
runs/vehicle_type/TYPE-EXP-004-local-smoke/type-exp-004_local_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-004-local-smoke/type-exp-004_local_smoke_summary.json
runs/vehicle_type/TYPE-EXP-004-local-smoke/type-exp-004_local_smoke_contact_sheet.jpg
```

Overall crop top-1 counts:

| Class | Count |
|---|---:|
| minibus | 14 |
| suv | 12 |
| sedan | 7 |
| pickup | 3 |
| hatchback | 2 |
| panelvan | 1 |

Per-video gated crop result:

| Video | Gate pass | Gated top-1 counts | Interpretation |
|---|---:|---|---|
| video_1 | 6 | suv 2, hatchback 2, pickup 1, minibus 1 | Mixed |
| video_2 | 5 | minibus 3, suv 2 | Fail |
| video_3 | 11 | minibus 7, suv 4 | Fail |

The crop-level smoke test already shows the same minibus drift that caused `TYPE-EXP-003` to be rejected.

## Local Video Smoke

Command:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_type_classifier_video_smoke.py \
  --checkpoint runs/vehicle_type/TYPE-EXP-004-local-smoke/artifacts/TYPE-EXP-004-efficientnet_b0-best.pth \
  --clips-dir runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/clips \
  --output-dir runs/vehicle_type/TYPE-EXP-004-local-video-smoke \
  --frame-stride 1
```

Artifacts:

```text
runs/vehicle_type/TYPE-EXP-004-local-video-smoke/type-exp-004_local_video_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-004-local-video-smoke/type-exp-004_local_video_smoke_summary.json
runs/vehicle_type/TYPE-EXP-004-local-video-smoke/video_1_type-exp-004_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-004-local-video-smoke/video_2_type-exp-004_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-004-local-video-smoke/video_3_type-exp-004_type_overlay.mp4
```

Overall video top-1 counts:

| Class | Count |
|---|---:|
| suv | 383 |
| minibus | 306 |
| sedan | 147 |
| pickup | 75 |
| hatchback | 57 |
| panelvan | 6 |
| kamyon | 1 |

Per-video gated result:

| Video | Sampled frames | Gate pass | Gated top-1 counts | Decision |
|---|---:|---:|---|---|
| video_1 | 344 | 154 | suv 80, hatchback 28, minibus 21, pickup 16, sedan 9 | Pass with noise |
| video_2 | 344 | 102 | minibus 52, suv 42, sedan 6, pickup 2 | Fail |
| video_3 | 287 | 177 | minibus 104, suv 72, hatchback 1 | Fail |

## Comparison With TYPE-EXP-002 And TYPE-EXP-003

Same local target ROI video holdout:

| Experiment | Overall raw top-1 | Overall gate pass | video_1 gated | video_2 gated | video_3 gated | Runtime decision |
|---|---|---:|---|---|---|---|
| TYPE-EXP-002 | suv 808, hatchback 142, minibus 9 | 729 | suv 215, hatchback 51 | suv 244, hatchback 16 | suv 192, hatchback 11 | Keep active |
| TYPE-EXP-003 | suv 504, minibus 382 | 564 | suv 169, minibus 56 | minibus 80, suv 62 | minibus 109, suv 79 | Reject |
| TYPE-EXP-004 | suv 383, minibus 306, sedan 147 | 433 | suv 80, hatchback 28, minibus 21 | minibus 52, suv 42 | minibus 104, suv 72 | Reject |

`TYPE-EXP-004` improves dataset-level minibus performance, but it is still worse than `TYPE-EXP-002` on the fixed local demo holdout.

## Interpretation

The likely issue is not simple class imbalance anymore. The model learned a stronger minibus decision boundary from Vehicle-10/focus data, but the local target SUV crop geometry, low-light quality, rear/side viewpoint, or crop framing overlaps with minibus-like visual cues. Because the active demo target vehicle should remain stable at track level, the runtime model cannot be promoted only from dataset metrics.

## Recommendation

1. Keep `TYPE-EXP-002` as the current vehicle type runtime baseline.
2. Use `TYPE-EXP-004` only as documented evidence that minibus dataset repair was attempted and improved benchmark metrics.
3. Do not run more minibus-only repair without a local holdout-aware validation set.
4. Next type experiment, if needed, should add target-geometry hard negatives and/or viewpoint-aware ROI augmentation, not simply more minibus examples.
5. Proceed with FTR/evidence adapter integration using `TYPE-EXP-002` and track-level gated temporal majority.

## Freeze Status

`TYPE-EXP-004` is closed as a non-promoted experiment.

Runtime active model remains `TYPE-EXP-002`.
