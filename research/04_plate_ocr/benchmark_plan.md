# Plate Detection + OCR Benchmark Plan

Tarih: 2026-06-11

## Amaç

ByteTrack ile seçilmiş target track üzerinde plate detection, OCR, Türk plaka post-processing ve temporal voting hattını ölçülebilir hale getirmek.

Bu benchmark final OCR accuracy iddiası kurmaz. İlk faz `manual qualitative review`, `smoke test` ve `pipeline usability` olarak raporlanır.

## Deneyler

| Experiment ID | Kapsam | Detector | OCR | Veri | Durum |
|---|---|---|---|---|---|
| `POCR-EXP-001` | Target ROI plate detector smoke test (2 model karşılaştırma, OCR yok) | Ultralytics YOLO plate + HF YOLOS | not_run | `Test/video_1-3.mp4` hedef track'in detected kareleri | script_ready: `scripts/benchmarks/run_plate_detection_smoke.py` |
| `POCR-EXP-002` | PaddleOCR OCR baseline | POCR-EXP-001 detector | PaddleOCR PP-OCRv5 Latin/mobile | selected plate crops | script_ready: `scripts/benchmarks/run_plate_ocr_baseline.py --engines paddle` |
| `POCR-EXP-003` | EasyOCR OCR comparison | POCR-EXP-001 detector | EasyOCR | selected plate crops | script_ready: `scripts/benchmarks/run_plate_ocr_baseline.py --engines easyocr` |
| `POCR-EXP-004` | Tesseract debug fallback | POCR-EXP-001 detector | Tesseract | selected plate crops | optional_script_ready: `scripts/benchmarks/run_plate_ocr_baseline.py --engines tesseract` |
| `POCR-EXP-005` | YOLO11n plate detector fine-tune + baseline comparison | YOLO11n single-class plate detector | not_run | Turkish Number Plates + Roboflow LPR, optional UFPR external benchmark | completed_colab: `notebooks/POCR_EXP_005_YOLO11N_Plate_Detector_Colab_outsaved.ipynb`; local target-video smoke pending |
| `POCR-EXP-006` | Local OCR baseline comparison | POCR-EXP-005 YOLO11n plate detector | CCT-S, CCT-XS, PaddleOCR, EasyOCR | 613 local plate crops | completed: CCT-XS selected |
| `POCR-EXP-007` | CCT-XS early-read/stability analysis | POCR-EXP-005 YOLO11n plate detector | CCT-XS original vs 2x/3x preprocessing | `video_3` per-crop timeline | completed: original + stability gate selected |

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
* `models/benchmarks/artifacts/POCR-EXP-004-tesseract-summary.json`
* `models/benchmarks/artifacts/plate_detection/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-summary.json`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-007-cct-xs-stability/pocr_exp_007_cct_xs_stability_summary.json`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-007-cct-xs-stability/pocr_exp_007_cct_xs_stability_summary.csv`
* `testing/reports/pocr_exp_002_004_plate_ocr_summary_<engine>.md`
* `testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `testing/reports/pocr_exp_007_cct_xs_stability.md`
* `testing/templates/manual_plate_ocr_review.csv`

## Başarı Kriteri

İlk MVP tamamlanmış sayılırsa:

* En az bir target track için plate crop üretilebilmeli.
* OCR sonucu raw ve normalized olarak event JSON'a yazılabilmeli.
* Format validation ve province code validation çalışmalı.
* Temporal voting candidate listesi üretilebilmeli.
* Final OCR değeri stability gate geçmeden evidence alanına kesin değer olarak yazılmamalı.
* Failure reason alanları boş bırakılmamalı.
* Plaka okunamazsa sistem bunu açıkça `not_detected`, `not_read` veya `low_confidence` olarak işaretlemeli.

## 2026-06-17 POCR-EXP-005 Sonucu

Colab fine-tune tamamlandı:

* Eğitim: YOLO11n, single-class `license_plate`, 80 epoch, `imgsz=640`, batch 48.
* Donanım: NVIDIA L4.
* Veri: Turkish Number Plates v2 + Roboflow LPR v13.
* Final YOLO split: train `85,039`, val `10,636`, test `10,757` image.
* Yeni model test metrikleri: precision `0.9951`, recall `0.9907`, mAP@0.5 `0.9948`, mAP@0.5:0.95 `0.8543`.
* Mevcut baseline test metrikleri: precision `0.9726`, recall `0.9586`, mAP@0.5 `0.9754`, mAP@0.5:0.95 `0.6089`.
* UFPR external benchmark eksik olduğu için genelleme iddiası sınırlıdır.

Kaynak dosyalar:

* `models/experiments/POCR_EXP_005_plate_detector_report.md`
* `testing/reports/pocr_exp_005_plate_detector_ftr_summary.md`
* `models/benchmarks/artifacts/plate_detection/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-summary.md`

Sonraki adım: `POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt` yerel `models/checkpoints/plate/` altına alınacak ve `Test/video_1-3.mp4` target ROI akışında detector-only smoke/manual review çalıştırılacak.

## 2026-06-17 POCR-EXP-006/007 Sonucu

`POCR-EXP-005` plate detector ile üretilen 613 local plate crop üzerinde OCR karşılaştırması tamamlandı.

| OCR | Crop | OCR read | Format valid | Province valid | Track vote | Mean latency | p95 latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| CCT-S | 613 | 606 | 591 | 591 | 3/3 | 9.258 ms | 10.378 ms |
| CCT-XS | 613 | 604 | 591 | 590 | 3/3 | 1.672 ms | 2.145 ms |
| PaddleOCR | 613 | 538 | 507 | 507 | 3/3 | 54.453 ms | 104.749 ms |
| EasyOCR | 613 | 604 | 413 | 407 | 3/3 | 7.475 ms | 12.223 ms |

Karar:

* Aktif OCR baseline: `fast-plate-ocr cct-xs-v2-global-model`.
* İkinci kontrol: `PaddleOCR 2.10 PP-OCRv4 en`.
* CCT-XS fine-tune bu aşamada açılmayacak.
* Final event/evidence OCR metni temporal stability gate sonrası yazılacak.

Kaynak dosyalar:

* `research/04_plate_ocr/decision_ocr_cct_xs_baseline_2026_06_17.md`
* `models/experiments/POCR_EXP_006_007_cct_xs_ocr_baseline.md`
* `testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `testing/reports/pocr_exp_007_cct_xs_stability.md`
