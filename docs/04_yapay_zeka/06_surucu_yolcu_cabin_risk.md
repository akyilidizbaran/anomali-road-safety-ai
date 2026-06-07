# Sürücü, Yolcu ve Araç İçi Risk Analizi

## Gerçekçilik İlkesi

Dışarıdan bakan telefon kamerası sürücüyü her zaman göremez. Cam yansıması, mesafe, açı, gece ve araç içi karanlık bu görevi zorlaştırır. Bu nedenle sistem koşullu çalışmalıdır.

## Akış

1. Hedef araç tespit edilir.
2. Araç ROI alınır.
3. Ön cam veya yan cam bölgesi çıkarılır.
4. Görünürlük skoru hesaplanır.
5. Görünürlük yeterliyse cabin risk modeli çalışır.
6. Görünürlük yetersizse “analiz güvenilir değil” çıktısı verilir.

## Olası Riskler

* Telefon kullanımı.
* Sigara.
* Emniyet kemeri belirsizliği.
* Dikkat dağınıklığı.
* Yolcu sayısı.
* Görüş engelleyici nesne.

## Metrikler

* Precision.
* Recall.
* F1.
* False positive rate.
* Visibility gating doğruluğu.

## Sorulacak Noktalar

* Kontrollü cabin risk videosu çekilecek mi?
* Bu modül final demo için zorunlu mu?
