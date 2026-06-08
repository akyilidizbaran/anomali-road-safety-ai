# Araştırma 4 - Plaka Tespiti ve Türk Plaka OCR Sistemi

## Amaç

Araç ROI’den plaka bölgesini bulmak, OCR yapmak, Türk plaka formatını doğrulamak ve evidence kartına güvenilir çıktı üretmek.

## Alt Başlıklar

* Vehicle ROI -> plate detector -> OCR mimarisi.
* YOLO tabanlı plate detector.
* PaddleOCR/PP-OCR, EasyOCR, CRNN, Tesseract, TrOCR karşılaştırması.
* Türk plaka format kontrolü.
* Regex ve post-processing.
* Karakter düzeyi hata düzeltme.
* Temporal voting.
* Plaka okunabilirlik skoru.
* Motion blur, düşük ışık, açı, uzaklık problemleri.
* Plate-level accuracy.
* Character-level accuracy.
* Edit distance.
* Türkiye plaka veri seti arama.
* Sentetik Türk plaka üretimi.
* KVKK ve izinli test verisi.

## Başlangıç Format Kararı

Türk plaka format doğrulaması için ilk yaklaşım kural tabanlı olacaktır:

* İl kodu kontrolü: `01`-`81`.
* Harf ve rakam blokları için regex tabanlı kontrol.
* OCR karakter düzeltme ve karıştırılan karakterlerin post-processing'i.
* Aynı track üzerinde temporal voting.
* Düşük güven durumunda plaka değerini zorla kesinleştirmeme; `unknown` veya `low_confidence` çıktısı.

Regex ve veri seti kararı literatür/açık kaynak çalışma araştırması sonrasında kesinleştirilecektir.

## Çıktı

OCR pipeline kararı, format kontrol kuralı ve test metriği seti.
