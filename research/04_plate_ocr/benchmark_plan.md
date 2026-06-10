# Plate Detection + OCR Benchmark Plan

Tarih: 2026-06-11

## Amaç

ByteTrack ile seçilmiş target track üzerinde plate detection, OCR, Türk plaka post-processing ve temporal voting hattını ölçülebilir hale getirmek.

Bu benchmark final OCR accuracy iddiası kurmaz. İlk faz `manual qualitative review`, `smoke test` ve `pipeline usability` olarak raporlanır.

## Deneyler

| Experiment ID | Kapsam | Detector | OCR | Veri | Durum |
|---|---|---|---|---|---|
| `POCR-EXP-001` | Target ROI plate detector smoke test | YOLO/ONNX plate detector | not_run | `Test/video_1-3.mp4` target tracks | planned |
| `POCR-EXP-002` | PaddleOCR OCR baseline | POCR-EXP-001 detector | PaddleOCR PP-OCRv5 Latin/mobile | selected plate crops | planned |
| `POCR-EXP-003` | EasyOCR OCR comparison | POCR-EXP-001 detector | EasyOCR | selected plate crops | planned |
| `POCR-EXP-004` | Tesseract debug fallback | POCR-EXP-001 detector | Tesseract | selected plate crops | optional |
| `POCR-EXP-005` | Temporal voting gain | best detector | best OCR | per-track candidate crops | planned |

## Input

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* Raw local videos: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
* Target fields:
  * `event_id`
  * `track_id`
  * `best_frame`
  * `bbox_history_sample`
  * `track_stability`
  * `condition_profile`

## Plate Detection Metrics

* `plate_detected_model`
* `plate_bbox_correct_manual`
* `plate_confidence`
* `plate_quality_score`
* `false_positive_plate`
* `missed_plate`
* `mean_plate_detector_latency_ms`
* `p95_plate_detector_latency_ms`

Ground truth bbox yoksa precision/recall/mAP final metrik olarak yazılmayacak; manuel değerlendirme yapılacak.

## OCR Metrics

* `ocr_text_raw`
* `ocr_text_normalized`
* `ocr_confidence`
* `format_valid`
* `province_code_valid`
* `edit_distance_manual`
* `full_plate_match_manual`
* `partial_match_manual`
* `low_confidence_rejection`

## Track-Level Metrics

* `per_track_candidate_count`
* `best_frame_ocr_status`
* `temporal_vote_text`
* `temporal_vote_confidence`
* `temporal_voting_gain_manual`
* `time_to_first_readable_plate`
* `evidence_completeness_score`

## Çıkış Artifactleri

* `models/benchmarks/artifacts/POCR-EXP-001-plate-detection-summary.json`
* `models/benchmarks/artifacts/POCR-EXP-002-paddleocr-summary.json`
* `models/benchmarks/artifacts/POCR-EXP-003-easyocr-summary.json`
* `testing/reports/pocr_exp_001_003_plate_ocr_summary.md`
* `testing/templates/manual_plate_ocr_review.csv`

## Başarı Kriteri

İlk MVP tamamlanmış sayılırsa:

* En az bir target track için plate crop üretilebilmeli.
* OCR sonucu raw ve normalized olarak event JSON'a yazılabilmeli.
* Format validation ve province code validation çalışmalı.
* Temporal voting candidate listesi üretilebilmeli.
* Failure reason alanları boş bırakılmamalı.
* Plaka okunamazsa sistem bunu açıkça `not_detected`, `not_read` veya `low_confidence` olarak işaretlemeli.
