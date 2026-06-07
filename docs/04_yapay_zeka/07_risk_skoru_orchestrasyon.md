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

* Ortam/sahne bağlamı.
* Hava, ışık ve görüş kalitesi.
* Araç tespit güveni.
* Track stability.
* Plaka okunabilirliği.
* Şerit ihlali olasılığı.
* Hız aykırılığı.
* Cabin risk skoru.
* Genel yol durumu.
* Araç dışı kullanıcı/yaya yakınlığı.
* Model belirsizliği.
* Olay sürekliliği.

## Başlangıç Politikası

Rule-based skor sistemi kullanılabilir. Daha sonra öğrenilebilir risk modeli geliştirilebilir.

## Uzman Model Seçimi

Uzman model seçimi context-gated routing politikasına göre yapılmalıdır. Ortam/sahne analizi doğrudan alarm üretmez; model güveni, QoD adaylığı ve hangi uzmanların çağrılacağını etkileyen bağlam sinyalidir.

Detaylı politika: `docs/04_yapay_zeka/11_context_gated_model_routing.md`

Örnekler:

* OCR güveni düşük ama plaka kritik: Plate OCR + QoD candidate.
* Şerit yakınlığı: Lane expert + tracking window.
* Hız şüphesi: Speed estimation + calibration check.
* Düşük görüş: Scene model + QoD candidate.
* Yaya/bisikletli yakınlığı: External user risk analysis + critical window.

## Normal ve Kritik Mod Ayrımı

Normal modda tüm araçlar hafif detection/tracking hattıyla izlenir. Kritik modda yalnız riskli/hedef araç üzerinde ağır uzman modeller çağrılır. Bu ayrım latency ve kaynak kullanımını kontrol eder.

## Sorulacak Noktalar

* Threshold değerleri demo sırasında ayarlanabilir olacak mı?
