# Decision - Plate Detection + OCR Baseline v1

Tarih: 2026-06-11

## Karar

İlk plate/OCR baseline iki aşamalı kurulacaktır:

1. Hedef araç ROI içinde plate detection.
2. Plate crop üzerinde OCR.
3. Türk plaka post-processing.
4. Track-level temporal voting.
5. Evidence JSON update.

## İlk Baseline

* Plate detector: target ROI üzerinde çalışan YOLO11n tabanlı single-class `license_plate` detector.
* İlk kaynak adayları:
  * Turkish Number Plates Roboflow dataset, Türkiye plaka geometrisine en yakın birincil fine-tune verisi.
  * Roboflow/CC BY 4.0 kaynaklı License Plate Recognition dataset/model ailesi, hacim artırma ve pretrained smoke test kaynağı.
  * HF `morsetechlab/yolov11-license-plate-detection` yalnız lisans/dataset contamination notuyla smoke test.
  * HF `nickmuchi/yolos-small-finetuned-license-plate-detection` ikinci detector adayı.
* OCR: İlk araştırma kararında PaddleOCR PP-OCRv5 Latin/mobile recognition adaydı; 2026-06-17 lokal karşılaştırması sonrası aktif OCR baseline `fast-plate-ocr cct-xs-v2-global-model` olarak güncellendi.
* OCR ikinci aday/kontrol: PaddleOCR 2.10 PP-OCRv4 en.
* OCR önerilmeyen aday: EasyOCR, mevcut crop setinde düşük güvenli ve farklı temporal vote'lara kaydı.
* Debug/fallback: Tesseract, sistem binary'si hazır olduğunda debug amaçlı denenebilir.

## Gerekçe

* Target ROI üzerinde çalışmak latency ve false positive riskini düşürür.
* İki aşamalı pipeline evidence package ile daha uyumludur.
* Plate detection hatası ile OCR hatası ayrı raporlanabilir.
* Türk plaka regex/post-processing ve temporal voting modüler şekilde eklenebilir.
* Fine-tune açmadan önce pretrained/public baseline uçtan uca çalıştırılmalıdır.

## Ertelenenler

* End-to-end ALPR.
* LPRNet/CRNN fine-tune.
* TrOCR/PARSeq/ViT tabanlı OCR.
* OpenALPR entegrasyonu.
* Türk plaka sentetik veri üretimi.
* Low-light specialist plate detector fine-tune.

## Etki

* `target_vehicle_selected` skeleton eventleri plate/OCR ile zenginleştirilecek.
* Evidence status `partial` seviyesinden plate crop + OCR metadata içeren daha denetlenebilir pakete yaklaşacak.
* QoD kararı plate/OCR kalite sinyallerini kullanabilecek.

## Kaynak Notları

* Ultralytics tabanlı modeller AGPL-3.0 / Enterprise lisans notuyla değerlendirilmelidir.
* PaddleOCR, EasyOCR ve Tesseract Apache-2.0 çizgisinde daha düşük lisans riski taşır.
* Roboflow/HF dataset/model lisansı model card ve dataset sayfasından her koşu öncesi doğrulanmalıdır.

## 2026-06-15 Güncellemesi

Detay literatür ve veri/model önerisi:

* `research/04_plate_ocr/plate_detection_literature_recommendation_2026_06_15.md`

Güncel plate detection kararı:

* İlk gerçek fine-tune modeli: `YOLO11n single-class license_plate detector`.
* Birincil veri: `Turkish Number Plates` Roboflow dataset.
* Hacim destek verisi: `License Plate Recognition` Roboflow dataset; kendi duplicate temizliği ve split üretimi şart.
* Benchmark/generalization: `UFPR-ALPR`.
* Opsiyonel ileriki pretraining/adverse condition kaynağı: `CCPD`.
* OCR'a geçiş kriteri: target track başına en az bir usable plate crop + doğru failure reason alanları.

## 2026-06-17 OCR Baseline Güncellemesi

Detay karar dosyası:

* `research/04_plate_ocr/decision_ocr_cct_xs_baseline_2026_06_17.md`

Güncel OCR kararı:

* Aktif OCR baseline: `fast-plate-ocr cct-xs-v2-global-model`.
* İkinci kontrol adayı: `PaddleOCR 2.10 PP-OCRv4 en`.
* EasyOCR mevcut `POCR-EXP-005` plate crop setinde önerilmez.
* CCT-XS fine-tune bu aşamada açılmayacak.
* Event/evidence tarafında tek-frame OCR değil, `stable_count>=3`, `window_size=7`, `min_confidence>=0.75`, `format_valid=true`, `province_code_valid=true` koşullarını sağlayan temporal vote kullanılacak.

Gerekçe:

* CCT-XS ve PaddleOCR 3/3 target track için aynı temporal vote sonucuna ulaştı.
* CCT-XS ortalama OCR latency `1.672 ms`, PaddleOCR `54.453 ms` ölçüldü.
* CCT-S aynı sonucu üretse de ortalama latency `9.258 ms` ile CCT-XS'ten belirgin yavaştır.
* `video_3` gecikmesi sistematik karakter karıştırma değil, uzak/karanlık erken frame okunabilirliği kaynaklıdır.
