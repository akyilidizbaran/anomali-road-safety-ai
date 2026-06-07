# Plaka Tespiti ve Türk Plaka OCR

## Amaç

Hedef araç ROI’sinden plaka bölgesini bulmak, OCR ile metin okumak, Türk plaka formatını doğrulamak ve evidence kartına güven skorlarıyla eklemek.

## Önerilen Mimari

1. Araç bbox alınır.
2. Vehicle ROI crop çıkarılır.
3. Plate detector çalışır.
4. Plate crop OCR sistemine verilir.
5. OCR sonucu format post-processing’den geçer.
6. Temporal voting ile çoklu frame sonucu birleştirilir.

## Türk Plaka Format Kontrolü

Örnek format:

```text
^[0-9]{2}[A-Z]{1,3}[0-9]{2,4}$
```

Boşluk ve tire varyasyonları normalize edilmelidir.

## Zorluklar

* Motion blur.
* Düşük ışık.
* Plaka açısı.
* Uzaklık.
* Kirli veya kapalı plaka.
* Türk plaka veri seti eksikliği.

## Metrikler

* Plate detection mAP.
* Plate recall.
* Character accuracy.
* Full plate accuracy.
* Edit distance.

## Sorulacak Noktalar

* Yerel Türk plaka verisi toplanacak mı?
* Sentetik Türk plaka üretimi yapılacak mı?
