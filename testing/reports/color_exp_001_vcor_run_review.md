# COLOR-EXP-001 VCoR Vehicle Color Classifier Run Review

Date: 2026-06-22

## Verdict

`COLOR-EXP-001` is a successful dedicated vehicle color classifier run for the FTR `arac_bilgisi.renk` field.

The run is strong enough to move the project forward to the `TYPE-EXP-001` vehicle type phase. Final runtime promotion should still wait for target ROI smoke inference and manual review on our three local videos.

## Dataset Mapping

The notebook mapped VCoR images into the 9 FTR color classes:

| FTR color | Count |
|---|---:|
| `beyaz` | 575 |
| `siyah` | 579 |
| `gri` | 1127 |
| `kirmizi` | 909 |
| `mavi` | 1060 |
| `sari` | 1124 |
| `yesil` | 804 |
| `turuncu` | 762 |
| `kahverengi` | 1979 |

Mapped image count: `8919`

Skipped image count: `1454`

Split:

| Split | Count |
|---|---:|
| train | 6242 |
| val | 1339 |
| test | 1338 |

## Backbone Comparison

| Backbone | Best validation macro-F1 | Best epoch |
|---|---:|---:|
| `efficientnet_b0` | 0.937725 | 9 |
| `mobilenet_v3_large` | 0.923399 | 6 |

Selected checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_color/COLOR-EXP-001-efficientnet_b0-best.pth
```

Label map:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_color/COLOR-EXP-001-label-map.json
```

## Test Metrics

Overall:

| Metric | Value |
|---|---:|
| test accuracy | 0.928999 |
| test macro-F1 | 0.929729 |
| test weighted-F1 | 0.929092 |

Per-class:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `beyaz` | 0.852632 | 0.941860 | 0.895028 | 86 |
| `siyah` | 0.865979 | 0.965517 | 0.913043 | 87 |
| `gri` | 0.880000 | 0.911243 | 0.895349 | 169 |
| `kirmizi` | 0.949275 | 0.963235 | 0.956204 | 136 |
| `mavi` | 0.987261 | 0.974843 | 0.981013 | 159 |
| `sari` | 0.943750 | 0.893491 | 0.917933 | 169 |
| `yesil` | 0.959677 | 0.983471 | 0.971429 | 121 |
| `turuncu` | 0.944954 | 0.903509 | 0.923767 | 114 |
| `kahverengi` | 0.936396 | 0.892256 | 0.913793 | 297 |

## Quality Notes

* The dataset-level result is strong: every FTR color class has F1 near or above `0.895`.
* `efficientnet_b0` outperformed `mobilenet_v3_large`; it should be the active color checkpoint candidate.
* The notebook emitted Colab/PyTorch DataLoader worker shutdown warnings during Cell 8. These were not fatal and the run completed, but the active notebook was patched to use `NUM_WORKERS=0` to prevent noisy future runs.
* Cell 10 target ROI smoke inference was not executed in the output-saved notebook. This means the model has not yet been checked on our 3 local target vehicle crop sequences.

## Decision

Proceed to `TYPE-EXP-001`.

Before promoting `COLOR-EXP-001` to the runtime/FTR adapter, run target ROI smoke inference or local model inference on the same crop set used by `VEHINFO-EXP-001`, then compare:

1. `COLOR-EXP-001` final temporal color vote
2. `VEHINFO-EXP-001` OpenVINO + HSV/Lab vote
3. manual review on `Test/video_1-3.mp4`

If the local target ROI smoke confirms stable `siyah` on the three current videos, the color branch can be treated as ready for `VEHINFO-EXP-002` fusion.

## Artifacts Reported By Notebook

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_color/COLOR-EXP-001/COLOR-EXP-001-summary.json
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_color/COLOR-EXP-001/COLOR-EXP-001-test_classification_report.csv
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_color/COLOR-EXP-001/COLOR-EXP-001-test_confusion_matrix.csv
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_color/COLOR-EXP-001/COLOR-EXP-001-test_confusion_matrix.png
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_color/COLOR-EXP-001/COLOR-EXP-001-test_predictions.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_color/COLOR-EXP-001-efficientnet_b0-best.pth
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_color/COLOR-EXP-001-label-map.json
```
