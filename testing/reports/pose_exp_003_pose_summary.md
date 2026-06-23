# POSE-EXP-003 Driver Upper-Body / Pose Baseline

Tarih: 2026-06-13T12:28:53Z

## Nihai Karar

**Action-grade cabin pose için reddedildi.** Yüz/omuz/torso devamlılığı önceki
modellerden daha iyi olsa da telefonla konuşma pozundaki bükülmüş kol üç videoda
tutarlı izlenmedi. Phone arm-chain oranları `0.1070 / 0.8134 / 0.2015` oldu.
Eksik dirsek ve bilek tahminleri temporal smoothing ile doldurulmayacaktır.

## Zincir

`YuNet driver face -> face-anchored upper-body ROI -> pose -> torso ROI -> temporal decision`

## Konfigürasyon

* Model: `rtmpose_l_body7_384x288_onnx`
* Backend: `rtmpose_onnx`
* Model path: `models/checkpoints/cabin/rtmpose-l_simcc-body7_384x288.onnx`
* Cabin input: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Frame stride: `1`
* Pose confidence: `0.25`
* Keypoint confidence: `0.35`

## Otomatik Sonuç

| Video | Profil | Evaluable | Pose Rate | Seatbelt Anchor | Phone Anchor | Upper Body | Longest Miss | Miss sec | P95 Jitter | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| video_1.mp4 | side_driver_window | 187 | 1.0 | 0.6684 | 0.107 | True | 13 | 0.26 | 0.1712 | 36.087 | 39.751 |
| video_2.mp4 | side_driver_window | 209 | 1.0 | 0.9617 | 0.8134 | True | 6 | 0.12 | 0.1377 | 39.864 | 50.504 |
| video_3.mp4 | front_lhd | 134 | 0.9925 | 0.9179 | 0.2015 | True | 2 | 0.04 | 0.2731 | 39.241 | 48.336 |

## Yorumlama

* `seatbelt_anchor_ready`, driver yüzüyle anatomik olarak uyumlu iki omuz ve torso bulunduğunda true olur.
* `phone_anchor_ready`, seatbelt anchor'a ek olarak en az bir güvenilir omuz-dirsek-bilek zinciri gerektirir.
* Kalçalar görünmüyorsa torso alt sınırı omuz genişliğinden kontrollü biçimde tahmin edilir.
* Bu deney seatbelt veya phone sınıflandırması yapmaz; yalnız specialist modüller için anchor üretir.
* Model seçimi otomatik oranlar ve tam overlay manuel review birlikte değerlendirildikten sonra yapılır.

## Manuel Review

* Şablon: `testing/templates/manual_driver_pose_review.csv`
* Büyük ROI ve overlay çıktıları `runs/cabin_pose/` altında Git dışındadır.
