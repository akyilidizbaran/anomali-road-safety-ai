# POCR-EXP-007 CCT-XS OCR Stability Review

Tarih: `2026-06-17T09:56:38Z`

## Amaç

Bu rapor, video üzerinde geç başlayan OCR davranışının model fine-tune gerektirip gerektirmediğini veya temporal stability gating ile yönetilip yönetilemeyeceğini kontrol eder. Mevcut per-crop OCR çıktıları okunur; OCR yeniden çalıştırılmaz.

## Stabilite Kuralı

* Stabil tekrar sayısı: `3` aynı format-valid/province-valid okuma
* Kayan pencere: `7` OCR crop gözlemi
* Minimum OCR confidence: `0.75`
* Manuel karşılaştırma beklenen plaka: `34TC8532`

## Sonuçlar

| Config | Video | Read / Crop | Vote | İlk Okuma | İlk Beklenen | İlk Stabil | Stabil Metin | Ort. ms |
|---|---|---:|---|---:|---:|---:|---|---:|
| baseline_1x_original | video_3.mp4 | 202/206 | 34TC8532 | 3 | 19 | 25 | 34TC8532 | 1.642 |
| upscale2_original_clahe | video_3.mp4 | 205/206 | 34TC8532 | 2 | 18 | 20 | 34TC8532 | 5.564 |
| upscale3_original_clahe | video_3.mp4 | 205/206 | 34TC8532 | 2 | 18 | 17 | 34TC8512 | 5.182 |

## Yorum

* `first_stable_vote_frame`, `first_expected_plate_frame` değerine yakınsa ilk çözüm fine-tune değildir.
* Upscale yalnız stabil doğru okumayı anlamlı biçimde öne çekiyor ve yanlış erken vote üretmiyorsa promote edilmelidir.
* Upscale erken düşük güvenli/yanlış okumaları artırıyorsa CCT-XS original yol korunmalı ve stability gate kullanılmalıdır.

## Karar

* Bu analiz fine-tune ihtiyacını kanıtlamaz; gecikme uzak/karanlık frame'lerde okunabilirlik sınırına bağlıdır.
* CCT-XS original baseline aktif kalmalıdır.
* Runtime evidence için final OCR değeri, tek frame sonucu değil, stabil tekrar sonrası temporal vote olarak yazılmalıdır.
* Upscale/CLAHE manuel review'da ayrıca izlenebilir; fakat latency artışı ve erken yanlış vote riski nedeniyle varsayılan yapılmamalıdır.
