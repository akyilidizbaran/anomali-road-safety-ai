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

## Güncel Baseline Kararı

2026-06-17 itibarıyla plaka/OCR hattı aşağıdaki şekilde sabitlenmiştir:

* Plate detector: `POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt`.
* OCR baseline: `fast-plate-ocr cct-xs-v2-global-model`.
* OCR ikinci kontrol adayı: `PaddleOCR 2.10 PP-OCRv4 en`.
* EasyOCR mevcut crop setinde önerilen aday değildir.
* CCT-XS fine-tune bu aşamada açılmayacaktır.

Bu kararın gerekçesi CCT-XS'in CCT-S ve PaddleOCR ile aynı track-level temporal vote sonucuna ulaşırken çok daha düşük latency üretmesidir. CCT-XS ortalama OCR latency `1.672 ms`, CCT-S `9.258 ms`, PaddleOCR `54.453 ms` olarak ölçülmüştür.

## Temporal Stability Gate

Final event/evidence plaka metni tek frame OCR sonucu olarak yazılmamalıdır. Track boyunca gelen OCR gözlemleri aşağıdaki kapıdan geçmelidir:

| Parametre | Değer |
|---|---:|
| `stable_count` | 3 |
| `window_size` | 7 |
| `min_confidence` | 0.75 |
| `format_valid` | true |
| `province_code_valid` | true |

Bu kural, özellikle uzak/karanlık erken frame'lerde oluşan düşük güvenli veya yanlış erken OCR adaylarının final evidence değerine taşınmasını önler.

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

`video_3` incelemesi, mevcut problem tipinin karakter karıştırma değil, uzak/karanlık erken frame okunabilirliği olduğunu göstermiştir. CCT-XS original akışta ilk doğru plaka okuması frame `19`, ilk stabil temporal vote frame `25`te oluşmuştur. 2x/3x preprocessing küçük erken okuma kazancı sağlasa da latency ve yanlış erken vote riski nedeniyle varsayılan yapılmamıştır.

## Metrikler

* Plate detection mAP.
* Plate recall.
* Character accuracy.
* Full plate accuracy.
* Edit distance.

## Sorulacak Noktalar

* Yeni videolarda CCT-XS sistematik karakter karıştırması yapıyor mu?
* Track-level temporal voting hatalı final vote üretirse OCR fine-tune için hangi etiketli crop veri seti kullanılacak?
* Yerel Türk plaka verisi toplanacaksa KVKK/izin/saklama politikası nasıl uygulanacak?
* Sentetik Türk plaka üretimi hangi aşamada açılacak?
