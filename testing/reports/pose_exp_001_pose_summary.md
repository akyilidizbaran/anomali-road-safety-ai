# POSE-EXP-001 Driver Upper-Body / Pose Baseline

Tarih: 2026-06-12T19:40:42Z

## Zincir

`YuNet driver face -> face-anchored upper-body ROI -> pose -> torso ROI -> temporal decision`

## Konfigürasyon

* Model: `yolo11n_pose_coco17`
* Backend: `ultralytics`
* Model path: `yolo11n-pose.pt`
* Cabin input: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Frame stride: `1`
* Pose confidence: `0.25`
* Keypoint confidence: `0.35`

## Otomatik Sonuç

| Video | Profil | Evaluable | Pose Rate | Seatbelt Anchor | Phone Anchor | Upper Body | Longest Miss | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| video_1.mp4 | side_driver_window | 187 | 1.0 | 0.9733 | 0.2299 | False | 39 | 66.902 | 103.392 |
| video_2.mp4 | side_driver_window | 209 | 0.9617 | 0.9617 | 0.7273 | True | 7 | 67.388 | 108.263 |
| video_3.mp4 | front_lhd | 134 | 0.9403 | 0.8731 | 0.1716 | False | 58 | 72.939 | 109.657 |

## Yorumlama

* `seatbelt_anchor_ready`, driver yüzüyle anatomik olarak uyumlu iki omuz ve torso bulunduğunda true olur.
* `phone_anchor_ready`, seatbelt anchor'a ek olarak en az bir güvenilir omuz-dirsek-bilek zinciri gerektirir.
* Kalçalar görünmüyorsa torso alt sınırı omuz genişliğinden kontrollü biçimde tahmin edilir.
* Bu deney seatbelt veya phone sınıflandırması yapmaz; yalnız specialist modüller için anchor üretir.
* Model seçimi otomatik oranlar ve tam overlay manuel review birlikte değerlendirildikten sonra yapılır.

## Manuel Review

* Şablon: `testing/templates/manual_driver_pose_review.csv`
* Büyük ROI ve overlay çıktıları `runs/cabin_pose/` altında Git dışındadır.

## Manual Review Decision

**Rejected.** Full-video review showed anatomically unstable skeletons, especially at distance, and unreliable elbow/wrist anchors. Automatic detection rates must not be interpreted as pose correctness.
