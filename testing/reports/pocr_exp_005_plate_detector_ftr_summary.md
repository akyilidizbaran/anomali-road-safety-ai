# POCR-EXP-005 Plate Detector - FTR Summary

Tarih: 2026-06-17

## Kapsam

Bu belge, FTR/PCR rapor şablonunda istenen **veri seti**, **model mimarisi**, **eğitim süreci**, **başarım metrikleri**, **sistem çıktısı** ve **sınırlılıklar** başlıklarını beslemek için hazırlanmıştır.

Bu çalışma yalnız plaka bbox tespitini kapsar. OCR, plaka metni okuma, karakter doğruluğu ve Türk plaka regex doğrulaması bu koşunun kapsamı değildir.

## Rapor Şablonuna Verilecek Kısa Cevap

Araç takip modülüyle seçilen hedef araç ROI üzerinde çalıştırılmak üzere YOLO11n tabanlı tek sınıflı bir `license_plate` tespit modeli fine-tune edilmiştir. Eğitimde Turkish Number Plates ve Roboflow License Plate Recognition veri kaynakları birleştirilmiş, etiketler tek sınıf altında normalize edilmiş, duplicate/near-duplicate temizliği sonrası deterministik train/validation/test ayrımı üretilmiştir. Model, aynı validation/test split üzerinde mevcut lokal plate detector baseline'ına göre daha yüksek `mAP@0.5:0.95` sağlamıştır. Ancak OCR ve gerçek demo video manuel doğrulaması ayrı aşamada yapılacaktır.

## Veri Seti Bilgisi

| Alan | Açıklama |
|---|---|
| Birincil veri | Turkish Number Plates Roboflow, version 2 |
| Hacim destek verisi | Roboflow License Plate Recognition, version 13 |
| Raw kayıt | 107,350 image kaydı |
| Normalize/dedup sonrası | 106,432 kayıt |
| Sınıf | `license_plate` |
| Etiket türü | YOLO bbox |
| Final train | 85,039 image / 88,765 bbox |
| Final val | 10,636 image / 11,086 bbox |
| Final test | 10,757 image / 11,220 bbox |
| Dış benchmark | UFPR-ALPR yok, skipped |

## Model ve Eğitim

| Alan | Değer |
|---|---|
| Deney ID | `POCR-EXP-005-YOLO11N-PLATE-DETECTOR` |
| Başlangıç modeli | Ultralytics `yolo11n.pt` |
| Eğitim tipi | Pretrained modelden fine-tune |
| Framework | Ultralytics 8.4.68 / PyTorch 2.11.0 |
| Girdi boyutu | 640 |
| Epoch | 80 |
| Batch | 48 |
| Donanım | NVIDIA L4 |
| Eğitim süresi | yaklaşık 18.75 saat |
| Checkpoint | `POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt` |
| Export | `.pt` ve `.onnx` üretildi |

## Başarım Metrikleri

| Model | Split | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---:|---:|---:|---:|
| POCR-EXP-005 | val | 0.9947 | 0.9891 | 0.9948 | 0.8569 |
| POCR-EXP-005 | test | 0.9951 | 0.9907 | 0.9948 | 0.8543 |
| Baseline `license_plate_detector.pt` | val | 0.9722 | 0.9576 | 0.9754 | 0.6097 |
| Baseline `license_plate_detector.pt` | test | 0.9726 | 0.9586 | 0.9754 | 0.6089 |

Test split üzerinde iyileşme:

| Metrik | Fark |
|---|---:|
| Precision | +0.0225 |
| Recall | +0.0321 |
| mAP@0.5 | +0.0194 |
| mAP@0.5:0.95 | +0.2454 |

## Rapor İçin Doğru Yorum

Bu sonuç, plaka bbox tespit modeli için güçlü bir eğitim/validasyon kanıtı sağlar. Özellikle `mAP@0.5:0.95` artışı, plaka kutusunun daha hassas yerleştiğine işaret eder.

Ancak aşağıdaki sınırlılıklar korunmalıdır:

* Bu sonuç OCR doğruluğu değildir.
* Gerçek demo videolarında target vehicle ROI üzerinde manuel doğrulama yapılmadan runtime model terfisi kesinleştirilmemelidir.
* UFPR-ALPR gibi dış bir benchmark henüz koşulmadığı için genelleme iddiası sınırlıdır.
* Roboflow kaynaklarının lisans/dataset contamination notları final rapor öncesi yeniden doğrulanmalıdır.
* Plaka görselleri kişisel veri riski taşıdığı için raw crop ve annotated video çıktıları Git'e eklenmemelidir.

## Evidence Pipeline Bağlantısı

Bu model, nihai sistemde şu alanları besleyecektir:

```json
{
  "plate_detected": true,
  "plate_bbox_xyxy": [0, 0, 0, 0],
  "plate_confidence": 0.0,
  "plate_crop_uri": "runs/plate_ocr/...",
  "plate_detector_model": "POCR-EXP-005-YOLO11N-PLATE-DETECTOR",
  "plate_detection_status": "detected | not_detected | low_confidence",
  "failure_reason": null
}
```

OCR aşaması bu bbox/crop çıktısı üzerine kurulacaktır.

## İndirilecek Model

Drive path:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt
```

Drive URL:

```text
https://drive.google.com/file/d/1DnmlwCEfGXyx0XYgzixPErnvY9IvlIOd/view
```

Yerel test path'i:

```text
models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt
```

## Sonraki Test

Yeni model indirildikten sonra `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4` üzerinde detector-only smoke test yapılacaktır. Beklenen kontrol:

* target vehicle ROI içinde plaka bbox üretiyor mu?
* false positive azalıyor mu?
* plate confidence dağılımı önceki baseline'a göre daha iyi mi?
* plaka crop'ları OCR için kullanılabilir mi?
* düşük ışık ve uzak plaka durumlarında failure reason doğru işaretlenebiliyor mu?

Bu test geçmeden OCR fazına geçmek teknik olarak erken olur.
