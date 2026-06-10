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

* Plate detector: target ROI üzerinde çalışan indirilebilir YOLO/ONNX license plate detector.
* İlk kaynak adayları:
  * Roboflow/CC BY 4.0 kaynaklı license plate recognition dataset/model ailesi.
  * HF `morsetechlab/yolov11-license-plate-detection` yalnız lisans notuyla smoke test.
  * HF `nickmuchi/yolos-small-finetuned-license-plate-detection` ikinci detector adayı.
* OCR: PaddleOCR PP-OCRv5 Latin/mobile recognition.
* OCR ikinci aday: EasyOCR.
* Debug/fallback: Tesseract.

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
