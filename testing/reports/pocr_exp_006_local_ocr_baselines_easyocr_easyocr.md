# Plate OCR Baselines

Tarih: 2026-06-17T08:20:20Z

## Amaç

Plate detector crop'lari ustunde OCR baseline'larini calistirip Turk plaka normalize + temporal voting hattini olculebilir hale getirmek.

## Konfigurasyon

* Detection summary: `models/benchmarks/artifacts/plate_detection/POCR-EXP-005-local-video-smoke-yolo-summary.json`
* Kaynak detector: `yolo`
* OCR engine'leri: `easyocr`
* Variantlar: `original` | upscale `1.0`
* OCR confidence esigi: `0.35`
* OCR model ref'leri: easyocr=EasyOCR(lang=en, gpu=False, mode=recognizer_only)

## Sonuc (engine x video)

| Engine | Video | Crop | Okunabilir | Format Valid | Province Valid | Vote | Vote Conf | Ort. Latency (ms) |
|---|---|---:|---:|---:|---:|---|---:|---:|
| easyocr | video_1.mp4 | 206 | 206 | 187 | 185 | 04IC0522 | 0.1279 | 6.156 |
| easyocr | video_2.mp4 | 201 | 201 | 177 | 177 | 04IC0522 | 0.2704 | 6.961 |
| easyocr | video_3.mp4 | 206 | 197 | 49 | 45 | 04C0522 | 0.1536 | 9.294 |

## Ciktilar

* Summary JSON'ler: `models/benchmarks/artifacts/POCR-EXP-00X-*-summary.json`
* Manuel review seed CSV: `runs/plate_ocr/POCR-EXP-006-local-ocr-baselines-easyocr/manual_review_<engine>.csv`
* Manuel review referansi: `testing/templates/manual_plate_ocr_review.csv`

## Notlar

* Bu faz final OCR accuracy iddiasi kurmaz; detector sonrasi baseline usability calismasidir.
* Temporal vote, ayni track icindeki tekrarli crop'larda en istikrarli metni secer.
* Format valid = Turk plaka regex uyumu; province valid = 01-81 il kodu kontrolu.
* Ham crop'lar ve OCR uzerine yazili goruntuler Git'e eklenmez.
