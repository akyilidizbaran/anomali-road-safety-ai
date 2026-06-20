# Speed Module Phase Lock - 2026-06-20

## Karar

Hız kestirimi modülü bu faz için kilitlenmiştir.

Bu karar, hız çıktısının tamamen bırakıldığı anlamına gelmez. Hız artık FTR ana teslimini
bloklamayan, event/evidence içinde kullanılabilecek **yaklaşık ve destekleyici hız sinyali**
olarak korunacaktır.

## Kilitlenen Çıktı Dili

| Alan | Kilitlenen ifade |
|---|---|
| Hız modu | `dataset_calibrated_approximate_candidate` |
| Kullanım yeri | event/evidence destek sinyali, risk yorumlama, slalom/motion support |
| Rapor dili | kontrollü veri setinde kalibre edilmiş yaklaşık hız adayı |
| FTR etkisi | FTR `results.json` şemasını bloklamaz; hız alanı yazılmaz |
| Yasak iddia | kesin km/s, hukuki/cezai hız ölçümü, tek frame'den güvenilir hız |

## Neden Kilitledik?

1. VS13 üzerinde geniş değerlendirme tamamlandı.
   * 13 araç paketi.
   * 156 video.
   * Leave-one-vehicle-out cross-validation.
   * En iyi sonuç: `huber_features`.
   * MAE `2.7088 km/h`, RMSE `3.4750 km/h`.

2. Lokal 3 demo videoda trend korundu.
   * `video_1` ve `video_2` düşük hız bandında kaldı.
   * `video_3` daha hızlı video olarak ayrıştı.
   * Bu test ground-truth hız doğrulaması değil, transfer smoke/trend kontrolüdür.

3. Daha fazla tuning şu anda düşük getirili.
   * Lokal 3 videoda gerçek hız etiketi yok.
   * Ek tuning, gerçek doğruluğu kanıtlamak yerine yalnız bu 3 videoya iyi görünen grafik
     üretme riski taşır.
   * FTR ana hedeflerinde araç bilgisi, plaka, renk, sürücü eylemi, nesne/yolcu ve Docker
     contract daha önceliklidir.

## Benchmark Tarafında Önce / Sonra

`SPEED-EXP-006`, 3 araç paketli ilk VS13 sanity check idi. `SPEED-EXP-006B`, 13 araç ve
leave-one-vehicle-out değerlendirme ile aynı fikri daha sağlam test etti.

| Aşama | Veri | Yöntem | MAE | RMSE | Yorum |
|---|---:|---|---:|---:|---|
| `SPEED-EXP-006` | 18 video / 3 araç | `global_alpha` | `8.07 km/h` test | `12.29 km/h` test | Pipeline sağlıklı ama orta hızlarda yüksek hata var |
| `SPEED-EXP-006` patch analizi | 18 video / 3 araç | `linear_raw` | `7.59 km/h` test | `10.43 km/h` test | Küçük iyileşme, fakat hâlâ kapanış için zayıf |
| `SPEED-EXP-006B` | 156 video / 13 araç | `linear_raw` | `3.0852 km/h` LOO | `3.7100 km/h` LOO | Geniş subset ile raw kalibrasyon güçlendi |
| `SPEED-EXP-006B` locked | 156 video / 13 araç | `huber_features` | `2.7088 km/h` LOO | `3.4750 km/h` LOO | Bu faz için raporlanabilir yaklaşık hız adayı |

## Demo Videolarda Önce / Sonra

Lokal 3 video için ground-truth hız yoktur. Bu tablo doğruluk değil, aynı pipeline'ın ürettiği
trend ve çıktı değişimini gösterir.

| Video | Önceki çıktı: `005A/005D` | 006B transfer çıktı | Değişim | Kilit yorumu |
|---|---:|---:|---:|---|
| `video_1.mp4` | `2.64 km/h`, relative `normal` | `3.53 km/h` | `+0.89 km/h` | Düşük hız bandı korunuyor |
| `video_2.mp4` | `2.33 km/h`, relative `normal` | `3.20 km/h` | `+0.87 km/h` | Düşük hız bandı korunuyor |
| `video_3.mp4` | `15.06 km/h`, relative `fast` | `16.23 km/h` | `+1.16 km/h` | Daha hızlı video ayrışıyor |

## Confidence Yorumu

| Kaynak | Confidence anlamı | Kilit kararı |
|---|---|---|
| `005A` | bbox geometry sinyalinin iç stabilitesi | Ground-truth doğruluk değildir |
| `005D` | relative + plate + bbox sinyal agreement skoru | Evidence destek skorudur |
| `006B demo transfer` | 006B best parametrelerinin lokal timeline üzerinde kararlı çalışması | Transfer smoke confidence olarak yorumlanır |
| `006B VS13` | kontrollü bilinen hızlı veri üzerinde LOO hata metriği | Raporlanabilir ana doğrulama kaynağıdır |

## Kilitlenen Artifact'ler

| Tür | Dosya |
|---|---|
| Geniş subset review | `testing/reports/speed_exp_006b_wide_subset_calibration_review.md` |
| Demo transfer raporu | `testing/reports/speed_exp_006b_demo_transfer.md` |
| Demo transfer summary | `models/benchmarks/artifacts/speed/SPEED-EXP-006B-demo-transfer/speed_exp_006b_demo_transfer_summary.json` |
| Demo transfer timeseries | `models/benchmarks/artifacts/speed/SPEED-EXP-006B-demo-transfer/speed_exp_006b_demo_transfer_timeseries.csv` |
| Ana hız dokümanı | `docs/04_yapay_zeka/03_hiz_kestirimi.md` |
| Aktif Colab notebook | `notebooks/SPEED_EXP_006B_VS13_Wide_Subset_Speed_Calibration_Colab.ipynb` |

## Bundan Sonra Hız İçin Ne Yapılmayacak?

Bu fazda aşağıdakiler yapılmayacak:

* Yeni speed dataset arayışıyla FTR ana işlerinin bloklanması.
* 3 lokal demo videoya özel overfit/tuning.
* Kesin hız iddiası üreten event alanları.
* FTR `results.json` içine resmi olmayan hız alanı ekleme.

## Opsiyonel Future Scope

Zaman kalırsa veya final sonrası daha güçlü hız çalışması istenirse:

1. `Cell 10B` ile `speed_exp_006b_final_huber_features.joblib` export edilir.
2. Lokal inference script'i gerçek `.joblib` artifact'iyle tekrar çalıştırılır.
3. Saha demosunda ölçülü kısa referans segment veya radar/GPS ground-truth ile 10-20 video
   toplanır.
4. `SPEED-EXP-006C` segment selector diagnostics açılır.

Bu maddeler mevcut FTR fazı için zorunlu değildir.
