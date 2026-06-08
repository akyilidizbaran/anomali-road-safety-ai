# BDD100K Vehicle Detection Dataset Card

## Dataset

* Name: BDD100K
* Source URL: https://github.com/ucbdrive/bdd100k
* Format reference: https://github.com/ucbdrive/bdd100k/blob/master/doc/format.md
* License reference: https://github.com/ucbdrive/bdd100k/blob/master/LICENSE
* Version/date accessed: 2026-06-08
* License: BSD-3-Clause in GitHub repository; project will keep code/data usage private/licensed. Download portal terms should still be archived for traceability.
* Citation: BDD100K paper / official citation to be added from dataset source.

## Intended Use

* Module: Vehicle Detection
* Task: 4-class vehicle object detection
* Training / validation / test: Training and validation for condition-aware general vehicle detector.

## Data Characteristics

* Target classes:
  * `car`
  * `bus`
  * `truck`
  * `motorcycle`
* Annotation format: BDD100K JSON with `box2d` object boxes.
* Condition metadata:
  * `attributes.weather`
  * `attributes.timeofday`
  * `attributes.scene`
* Environment: driving scenes, road scenes, varied weather/time-of-day.

## Mapping

See:

* `bdd100k_vehicle_detection_mapping.yaml`

## Privacy and Safety

* Contains plates: possible.
* Contains faces: possible.
* Contains cabin/driver/passenger: possible depending on frames.
* Redistribution allowed: must be confirmed from official terms.
* Git repo storage allowed: No raw images, labels, crops, run outputs, or model weights.

## Decision

* Status: Accepted candidate / primary first fine-tune dataset.
* Reason: BDD100K provides road scene object annotations and condition metadata suitable for condition-aware validation.
* Required preprocessing:
  * map vehicle categories to 4 MVP classes,
  * preserve condition metadata,
  * convert BDD JSON boxes to YOLO label format,
  * create condition breakdown validation lists.
* Risks:
  * download portal terms should be archived for traceability,
  * class naming must be verified on the downloaded label version,
  * image-level split must avoid leakage where applicable,
  * metadata imbalance may require controlled sampling.
