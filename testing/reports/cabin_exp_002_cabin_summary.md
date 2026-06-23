# CABIN-EXP-002 Cabin Visibility + Driver Baseline

Tarih: 2026-06-12T18:11:43Z

## Amaç

Hedef araç ROI içinde cabin görünürlüğünü ölçmek, yalnız görünürlük yeterliyse yüz/occupant tespiti çalıştırmak ve temporal driver candidate kararı üretmek.

## Konfigürasyon

* Face model: `blazeface_short_range`
* Model path: `models/checkpoints/cabin/blaze_face_short_range.tflite`
* Input events: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json`
* Frame stride: `5`
* Face confidence: `0.5`

## Sonuç

| Video | View Profile | Kare | Visibility | Görünür Kare Oranı | Yüz Tespit Oranı | Occupant | Driver | Mean ms | P95 ms |
|---|---|---:|---|---:|---:|---:|---|---:|---:|
| video_1.mp4 | side_driver_window | 69 | limited | 0.6812 | 0.1489 | 1 | False | 1.548 | 3.935 |
| video_2.mp4 | side_driver_window | 69 | limited | 0.7246 | 0.16 | 1 | False | 1.181 | 1.365 |
| video_3.mp4 | front_lhd | 57 | limited | 0.5789 | 0.5152 | 1 | True | 0.998 | 1.156 |

## Sınırlar

* Telefon, kemer ve sigara bu deneyde çalıştırılmaz.
* Occupant varlığı risk skorunu yükseltmez.
* Driver rolü yalnız açık view-profile politikasıyla atanır.
* Ground truth olmadığı için sonuçlar manuel review ile doğrulanmalıdır.

## Manuel Review

* Şablon: `testing/templates/manual_cabin_review.csv`
* Crop ve overlay videoları `runs/cabin/` altında, Git dışındadır.
