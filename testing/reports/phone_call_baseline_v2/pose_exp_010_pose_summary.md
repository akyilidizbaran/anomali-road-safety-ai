# POSE-EXP-010 Driver Upper-Body / Pose Baseline

Tarih: 2026-06-18T10:28:33Z

## Zincir

`YuNet driver face -> face-anchored upper-body ROI -> pose -> torso ROI -> temporal decision`

## Konfigürasyon

* Model: `vitpose_b_arm_focus_observations_v1`
* Backend: `vitpose_hf`
* Model path: `usyd-community/vitpose-base-simple`
* Cabin input: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Frame stride: `1`
* Pose confidence: `0.25`
* Keypoint confidence: `0.22`
* Temporal stabilization: `False`

## Otomatik Sonuç

| Video | Profil | Evaluable | Pose Rate | Seatbelt Anchor | Phone Anchor | Hand | Hand Near Face | Upper Body | Longest Miss | Miss sec | P95 Jitter | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| video_1.mp4 | side_driver_window | 187 | 1.0 | 0.9733 | 0.9465 | 0.0 | 0.0 | True | 2 | 0.04 | 0.3898 | 57.688 | 57.951 |
| video_2.mp4 | side_driver_window | 209 | 1.0 | 1.0 | 0.9952 | 0.0 | 0.0 | True | 0 | 0.0 | 0.1497 | 51.037 | 54.696 |
| video_3.mp4 | front_lhd | 134 | 1.0 | 0.9925 | 0.903 | 0.0 | 0.0 | True | 1 | 0.02 | 0.2404 | 51.021 | 57.217 |

## Yorumlama

* `seatbelt_anchor_ready`, driver yüzüyle anatomik olarak uyumlu iki omuz ve torso bulunduğunda true olur.
* `phone_anchor_ready`, seatbelt anchor'a ek olarak en az bir güvenilir omuz-dirsek-bilek zinciri gerektirir.
* Arm anchors enabled: `True`. `False` ise dirsek/bilek yalnız tanısal model çıktısıdır; overlay veya risk anchor'ı değildir.
* Kalçalar görünmüyorsa torso alt sınırı omuz genişliğinden kontrollü biçimde tahmin edilir.
* Bu deney seatbelt veya phone sınıflandırması yapmaz; yalnız specialist modüller için anchor üretir.
* Model seçimi otomatik oranlar ve tam overlay manuel review birlikte değerlendirildikten sonra yapılır.

## Manuel Review

* Şablon: `testing/templates/manual_driver_pose_review.csv`
* Büyük ROI ve overlay çıktıları `runs/cabin_pose/` altında Git dışındadır.
