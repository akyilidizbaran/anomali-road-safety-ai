# POSE-EXP-010 Driver Upper-Body / Pose Baseline

Tarih: 2026-06-17T18:43:43Z

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
| video_2.mp4 | side_driver_window | 209 | 1.0 | 1.0 | 0.9952 | 0.0 | 0.0 | True | 0 | 0.0 | 0.1497 | 55.505 | 54.145 |

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
