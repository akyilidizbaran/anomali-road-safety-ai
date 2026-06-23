# CABIN-EXP-004 Cabin Visibility + Driver Baseline

Tarih: 2026-06-12T19:14:54Z

## Amaç

Hedef araç ROI içinde cabin görünürlüğünü ölçmek, yalnız görünürlük yeterliyse yüz/occupant tespiti çalıştırmak ve temporal driver candidate kararı üretmek.

## Konfigürasyon

* Face model: `opencv_yunet_2026may`
* Model path: `models/checkpoints/cabin/face_detection_yunet_2026may.onnx`
* Input events: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json`
* Frame stride: `1`
* Face confidence: `0.5`

## Sonuç

| Video | View Profile | Kare | Visibility | Görünür Kare Oranı | Yüz Tespit Oranı | Occupant | Driver | Mean ms | P95 ms |
|---|---|---:|---|---:|---:|---:|---|---:|---:|
| video_1.mp4 | side_driver_window | 342 | limited | 0.6813 | 0.9742 | 2 | True | 36.486 | 65.038 |
| video_2.mp4 | side_driver_window | 341 | limited | 0.7185 | 0.8735 | 2 | True | 39.283 | 67.49 |
| video_3.mp4 | front_lhd | 285 | limited | 0.5474 | 0.8718 | 1 | True | 10.751 | 29.855 |

## Sınırlar

* Telefon, kemer ve sigara bu deneyde çalıştırılmaz.
* Occupant varlığı risk skorunu yükseltmez.
* Driver rolü yalnız açık view-profile politikasıyla atanır.
* Ground truth olmadığı için sonuçlar manuel review ile doğrulanmalıdır.

## Manuel Review

* Şablon: `testing/templates/manual_cabin_review.csv`
* Crop ve overlay videoları `runs/cabin/` altında, Git dışındadır.
