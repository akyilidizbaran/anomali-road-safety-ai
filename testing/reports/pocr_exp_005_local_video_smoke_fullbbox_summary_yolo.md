# POCR-EXP-005-FULLBBOX Plate Detection Smoke Test (detector-only)

Tarih: 2026-06-17T11:42:59Z

## Amaç

Hedef aracın tespit edildiği her karede araç ROI'si üzerinde plaka TESPİTİ yapmak ve seçili plaka model(ler)ini değerlendirmek. OCR (metin okuma) bu aşamada yoktur.

## Konfigürasyon

* Araç detector: `models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt` / tracker `bytetrack.yaml`
* Plaka modelleri: `yolo`
* ROI padding: `0.1`  | plate conf: `0.25`

## Sonuç (model × video)

| Video | Model | Hedef Kare | Plakalı Kare | Tespit Oranı | Maks Conf | Ort. Latency (ms) |
|---|---|---:|---:|---:|---:|---:|
| video_1.mp4 | yolo | 344 | 206 | 0.5988 | 0.838 | 21.531 |
| video_2.mp4 | yolo | 327 | 198 | 0.6055 | 0.8396 | 16.839 |
| video_3.mp4 | yolo | 279 | 216 | 0.7742 | 0.8578 | 19.736 |

## Manuel İnceleme

* Annotated videolar (orijinal kare üzerine kutular, ignore'lu): `runs/plate_ocr/POCR-EXP-005-fullbbox/annotated/<video>_plate_detection_<model>.mp4`
* Plaka kırpıntıları (ignore'lu): `runs/plate_ocr/POCR-EXP-005-fullbbox/plates/<model>/<video>/`
* Manuel review şablonu: `testing/templates/manual_plate_ocr_review.csv`

## Notlar

* Bu çalışma final plaka okuma doğruluğu iddiası kurmaz; detector smoke test'tir.
* Ham plaka görselleri kişisel veri sayılır ve Git'e eklenmez.
* Tespit oranı yüksek/güveni yüksek + yan profilde false positive üretmeyen model tercih edilir; nihai karar kullanıcının manuel incelemesiyle verilecektir.
