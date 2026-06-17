# POCR-EXP-005 Plate Detection Smoke Test (detector-only)

Tarih: 2026-06-17T07:05:16Z

## Amaç

Hedef aracın tespit edildiği her karede araç ROI'si üzerinde plaka TESPİTİ yapmak ve seçili plaka model(ler)ini değerlendirmek. OCR (metin okuma) bu aşamada yoktur.

## Konfigürasyon

* Araç detector: `models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt` / tracker `bytetrack.yaml`
* Plaka modelleri: `yolo`
* ROI padding: `0.1`  | plate conf: `0.25`

## Sonuç (model × video)

| Video | Model | Hedef Kare | Plakalı Kare | Tespit Oranı | Maks Conf | Ort. Latency (ms) |
|---|---|---:|---:|---:|---:|---:|
| video_1.mp4 | yolo | 338 | 206 | 0.6095 | 0.838 | 22.453 |
| video_2.mp4 | yolo | 321 | 198 | 0.6168 | 0.8396 | 16.652 |
| video_3.mp4 | yolo | 263 | 206 | 0.7833 | 0.8578 | 16.454 |

## Manuel İnceleme

* Annotated videolar (orijinal kare üzerine kutular, ignore'lu): `runs/plate_ocr/POCR-EXP-005-local-smoke/annotated/<video>_plate_detection_<model>.mp4`
* Plaka kırpıntıları (ignore'lu): `runs/plate_ocr/POCR-EXP-005-local-smoke/plates/<model>/<video>/`
* Manuel review şablonu: `testing/templates/manual_plate_ocr_review.csv`

## Notlar

* Bu çalışma final plaka okuma doğruluğu iddiası kurmaz; detector smoke test'tir.
* Ham plaka görselleri kişisel veri sayılır ve Git'e eklenmez.
* Tespit oranı yüksek/güveni yüksek + yan profilde false positive üretmeyen model tercih edilir; nihai karar kullanıcının manuel incelemesiyle verilecektir.
