# Araştırma 4 - Plaka Tespiti ve Türk Plaka OCR Sistemi

## Amaç

Araç ROI’den plaka bölgesini bulmak, OCR yapmak, Türk plaka formatını doğrulamak ve evidence kartına güvenilir çıktı üretmek.

## Alt Başlıklar

* Vehicle ROI -> plate detector -> OCR mimarisi.
* YOLO tabanlı plate detector.
* PaddleOCR/PP-OCR, EasyOCR, CRNN, Tesseract, TrOCR karşılaştırması.
* Türk plaka format kontrolü.
* Regex ve post-processing.
* Karakter düzeyi hata düzeltme.
* Temporal voting.
* Plaka okunabilirlik skoru.
* Motion blur, düşük ışık, açı, uzaklık problemleri.
* Plate-level accuracy.
* Character-level accuracy.
* Edit distance.
* Türkiye plaka veri seti arama.
* Sentetik Türk plaka üretimi.
* KVKK ve izinli test verisi.

## Başlangıç Format Kararı

Türk plaka format doğrulaması için ilk yaklaşım kural tabanlı olacaktır:

* İl kodu kontrolü: `01`-`81`.
* Harf ve rakam blokları için regex tabanlı kontrol.
* OCR karakter düzeltme ve karıştırılan karakterlerin post-processing'i.
* Aynı track üzerinde temporal voting.
* Düşük güven durumunda plaka değerini zorla kesinleştirmeme; `unknown` veya `low_confidence` çıktısı.

Regex ve veri seti kararı literatür/açık kaynak çalışma araştırması sonrasında kesinleştirilecektir.

## Çıktı

OCR pipeline kararı, format kontrol kuralı ve test metriği seti.

## 2026-06-11 Araştırma Sonucu

İlk plate/OCR MVP iki aşamalı kurulacaktır:

1. Hedef araç ROI içinde plate detection.
2. Plate crop üzerinde OCR.
3. Türk plaka regex/il kodu post-processing.
4. Track-level temporal voting.
5. Evidence JSON update.

İlgili dosyalar:

* `deep_research/deep_research_report.md`
* `decision_plate_ocr_baseline_v1.md`
* `decision_ocr_cct_xs_baseline_2026_06_17.md`
* `plate_detection_literature_recommendation_2026_06_15.md`
* `benchmark_plan.md`
* `dataset_license_checklist.md`
* `RUN_POCR_EXP_005.md`
* `../../models/experiments/POCR_EXP_005_plate_detector_report.md`
* `../../testing/reports/pocr_exp_005_plate_detector_ftr_summary.md`
* `../../testing/templates/manual_plate_ocr_review.csv`
* `../../models/benchmarks/plate_ocr/plate_ocr_baseline_comparison.csv`

İlk araştırma aşamasında PaddleOCR güçlü OCR adayı olarak seçilmişti. `POCR-EXP-006/007` lokal karşılaştırması sonrası aktif OCR baseline `fast-plate-ocr cct-xs-v2-global-model` olarak güncellendi. PaddleOCR ikinci kontrol adayıdır; EasyOCR mevcut crop setinde önerilmez. Fine-tune ilk MVP'de açılmayacaktır.

Calistirma script'leri:

* `../../scripts/benchmarks/run_plate_detection_smoke.py`
* `../../scripts/benchmarks/run_plate_ocr_baseline.py`
* `RUN_POCR_EXP_001.md`
* `RUN_POCR_EXP_002.md`
* `RUN_POCR_EXP_005.md`

## 2026-06-17 POCR-EXP-005 Durumu

YOLO11n tabanlı single-class `license_plate` detector fine-tune koşusu tamamlandı. Yeni `best.pt`, aynı val/test split üzerinde önceki lokal baseline'a göre belirgin şekilde daha yüksek `mAP@0.5:0.95` verdi.

Önemli notlar:

* Bu sonuç plate detection sonucudur; OCR doğruluğu değildir.
* UFPR dış benchmark koşmadı.
* Yeni model, lokal `Test/video_1-3.mp4` target ROI smoke/manual review geçmeden runtime default olarak terfi ettirilmeyecek.
* İndirilecek aday model: `POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt`.

## 2026-06-17 POCR-EXP-006/007 OCR Durumu

`POCR-EXP-005` plate detector tarafından üretilen 613 crop üzerinde CCT-S, CCT-XS, PaddleOCR ve EasyOCR karşılaştırıldı.

Aktif karar:

* OCR baseline: `fast-plate-ocr cct-xs-v2-global-model`.
* İkinci kontrol: `PaddleOCR 2.10 PP-OCRv4 en`.
* Fine-tune: bu aşamada açılmayacak.
* Stabilite kapısı: `stable_count>=3`, `window_size=7`, `min_confidence>=0.75`, format ve il kodu valid.

Karar kaynakları:

* `decision_ocr_cct_xs_baseline_2026_06_17.md`
* `../../models/experiments/POCR_EXP_006_007_cct_xs_ocr_baseline.md`
* `../../testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `../../testing/reports/pocr_exp_007_cct_xs_stability.md`
