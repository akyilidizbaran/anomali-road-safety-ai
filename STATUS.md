# Project Status

## Current Phase

FTR delivery contract alignment, model integration and Docker submission preparation.

## Done

* Project scope and constraints.
* Official PDR/OTR and PCR/FTR report structure mapping.
* Architecture documentation.
* AI module roadmap.
* Number Verification, normal mode, QoD and evidence flow documentation.
* Research topic map.
* Data, model and test strategy drafts.
* Vehicle detection deep research package and YOLO11n initial baseline decision.
* Local dark manual test videos placed under ignored `Test/` folder.
* Condition-specific vehicle detector routing plan.
* FTR delivery PDF reviewed and mapped to repo requirements.
* FTR `results.json` output contract added.
* FTR compliance matrix added.

## In Progress

* FTR output adapter/validator planning.
* Docker submission skeleton planning.
* Vehicle info pipeline consolidation: type, plate, color.
* Cabin/action/object/passenger model planning.

## Not Implemented Yet

* Root Dockerfile and FTR `main.py` entrypoint.
* `/app/data/input/video.mp4` -> `/app/data/output/results.json` runnable package.
* Vehicle color model.
* FTR exact vehicle type mapping.
* Driver action, object and passenger detection models.
* Tesla T4 runtime validation.
* Real 5G/QoD and Number Verification API integration.

## Reliability Note

This repository must not be presented as a finished field-performance system. It is the technical planning and development repository for a staged implementation.

## FTR Priority Note

The official FTR scoring output is not the internal rich event/evidence JSON. It is the
competition `results.json` containing `arac_bilgisi` and `tespitler`. Internal evidence,
QoD, speed and dashboard work must feed or support that output, not replace it.
