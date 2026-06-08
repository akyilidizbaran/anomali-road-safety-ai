# VD-EXP-002 - BDD100K YOLO11n Condition-Aware General Detector

## Experiment Metadata

* Experiment ID: `VD-EXP-002`
* Module: Vehicle Detection
* Goal: BDD100K üzerinden ilk condition-aware general road-domain vehicle detector fine-tune.
* Training runtime: Google Colab GPU
* Inference/runtime target: MacBook local edge/backend
* Model: YOLO11n
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

* YOLO formatted dataset under Google Drive.
* `data.yaml`
* condition metadata CSV
* train/val split lists
* overall validation metrics
* condition breakdown validation metrics
* trained `.pt` checkpoint in Drive
* optional ONNX export in Drive

## Acceptance Criteria

* Training runs without dataset conversion errors.
* Model produces 4-class vehicle detections.
* Overall validation metrics are saved.
* Condition breakdown validation is saved.
* Model can be exported or copied for MacBook runtime benchmark.
* No raw data, weights, image crops, or run artifacts are committed to Git.
