# DRIVER-EXP-001 Driver Detection Summary

Tarih: 2026-06-23T19:17:42Z

## Amaç

Bu modül sürücü eylemi tanımaz. Yalnız hedef araç içinde sürücü adayı var mı, rol ataması güvenilir mi ve sonraki driver-action uzmanları çalıştırılabilir mi sorusuna cevap verir.

## Kaynaklar

* Input events: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json`
* Cabin summary: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-driver-detection.json`

## Aggregate

* Video count: `3`
* Status counts: `{'detected': 3}`
* Driver detected video count: `3`
* Mean driver confidence: `0.7986`

## Video Sonuçları

| Video | Event ID | Track | Status | Driver | Conf | View | Occupants | Passengers | Failure |
|---|---|---|---|---|---:|---|---:|---:|---|
| video_1.mp4 | EVT-TRK-EXP-001-video_1-TRK-001 | TRK-001 | detected | True | 0.8117 | side_driver_window | 2 | 1 | None |
| video_2.mp4 | EVT-TRK-EXP-001-video_2-TRK-001 | TRK-001 | detected | True | 0.7988 | side_driver_window | 2 | 1 | None |
| video_3.mp4 | EVT-TRK-EXP-001-video_3-TRK-002 | TRK-002 | detected | True | 0.7853 | front_lhd | 1 | 0 | None |

## Karar

`DRIVER-EXP-001`, mevcut faz için driver presence / role-assignment modülü olarak kabul edilebilir. Çıktı action, phone, smoking, seatbelt veya hukuki risk kararı değildir; yalnız sonraki uzman modellerin çalıştırılması için gate/evidence sinyalidir.
