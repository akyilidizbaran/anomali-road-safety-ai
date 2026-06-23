# VLM / Llama Arm-State Notu

Tarih: 2026-06-14

Arkadaş ekipten gelen örnek görselde Llama ailesiyle üretilmiş olduğu söylenen
tek-kare açıklamalı overlay görülmüştür. Bu çıktı araştırma açısından değerlidir,
ancak doğrudan pose/arm-state baseline yerine konulamaz.

## Neden Ayrı Değerlendirilecek?

* VLM çıktısı çoğu zaman metin/prompt tabanlı yorumdur; frame-frame keypoint
  sürekliliği garanti etmez.
* Telefon, yorgunluk veya kol durumu iddiası JSON contract'a bağlanmadan risk
  sinyali sayılamaz.
* Tek kare başarısı temporal persistence, false positive ve latency kabul kapısını
  karşılamaz.

## Kullanım Şekli

VLM hattı ancak şu rollerden biriyle açılabilir:

* manual review hızlandırıcı,
* pseudo-label üretici,
* pose/arm-state overlay kalite denetçisi,
* object+arm specialist için challenger.

Runtime baseline olması için gerekli minimum bilgiler:

* kesin model adı ve sürümü,
* prompt,
* input crop politikası,
* deterministik JSON şeması,
* üç-video full-rate veya sampled latency,
* false-positive negatif örnekleri,
* temporal voting yöntemi.

## Ölçüm Hattı

`scripts/benchmarks/run_driver_vlm_arm_state_challenger.py`, local Ollama-style
vision modeline seçili cabin/vehicle crop'larını gönderir ve yalnız JSON cevapları
kabul eder. Parse failure, latency ve state rate ayrı raporlanır.
