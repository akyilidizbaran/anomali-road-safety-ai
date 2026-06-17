# POCR-EXP-002/003/004 Plate OCR Baselines

Tarih: 2026-06-12T15:23:55Z

## Amaç

POCR-EXP-001 crop'lari ustunde OCR baseline'larini calistirip Turk plaka normalize + temporal voting hattini olculebilir hale getirmek.

## Konfigurasyon

* Detection summary: `models/benchmarks/artifacts/POCR-EXP-001-plate-detection-yolo-summary.json`
* Kaynak detector: `yolo`
* OCR engine'leri: `easyocr`
* Variantlar: `original, gray` | upscale `2.0`
* OCR confidence esigi: `0.35`

## Sonuc (engine x video)

| Engine | Video | Crop | Okunabilir | Format Valid | Province Valid | Vote | Vote Conf | Ort. Latency (ms) |
|---|---|---:|---:|---:|---:|---|---:|---:|
| easyocr | video_1.mp4 | 213 | 204 | 120 | 120 | 34TC8532 | 0.3762 | 560.72 |
| easyocr | video_2.mp4 | 194 | 191 | 93 | 93 | 34TC8532 | 0.4298 | 640.867 |
| easyocr | video_3.mp4 | 220 | 176 | 100 | 99 | 04TC0532 | 0.2325 | 339.437 |

## Ciktilar

* Summary JSON'ler: `models/benchmarks/artifacts/POCR-EXP-00X-*-summary.json`
* Manuel review seed CSV: `runs/plate_ocr/POCR-EXP-002-004-ocr/manual_review_<engine>.csv`
* Manuel review referansi: `testing/templates/manual_plate_ocr_review.csv`

## Notlar

* Bu faz final OCR accuracy iddiasi kurmaz; detector sonrasi baseline usability calismasidir.
* Temporal vote, ayni track icindeki tekrarli crop'larda en istikrarli metni secer.
* Format valid = Turk plaka regex uyumu; province valid = 01-81 il kodu kontrolu.
* Ham crop'lar ve OCR uzerine yazili goruntuler Git'e eklenmez.
