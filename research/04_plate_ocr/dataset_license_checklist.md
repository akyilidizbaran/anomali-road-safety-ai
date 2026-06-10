# Plate OCR Dataset and License Checklist

Tarih: 2026-06-11

## Amaç

Plate detection/OCR için kullanılabilecek dataset ve model kaynaklarını lisans/uygunluk açısından izlemek.

## Kaynaklar

| Kaynak | Link | Lisans / Erişim | Not | Kullanım Kararı |
|---|---|---|---|---|
| Roboflow LPR dataset/model | https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e | Sürüm sayfalarında CC BY 4.0 görülüyor | Detection bbox için güçlü ilk aday | Baseline/fine-tune adayı |
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

## Kontrol Edilecekler

* Dataset lisansı final rapor öncesi tekrar doğrulanacak.
* Model card lisansı model indirilmeden önce kaydedilecek.
* Plaka görselleri kişisel veri gibi ele alınacak.
* Raw plate crop artifactleri Git'e eklenmeyecek.
* Rapor/demo ekranlarında plaka metni maskeleme opsiyonu korunacak.
