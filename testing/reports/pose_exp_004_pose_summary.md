# POSE-EXP-004 Driver Upper-Body / Pose Baseline

Tarih: 2026-06-13T14:52:36Z

## Zincir

`YuNet driver face -> face-anchored upper-body ROI -> pose -> torso ROI -> temporal decision`

## Konfigürasyon

* Model: `rtmw_l_cocktail14_wholebody_384x288_onnx`
* Backend: `rtmpose_onnx`
* Model path: `models/checkpoints/cabin/rtmw-l_simcc-cocktail14_384x288.onnx`
* Cabin input: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Frame stride: `1`
* Pose confidence: `0.25`
* Keypoint confidence: `1.5`

## Otomatik Sonuç

| Video | Profil | Evaluable | Pose Rate | Seatbelt Anchor | Phone Anchor | Hand | Hand Near Face | Upper Body | Longest Miss | Miss sec | P95 Jitter | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| video_1.mp4 | side_driver_window | 187 | 1.0 | 0.9679 | 0.8342 | 0.7005 | 0.5668 | True | 2 | 0.04 | 0.2101 | 160.94 | 208.088 |
| video_2.mp4 | side_driver_window | 209 | 1.0 | 0.9856 | 0.9856 | 0.9856 | 0.9856 | True | 3 | 0.06 | 0.1952 | 132.523 | 152.597 |
| video_3.mp4 | front_lhd | 134 | 1.0 | 0.9552 | 0.6343 | 0.2388 | 0.0746 | True | 3 | 0.06 | 0.3092 | 147.148 | 193.47 |

## Yorumlama

* `seatbelt_anchor_ready`, driver yüzüyle anatomik olarak uyumlu iki omuz ve torso bulunduğunda true olur.
* `phone_anchor_ready`, seatbelt anchor'a ek olarak en az bir güvenilir omuz-dirsek-bilek zinciri gerektirir.
* Kalçalar görünmüyorsa torso alt sınırı omuz genişliğinden kontrollü biçimde tahmin edilir.
* Bu deney seatbelt veya phone sınıflandırması yapmaz; yalnız specialist modüller için anchor üretir.
* Model seçimi otomatik oranlar ve tam overlay manuel review birlikte değerlendirildikten sonra yapılır.

## Manuel Review

* Şablon: `testing/templates/manual_driver_pose_review.csv`
* Büyük ROI ve overlay çıktıları `runs/cabin_pose/` altında Git dışındadır.
