# Plate OCR Dataset and License Checklist

Tarih: 2026-06-11

## Amaç

Plate detection/OCR için kullanılabilecek dataset ve model kaynaklarını lisans/uygunluk açısından izlemek.

## Kaynaklar

| Kaynak | Link | Lisans / Erişim | Not | Kullanım Kararı |
|---|---|---|---|---|
| Turkish Number Plates Roboflow | https://universe.roboflow.com/plakatanima-vnt3k/turkish-number-plates | CC BY 4.0 olarak listeleniyor | 2,246 image, Türkiye plaka geometrisine en yakın açık kaynak aday | Birincil plate detector fine-tune verisi |
| Roboflow LPR dataset/model | https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e | Sürüm sayfalarında CC BY 4.0 görülüyor | 10,125 image; model card'larda split contamination uyarısı bulunduğu için reported metrics final kanıt değildir | Hacim destek verisi; duplicate temizliği ve kendi split şart |
| HF `keremberke/license-plate-object-detection` | https://huggingface.co/datasets/keremberke/license-plate-object-detection | CC BY 4.0 | Roboflow export, COCO bbox | Baseline/fine-tune adayı |
| HF `morsetechlab/yolov11-license-plate-detection` | https://huggingface.co/morsetechlab/yolov11-license-plate-detection | AGPL-3.0 tag | Hazır YOLO11 detector | Smoke test, lisans notu şart |
| HF `nickmuchi/yolos-small-finetuned-license-plate-detection` | https://huggingface.co/nickmuchi/yolos-small-finetuned-license-plate-detection | Model card kontrol edilmeli | Transformers detector | İkinci detector adayı |
| CCPD | https://github.com/detectrecog/ccpd | Lisans ayrıca doğrulanmalı | Büyük Çin plate dataset | TR formatına uzak, benchmark/fine-tune araştırması |
| UFPR-ALPR | https://web.inf.ufpr.br/vri/databases/ufpr-alpr/ | Akademik kullanım/request notu | 4,500 annotated image, video-derived | Araştırma/benchmark |
| AOLP | https://github.com/AvLab-CV/AOLP | Lisans doğrulanmalı | 2,049 Taiwan plate image | Küçük benchmark |
| OpenALPR | https://github.com/openalpr/openalpr | AGPL-3.0/commercial | Eski ama ALPR odaklı | Ertele |
| PaddleOCR | https://github.com/PaddlePaddle/PaddleOCR | Apache-2.0 | OCR baseline | Kullan |
| EasyOCR | https://github.com/JaidedAI/EasyOCR | Apache-2.0 | OCR comparison | Kullan |
| Tesseract | https://github.com/tesseract-ocr/tesseract | Apache-2.0 | Debug fallback | Kullan |

## 2026-06-17 POCR-EXP-005 Veri Kullanımı

POCR-EXP-005 koşusunda kullanılan Roboflow kaynakları:

| Kaynak | Version | Raw split | Normalize/dedup sonrası katkı | Kullanım |
|---|---:|---|---|---|
| Turkish Number Plates Roboflow | 2 | train `4,857`, val `419`, test `208` | train `4,332`, val `523`, test `598` | Türkiye plaka geometrisi için birincil kaynak |
| Roboflow LPR | 13 | train `98,798`, val `2,048`, test `1,020` | train `80,707`, val `10,113`, test `10,159` | Hacim ve çeşitlilik desteği |

Koşu çıktısında toplam normalize/dedup metadata satırı `106,432` olarak kaydedildi. Final YOLO splitleri:

* train: `85,039` image / label
* val: `10,636` image / label
* test: `10,757` image / label

Lisans notu:

* Roboflow sayfalarında lisans CC BY 4.0 olarak izlenmektedir; final rapor öncesi dataset sayfaları yeniden kontrol edilmelidir.
* Ultralytics tabanlı eğitim ve checkpoint için AGPL-3.0 / Enterprise lisans değerlendirmesi ayrıca yapılmalıdır.
* Raw image, plate crop, annotated video ve model ağırlıkları Git'e eklenmeyecektir.
* Plaka görüntüleri kişisel veri riski taşıdığı için evidence çıktılarında erişim kontrolü ve gerekirse maskeleme politikası korunmalıdır.

## Kontrol Edilecekler

* Dataset lisansı final rapor öncesi tekrar doğrulanacak.
* Model card lisansı model indirilmeden önce kaydedilecek.
* Plaka görselleri kişisel veri gibi ele alınacak.
* Raw plate crop artifactleri Git'e eklenmeyecek.
* Rapor/demo ekranlarında plaka metni maskeleme opsiyonu korunacak.
