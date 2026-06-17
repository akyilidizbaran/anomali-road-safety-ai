# Track Event + Plate OCR Enrichment Summary

Tarih: 2026-06-12T15:31:31Z

## Amaç

Seçilen PaddleOCR baseline sonucunu tracking event skeleton kayıtlarına bağlamak.

## Kaynaklar

* Input event skeleton: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* OCR summary: `models/benchmarks/artifacts/POCR-EXP-002-paddleocr-summary.json`
* OCR engine: `paddle`

## Sonuç

| Video | Event ID | Final Plate | OCR Status | Format Valid | Confidence | Vote Conf |
|---|---|---|---|---:|---:|---:|
| video_1.mp4 | EVT-TRK-EXP-001-video_1-TRK-001 | 34TC8532 | read | True | 0.5349 | 0.5349 |
| video_2.mp4 | EVT-TRK-EXP-001-video_2-TRK-001 | 34TC8532 | read | True | 0.4419 | 0.4419 |
| video_3.mp4 | EVT-TRK-EXP-001-video_3-TRK-002 | 34TC8532 | read | True | 0.8336 | 0.8336 |

## Çıktı

* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json`

## Sonraki Adım

Plate/OCR baseline artık event/evidence hattına bağlı. Sonraki mantıklı faz speed estimation veya evidence package enrichment detaylandırmasıdır.
