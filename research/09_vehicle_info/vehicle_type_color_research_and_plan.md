# Vehicle Type + Vehicle Color Strategy for FTR

Date: 2026-06-22

## 1. Objective

The FTR output contract requires a single `arac_bilgisi` block with:

```json
{
  "tip": "sedan",
  "plaka": "34ABC123",
  "renk": "beyaz",
  "confidence_score": 0.94
}
```

The two unfinished fields are:

* `tip`: one of `sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan`, `kamyon`
* `renk`: one of `beyaz`, `siyah`, `gri`, `kirmizi`, `mavi`, `sari`, `yesil`, `turuncu`, `kahverengi`

The current repo already has a vehicle detector, tracker, plate/OCR pipeline, and `VATTR-EXP-001` vehicle attribute model. However, `VATTR-EXP-001` was trained as a body/dimension-prior model for speed sanity-checking, not as the final FTR `tip` model. Its local target-crop confidence values were low enough that it should not be the sole FTR type source.

## 2. Current Repo State

### Existing vehicle type assets

* Vehicle detector: `models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt`
  * Detects broad vehicle classes such as car, bus, truck, motorcycle.
  * Useful for coarse gating: truck-like -> `kamyon`, bus/van-like -> candidate large/passenger vehicle.
* Vehicle attribute model: `models/checkpoints/vehicle_attribute/VATTR-EXP-001-efficientnet_b0-best.pth`
  * Labels: `combi`, `hatchback`, `mpv`, `sedan`, `suv`, `van`.
  * Hard-final test macro-F1: `0.8579` on BoxCars split.
  * On our local target crops, confidence was low: around `0.42-0.46`; therefore it must be gated.

### Existing color assets

There is currently no active repo model or heuristic for `arac_bilgisi.renk`.

## 3. Why The Current Type Model Is Not Enough

`VATTR-EXP-001` is valuable, but it does not close FTR type output by itself:

| Issue | Impact |
|---|---|
| Label set mismatch | It has `combi`, `mpv`, `van`; FTR requires `pickup`, `minibus`, `panelvan`, `kamyon`. |
| Low local target-crop confidence | On the three local videos, its confidence was below the gate used for speed fusion. |
| Training objective | It was designed as a dimension/body prior for speed, not a final FTR type classifier. |
| Dataset domain | BoxCars is traffic-surveillance oriented, but the FTR target labels require a specific Turkish competition mapping. |

Conclusion: keep VATTR as a secondary evidence signal, but do not let it write `arac_bilgisi.tip` alone.

## 4. External Baseline Candidates

### 4.1 OpenVINO `vehicle-attributes-recognition-barrier-0039` / `0042`

OpenVINO provides pretrained vehicle attribute classifiers for traffic-analysis scenarios. The documented outputs are:

* Color classes: `white`, `gray`, `yellow`, `red`, `green`, `blue`, `black`
* Type classes: `car`, `bus`, `truck`, `van`
* Model `0039` is very small: 0.126 GFLOPs, 0.626M parameters, minimum object width 72 px.

Strengths:

* Ready pretrained baseline.
* Very lightweight and edge-friendly.
* Provides both type and color heads.
* Good first local smoke-test candidate.

Weaknesses:

* Type output is too coarse for FTR: cannot distinguish `sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan`.
* Color output misses FTR `turuncu` and `kahverengi`.
* Designed for front-facing vehicles with occlusion below 50%; our demo has low light and variable viewpoint.

Use in this project:

* `VEHINFO-EXP-001` baseline for quick type/color evidence.
* Color head can directly support `beyaz`, `siyah`, `gri`, `kirmizi`, `mavi`, `sari`, `yesil`.
* Missing color classes require heuristic/model fallback for `turuncu` and `kahverengi`.
* Type head should only be a coarse signal in a fusion layer.

Sources:

* OpenVINO tutorial: https://docs.openvino.ai/2024/notebooks/vehicle-detection-and-recognition-with-output.html
* Open Model Zoo model card: https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/intel/vehicle-attributes-recognition-barrier-0039/README.md
* Open Model Zoo `0042`: https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/intel/vehicle-attributes-recognition-barrier-0042/README.md

### 4.2 NVIDIA TAO VehicleTypeNet

NVIDIA VehicleTypeNet is a pretrained ResNet18 classification model with six classes:

* `coupe`
* `sedan`
* `SUV`
* `van`
* `large vehicle`
* `truck`

Strengths:

* Better type granularity than OpenVINO for FTR-relevant classes: `sedan`, `SUV`, `van`, `truck`.
* Pretrained and documented for vehicle type classification.
* Potentially better direct baseline for `tip` than current VATTR.

Weaknesses:

* Still missing exact FTR labels: `hatchback`, `pickup`, `minibus`, `panelvan`.
* TAO/NGC workflow may be heavier than current PyTorch/OpenCV pipeline.
* Runtime integration into our MacBook/Colab workflow needs a separate spike.

Use in this project:

* Good candidate for `TYPE-EXP-001` pretrained baseline if setup is not too heavy.
* Can be used as another vote in type fusion.

Sources:

* NGC model card: https://catalog.ngc.nvidia.com/orgs/nvidia/teams/tao/models/vehicletypenet
* NVIDIA docs: https://docs.nvidia.com/tao/archive/5.3.0/text/model_zoo/cv_models/vehicletypenet.html

### 4.3 CompCars

CompCars contains 214,345 images, 1,687 car models, and attributes including car type. It includes web-nature and surveillance-nature scenarios.

Strengths:

* Strong candidate for fine-tuning FTR vehicle type.
* Contains type-level metadata and surveillance-like samples.
* More semantically aligned with `sedan`, `suv`, `hatchback` style labels than broad detector classes.

Weaknesses:

* Label cleanup/mapping required.
* Some analyses note that not all models have type labels.
* Dataset access/licensing and exact split conversion must be controlled.

Use in this project:

* Best medium-term dataset for a custom FTR type classifier.
* Should be merged carefully with BoxCars/Stanford Cars rather than replacing all existing work.

Sources:

* CompCars paper/PDF: https://mmlab.ie.cuhk.edu.hk/datasets/comp_cars/CompCars.pdf
* Dataset summary/reference: https://hyper.ai/en/datasets/17931
* Hierarchical classification discussion: https://www.mdpi.com/1424-8220/21/2/596

### 4.4 Stanford Cars

Stanford Cars has 16,185 images over 196 make/model/year classes. Type can be derived from class strings for many labels.

Strengths:

* Easy Kaggle access.
* Useful for `sedan`, `suv`, `hatchback`, `pickup`, `van` semantic pretraining.
* Many existing EfficientNet/ResNet recipes.

Weaknesses:

* Web/curated images, not traffic surveillance.
* No native FTR type labels; type mapping must be parsed from class names.
* Weak for `minibus`, `panelvan`, `kamyon`.

Use in this project:

* Supplemental type fine-tune data, not the only source.

Sources:

* Kaggle mirror: https://www.kaggle.com/datasets/eduardo4jesus/stanford-cars-dataset
* Stanford Cars overview example: https://debuggercafe.com/stanford-cars-classification-using-efficientnet-pytorch/

### 4.5 BoxCars116k

BoxCars116k is surveillance-oriented and already used in `VATTR-EXP-001`.

Strengths:

* Surveillance domain and multiple viewpoints are useful.
* Existing repo pipeline already knows how to train on it.
* Good for body/dimension prior and some type signals.

Weaknesses:

* Current local confidence was low.
* FTR exact labels are still not fully covered.
* Training objective should be redesigned if used for final FTR type.

Use in this project:

* Keep as one source for `TYPE-EXP-002` custom type classifier.
* Do not use current VATTR output alone as final FTR type.

Sources:

* GitHub: https://github.com/JakubSochor/BoxCars
* Paper: https://arxiv.org/abs/1703.00686

## 5. Vehicle Color Dataset Candidates

### 5.1 UFPR-VCR

UFPR-VCR contains 10,039 vehicle images from real-world conditions including frontal/rear views, partial occlusions, lighting variation, and nighttime scenes.

Strengths:

* Very relevant to our low-light/dark demo issue.
* Vehicle-color specific.
* Includes multiple vehicle categories and real-world conditions.

Weaknesses:

* Access may require request/registration.
* Need exact color-to-FTR mapping.

Use in this project:

* Best quality candidate for `COLOR-EXP-001` if accessible.

Sources:

* GitHub: https://github.com/lima001/ufpr-vcr-dataset
* Paper PDF: https://raysonlaroca.github.io/papers/lima2024toward.pdf

### 5.2 VCoR

VCoR has 10k+ samples and 15 vehicle color classes.

Strengths:

* Close to FTR color label needs.
* Existing public Kaggle mirror exists.
* Prior work reports strong performance using modern vision models.

Weaknesses:

* Need verify dataset license and class folder structure before final use.
* Some colors beyond FTR must be merged.

Use in this project:

* Practical first fine-tune dataset for a 9-class FTR color classifier.

Sources:

* Kaggle: https://www.kaggle.com/datasets/landrykezebou/vcor-vehicle-color-recognition-dataset
* Refined Stanford Cars + VCoR training repo: https://github.com/morrisfl/stanford_cars_refined

### 5.3 Vehicle Color Recognition Dataset, 15,601 images

This dataset is commonly referenced as an 8-color frontal-view vehicle color dataset: black, blue, cyan, gray, green, red, white, yellow.

Strengths:

* Good simple color classifier training source.
* Includes illumination/haze/overexposure challenge according to project descriptions.

Weaknesses:

* Original download host may be fragile.
* Missing `turuncu`, `kahverengi`; `cyan` must be mapped or dropped.

Use in this project:

* Secondary/fallback color training source if VCoR/UFPR-VCR access is difficult.

Sources:

* GitHub wrapper: https://github.com/jwhabi/Vehicle-Color-Identification

## 6. Recommended Architecture

Use a hierarchical, track-level fusion layer instead of a single classifier.

```text
vehicle detection + ByteTrack target
        -> target vehicle crop sequence
        -> type/color specialists per crop
        -> per-frame predictions
        -> track-level temporal voting
        -> FTR mapper
        -> arac_bilgisi.tip / arac_bilgisi.renk / confidence_score
```

### 6.1 Type fusion

Inputs:

* `detector_class`: car/bus/truck/motorcycle from YOLO detector.
* `openvino_type`: car/bus/truck/van from OpenVINO attributes model.
* `vattr_body`: combi/hatchback/mpv/sedan/suv/van from current VATTR model.
* Optional `vehicletypenet_type`: coupe/sedan/SUV/van/large vehicle/truck.
* Track stability, bbox quality, viewpoint/condition profile.

FTR mapping proposal:

| Evidence | FTR candidate | Confidence policy |
|---|---|---|
| Detector truck OR OpenVINO truck OR VehicleTypeNet truck | `kamyon` | high if detector and attribute agree |
| Detector bus OR OpenVINO bus OR VehicleTypeNet large vehicle | `minibus` | medium/low; FTR has no bus label, so mark fallback reason |
| OpenVINO van OR VehicleTypeNet van OR VATTR van | `panelvan` | medium; use `minibus` only with extra passenger-window evidence |
| VATTR sedan OR VehicleTypeNet sedan | `sedan` | high only if temporal vote stable |
| VATTR suv OR VehicleTypeNet SUV | `suv` | high only if temporal vote stable |
| VATTR hatchback | `hatchback` | high only if temporal vote stable |
| pickup evidence absent | `pickup` | do not emit by default without custom model/fine-tune |
| Low confidence/disagreement | best fallback from detector/VATTR with low confidence | keep warning in internal evidence |

Important: because FTR has exact labels, the adapter must not emit `car`, `bus`, `truck`, `van`, `combi`, or `mpv` directly.

### 6.2 Color fusion

Inputs:

* OpenVINO color head: white/gray/yellow/red/green/blue/black.
* HSV/Lab heuristic on vehicle body pixels.
* Optional fine-tuned FTR color classifier.
* Temporal voting over target track.

FTR mapping proposal:

| Source color | FTR color |
|---|---|
| white | `beyaz` |
| black | `siyah` |
| gray/silver | `gri` |
| red | `kirmizi` |
| blue/cyan | `mavi` |
| yellow/gold | `sari` |
| green | `yesil` |
| orange | `turuncu` |
| brown/beige/tan | `kahverengi` |

OpenVINO cannot directly output `turuncu` or `kahverengi`; those require heuristic or fine-tuned classifier.

## 7. Implementation Plan

### VEHINFO-EXP-001 — Ready pretrained attribute baseline

Goal: run a quick no-training baseline on the three local videos.

Use:

* Existing YOLO + ByteTrack target crops.
* OpenVINO `vehicle-attributes-recognition-barrier-0039` or `0042`.
* Existing VATTR as secondary type evidence.
* HSV/Lab color heuristic as backup.

Outputs:

* Per-frame type/color CSV.
* Track-level temporal vote summary.
* Overlay video with `tip`, `renk`, confidence, warnings.
* FTR mapping preview JSON.

Decision rule:

* If OpenVINO+heuristic color is stable and visually correct on our videos, use as baseline for `renk`.
* If type remains coarse/unstable, use it only as fallback and move to TYPE fine-tune.

### COLOR-EXP-001 — FTR 9-color classifier

Goal: train a dedicated vehicle color classifier.

Recommended dataset order:

1. VCoR Kaggle mirror for practical access.
2. UFPR-VCR if access is granted, especially for night/real-world robustness.
3. 15,601-image 8-color dataset as secondary/fallback.

Model:

* MobileNetV3-Large or EfficientNet-B0 first.
* Optional stronger backbone: ConvNeXt-Tiny or SigLIP/CLIP linear probe if time allows.

Output labels:

`beyaz`, `siyah`, `gri`, `kirmizi`, `mavi`, `sari`, `yesil`, `turuncu`, `kahverengi`

### TYPE-EXP-001 — FTR vehicle type classifier

Goal: train a dedicated FTR label classifier.

Recommended data:

1. CompCars type metadata.
2. Stanford Cars type parsed from model labels.
3. Existing BoxCars body split as surveillance-domain supplement.
4. Optional NVIDIA VehicleTypeNet as pretrained comparison baseline.

Output labels:

`sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan`, `kamyon`

Hardest labels:

* `pickup`: likely underrepresented; requires targeted data.
* `minibus` vs `panelvan`: may need custom mapping or additional data.
* `kamyon`: can be bootstrapped from broad detector/truck labels.

### VEHINFO-EXP-002 — Fusion + FTR adapter

Goal: write final `arac_bilgisi` using temporal voting.

Rules:

* Use track-level voting, not a single frame.
* Keep `unknown/low_confidence` internally, but FTR adapter must emit one allowed label.
* Aggregate `confidence_score` from type, plate, and color confidence:

```text
confidence_score = weighted_mean(type_conf, plate_conf, color_conf)
```

with conservative clipping if any major field is low confidence.

## 8. Recommendation

### Immediate next step

Implement `VEHINFO-EXP-001` locally:

* OpenVINO vehicle attributes model for type/color baseline.
* Current VATTR as secondary type signal.
* HSV/Lab heuristic for missing color classes and sanity-check.
* Track-level temporal voting.
* Overlay videos for manual review.

This gives the fastest answer to whether a no-training baseline can close `tip` and `renk` for the current videos.

### Medium-term step

Train two separate classifiers:

* `COLOR-EXP-001`: VCoR/UFPR-VCR -> 9 FTR color labels.
* `TYPE-EXP-001`: CompCars + Stanford Cars + BoxCars -> 7 FTR type labels.

Do not merge type and color into one model yet. They fail for different reasons: type is shape/viewpoint/semantic, color is illumination/white-balance/body-pixel segmentation.

## 9. Acceptance Criteria

A model/strategy can be promoted to FTR adapter only if:

* It outputs only FTR-valid labels.
* It has per-track temporal voting.
* It produces confidence and fallback reason.
* It is manually reviewed on `Test/video_1-3.mp4`.
* It has a small report under `testing/reports/`.
* It can run without internet at final runtime.

## 10. Final Position

* Current VATTR is not enough for FTR `tip`, but should be reused as one evidence source.
* OpenVINO vehicle attributes model is the best immediate no-training baseline for both type and color, but its type labels are too coarse and its color labels miss `turuncu/kahverengi`.
* Dedicated fine-tunes are still needed for a strong final result:
  * color: VCoR/UFPR-VCR
  * type: CompCars/Stanford/BoxCars plus FTR-specific mapping
