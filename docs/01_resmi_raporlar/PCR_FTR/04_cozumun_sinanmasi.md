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

## COND-EXP-001 Kondisyon Profili İlk Sonuçları

İlk kondisyon profili classifier koşusu MobileNetV3-Small ile Google Colab üzerinde tamamlanmıştır. Drive üzerinde `best.pt`, `summary.json`, `history.csv`, `backbone_comparison.csv` ve Markdown özet dosyaları doğrulanmıştır.

| Metrik | Değer |
|---|---:|
| Validation macro-F1 | 0.6578 |
| Test accuracy | 0.7455 |
| Test macro-F1 | 0.6582 |
| Test weighted-F1 | 0.7444 |
| Mean confidence | 0.7540 |

Sınıf bazlı rapor notu:

* `night_low_light` F1 `0.845` ile düşük ışık sinyalinde ilk baseline için güçlü görünmektedir.
* `rain` F1 `0.770` ile kullanılabilir ilk sinyal üretmektedir.
* `fog_low_visibility` F1 `0.200` ve test support `10` olduğu için bu sınıf final raporda güçlü doğruluk iddiası olarak sunulmamalıdır.
* 3 demo dark video üzerinde smoke test çıktısı henüz boş kalmıştır; Drive `Test/video_1.mp4` - `video_3.mp4` yerleşimi tamamlandıktan sonra tekrar çalıştırılmalıdır.

Kaynak rapor:

* `testing/reports/cond_exp_001_condition_classifier_run_review.md`

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
