# CABIN-EXP-003 Event Enrichment Summary

Tarih: 2026-06-12T19:16:41Z

## Kaynaklar

* Input events: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json`
* Cabin summary: `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`

## Sonuç

| Video | Event ID | Visibility | Occupant | Driver | Face Rate |
|---|---|---|---:|---|---:|
| video_1.mp4 | EVT-TRK-EXP-001-video_1-TRK-001 | limited | 2 | True | 0.9742 |
| video_2.mp4 | EVT-TRK-EXP-001-video_2-TRK-001 | limited | 2 | True | 0.8735 |
| video_3.mp4 | EVT-TRK-EXP-001-video_3-TRK-002 | limited | 1 | True | 0.8718 |

## Çıktı

* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin.json`

Cabin occupant sinyali evidence metadata olarak eklenmiştir; risk skoru değiştirilmemiştir. Telefon ve kemer analizi çalıştırılmamıştır.
