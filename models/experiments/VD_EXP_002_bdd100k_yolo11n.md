# VD-EXP-002 - BDD100K YOLO11n Condition-Aware General Detector

## Experiment Metadata

* Experiment ID: `VD-EXP-002`
* Module: Vehicle Detection
* Goal: BDD100K üzerinden uçtan uca condition-aware general road-domain vehicle detector fine-tune ve baseline karşılaştırması.
* Training runtime: Google Colab GPU
* Inference/runtime target: MacBook local edge/backend
* Primary model: YOLO11n
* Optional challenger models: YOLO11s, YOLOv10n
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

Specialist detector bu deneyde eğitilmez. Bu deneyin amacı specialist açılmadan önce güçlü ve ölçülebilir `vehicle_detector_general` üretmektir.

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
* trained `.pt` checkpoint in Drive
* optional ONNX export in Drive

## Acceptance Criteria

* Training runs without dataset conversion errors.
* Model produces 4-class vehicle detections.
* Pretrained baseline metrics are saved.
* Overall validation metrics are saved.
* Baseline vs fine-tuned deltas are saved.
* Condition breakdown validation is saved.
* Model can be exported or copied for MacBook runtime benchmark.
* No raw data, weights, image crops, or run artifacts are committed to Git.

## Model Comparison Logic

Notebook first runs pretrained baseline validation for each enabled model, then trains the same model on the converted BDD100K split, then records:

* `overall_metrics.csv`
* `condition_breakdown_metrics.csv`
* `baseline_vs_finetuned_delta.csv`

The first required run is `VD-EXP-002 / YOLO11n`. `YOLO11s` and `YOLOv10n` are optional challenger runs controlled by the notebook `EXPERIMENTS` config.
