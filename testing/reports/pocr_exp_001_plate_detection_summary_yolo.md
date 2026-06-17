# POCR-EXP-001 Plate Detection Smoke Test (detector-only)

Tarih: 2026-06-11T17:18:29Z

## Amaç

Hedef aracın tespit edildiği her karede araç ROI'si üzerinde plaka TESPİTİ yapmak ve iki plaka modelini karşılaştırmak. OCR (metin okuma) bu aşamada yoktur.

## Konfigürasyon

* Araç detector: `yolo11n.pt` / tracker `bytetrack.yaml`
* Plaka modelleri: `yolo`
* ROI padding: `0.1`  | plate conf: `0.25`

## Sonuç (model × video)

| Video | Model | Hedef Kare | Plakalı Kare | Tespit Oranı | Maks Conf | Ort. Latency (ms) |
|---|---|---:|---:|---:|---:|---:|
| video_1.mp4 | yolo | 342 | 209 | 0.6111 | 0.7791 | 26.291 |
| video_2.mp4 | yolo | 340 | 192 | 0.5647 | 0.795 | 21.324 |
| video_3.mp4 | yolo | 284 | 212 | 0.7465 | 0.7787 | 24.904 |

## Manuel İnceleme

* Annotated videolar (orijinal kare üzerine kutular, ignore'lu): `runs/plate_ocr/POCR-EXP-001-plate-detection/annotated/<video>_plate_detection.mp4`
* Plaka kırpıntıları (ignore'lu): `runs/plate_ocr/POCR-EXP-001-plate-detection/plates/<model>/<video>/`
* Manuel review şablonu: `testing/templates/manual_plate_ocr_review.csv`

## Notlar

* Bu çalışma final plaka okuma doğruluğu iddiası kurmaz; detector smoke test'tir.
* Ham plaka görselleri kişisel veri sayılır ve Git'e eklenmez.
* Tespit oranı yüksek/güveni yüksek + yan profilde false positive üretmeyen model tercih edilir; nihai karar kullanıcının manuel incelemesiyle verilecektir.
