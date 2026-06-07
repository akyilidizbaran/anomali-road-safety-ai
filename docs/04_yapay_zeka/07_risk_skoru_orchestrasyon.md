# Risk Skoru ve Uzman Model Orkestrasyonu

## Amaç

Model çıktılarından tek bir olay risk skoru üretmek ve hangi uzman modellerin çalışacağını belirlemek.

## Risk Seviyeleri

| Skor | Seviye |
|---:|---|
| 0.00-0.30 | Düşük |
| 0.30-0.60 | Orta |
| 0.60-0.80 | Yüksek |
| 0.80-1.00 | Kritik |

## Risk Sinyalleri

* Araç tespit güveni.
* Track stability.
* Plaka okunabilirliği.
* Şerit ihlali olasılığı.
* Hız aykırılığı.
* Cabin risk skoru.
* Görüş koşulu.
* Model belirsizliği.
* Olay sürekliliği.

## Başlangıç Politikası

Rule-based skor sistemi kullanılabilir. Daha sonra öğrenilebilir risk modeli geliştirilebilir.

## Uzman Model Seçimi

Örnek:

* OCR güveni düşük ama plaka kritik: Plate OCR + QoD candidate.
* Şerit yakınlığı: Lane expert + tracking window.
* Hız şüphesi: Speed estimation + calibration check.
* Düşük görüş: Scene model + QoD candidate.

## Sorulacak Noktalar

* Threshold değerleri demo sırasında ayarlanabilir olacak mı?
