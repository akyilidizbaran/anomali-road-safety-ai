# Decision: Vehicle Type and Color Completion Strategy

Date: 2026-06-22

## Decision

FTR `arac_bilgisi.tip` and `arac_bilgisi.renk` will be completed through a staged vehicle-info pipeline, not through the current VATTR model alone.

1. `VEHINFO-EXP-001`: no-training baseline using OpenVINO vehicle attributes model + HSV/Lab color heuristic + current VATTR as secondary type evidence.
2. `COLOR-EXP-001`: dedicated FTR 9-color classifier fine-tuned on VCoR and/or UFPR-VCR.
3. `TYPE-EXP-001`: dedicated FTR 7-type classifier fine-tuned from CompCars, Stanford Cars, and BoxCars-derived mappings.
4. `VEHINFO-EXP-002`: track-level temporal voting and FTR adapter mapping into `arac_bilgisi`.

## Rationale

* Current `VATTR-EXP-001` was designed for speed dimension prior, not FTR final type. It has useful labels (`hatchback`, `sedan`, `suv`, `van`) but misses FTR labels (`pickup`, `minibus`, `panelvan`, `kamyon`) and gave low local confidence.
* OpenVINO vehicle attributes recognition is a very light ready baseline and gives both type/color, but its labels are too coarse for final FTR type and miss two FTR colors.
* Color and type should remain separate specialist problems because color is dominated by illumination/body-pixel extraction, while type is dominated by shape/viewpoint/semantic labels.

## Impact

* FTR `renk` moves from missing to an explicit implementation path.
* FTR `tip` becomes a fusion problem with clear fallback and confidence rules.
* `VATTR-EXP-001` remains useful but is downgraded from final type source to evidence signal.

## Sources

* OpenVINO vehicle attributes tutorial: https://docs.openvino.ai/2024/notebooks/vehicle-detection-and-recognition-with-output.html
* Open Model Zoo vehicle-attributes-recognition-barrier-0039: https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/intel/vehicle-attributes-recognition-barrier-0039/README.md
* NVIDIA VehicleTypeNet: https://docs.nvidia.com/tao/archive/5.3.0/text/model_zoo/cv_models/vehicletypenet.html
* CompCars: https://mmlab.ie.cuhk.edu.hk/datasets/comp_cars/CompCars.pdf
* BoxCars116k: https://arxiv.org/abs/1703.00686
* UFPR-VCR: https://github.com/lima001/ufpr-vcr-dataset
* VCoR Kaggle: https://www.kaggle.com/datasets/landrykezebou/vcor-vehicle-color-recognition-dataset
