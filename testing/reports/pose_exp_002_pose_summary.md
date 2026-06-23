# POSE-EXP-002 Driver Upper-Body / Pose Baseline

Tarih: 2026-06-12T19:49:10Z

## Zincir

`YuNet driver face -> face-anchored upper-body ROI -> pose -> torso ROI -> temporal decision`

## Konfigürasyon

* Model: `mediapipe_pose_landmarker_full`
* Backend: `mediapipe`
* Model path: `models/checkpoints/cabin/pose_landmarker_full.task`
* Cabin input: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Frame stride: `1`
* Pose confidence: `0.25`
* Keypoint confidence: `0.35`

## Otomatik Sonuç

| Video | Profil | Evaluable | Pose Rate | Seatbelt Anchor | Phone Anchor | Upper Body | Longest Miss | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| video_3.mp4 | front_lhd | 134 | 0.7388 | 0.2687 | 0.2015 | False | 91 | 41.35 | 73.716 |

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

**Rejected at video_3 smoke stage.** Corrected IMAGE-mode inference still produced anatomically unstable landmarks, 0.2687 seatbelt-anchor coverage, 0.2015 phone-anchor coverage and a 91-frame miss run. A three-video run is not justified.
