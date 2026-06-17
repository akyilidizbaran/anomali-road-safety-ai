# POCR-EXP-006 Local OCR Baseline Comparison

Tarih: 2026-06-17

## Amaç

`POCR-EXP-005` YOLO11n plate detector ile uretilen plaka crop'lari uzerinde ilk OCR baseline'larini lokal makinede calistirmak ve manuel review'a hazir bir track-level temporal voting ciktisi uretmek.

Bu rapor final OCR accuracy iddiasi kurmaz. Ground truth henuz manuel olarak dogrulanmadigi icin sonuclar "local baseline smoke/benchmark" olarak yorumlanmalidir.

## Girdi

* Plate detector summary: `models/benchmarks/artifacts/plate_detection/POCR-EXP-005-local-video-smoke-yolo-summary.json`
* Plate crop kaynagi: `runs/plate_ocr/POCR-EXP-005-local-smoke/plates/yolo/`
* Video kapsami: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
* Toplam islenen crop: `613`
* Target tracks: `3`

## Lokal OCR Ortami

Basarili kosulan baseline'lar:

* `fast-plate-ocr`
* `easyocr`
* `PaddleOCR`

Ortam notlari:

* `fast-plate-ocr` ve `EasyOCR`, `.venv-ocr-run` icinde kosuldu.
* `EasyOCR`, plate crop uzerinde recognition-only modda kosuldu; full text detector modeli gereksiz goruldu.
* `PaddleOCR`, temiz `.venv-paddle-run` icinde kosuldu. `.venv-ocr-run` icindeki PaddleOCR 2.7.3 denemesi Mac ARM runtime'da native segfault verdi; bu nedenle PaddleOCR 2.10 + PaddlePaddle 3.3.1 temiz venv tercih edildi.
* `Tesseract`: Sistem binary'si bulunmadigi icin bu fazda calistirilmadi.

## Calisan Baseline'lar

`fast-plate-ocr` ile iki model varyanti, ayrica EasyOCR ve PaddleOCR denendi:

| Baseline | Model | Crop | OCR Read | Format Valid | Province Valid | Track Vote | Mean OCR Latency | p95 OCR Latency |
|---|---|---:|---:|---:|---:|---|---:|---:|
| POCR-EXP-006-S | `cct-s-v2-global-model` | 613 | 606 | 591 | 591 | 3/3 | 9.258 ms | 10.378 ms |
| POCR-EXP-006-XS | `cct-xs-v2-global-model` | 613 | 604 | 591 | 590 | 3/3 | 1.672 ms | 2.145 ms |
| POCR-EXP-003 | `EasyOCR 1.7.2 recognizer-only` | 613 | 604 | 413 | 407 | 3/3 | 7.475 ms | 12.223 ms |
| POCR-EXP-002 | `PaddleOCR 2.10 PP-OCRv4 en` | 613 | 538 | 507 | 507 | 3/3 | 54.453 ms | 104.749 ms |

Fast-plate-ocr CCT-S, fast-plate-ocr CCT-XS ve PaddleOCR uc video icin temporal vote olarak `34TC8532` uretti. EasyOCR ise ayni crop setinde farkli ve dusuk guvenli vote'lara kaydi.

## Video Bazli Sonuc

### CCT-S

| Video | Crop | OCR Read | Format Valid | Province Valid | Temporal Vote | Vote Conf | Mean OCR Latency |
|---|---:|---:|---:|---:|---|---:|---:|
| `video_1.mp4` | 206 | 205 | 203 | 203 | `34TC8532` | 0.9914 | 9.076 ms |
| `video_2.mp4` | 201 | 197 | 193 | 193 | `34TC8532` | 0.9817 | 9.173 ms |
| `video_3.mp4` | 206 | 204 | 195 | 195 | `34TC8532` | 0.9173 | 9.523 ms |

### CCT-XS

| Video | Crop | OCR Read | Format Valid | Province Valid | Temporal Vote | Vote Conf | Mean OCR Latency |
|---|---:|---:|---:|---:|---|---:|---:|
| `video_1.mp4` | 206 | 205 | 203 | 203 | `34TC8532` | 0.9903 | 1.699 ms |
| `video_2.mp4` | 201 | 197 | 193 | 193 | `34TC8532` | 0.9733 | 1.720 ms |
| `video_3.mp4` | 206 | 202 | 195 | 194 | `34TC8532` | 0.9052 | 1.599 ms |

### EasyOCR

| Video | Crop | OCR Read | Format Valid | Province Valid | Temporal Vote | Vote Conf | Mean OCR Latency |
|---|---:|---:|---:|---:|---|---:|---:|
| `video_1.mp4` | 206 | 206 | 187 | 185 | `04IC0522` | 0.1279 | 6.156 ms |
| `video_2.mp4` | 201 | 201 | 177 | 177 | `04IC0522` | 0.2704 | 6.961 ms |
| `video_3.mp4` | 206 | 197 | 49 | 45 | `04C0522` | 0.1536 | 9.294 ms |

### PaddleOCR

| Video | Crop | OCR Read | Format Valid | Province Valid | Temporal Vote | Vote Conf | Mean OCR Latency |
|---|---:|---:|---:|---:|---|---:|---:|
| `video_1.mp4` | 206 | 203 | 203 | 203 | `34TC8532` | 0.9911 | 56.611 ms |
| `video_2.mp4` | 201 | 189 | 176 | 176 | `34TC8532` | 0.9650 | 65.022 ms |
| `video_3.mp4` | 206 | 146 | 128 | 128 | `34TC8532` | 0.4685 | 41.984 ms |

## Ilk Teknik Yorum

* `cct-xs-v2-global-model`, `cct-s-v2-global-model` ile ayni track-level temporal vote sonucunu uretirken yaklasik 5.5 kat daha dusuk ortalama OCR latency verdi.
* `cct-s-v2-global-model`, yalnizca 2 ek crop'ta OCR read ve 1 ek crop'ta province valid uretmesine ragmen latency maliyeti belirgin derecede daha yuksek.
* PaddleOCR de 3/3 track icin `34TC8532` sonucuna geldi, ancak ortalama OCR latency `54.453 ms` ile CCT-XS'e gore yaklasik 32.6 kat daha yavas.
* EasyOCR recognition-only hiz olarak orta seviyede olsa da temporal vote'lari `04IC0522`, `04IC0522`, `04C0522` seklinde dagildi ve vote confidence dusuk kaldi. Bu crop seti icin ilk tercih olmamali.
* Bu nedenle manuel review icin ilk aday `fast-plate-ocr cct-xs-v2-global-model`, ikinci kontrol adayi `PaddleOCR 2.10 PP-OCRv4 en` olmalidir.
* `34TC8532` sonucu gercek plaka ile manuel karsilastirilmadan dogru kabul edilmemelidir.

## Manuel Review Talimati

Kontrol edilecek lokal dosyalar:

* Annotated plate detection videolari: `runs/plate_ocr/POCR-EXP-005-local-smoke/annotated/`
* Plate crop klasorleri: `runs/plate_ocr/POCR-EXP-005-local-smoke/plates/yolo/`
* CCT-S review seed: `runs/plate_ocr/POCR-EXP-006-local-ocr-baselines/manual_review_fastplate.csv`
* CCT-XS review seed: `runs/plate_ocr/POCR-EXP-006-local-ocr-baselines-cct-xs/manual_review_fastplate.csv`
* EasyOCR review seed: `runs/plate_ocr/POCR-EXP-006-local-ocr-baselines-easyocr/manual_review_easyocr.csv`
* PaddleOCR review seed: `runs/plate_ocr/POCR-EXP-006-local-ocr-baselines-paddle/manual_review_paddle.csv`

Manual review'da ozellikle su sorular cevaplanmalidir:

* Plaka gorunur mu?
* Plate bbox plaka bolgesine oturuyor mu?
* Temporal vote `34TC8532` gercek plaka ile birebir eslesiyor mu?
* Eslesmiyorsa hata tam okuma hatasi mi, kismi okuma mi, detector crop hatasi mi?
* Duzgun crop varken OCR yaniliyorsa fine-tune veya farkli OCR modeli gerekir mi?

## Karar

* Lokal baseline asamasinda `fast-plate-ocr cct-xs-v2-global-model` birincil manual review adayi olarak secildi.
* PaddleOCR sonucu CCT-XS ile ayni temporal vote'a geldigi icin ikinci aday olarak saklanacak, fakat latency maliyeti yuksek.
* EasyOCR sonucu bu crop setinde zayif kaldigi icin su an onerilen aday degil.
* Manual review olumluysa OCR fine-tune'a gecmeden once `cct-xs` event/evidence enrichment hattina baglanabilir.
* Manual review olumsuzsa once OCR crop kalitesi ve plate detector crop secimi incelenmeli; sonra plaka OCR fine-tune veya baska OCR baseline'i acilmalidir.

## Cikti Dosyalari

* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-006-local-ocr-baselines/POCR-EXP-006-fast-plate-ocr-summary.json`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-006-local-ocr-baselines-cct-xs/POCR-EXP-006-fast-plate-ocr-summary.json`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-006-local-ocr-baselines-easyocr/POCR-EXP-003-easyocr-summary.json`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-006-local-ocr-baselines-paddle/POCR-EXP-002-paddleocr-summary.json`
* `testing/reports/pocr_exp_006_local_ocr_baselines_fastplate.md`
* `testing/reports/pocr_exp_006_local_ocr_baselines_cct_xs_fastplate.md`
* `testing/reports/pocr_exp_006_local_ocr_baselines_easyocr_easyocr.md`
* `testing/reports/pocr_exp_006_local_ocr_baselines_paddle_paddle.md`
