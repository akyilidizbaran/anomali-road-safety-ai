# Vehicle Detection Experiment Template

## Experiment Metadata

* Experiment ID:
* Date:
* Owner:
* Repo commit SHA:
* Module: Vehicle Detection
* Goal:
* Condition profile: general / dark / rain / fog_low_visibility / night_low_light

## Runtime

* Training runtime: Google Colab / local / cloud
* Inference runtime: MacBook local edge / Colab / other
* GPU/CPU:
* RAM:
* Python version:
* Framework version:

## Model

* Model family:
* Variant:
* Selected detector profile:
* Fallback detector:
* Pretrained weight:
* License note:
* Source URL:
* Model input size:

## Dataset

* Dataset:
* Dataset source URL:
* License:
* Split ID:
* Class mapping version:
* Train samples:
* Val samples:
* Test samples:
* Video-level split: yes/no

## Training Config

* Epochs:
* Batch size:
* Optimizer:
* Learning rate:
* Early stopping:
* Augmentation config:

## Detection Metrics

| Metric | Value |
|---|---:|
| mAP@0.5 | TBD |
| mAP@0.5:0.95 | TBD |
| Precision | TBD |
| Recall | TBD |
| F1 | TBD |
| Car AP | TBD |
| Bus AP | TBD |
| Truck AP | TBD |
| Motorcycle AP | TBD |

## Runtime Metrics

| Metric | Value |
|---|---:|
| Mean latency ms | TBD |
| P95 latency ms | TBD |
| FPS | TBD |
| Model load time ms | TBD |
| CPU usage % | TBD |
| GPU usage % | TBD |
| RAM MB | TBD |
| Model size MB | TBD |

## Pipeline Compatibility

| Check | Result |
|---|---|
| Output contract valid | TBD |
| Empty detection handled | TBD |
| Evidence crop usable | TBD |
| Tracking can initialize | TBD |
| Target selection input usable | TBD |
| ONNX export | TBD |
| Quantization attempt | TBD |

## Manual Video Review

Kullan:

* `testing/templates/manual_video_benchmark_review.csv`

| Metric | Value |
|---|---:|
| Visible vehicle count | TBD |
| Correct detection count | TBD |
| Missed vehicle count | TBD |
| False positive count | TBD |
| Correct class count | TBD |
| Bbox usable count | TBD |
| Evidence crop usable count | TBD |
| Manual accuracy | TBD |

## Failure Cases

* Small/far vehicles:
* Night/low light:
* Rain/fog/blur:
* Occlusion:
* Motorcycle/bicycle/person confusion:
* Bus/truck confusion:

## Decision

* Keep candidate: yes/no
* Reason:
* Risks:
* Next experiment:
