# Event Fusion ve Storage

## Event Fusion

Farklı model çıktıları tek event nesnesine birleştirilir:

* Vehicle output.
* Tracking output.
* Plate/OCR output.
* Speed output.
* Lane output.
* Cabin risk output.
* Scene output.
* QoD decision.
* Risk score.

## Storage

Saklanacaklar:

* Raw frame referansı.
* Crop image.
* Overlay screenshot.
* Event JSON.
* Explanation text.

## Evidence Integrity

Her event immutable ID almalıdır. Event üzerinde sonradan değişiklik yapılacaksa revision alanı tutulmalıdır.

## Sorulacak Noktalar

* Evidence JSON dosya sistemi mi DB mi?
