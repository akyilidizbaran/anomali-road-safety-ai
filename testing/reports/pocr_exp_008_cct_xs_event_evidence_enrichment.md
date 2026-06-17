# POCR-EXP-008 CCT-XS Event/Evidence Enrichment Summary

Tarih: 2026-06-17T10:26:49Z

## Amaç

Doğrulanan CCT-XS OCR baseline sonucunu tracking event skeleton kayıtlarına temporal stability gate ile bağlamak.

## Kaynaklar

* Input event skeleton: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* OCR summary: `models/benchmarks/artifacts/plate_ocr/POCR-EXP-007-cct-xs-baseline-percrop/POCR-EXP-006-fast-plate-ocr-summary.json`
* OCR engine: `fastplate`
* OCR model: `fast-plate-ocr(cct-xs-v2-global-model, device=cpu)`
* Stability gate: `stable_count=3`, `window_size=7`, `min_confidence=0.75`, `format_valid=True`, `province_code_valid=True`

## Sonuç

| Video | Event ID | Final Plate | OCR Status | Format Valid | Confidence | Vote Conf |
|---|---|---|---|---:|---:|---:|
| video_1.mp4 | EVT-TRK-EXP-001-video_1-TRK-001 | 34TC8532 | stable_read | True | 0.9903 | 0.9903 |
| video_2.mp4 | EVT-TRK-EXP-001-video_2-TRK-001 | 34TC8532 | stable_read | True | 0.9733 | 0.9733 |
| video_3.mp4 | EVT-TRK-EXP-001-video_3-TRK-002 | 34TC8532 | stable_read | True | 0.9052 | 0.9052 |

## Model Çıktılarından Count Özeti

| Video | Crops | OCR Read | Format Valid | Province Valid | Stable Text | First Stable Frame | Gate | Mean OCR ms |
|---|---:|---:|---:|---:|---|---:|---|---:|
| video_1.mp4 | 206 | 205 | 203 | 203 | 34TC8532 | 3 | passed | 1.92 |
| video_2.mp4 | 201 | 197 | 193 | 193 | 34TC8532 | 4 | passed | 1.89 |
| video_3.mp4 | 206 | 202 | 195 | 194 | 34TC8532 | 25 | passed | 1.642 |

## Çıktı

* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-fastplate.json`
* Model-derived count CSV: `models/benchmarks/artifacts/plate_ocr/POCR-EXP-008-cct-xs-event-enrichment/pocr_exp_008_cct_xs_model_counts.csv`
* Model-derived count JSON: `models/benchmarks/artifacts/plate_ocr/POCR-EXP-008-cct-xs-event-enrichment/pocr_exp_008_cct_xs_model_counts.json`

## Sonraki Adım

Plate/OCR baseline artık event/evidence hattına bağlı. Sonraki mantıklı faz relative speed / motion signal contract ve ilk speed baseline üretimidir.
