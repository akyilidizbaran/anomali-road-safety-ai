# Driver Upper-Body / Pose Baseline

Tarih: 2026-06-12

## Amaç

Seçilen YuNet driver yüzünü omuz, kol ve torso anchor'larına bağlamak. Bu faz
seatbelt veya phone sınıflandırması yapmaz.

Zincir:

`YuNet driver face -> driver upper-body ROI -> pose -> torso ROI -> temporal karar`

## Deneyler

* `POSE-EXP-001`: YOLO11n-pose COCO-17, ana pretrained aday.
* `POSE-EXP-002`: MediaPipe Pose Landmarker Full, 33-landmark challenger.
* `POSE-EXP-001/002`: Reddedilen generic pose adayları.
* `TORSO-EXP-001`: Tam-video manuel incelemede reddedilen deterministic fallback.
* `POSE-EXP-003`: RTMPose-L Body7 384x288 ONNX. Üç-video manuel review sonrası
  action-grade kol takibi için reddedildi.
* `POSE-EXP-004`: RTMW-L Cocktail14 384x288 ONNX, 133-keypoint whole-body/hand
  challenger.

## Dosyalar

* `deep_research_report.md`
* `sources.md`
* `decision_driver_pose_baseline_v1.md`
* `benchmark_plan.md`
* `dataset_license_checklist.md`
* `RUN_DRIVER_POSE_BASELINE.md`
* `decision_deterministic_torso_v1.md`
* `RUN_DRIVER_TORSO_BASELINE.md`
