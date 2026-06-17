# Plate OCR Baselines

Tarih: 2026-06-17T08:01:46Z

## Amaç

Plate detector crop'lari ustunde OCR baseline'larini calistirip Turk plaka normalize + temporal voting hattini olculebilir hale getirmek.

## Konfigurasyon

* Detection summary: `models/benchmarks/artifacts/plate_detection/POCR-EXP-005-local-video-smoke-yolo-summary.json`
* Kaynak detector: `yolo`
* OCR engine'leri: `fastplate`
* Variantlar: `original` | upscale `1.0`
* OCR confidence esigi: `0.35`
* OCR model ref'leri: fastplate=fast-plate-ocr(cct-s-v2-global-model, device=cpu)

## Sonuc (engine x video)

| Engine | Video | Crop | Okunabilir | Format Valid | Province Valid | Vote | Vote Conf | Ort. Latency (ms) |
|---|---|---:|---:|---:|---:|---|---:|---:|
| fastplate | video_1.mp4 | 2 | 2 | 2 | 2 | 34TC8532 | 1.0 | 10.447 |
| fastplate | video_2.mp4 | 2 | 2 | 2 | 2 | 34TC8532 | 1.0 | 8.288 |
| fastplate | video_3.mp4 | 2 | 2 | 0 | 0 | C1 | 1.0 | 9.156 |

## Ciktilar

* Summary JSON'ler: `models/benchmarks/artifacts/POCR-EXP-00X-*-summary.json`
* Manuel review seed CSV: `runs/plate_ocr/POCR-EXP-006-local-ocr-smoke/manual_review_<engine>.csv`
* Manuel review referansi: `testing/templates/manual_plate_ocr_review.csv`

## Notlar

* Bu faz final OCR accuracy iddiasi kurmaz; detector sonrasi baseline usability calismasidir.
* Temporal vote, ayni track icindeki tekrarli crop'larda en istikrarli metni secer.
* Format valid = Turk plaka regex uyumu; province valid = 01-81 il kodu kontrolu.
* Ham crop'lar ve OCR uzerine yazili goruntuler Git'e eklenmez.
