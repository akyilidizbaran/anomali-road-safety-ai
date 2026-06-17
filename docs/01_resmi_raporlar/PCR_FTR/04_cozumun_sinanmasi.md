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

## POCR-EXP-005 Plaka Tespiti İlk Sonuçları

YOLO11n tabanlı tek sınıflı plate detector fine-tune koşusu tamamlanmıştır. Bu sonuçlar yalnız plate bbox tespitini kapsar; OCR doğruluğu değildir.

| Model | Split | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---:|---:|---:|---:|
| POCR-EXP-005 | val | 0.9947 | 0.9891 | 0.9948 | 0.8569 |
| POCR-EXP-005 | test | 0.9951 | 0.9907 | 0.9948 | 0.8543 |
| Önceki baseline | test | 0.9726 | 0.9586 | 0.9754 | 0.6089 |

Test split üzerinde `mAP@0.5:0.95` artışı yaklaşık `+0.2454` olarak ölçülmüştür. Bu, plate bbox yerleşim kalitesinde belirgin iyileşme sinyali verir.

Sınırlılık:

* UFPR-ALPR dış benchmark bu koşuda bulunmadığı için skipped.
* Gerçek `Test/video_1-3.mp4` target vehicle ROI smoke/manual review henüz yapılmadı.
* OCR/format doğrulama ayrı deneydir.

Kaynak raporlar:

* `models/experiments/POCR_EXP_005_plate_detector_report.md`
* `testing/reports/pocr_exp_005_plate_detector_ftr_summary.md`

## POCR-EXP-006/007 OCR Baseline İlk Sonuçları

OCR karşılaştırması `POCR-EXP-005` plate detector tarafından üretilen 613 plate crop üzerinde yapılmıştır. Bu sonuçlar manual review öncesi local baseline ve stability testidir; etiketli OCR benchmark veya final plaka doğruluğu iddiası değildir.

| OCR motoru | Crop | OCR read | Format valid | Province valid | Track vote | Mean latency | p95 latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| CCT-S | 613 | 606 | 591 | 591 | 3/3 | 9.258 ms | 10.378 ms |
| CCT-XS | 613 | 604 | 591 | 590 | 3/3 | 1.672 ms | 2.145 ms |
| PaddleOCR | 613 | 538 | 507 | 507 | 3/3 | 54.453 ms | 104.749 ms |
| EasyOCR | 613 | 604 | 413 | 407 | 3/3 | 7.475 ms | 12.223 ms |

Video bazlı CCT-XS sonucu:

| Video | Crop | OCR read | Format valid | Temporal vote | Vote confidence | Mean latency |
|---|---:|---:|---:|---|---:|---:|
| `video_1.mp4` | 206 | 205 | 203 | `34TC8532` | 0.9903 | 1.699 ms |
| `video_2.mp4` | 201 | 197 | 193 | `34TC8532` | 0.9733 | 1.720 ms |
| `video_3.mp4` | 206 | 202 | 195 | `34TC8532` | 0.9052 | 1.599 ms |

`video_3` stability analizi:

| Config | Read / Crop | Vote | İlk beklenen | İlk stabil | Stabil metin | Mean latency |
|---|---:|---|---:|---:|---|---:|
| CCT-XS original | 202/206 | `34TC8532` | 19 | 25 | `34TC8532` | 1.642 ms |
| CCT-XS 2x + CLAHE | 205/206 | `34TC8532` | 18 | 20 | `34TC8532` | 5.564 ms |
| CCT-XS 3x + CLAHE | 205/206 | `34TC8532` | 18 | 17 | `34TC8512` | 5.182 ms |

Karar:

* Aktif OCR baseline CCT-XS olarak sabitlenmiştir.
* CCT-XS fine-tune bu aşamada açılmayacaktır.
* 2x/3x preprocessing varsayılan yapılmayacaktır.
* Event/evidence tarafında tek-frame OCR sonucu değil, temporal stability gate sonrası final vote kullanılacaktır.

Kaynak raporlar:

* `models/experiments/POCR_EXP_006_007_cct_xs_ocr_baseline.md`
* `testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `testing/reports/pocr_exp_007_cct_xs_stability.md`

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
