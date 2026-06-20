# SPEED-EXP-006B Wide-Subset Calibration Plan

Bu plan, FTR teslim hedefi ve mevcut hız deneyleri birlikte değerlendirilerek hazırlanmıştır.

## Karar

Hız modülü FTR `results.json` şemasında zorunlu alan değildir. Bu nedenle hız çalışması,
Docker/FTR ana teslim hattını bloklamamalıdır. Ancak proje raporu ve evidence katmanı için
mutlak km/s iddiası kurulacaksa, yalnız 3 araç paketli sanity check yeterli değildir.

Bu yüzden sıradaki hız adımı:

```text
SPEED-EXP-006B — VS13 wide-subset calibration / lightweight training
```

olarak belirlenmiştir.

## Neden 006B?

`SPEED-EXP-006` outhealth koşusu teknik olarak sağlıklı çalışmıştır:

* 18 video işlenmiştir.
* Tüm videolarda tracking `ok` dönmüştür.
* En iyi global-scale test MAE `8.07 km/h` seviyesindedir.

Ancak hata dağılımı homojen değildir. Özellikle orta hızlarda yaklaşık `21 km/h` seviyesine
çıkan over-estimation görülmüştür. Bu nedenle tek global kalibrasyonla hız modülünü kapatmak
bilimsel olarak savunulabilir değildir.

## FTR ile İlişki

FTR için öncelik hâlâ şudur:

1. `results.json` adapter/validator.
2. Araç bilgisi: tip, plaka, renk, confidence.
3. Tespitler: sürücü eylemi, nesneler, yolcular.
4. Docker runtime.

Hız çalışması bu sırayı değiştirmez. `006B` yalnız şu çıktılar için yapılır:

* raporda hız yaklaşımını ölçülebilir göstermek,
* speed/evidence katmanını savunulabilir hale getirmek,
* başarısız olursa hızın `relative/support evidence` kalacağını netleştirmek.

## 006B Deney Kapsamı

Notebook:

```text
notebooks/SPEED_EXP_006B_VS13_Wide_Subset_Speed_Calibration_Colab.ipynb
```

Ana farklar:

* VS13 içindeki 13 araç paketini destekler.
* Varsayılan olarak her araçtan dengeli `12` video seçer.
* `MAX_VIDEOS_PER_VEHICLE = None` yapılırsa seçili paketlerdeki tüm MP4 dosyaları kullanılabilir.
* Sabit train/val/test yerine leave-one-vehicle-out cross-validation kullanır.
* Global, lineer, robust ve hafif tabular regressor kalibrasyonlarını karşılaştırır.

## Eğitim / Kalibrasyon Kapsamı

Bu notebook yeni bir görüntü backbone'u eğitmez. Eğitilen veya optimize edilen şey hız
kalibrasyon katmanıdır.

### Birinci Aşama

Her parametre kombinasyonu için:

* `global_alpha`
* `linear_raw`
* `huber_raw`

kalibrasyonları denenir.

Optimize edilen parametreler:

* horizontal FOV varsayımı
* araç yüksekliği prior'ı
* moving-average window
* max segment speed gate
* track başı/sonu trim oranı
* minimum bbox height ratio

### İkinci Aşama

En iyi parametre adaylarında hafif tabular regressor denenir:

* `ridge_features`
* `huber_features`
* `random_forest_features`
* `gradient_boosting_features`

Feature set:

* raw bbox speed
* candidate confidence
* speed CV
* selected observation count
* mean detection confidence
* valid segment count
* valid segment ratio

## Başarı Kriteri

Bu deneyden sonra iki olası karar vardır:

1. Leave-one-vehicle-out MAE/RMSE makul ve araçlar arasında stabil ise:
   `dataset-calibrated approximate speed candidate` olarak raporlanır.
2. Hata araç, hız aralığı veya görüntü segmentine bağlı yüksek kalırsa:
   hız modülü FTR için `relative/support evidence` olarak kalır.

## Çıktılar

Notebook Drive altında şu dosyaları üretir:

* `vs13b_first_stage_loo_metrics.csv`
* `vs13b_first_stage_loo_predictions.csv`
* `vs13b_second_stage_feature_model_metrics.csv`
* `vs13b_second_stage_feature_model_predictions.csv`
* `vs13b_combined_calibration_metrics.csv`
* `vs13b_best_loo_predictions.csv`
* `speed_exp_006b_vs13_wide_subset_calibration_summary.json`
* plot klasörü

## Sonraki Karar

006B sonuçları iyi çıkarsa hız modülü raporda yaklaşık kalibre hız adayı olarak anlatılır.
İyi çıkmazsa hız konusu kapatılır ve FTR ana işlerine dönülür.
