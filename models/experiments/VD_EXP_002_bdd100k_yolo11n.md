# VD-EXP-002 - BDD100K YOLO11n Condition-Aware General Detector

## Experiment Metadata

* Experiment ID: `VD-EXP-002`
* Module: Vehicle Detection
* Goal: BDD100K üzerinden uçtan uca condition-aware general road-domain vehicle detector fine-tune, condition breakdown ve gerekiyorsa specialist detector karşılaştırması.
* Training runtime: Google Colab GPU
* Inference/runtime target: MacBook local edge/backend
* Primary model: YOLO11n
* Optional challenger models: YOLO11s, YOLOv10n
* Optional specialist profiles: `night_low_light`, `rain`, `fog_low_visibility`
* Starting weights: `yolo11n.pt`
* Dataset: BDD100K 4-class vehicle subset
* Notebook: `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`

## Target Classes

| ID | Class |
|---:|---|
| 0 | `car` |
| 1 | `bus` |
| 2 | `truck` |
| 3 | `motorcycle` |

## Condition-Aware Scope

Bu deneyde `general` detector yalnız gündüz/normal model değildir. BDD100K metadata korunarak validation şu kırılımlarda izlenir:

* `day_clear`
* `night_low_light`
* `rain`
* `fog_low_visibility`
* `low_light_transition`
* `adverse_other`
* `unknown`

Varsayılan ilk koşuda specialist detector eğitilmez. Bu deneyin ilk amacı specialist açılmadan önce güçlü ve ölçülebilir `vehicle_detector_general` üretmektir.

Notebook aynı protokol içinde specialist deneylerini de destekler. Specialist deneyleri yalnız general modelin ilgili condition kırılımında zayıf kaldığı kanıtlanırsa açılır:

* `VD-EXP-003-NIGHT` - BDD100K `night_low_light` subset
* `VD-EXP-004-RAIN` - BDD100K `rain` subset
* `VD-EXP-005-FOG` - BDD100K `fog_low_visibility` subset

## Expected Colab Outputs

* Optional BDD100K download into Google Drive.
* YOLO formatted dataset under Google Drive.
* `data.yaml`
* condition metadata CSV
* train/val split lists
* pretrained baseline metrics
* overall validation metrics
* condition breakdown validation metrics
* baseline vs fine-tuned delta metrics
* specialist vs general comparison metrics, specialist deneyleri açılırsa
* trained `.pt` checkpoint in Drive
* optional ONNX export in Drive

## Completed Run Summary - 2026-06-15

`VD_EXP_002_BDD100K_YOLO11n_Colab_outputsaved.ipynb` çıktısına göre koşu tamamlandı.

Dataset dağılımı:

| Split | Image | Vehicle BBox |
|---|---:|---:|
| train | 23055 | 251753 |
| val | 4918 | 54124 |
| test | 4931 | 54026 |

Condition profile dağılımı:

| Profile | Train | Val | Test |
|---|---:|---:|---:|
| `general` | 23055 | 4918 | 4931 |
| `night_low_light` | 10116 | 2220 | 2103 |
| `rain` | 1625 | 335 | 360 |
| `fog_low_visibility` | 28 | 3 | 11 |

General fine-tuned YOLO11n metriği:

| Split | mAP50 | mAP50-95 | Precision | Recall |
|---|---:|---:|---:|---:|
| validation | 0.488905 | 0.322091 | 0.647045 | 0.425098 |
| test | 0.506167 | 0.332283 | 0.632970 | 0.455739 |

Specialist kararı:

| Specialist | Sonuç | Karar |
|---|---|---|
| `night_low_light` | Recall küçük arttı, mAP50-95 general modelden düşük kaldı. | Candidate; active değil |
| `rain` | Recall küçük arttı, mAP50-95 general modelden düşük kaldı. | Candidate; active değil |
| `fog_low_visibility` | Train/val/test sayısı çok düşük. | Skipped |

Aktif detector baseline:

```text
vehicle_detector_general_yolo11n_bdd100k_v1
```

Checkpoint Drive path:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/VD-EXP-002/train/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt
```

Local smoke test için beklenen path:

```text
models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

Detay rapor:

* `testing/reports/vd_exp_002_finetuned_general_detector_summary.md`
* `testing/reports/vd_exp_002_dark_video_smoke_test_runbook.md`

## Acceptance Criteria

* Training runs without dataset conversion errors.
* Model produces 4-class vehicle detections.
* Pretrained baseline metrics are saved.
* Overall validation metrics are saved.
* Baseline vs fine-tuned deltas are saved.
* Condition breakdown validation is saved.
* Specialist experiments are skipped cleanly if disabled or if the selected subset is too small.
* Specialist comparison tables are saved when any specialist run is enabled.
* Model can be exported or copied for MacBook runtime benchmark.
* No raw data, weights, image crops, or run artifacts are committed to Git.

## Model Comparison Logic

Notebook first runs pretrained baseline validation for each enabled model, then trains the same model on the converted BDD100K split, then records:

* `overall_metrics.csv`
* `condition_breakdown_metrics.csv`
* `baseline_vs_finetuned_delta.csv`

The first required run is `VD-EXP-002 / YOLO11n`. `YOLO11s` and `YOLOv10n` are optional challenger runs controlled by the notebook `EXPERIMENTS` config.
