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
* `benchmark_plan.md`
* `dataset_license_checklist.md`
* `../../testing/templates/manual_plate_ocr_review.csv`
* `../../models/benchmarks/plate_ocr/plate_ocr_baseline_comparison.csv`

İlk OCR baseline PaddleOCR PP-OCRv5 Latin/mobile recognition olarak seçildi. EasyOCR ikinci aday, Tesseract debug/fallback adayıdır. Fine-tune ilk MVP'de açılmayacaktır.
