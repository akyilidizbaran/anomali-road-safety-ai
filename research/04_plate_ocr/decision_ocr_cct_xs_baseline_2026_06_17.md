# Decision - OCR Baseline CCT-XS v1

Tarih: 2026-06-17

## Karar

Plate OCR tarafında aktif baseline olarak `fast-plate-ocr cct-xs-v2-global-model` kullanılacaktır.

Bu karar, `POCR-EXP-005` YOLO11n plate detector tarafından üretilen 613 plaka crop üzerinde yapılan lokal karşılaştırmaya dayanır. CCT-XS; CCT-S ve PaddleOCR ile aynı track-level temporal vote sonucuna ulaşmış, ancak çok daha düşük latency üretmiştir. EasyOCR bu crop setinde düşük güvenli ve farklı vote'lara kaydığı için aktif aday yapılmamıştır.

## Seçilen OCR Akışı

Runtime MVP akışı:

1. ByteTrack target vehicle seçer.
2. POCR-EXP-005 YOLO11n plate detector hedef araç ROI içinde plaka bbox üretir.
3. Plaka crop, CCT-XS OCR modeline verilir.
4. OCR sonucu Türk plaka regex + il kodu kontrolünden geçer.
5. Track-level temporal voting ile tek-frame hataları bastırılır.
6. Event/evidence JSON içine final OCR sonucu, güven, vote, uyarı ve kaynak referansları yazılır.

## Kararın Dayandığı Sonuçlar

Toplam test kapsamı:

* Video: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
* Target track: 3
* Plate crop: 613
* Plate detector: `POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt`

OCR baseline karşılaştırması:

| Baseline | Model | Crop | OCR read | Format valid | Province valid | Track vote | Mean latency | p95 latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| CCT-S | `cct-s-v2-global-model` | 613 | 606 | 591 | 591 | 3/3 | 9.258 ms | 10.378 ms |
| CCT-XS | `cct-xs-v2-global-model` | 613 | 604 | 591 | 590 | 3/3 | 1.672 ms | 2.145 ms |
| PaddleOCR | `PaddleOCR 2.10 PP-OCRv4 en` | 613 | 538 | 507 | 507 | 3/3 | 54.453 ms | 104.749 ms |
| EasyOCR | `EasyOCR 1.7.2 recognizer-only` | 613 | 604 | 413 | 407 | 3/3 | 7.475 ms | 12.223 ms |

Track-level temporal vote:

| Model | `video_1` | `video_2` | `video_3` |
|---|---|---|---|
| CCT-S | `34TC8532` | `34TC8532` | `34TC8532` |
| CCT-XS | `34TC8532` | `34TC8532` | `34TC8532` |
| PaddleOCR | `34TC8532` | `34TC8532` | `34TC8532` |
| EasyOCR | `04IC0522` | `04IC0522` | `04C0522` |

## Video 3 Stability Kararı

`video_3` için gözlenen davranış karakter karıştırma değil, uzak/karanlık erken frame'lerde okunabilirlik sınırıdır. CCT-XS okuma başladıktan sonra doğru temporal vote'a ulaşır.

Stability analizi:

| Config | Read / Crop | Vote | İlk okuma | İlk beklenen `34TC8532` | İlk stabil vote | Stabil metin | Mean latency |
|---|---:|---|---:|---:|---:|---|---:|
| CCT-XS original | 202/206 | `34TC8532` | 3 | 19 | 25 | `34TC8532` | 1.642 ms |
| CCT-XS 2x + CLAHE | 205/206 | `34TC8532` | 2 | 18 | 20 | `34TC8532` | 5.564 ms |
| CCT-XS 3x + CLAHE | 205/206 | `34TC8532` | 2 | 18 | 17 | `34TC8512` | 5.182 ms |

Bu nedenle CCT-XS için bu aşamada fine-tune açılmayacaktır. Varsayılan akışta upscale/CLAHE de açılmayacaktır. Bunun yerine final event OCR değeri aşağıdaki stabilite kapısından sonra yazılacaktır:

* `stable_count >= 3`
* `window_size = 7`
* `min_confidence >= 0.75`
* `format_valid = true`
* `province_code_valid = true`

## Neden CCT-XS?

* CCT-S ile aynı final temporal vote sonucuna ulaşır.
* PaddleOCR ile aynı final temporal vote sonucuna ulaşır.
* CCT-S'e göre yaklaşık 5.5 kat daha hızlıdır.
* PaddleOCR'a göre yaklaşık 32 kat daha hızlıdır.
* MacBook/local edge runtime için daha uygundur.
* Plate-specific OCR olduğu için genel OCR motorlarına göre plaka crop setinde daha tutarlı davranmıştır.

## Sınırlılıklar

* Bu karar 3 demo video ve 613 crop üzerinde local baseline sonucudur.
* Ground-truth etiketli OCR benchmark değildir.
* `34TC8532` sonucu manuel görsel kontrol ile doğrulanmadan kesin doğru kabul edilmemelidir.
* Modelin Türk plaka domaininde geniş genelleme başarısı henüz kapsamlı OCR dataset benchmark ile kanıtlanmış değildir.
* CCT-XS model lisansı ve model hub bilgisi final rapor/paketleme öncesinde tekrar doğrulanmalıdır.

## Ertelenenler

* CCT-XS fine-tune.
* CRNN/LPRNet/PARSeq gibi özel OCR model eğitimi.
* Türk plaka sentetik OCR veri üretimi.
* PaddleOCR'i runtime default yapmak.
* 2x/3x upscale'ı varsayılan yapmak.

## Etkilediği Yerler

* `docs/04_yapay_zeka/02_plaka_ocr.md`
* `docs/01_resmi_raporlar/PCR_FTR/03_3_cozum_detaylari.md`
* `docs/01_resmi_raporlar/PCR_FTR/04_cozumun_sinanmasi.md`
* `architecture/contracts/model_output_contract.md`
* `testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `testing/reports/pocr_exp_007_cct_xs_stability.md`

## Kaynak Dosyalar

* `testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `testing/reports/pocr_exp_007_cct_xs_stability.md`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-007-cct-xs-stability/pocr_exp_007_cct_xs_stability_summary.csv`
* `runs/plate_ocr/POCR-EXP-007-cct-xs-early-read-review/baseline-percrop/fastplate/video_3_ocr_overlay.mp4`
