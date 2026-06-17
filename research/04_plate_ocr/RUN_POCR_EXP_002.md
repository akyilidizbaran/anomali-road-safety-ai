# POCR-EXP-002/003/004 - OCR Baseline Calistirma Talimati

Tarih: 2026-06-12

Bu adim `POCR-EXP-001` sonrasinda uretilen plaka crop'lari ustunde OCR baseline'larini
calistirir. Varsayilan detector kaynagi `POCR-EXP-001-plate-detection-yolo-summary.json`
ve `runs/plate_ocr/POCR-EXP-001-plate-detection/plates/yolo/` altindaki crop'lardir.

## 1) Ortami hazirla

```bash
cd "/Users/elifsena/Downloads/5G Teknofest"
source .venv-yolo/bin/activate
```

## 2) OCR bagimliliklarini kur

### PaddleOCR (`POCR-EXP-002`)

```bash
pip install paddlepaddle paddleocr
```

> `paddleocr` paketi tek basina yetmez; runtime icin `paddlepaddle` da gerekir.
> Ilk kosuda model dosyalari indirilebilir. Internet acik olmali.

### EasyOCR (`POCR-EXP-003`)

```bash
pip install easyocr
```

### Tesseract (`POCR-EXP-004`, opsiyonel)

```bash
pip install pytesseract
brew install tesseract
```

> Tesseract debug/fallback icindir; ilk tercih PaddleOCR ve EasyOCR karsilastirmasidir.

## 3) Hizli kosular

Yalniz PaddleOCR:

```bash
python scripts/benchmarks/run_plate_ocr_baseline.py --engines paddle
```

Yalniz EasyOCR:

```bash
python scripts/benchmarks/run_plate_ocr_baseline.py --engines easyocr
```

Iki engine'i ayni crop setinde karsilastir:

```bash
python scripts/benchmarks/run_plate_ocr_baseline.py --engines paddle easyocr
```

## 4) Faydalı bayraklar

- `--detector-key yolo` veya `--detector-key yolos` - Hangi plate detector crop'larinin okunacagini sec.
- `--frame-stride 5` - Crop listesinden her 5. dosyayi isle; hizli smoke test icin.
- `--limit-per-video 50` - Video basi crop sayisini sinirla.
- `--variants original gray clahe` - OCR oncesi preprocess varyantlari.
- `--upscale 2.0` - Crop'i OCR oncesi buyut.
- `--min-ocr-confidence 0.35` - Temporal voting icin minimum OCR confidence.
- `--keep-per-crop` - Tum crop sonucunu summary JSON'a gom; dosyayi buyutur.

## 5) Uretilen ciktilar

- Summary JSON:
  - `models/benchmarks/artifacts/POCR-EXP-002-paddleocr-summary.json`
  - `models/benchmarks/artifacts/POCR-EXP-003-easyocr-summary.json`
  - `models/benchmarks/artifacts/POCR-EXP-004-tesseract-summary.json`
- Markdown raporu:
  - `testing/reports/pocr_exp_002_004_plate_ocr_summary_<engine>.md`
- Manuel review seed CSV:
  - `runs/plate_ocr/POCR-EXP-002-004-ocr/manual_review_<engine>.csv`

## 6) Manuel inceleme

`testing/templates/manual_plate_ocr_review.csv` alanlarini kullanarak su sorulari kontrol et:

- Temporal vote ile secilen plaka metni okunabilir mi?
- `normalized_text` Turk plaka formatina mantikli donmus mu?
- Ozellikle `video_3` icinde tekrarli karelerde ayni plaka korunuyor mu?
- `video_1` ve `video_2` gibi zor gorunumlerde sistem `not_read` / dusuk kalite davranisina yakin mi?

Karar metrikleri:

- `ocr_read_count`
- `format_valid_count`
- `province_valid_count`
- `temporal_vote.plate_text`
- `time_to_first_readable_plate_seconds`

Secilen engine, bir sonraki adimda event/evidence JSON zenginlesmesine baglanacaktir.
