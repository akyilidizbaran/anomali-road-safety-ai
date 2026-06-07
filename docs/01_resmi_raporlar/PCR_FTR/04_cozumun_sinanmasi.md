# 4. Çözümün Sınanması

## Resmi Beklenti

Modelin nasıl test edildiği kanıtlarla sunulmalıdır. Accuracy, precision, recall, F1, FPS gibi metrikler tablo/grafik halinde verilmelidir.

## Görev Bazlı Metrikler

| Görev | Metrikler |
|---|---|
| Araç tespiti | mAP@0.5, mAP@0.5:0.95, precision, recall, F1 |
| Takip | IDF1, MOTA, ID switch, track stability |
| Plaka | plate mAP, plate recall |
| OCR | plate accuracy, character accuracy, edit distance |
| Hız | MAE, RMSE |
| Şerit | IoU, F1, lane accuracy |
| Hava/görüş | accuracy, macro F1 |
| Cabin risk | F1, precision, recall, confusion matrix |

## Sistem Metrikleri

* Camera preview FPS.
* Pipeline FPS.
* Uçtan uca latency.
* Ortalama inference süresi.
* Model boyutu.
* RAM/CPU/GPU kullanımı.
* Evidence kayıt süresi.

## Çözümümüze Neden Güveniyoruz?

Bu soru yalnız accuracy ile cevaplanmamalıdır. Cevap şu kanıtlarla kurulmalıdır:

* Görev bazlı test metrikleri.
* Demo senaryo sonuçları.
* Event JSON bütünlüğü.
* Evidence paketlerinin denetlenebilirliği.
* Model confidence ve risk score açıklamaları.
* Hız için kalibrasyon/hata ölçümü.
* Görünürlük yetersizliğinde analiz yapmama politikası.

## Sorulacak Noktalar

* Ground truth hız verisi nasıl alınacak?
* Event-level doğruluk için kaç demo senaryosu hazırlanacak?
