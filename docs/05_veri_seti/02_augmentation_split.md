# Augmentation ve Split Planı

## Augmentation

Araç/plaka/şerit görevleri için:

* Motion blur.
* Brightness/contrast.
* Rain/fog simulation.
* Perspective transform.
* JPEG compression.
* Random crop.
* Shadow augmentation.

## Dikkat

OCR için fazla agresif augmentation karakter yapısını bozabilir. Şerit için perspective augmentation dikkatli uygulanmalıdır.

## Split Kuralları

* Aynı videodan gelen kareler farklı splitlere karışmamalı.
* Train/validation/test video-level ayrılmalı.
* Kritik olaylar test setinde temsil edilmeli.
* Veri dengesizse class weighting veya oversampling düşünülmeli.

## Sorulacak Noktalar

* Kritik olay sayısı yeterli olacak mı?
* Test seti canlı demo alanından bağımsız olacak mı?
