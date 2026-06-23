# POSE-EXP-007 Driver Upper-Body / Pose Baseline

Tarih: 2026-06-14T13:55:19Z

## Zincir

`YuNet driver face -> face-anchored upper-body ROI -> pose -> torso ROI -> temporal decision`

## Konfigürasyon

* Model: `vitpose_b_temporal_hysteresis_v2`
* Backend: `vitpose_hf`
* Model path: `usyd-community/vitpose-base-simple`
* Cabin input: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Frame stride: `1`
* Pose confidence: `0.25`
* Keypoint confidence: `0.3`
* Temporal stabilization: `True`

## Otomatik Sonuç

| Video | Profil | Evaluable | Pose Rate | Seatbelt Anchor | Phone Anchor | Hand | Hand Near Face | Upper Body | Longest Miss | Miss sec | P95 Jitter | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| video_3.mp4 | front_lhd | 134 | 1.0 | 1.0 | 0.9254 | 0.0 | 0.0 | True | 0 | 0.0 | 0.095 | 55.11 | 58.362 |

## Yorumlama

* `seatbelt_anchor_ready`, driver yüzüyle anatomik olarak uyumlu iki omuz ve torso bulunduğunda true olur.
* `phone_anchor_ready`, seatbelt anchor'a ek olarak en az bir güvenilir omuz-dirsek-bilek zinciri gerektirir.
* Kalçalar görünmüyorsa torso alt sınırı omuz genişliğinden kontrollü biçimde tahmin edilir.
* Bu deney seatbelt veya phone sınıflandırması yapmaz; yalnız specialist modüller için anchor üretir.
* Model seçimi otomatik oranlar ve tam overlay manuel review birlikte değerlendirildikten sonra yapılır.

## Manuel Review

* Şablon: `testing/templates/manual_driver_pose_review.csv`
* Büyük ROI ve overlay çıktıları `runs/cabin_pose/` altında Git dışındadır.
