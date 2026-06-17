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

Basarili kurulan paketler:

* `fast-plate-ocr`
* `onnxruntime`
* `easyocr`
* `opencv-python-headless`
* `torch`

Calistirilamayan baseline'lar:

* `PaddleOCR`: PaddlePaddle kurulumu bu lokal ortamda pratik sekilde tamamlanamadi. Python 3.14 ile wheel bulunmadi; Python 3.12 venv icinde PaddlePaddle indirmesi cok uzun surdu ve baseline kosusuna gecilemedi.
* `EasyOCR`: Paket import edildi, ancak ilk model download adimi cok yavas ilerledi ve kesildi. Bu nedenle EasyOCR sonucu model kalitesi basarisizligi degil, lokal model indirme/runtime engeli olarak isaretlenmelidir.
* `Tesseract`: Sistem binary'si bulunmadigi icin bu fazda calistirilmadi.

## Calisan Baseline'lar

`fast-plate-ocr` ile iki model varyanti denendi:

| Baseline | Model | Crop | OCR Read | Format Valid | Province Valid | Track Vote | Mean OCR Latency | p95 OCR Latency |
|---|---|---:|---:|---:|---:|---|---:|---:|
| POCR-EXP-006-S | `cct-s-v2-global-model` | 613 | 606 | 591 | 591 | 3/3 | 9.258 ms | 10.378 ms |
| POCR-EXP-006-XS | `cct-xs-v2-global-model` | 613 | 604 | 591 | 590 | 3/3 | 1.672 ms | 2.145 ms |

Her iki modelde de uc video icin temporal vote ayni sonucu verdi: `34TC8532`.

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

## Ilk Teknik Yorum

* `cct-xs-v2-global-model`, `cct-s-v2-global-model` ile ayni track-level temporal vote sonucunu uretirken yaklasik 5.5 kat daha dusuk ortalama OCR latency verdi.
* `cct-s-v2-global-model`, yalnizca 2 ek crop'ta OCR read ve 1 ek crop'ta province valid uretmesine ragmen latency maliyeti belirgin derecede daha yuksek.
* Bu nedenle manuel review icin ilk aday `fast-plate-ocr cct-xs-v2-global-model` olmalidir.
* `34TC8532` sonucu gercek plaka ile manuel karsilastirilmadan dogru kabul edilmemelidir.

## Manuel Review Talimati

Kontrol edilecek lokal dosyalar:

* Annotated plate detection videolari: `runs/plate_ocr/POCR-EXP-005-local-smoke/annotated/`
* Plate crop klasorleri: `runs/plate_ocr/POCR-EXP-005-local-smoke/plates/yolo/`
* CCT-S review seed: `runs/plate_ocr/POCR-EXP-006-local-ocr-baselines/manual_review_fastplate.csv`
* CCT-XS review seed: `runs/plate_ocr/POCR-EXP-006-local-ocr-baselines-cct-xs/manual_review_fastplate.csv`

Manual review'da ozellikle su sorular cevaplanmalidir:

* Plaka gorunur mu?
* Plate bbox plaka bolgesine oturuyor mu?
* Temporal vote `34TC8532` gercek plaka ile birebir eslesiyor mu?
* Eslesmiyorsa hata tam okuma hatasi mi, kismi okuma mi, detector crop hatasi mi?
* Duzgun crop varken OCR yaniliyorsa fine-tune veya farkli OCR modeli gerekir mi?

## Karar

* Lokal baseline asamasinda `fast-plate-ocr cct-xs-v2-global-model` manuel review adayi olarak secildi.
* PaddleOCR ve EasyOCR bu fazda kalite nedeniyle degil, lokal kurulum/model indirme engelleri nedeniyle ertelendi.
* Manual review olumluysa OCR fine-tune'a gecmeden once `cct-xs` event/evidence enrichment hattina baglanabilir.
* Manual review olumsuzsa once OCR crop kalitesi ve plate detector crop secimi incelenmeli; sonra plaka OCR fine-tune veya baska OCR baseline'i acilmalidir.

## Cikti Dosyalari

* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-006-local-ocr-baselines/POCR-EXP-006-fast-plate-ocr-summary.json`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-006-local-ocr-baselines-cct-xs/POCR-EXP-006-fast-plate-ocr-summary.json`
* `testing/reports/pocr_exp_006_local_ocr_baselines_fastplate.md`
* `testing/reports/pocr_exp_006_local_ocr_baselines_cct_xs_fastplate.md`
