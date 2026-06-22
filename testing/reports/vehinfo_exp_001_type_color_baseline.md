# VEHINFO-EXP-001 Type/Color Baseline

- Generated: `2026-06-22T16:51:57Z`
- Scope: target vehicle ROI crop'lari uzerinde arac tipi ve renk icin ilk baseline.
- This is not final FTR accuracy; it is a smoke/diagnostic run before dedicated `COLOR-EXP-001` and `TYPE-EXP-001` fine-tune.

## Inputs

- Event skeleton: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
- Crop directory: `runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames`
- OpenVINO model: `vehicle-attributes-recognition-barrier-0039`
- VATTR checkpoint: `models/checkpoints/vehicle_attribute/VATTR-EXP-001-efficientnet_b0-best.pth`

## Event-Level Results

| Video | Event | Track | Type Candidate | Type Conf. | Color Candidate | Color Conf. | Warnings |
|---|---|---:|---|---:|---|---:|---|
| video_1.mp4 | `EVT-TRK-EXP-001-video_1-TRK-001` | `TRK-001` | suv | 0.575722 | siyah | 0.781397 | openvino_hsv_color_disagreement |
| video_2.mp4 | `EVT-TRK-EXP-001-video_2-TRK-001` | `TRK-001` | suv | 0.519102 | siyah | 0.767283 | openvino_hsv_color_disagreement, track_type_temporal_vote_low_confidence, vattr_combi_mapping_ambiguous, vehicle_type_low_confidence |
| video_3.mp4 | `EVT-TRK-EXP-001-video_3-TRK-002` | `TRK-002` | panelvan | 0.365252 | siyah | 0.661287 | openvino_hsv_color_disagreement, track_type_temporal_vote_low_confidence, vehicle_type_coarse_fallback, vehicle_type_low_confidence |

## Interpretation

- `tip` sonucu OpenVINO coarse type ile VATTR body-style kanitinin temporal oyundan gecirilmis adayidir.
- `renk` sonucu OpenVINO renk sinifi ile HSV/Lab heuristic kontrolunun temporal oyundan gecirilmis adayidir.
- Dusuk guven veya uyusmazlik uyarilari, sonraki dedicated fine-tune kapsaminda iyilestirilecek hata kaynaklarini isaret eder.
- Bu deney, resmi `results.json` icin nihai `arac_bilgisi` karari degil; FTR adapter'a baglanmadan once review edilecek ara contract'tir.

## Artifacts

- Per-crop CSV: `models/benchmarks/artifacts/vehicle_info/VEHINFO-EXP-001-type-color-baseline/vehinfo_exp_001_type_color_per_crop.csv`
- Summary JSON: `models/benchmarks/artifacts/vehicle_info/VEHINFO-EXP-001-type-color-baseline/vehinfo_exp_001_type_color_summary.json`
- Enriched events JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-vehinfo001.json`
- Review videos:
  - `runs/vehicle_info/VEHINFO-EXP-001-type-color-baseline/video_1_vehinfo001_overlay.mp4`
  - `runs/vehicle_info/VEHINFO-EXP-001-type-color-baseline/video_2_vehinfo001_overlay.mp4`
  - `runs/vehicle_info/VEHINFO-EXP-001-type-color-baseline/video_3_vehinfo001_overlay.mp4`
