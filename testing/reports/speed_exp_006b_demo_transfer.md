# SPEED-EXP-006B Demo Transfer Smoke Test

Bu rapor, VS13 üzerinde seçilen `SPEED-EXP-006B` en iyi geometry parametrelerinin yerel 3 demo videoya uygulanmasını özetler.

## Kritik Sınır

006B Colab koşusu `huber_features` metriklerini üretmiştir; çıktı notebook'unda final sklearn
model artifact'i export edilmemiştir. Bu nedenle bu lokal koşu, öğrenilmiş `huber_features`
modelinin birebir inference'ı değil; 006B best geometry parametrelerinin transfer smoke test'idir.

Aktif Colab notebook'a sonradan `Cell 10B` final model export hücresi eklenmiştir. Notebook
tekrar çalıştırılırsa `speed_exp_006b_final_huber_features.joblib` artifact'i üretilebilir.

## 006B Referans Sonucu

* En iyi yöntem: `huber_features`
* VS13 LOO MAE: `2.7088 km/h`
* VS13 LOO RMSE: `3.475 km/h`
* VS13 P90 absolute error: `5.9034 km/h`

## Demo Transfer Sonuçları

| Video | 005A km/h | 006B transfer km/h | 006B median km/h | Conf | Valid segments | Speed CV | Plot |
|---|---:|---:|---:|---:|---:|---:|---|
| `video_1.mp4` | 2.640442 | 3.526502 | 3.471962 | 0.6994 | 340/341 | 1.238415 | `runs/speed/SPEED-EXP-006B-demo-transfer/plots/video_1_speed_006b_transfer.png` |
| `video_2.mp4` | 2.334246 | 3.204902 | 3.152261 | 0.6974 | 336/340 | 1.622159 | `runs/speed/SPEED-EXP-006B-demo-transfer/plots/video_2_speed_006b_transfer.png` |
| `video_3.mp4` | 15.064621 | 16.227622 | 15.163884 | 0.6985 | 282/284 | 0.678591 | `runs/speed/SPEED-EXP-006B-demo-transfer/plots/video_3_speed_006b_transfer.png` |

## Yorum

* Bu test, bizim üç videoda hız eğrisinin davranışını görmek içindir; ground-truth hız yoktur.
* 006B transfer değerleri raporda `dataset_calibrated_parameter_transfer` veya `support_evidence` olarak anılmalıdır.
* Final `huber_features` modelinin birebir lokal inference'ı istenirse aktif Colab notebook'taki `Cell 10B` tekrar çalıştırılmalı ve `.joblib` artifact'i lokal teste alınmalıdır.
* Demo videoda GT hız bulunmadığı için grafiklerin amacı anomali/pik, trend ve confidence kontrolüdür.

## Üretilen Çıktılar

* Summary JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-006B-demo-transfer/speed_exp_006b_demo_transfer_summary.json`
* Timeseries CSV: `models/benchmarks/artifacts/speed/SPEED-EXP-006B-demo-transfer/speed_exp_006b_demo_transfer_timeseries.csv`
* Summary plot: `runs/speed/SPEED-EXP-006B-demo-transfer/plots/speed_006b_demo_transfer_comparison.png`
