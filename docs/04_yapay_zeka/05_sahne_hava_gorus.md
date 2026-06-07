# Sahne, Hava, Işık ve Görüş Koşulu Analizi

## Amaç

Görüntü koşullarını sınıflandırarak model güveni, uzman model seçimi ve QoD adaylığını desteklemek.

## Sınıflar

* Açık gündüz.
* Düşük ışık.
* Gece.
* Yağmur.
* Sis/pus.
* Çok düşük görüş.

## Aday Modeller

* ResNet18 baseline.
* MobileNetV3.
* EfficientNet-lite.

## Kullanım

* Düşük görüşte QoD adaylığı.
* OCR ve lane güven skorunu yorumlama.
* Risk skorunda belirsizlik sinyali.
* Uzman model çağrı politikasını değiştirme.

## Metrikler

* Accuracy.
* Macro F1.
* Confusion matrix.

## Sorulacak Noktalar

* Hava/görüş modülü finalde çalışır olacak mı, raporda tasarım olarak mı kalacak?
