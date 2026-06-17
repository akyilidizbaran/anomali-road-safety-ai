# POCR-EXP-006/007 - CCT-XS Plate OCR Baseline Report

Tarih: 2026-06-17

## Durum

`fast-plate-ocr cct-xs-v2-global-model`, plaka OCR için aktif baseline adayı olarak sabitlendi. Bu çalışma plate detector sonrası üretilen plate crop'lar üzerinde OCR okuma, Türk plaka format doğrulama ve track-level temporal voting davranışını ölçer.

Bu rapor final OCR accuracy iddiası kurmaz. Sonuçlar `Test/video_1-3.mp4` üzerinde local smoke/benchmark ve manuel review hazırlığı olarak yorumlanmalıdır.

## Amaç

`POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt` ile üretilen plate crop'lar üzerinde aşağıdaki soruları yanıtlamak:

* İlk runtime OCR baseline hangisi olmalı?
* CCT-S, CCT-XS, PaddleOCR ve EasyOCR arasında latency/doğruluk dengesi nasıl?
* Video 3'te geç okuma davranışı fine-tune gerektiriyor mu?
* Evidence JSON için tek-frame OCR mı, temporal stability gate mi kullanılmalı?

## Girdi

| Alan | Değer |
|---|---|
| Plate detector | `POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt` |
| Detection summary | `models/benchmarks/artifacts/plate_detection/POCR-EXP-005-local-video-smoke-yolo-summary.json` |
| Plate crop kaynağı | `runs/plate_ocr/POCR-EXP-005-local-smoke/plates/yolo/` |
| Video | `video_1.mp4`, `video_2.mp4`, `video_3.mp4` |
| Toplam crop | 613 |
| Target track | 3 |

## Denenen OCR Baseline'ları

| Deney | OCR motoru | Model | Not |
|---|---|---|---|
| POCR-EXP-006-S | fast-plate-ocr | `cct-s-v2-global-model` | Daha büyük CCT varyantı |
| POCR-EXP-006-XS | fast-plate-ocr | `cct-xs-v2-global-model` | Aktif aday |
| POCR-EXP-002 | PaddleOCR | `PaddleOCR 2.10 PP-OCRv4 en` | İkinci kontrol adayı |
| POCR-EXP-003 | EasyOCR | `EasyOCR 1.7.2 recognizer-only` | Bu crop setinde önerilmedi |

## Genel Sonuç Tablosu

| Model | Crop | OCR read | Format valid | Province valid | Track vote | Mean OCR latency | p95 OCR latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| CCT-S | 613 | 606 | 591 | 591 | 3/3 | 9.258 ms | 10.378 ms |
| CCT-XS | 613 | 604 | 591 | 590 | 3/3 | 1.672 ms | 2.145 ms |
| PaddleOCR | 613 | 538 | 507 | 507 | 3/3 | 54.453 ms | 104.749 ms |
| EasyOCR | 613 | 604 | 413 | 407 | 3/3 | 7.475 ms | 12.223 ms |

## Video Bazlı CCT-XS Sonucu

| Video | Crop | OCR read | Format valid | Province valid | Temporal vote | Vote conf | Mean latency |
|---|---:|---:|---:|---:|---|---:|---:|
| `video_1.mp4` | 206 | 205 | 203 | 203 | `34TC8532` | 0.9903 | 1.699 ms |
| `video_2.mp4` | 201 | 197 | 193 | 193 | `34TC8532` | 0.9733 | 1.720 ms |
| `video_3.mp4` | 206 | 202 | 195 | 194 | `34TC8532` | 0.9052 | 1.599 ms |

## Stability Analizi

`video_3` için CCT-XS original, CCT-XS 2x+CLAHE ve CCT-XS 3x+CLAHE karşılaştırılmıştır.

| Config | Read / Crop | Vote | İlk okuma | İlk beklenen | İlk stabil | Stabil metin | Mean latency |
|---|---:|---|---:|---:|---:|---|---:|
| CCT-XS original | 202/206 | `34TC8532` | 3 | 19 | 25 | `34TC8532` | 1.642 ms |
| CCT-XS 2x + CLAHE | 205/206 | `34TC8532` | 2 | 18 | 20 | `34TC8532` | 5.564 ms |
| CCT-XS 3x + CLAHE | 205/206 | `34TC8532` | 2 | 18 | 17 | `34TC8512` | 5.182 ms |

Yorum:

* 2x upscale yalnız sınırlı erken okuma kazancı sağlar.
* 2x/3x latency maliyetini yükseltir.
* 3x erken stabil vote'u yanlış adaya kaydırabildiği için varsayılan yapılmamalıdır.
* Gecikme OCR karakter karıştırması değil, uzak/karanlık frame okunabilirliği kaynaklıdır.

## Runtime Kararı

Aktif OCR baseline:

```text
fast-plate-ocr(cct-xs-v2-global-model, device=cpu)
```

Event/evidence tarafında OCR metni yalnız stabilite kapısından sonra final alanına yazılmalıdır:

| Parametre | Değer |
|---|---:|
| `stable_count` | 3 |
| `window_size` | 7 |
| `min_confidence` | 0.75 |
| `format_valid` | true |
| `province_code_valid` | true |

Tek-frame OCR sonucu, yalnız aday/ham gözlem olarak saklanmalıdır. Final plaka değeri track-level temporal vote ile üretilmelidir.

## Fine-Tune Kararı

Bu aşamada CCT-XS fine-tune açılmayacaktır.

Gerekçe:

* Gözlenen sorun sistematik karakter karıştırma değildir.
* Okunabilir frame başladıktan sonra CCT-XS doğru temporal vote üretmektedir.
* 2x/3x preprocessing kazancı sınırlıdır ve latency/yanlış erken vote riski getirir.
* OCR fine-tune için etiketli plate crop + metin ground truth veri seti gerekir; mevcut 3 demo video yeterli değildir.

Fine-tune yeniden açılacak koşullar:

* Net ve yeterli çözünürlüklü crop'larda sistematik karakter karışıklığı görülürse.
* Yeni test videolarında CCT-XS ve PaddleOCR sürekli farklı doğru/yanlış sonuçlara ayrılırsa.
* Track-level temporal voting hatalı final vote üretirse.
* Türk plaka formatına özgü sistematik hata pattern'i yeterli etiketli veriyle kanıtlanırsa.

## Çıktılar

Raporlar:

* `testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `testing/reports/pocr_exp_007_cct_xs_stability.md`
* `testing/reports/pocr_exp_007_cct_xs_baseline_percrop_fastplate.md`
* `testing/reports/pocr_exp_007_cct_xs_upscale2_clahe_fastplate.md`
* `testing/reports/pocr_exp_007_cct_xs_upscale3_clahe_fastplate.md`

Küçük artifactler:

* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-007-cct-xs-stability/pocr_exp_007_cct_xs_stability_summary.json`
* `models/benchmarks/artifacts/plate_ocr/POCR-EXP-007-cct-xs-stability/pocr_exp_007_cct_xs_stability_summary.csv`

Manuel video review çıktıları Git'e eklenmez:

* `runs/plate_ocr/POCR-EXP-006-manual-video-review/`
* `runs/plate_ocr/POCR-EXP-007-cct-xs-early-read-review/`

## Sonraki Adım

1. CCT-XS stability gate'i event/evidence enrichment script'ine bağla.
2. Event JSON içinde `ocr_observations`, `temporal_vote`, `stability_gate` ve `final_ocr_status` alanlarını üret.
3. Manual review sonucu doğruysa OCR fine-tune backlog'da kalsın; sıradaki AI modülüne veya evidence package zenginleştirmeye geç.
