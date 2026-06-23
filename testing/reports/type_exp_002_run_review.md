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

## Dataset-Level Interpretation

`TYPE-EXP-002` is a real improvement over `TYPE-EXP-001` for the commercial/large-vehicle side:

- `kamyon` is now trained and performs strongly in the dataset split.
- `panelvan` and `pickup` are strong compared with the first run.

It is **not yet a final universal FTR vehicle type model**:

- `minibus` remains the main blocker. It has only 209 raw examples and a test F1 of `0.0625`.
- `sedan`, `suv`, and `hatchback` are still moderate and likely affected by source taxonomy and viewpoint mismatch.

## Local Manual Test Status

DNS/Drive download blocking was resolved and the `TYPE-EXP-002` checkpoint was tested locally.

Local checkpoint:

```text
runs/vehicle_type/TYPE-EXP-002-local-smoke/artifacts/TYPE-EXP-002-efficientnet_b0-best.pth
```

The checkpoint loads correctly and reports:

| Field | Value |
|---|---|
| Experiment ID | `TYPE-EXP-002` |
| Backbone | `efficientnet_b0` |
| Best validation macro-F1 | `0.6301` |
| Labels | `sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan`, `kamyon` |

### Target ROI Crop Smoke

Input:

```text
runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames
```

Output:

```text
runs/vehicle_type/TYPE-EXP-002-local-smoke/type-exp-002_local_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-002-local-smoke/type-exp-002_local_smoke_summary.json
runs/vehicle_type/TYPE-EXP-002-local-smoke/type-exp-002_local_smoke_contact_sheet.jpg
```

Summary:

| Video | Frames | Top-1 counts | Gate-pass frames | Gated top-1 counts | Mean confidence | Mean margin |
|---|---:|---|---:|---|---:|---:|
| `video_1` | 13 | `suv=9`, `hatchback=3`, `panelvan=1` | 9 | `suv=7`, `hatchback=2` | 0.6642 | 0.5385 |
| `video_2` | 13 | `suv=10`, `hatchback=1`, `minibus=1`, `kamyon=1` | 7 | `suv=7` | 0.6115 | 0.4572 |
| `video_3` | 13 | `suv=13` | 10 | `suv=10` | 0.7261 | 0.6115 |

Overall, 32 of 39 sampled ROI crops are classified as `suv`. After the confidence/margin gate, all three videos have a `suv` majority.

### Target ROI Clip Overlay Smoke

Input:

```text
runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/clips
```

Output:

```text
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/type-exp-002_local_video_smoke_predictions.csv
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/type-exp-002_local_video_smoke_summary.json
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/video_1_type-exp-002_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/video_2_type-exp-002_type_overlay.mp4
runs/vehicle_type/TYPE-EXP-002-local-video-smoke/video_3_type-exp-002_type_overlay.mp4
```

Summary:

| Video | Sampled frames | Top-1 counts | Gate-pass frames | Gated top-1 counts | Mean confidence | Mean margin |
|---|---:|---|---:|---|---:|---:|
| `video_1` | 344 | `suv=267`, `hatchback=66`, `pickup=2`, `minibus=3`, `kamyon=1`, `sedan=3`, `panelvan=2` | 266 | `suv=215`, `hatchback=51` | 0.7358 | 0.6317 |
| `video_2` | 344 | `suv=280`, `hatchback=51`, `minibus=6`, `panelvan=1`, `kamyon=5`, `sedan=1` | 260 | `suv=244`, `hatchback=16` | 0.7240 | 0.6134 |
| `video_3` | 287 | `suv=261`, `hatchback=25`, `kamyon=1` | 203 | `suv=192`, `hatchback=11` | 0.7133 | 0.5938 |

Overall, the clip smoke test produced `suv=808/975` raw top-1 predictions. After the gate, `suv=651/729` frames remain. This is strong enough for the current three target tracks to emit a track-level `suv` result, but the output must be produced with temporal/gated majority voting, not with a single-frame top-1 decision.

## Local Tooling Status

- `scripts/benchmarks/run_type_classifier_smoke.py` now derives output filenames from the checkpoint experiment ID.
- `scripts/benchmarks/run_type_classifier_video_smoke.py` was added to generate annotated MP4 overlays from target ROI clips.
- Both scripts were validated with the `TYPE-EXP-002` checkpoint.

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

Lock `TYPE-EXP-002` as the current working baseline for the active 3-video demo target vehicle type signal, with a clear caveat:

- For the current target track, report `tip=suv` only after track-level temporal/gated majority.
- Do not describe the model as final for all FTR vehicle types.
- Keep `minibus` and `sedan/suv/hatchback` separation as the next dataset-improvement area.

Recommended next steps:

1. Add the vehicle-type adapter output to the FTR/evidence vehicle info fusion layer.
2. Use `min_confidence=0.60`, `min_margin=0.15`, and per-track majority voting as the first gate.
3. Store raw per-frame predictions in evidence/debug artifacts, but expose only the voted track-level label in final structured output.
4. Add targeted `minibus` data before the next full training run.
5. Consider splitting `minibus` vs `panelvan` review data manually, because the dataset taxonomies do not cleanly match the FTR labels.
