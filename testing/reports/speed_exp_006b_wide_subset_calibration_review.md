# SPEED-EXP-006B Wide-Subset Calibration Review

## Durum

`SPEED_EXP_006B_VS13_Wide_Subset_Speed_Calibration_Colab_healthfinished.ipynb`
çıktısı incelendi. Notebook hatasız tamamlandı; `KeyError: split` problemi bu koşuda tekrar
görülmedi.

Bu çalışma yeni bir neural hız backbone'u eğitmez. Mevcut tek kamera + YOLO + ByteTrack +
bbox-geometry hız adayını, VS13 bilinen hızlı videolar üzerinde kalibrasyon/regresyon katmanı
ile ölçer.

## Veri ve Değerlendirme

| Alan | Sonuç |
|---|---:|
| VS13 araç paketi | 13 |
| Video sayısı | 156 |
| Araç başına video | 12 |
| GT hız aralığı | yaklaşık 30-105 km/h |
| Değerlendirme | leave-one-vehicle-out cross-validation |
| İlk aşama grid | 2160 parametre konfigürasyonu |
| İkinci aşama feature model | top 20 parametre konfigürasyonu |

Araç paketleri:

`CitroenC4Picasso`, `KiaSportage`, `Mazda3`, `MercedesAMG550`, `MercedesGLA`,
`NissanQashqai`, `OpelInsignia`, `Peugeot208`, `Peugeot3008`, `Peugeot307`,
`RenaultCaptur`, `RenaultScenic`, `VWPassat`.

## En İyi Sonuç

En iyi model `huber_features` olarak seçildi.

| Metrik | Değer |
|---|---:|
| `loo_mae_kmh` | 2.7088 |
| `loo_rmse_kmh` | 3.4750 |
| `loo_median_abs_error_kmh` | 2.1109 |
| `loo_p90_abs_error_kmh` | 5.9034 |
| `loo_mean_rel_error_pct` | 4.0835 |

En iyi parametreler:

| Parametre | Değer |
|---|---:|
| `horizontal_fov_deg` | 60.0 |
| `vehicle_height_m` | 1.5 |
| `moving_average_window` | 9 |
| `max_segment_speed_kmh` | 140.0 |
| `segment_trim_fraction` | 0.0 |
| `min_bbox_height_ratio` | 0.1 |

## Baseline'a Göre İyileşme

Birinci aşama en iyi raw kalibrasyon sonucu `linear_raw` idi:

| Model | MAE | RMSE | Median AE | P90 AE | Mean Relative Error |
|---|---:|---:|---:|---:|---:|
| `linear_raw` | 3.0852 | 3.7100 | 2.8369 | 5.6488 | 4.7456% |
| `huber_features` | 2.7088 | 3.4750 | 2.1109 | 5.9034 | 4.0835% |

`huber_features`, MAE tarafında yaklaşık `0.38 km/h` iyileşme sağlar. Bu yaklaşık `12.2%`
MAE azalımıdır. P90 hata `linear_raw` sonucuna göre biraz daha yüksektir; bu nedenle model
tek başına hukuki/cezai hız ölçümü gibi sunulmamalıdır.

## Üretilen Drive Çıktıları

Colab çıktıları Drive altında şu konumlara yazıldı:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/vs13b_wide_subset_manifest.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/vs13b_first_stage_loo_metrics.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/vs13b_first_stage_loo_predictions.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/vs13b_combined_calibration_metrics.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/vs13b_best_loo_predictions.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/speed_exp_006b_vs13_wide_subset_calibration_summary.json
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/speed_exp_006b_vs13_wide_subset_calibration_report.md
/content/drive/MyDrive/anomali-road-safety-ai/runs/speed/SPEED-EXP-006B-VS13-wide-subset-calibration/plots/
```

## Yorum

Bu sonuç, önceki 3 araçlık `SPEED-EXP-006` sanity check'e göre çok daha güçlüdür. 13 araç
paketi ve leave-one-vehicle-out değerlendirme, modelin yalnız tek araç/paket üzerinde ezber
yapmadığını göstermeye daha yakındır.

Buna rağmen sonuç şu şekilde sınırlandırılmalıdır:

* Bu yöntem tek frame'den hız ölçümü değildir; video boyunca track/bbox zaman serisi kullanır.
* Sonuç kontrollü VS13 veri yapısında geçerlidir; karanlık yol kenarı demo videosuna birebir
  transfer garantisi vermez.
* FTR resmi `results.json` şeması hız alanı istemez; hız bu fazda ana puanlanan çıktı değildir.
* Hız çıktısı event/evidence içinde `dataset_calibrated_approximate_candidate` veya
  `support_evidence` olarak tutulmalıdır.

## Karar

`SPEED-EXP-006B` mevcut faz için başarılı kabul edilebilir. Hız modülü artık raporda
“VS13 üzerinde kalibre edilmiş yaklaşık hız adayı” olarak anlatılabilir.

FTR ana teslim hattını daha fazla hız deneyiyle bloklamamak gerekir. Sonraki mühendislik
önceliği:

1. FTR `results.json` adapter/validator.
2. Root Dockerfile + inference entrypoint.
3. Aktif vehicle/plate/OCR çıktılarının FTR contract'ına bağlanması.

`SPEED-EXP-006C` yalnız zaman kalırsa hata segmentlerini incelemek için açılmalıdır; zorunlu
sonraki adım değildir.
