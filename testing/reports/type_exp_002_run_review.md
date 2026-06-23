# TYPE-EXP-002 Run Review

## Reviewed Artifact

Output notebook:

```text
notebooks/TYPE_EXP_002_Multisource_FTR_Vehicle_Type_Classifier_Colab_save.ipynb
```

Drive checkpoint reported by notebook:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-002-efficientnet_b0-best.pth
```

## Dataset Coverage

The run successfully collected and trained on all 7 FTR vehicle type labels:

| FTR type | Raw/used images | Main sources |
|---|---:|---|
| `sedan` | 2872 | Stanford Cars, Car Body Type |
| `suv` | 2683 | Stanford Cars, Car Body Type |
| `hatchback` | 1573 | Stanford Cars, Car Body Type |
| `pickup` | 3566 | Stanford Cars, Car Body Type, MIO-TCD |
| `minibus` | 209 | Stanford Cars only |
| `panelvan` | 3108 | Stanford Cars, Car Body Type, MIO-TCD |
| `kamyon` | 3600 | MIO-TCD |

This fixes the `TYPE-EXP-001` blocker where `kamyon` had `0` support.

## Training Result

Best backbone:

```text
efficientnet_b0
```

Reported metrics:

| Metric | Value |
|---|---:|
| Validation macro-F1 | 0.6301 |
| Validation accuracy | 0.7408 |
| Test macro-F1 | 0.6312 |
| Test accuracy | 0.7392 |
| Train / val / test | 12326 / 2643 / 2642 |

Per-class test metrics:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `sedan` | 0.5267 | 0.6636 | 0.5873 | 431 |
| `suv` | 0.5488 | 0.6005 | 0.5735 | 403 |
| `hatchback` | 0.6114 | 0.5466 | 0.5772 | 236 |
| `pickup` | 0.8681 | 0.7626 | 0.8119 | 535 |
| `minibus` | 0.0606 | 0.0645 | 0.0625 | 31 |
| `panelvan` | 0.9628 | 0.7768 | 0.8599 | 466 |
| `kamyon` | 0.9225 | 0.9704 | 0.9458 | 540 |

## Interpretation

`TYPE-EXP-002` is a real improvement over `TYPE-EXP-001` for the commercial/large-vehicle side:

- `kamyon` is now trained and performs strongly in the dataset split.
- `panelvan` and `pickup` are strong compared with the first run.

It is **not yet a final FTR vehicle type model**:

- `minibus` remains the main blocker. It has only 209 raw examples and a test F1 of `0.0625`.
- `sedan`, `suv`, and `hatchback` are still moderate and likely affected by source taxonomy and viewpoint mismatch.
- The Colab target ROI smoke cell skipped because ROI crops were not present in Drive.
- Local target ROI/video smoke test could not be completed until the `TYPE-EXP-002-efficientnet_b0-best.pth` checkpoint is available on the local machine.

## Local Manual Test Status

The local smoke test code path is ready:

- `scripts/benchmarks/run_type_classifier_smoke.py` now derives output filenames from the checkpoint experiment ID.
- `scripts/benchmarks/run_type_classifier_video_smoke.py` was added to generate annotated MP4 overlays from target ROI clips.
- Both scripts were validated with the existing `TYPE-EXP-001` checkpoint.

The `TYPE-EXP-002` checkpoint could not be downloaded by shell during this review:

- Google Drive connector saw the file and confirmed its size: `16,375,323` bytes.
- Local direct download failed because the machine could not resolve Google auth/download hosts.
- Therefore, no `TYPE-EXP-002` local manual overlay should be claimed yet.

## Manual Test Command

Place the checkpoint here:

```text
runs/vehicle_type/TYPE-EXP-002-local-smoke/artifacts/TYPE-EXP-002-efficientnet_b0-best.pth
```

Then run image crop smoke:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_type_classifier_smoke.py \
  --checkpoint runs/vehicle_type/TYPE-EXP-002-local-smoke/artifacts/TYPE-EXP-002-efficientnet_b0-best.pth \
  --input-dir runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames \
  --output-dir runs/vehicle_type/TYPE-EXP-002-local-smoke
```

Run target ROI clip overlay smoke:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_type_classifier_video_smoke.py \
  --checkpoint runs/vehicle_type/TYPE-EXP-002-local-smoke/artifacts/TYPE-EXP-002-efficientnet_b0-best.pth \
  --clips-dir runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/clips \
  --output-dir runs/vehicle_type/TYPE-EXP-002-local-video-smoke \
  --frame-stride 1
```

Expected output examples:

```text
runs/vehicle_type/TYPE-EXP-002-local-smoke/type-exp-002_local_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-002-local-smoke/type-exp-002_local_smoke_contact_sheet.jpg
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/video_1_type-exp-002_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/video_2_type-exp-002_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/video_3_type-exp-002_type_overlay.mp4
```

## Next Decision

Do not lock `TYPE-EXP-002` yet.

Recommended next steps:

1. Download/copy the `TYPE-EXP-002-efficientnet_b0-best.pth` checkpoint locally and run the two smoke commands above.
2. If the same target vehicle remains unstable across the three videos, add track-level temporal voting before rejecting the checkpoint.
3. Add targeted `minibus` data before the next full training run.
4. Consider splitting `minibus` vs `panelvan` review data manually, because the dataset taxonomies do not cleanly match the FTR labels.

