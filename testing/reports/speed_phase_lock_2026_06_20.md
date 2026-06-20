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

## VS13 Genel Performans Karşılaştırması

Hız modülünün ana doğrulama kaynağı 3 lokal demo video değildir. Lokal videolarda ground-truth
hız olmadığı için bu videolar yalnız transfer/trend smoke test olarak kullanılabilir. Genel
performans kararı, bilinen hız etiketleri bulunan VS13 veri seti üzerinde yapılan kontrollü
kalibrasyon deneylerinden gelir.

`SPEED-EXP-006`, 3 araç paketli ilk VS13 sanity check idi. `SPEED-EXP-006B`, 13 araç ve
156 video üzerinde leave-one-vehicle-out değerlendirme ile aynı fikri daha sağlam test etti.

| Aşama | Veri | Değerlendirme | Yöntem | MAE | RMSE | Median AE | P90 AE | Mean rel. error | Yorum |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| `SPEED-EXP-006` | 18 video / 3 araç | train/val/test | `global_alpha` | `8.07 km/h` test | `12.29 km/h` test | `-` | `-` | `12.67%` test | Pipeline sağlıklı ama orta hızlarda yüksek hata var |
| `SPEED-EXP-006` patch analizi | 18 video / 3 araç | test | `linear_raw` | `7.59 km/h` | `10.43 km/h` | `-` | `-` | `-` | Küçük iyileşme, fakat hâlâ kapanış için zayıf |
| `SPEED-EXP-006B` first-stage | 156 video / 13 araç | leave-one-vehicle-out | `linear_raw` | `3.0852 km/h` | `3.7100 km/h` | `2.8369 km/h` | `5.6488 km/h` | `4.7456%` | Geniş subset ile raw kalibrasyon güçlendi |
| `SPEED-EXP-006B` alternative | 156 video / 13 araç | leave-one-vehicle-out | `ridge_features` | `2.7128 km/h` | `3.4733 km/h` | `2.2855 km/h` | `6.0888 km/h` | `4.1510%` | Final modele çok yakın güçlü alternatif |
| `SPEED-EXP-006B` alternative | 156 video / 13 araç | leave-one-vehicle-out | `huber_features`, `vehicle_height=1.7` | `2.7127 km/h` | `3.5042 km/h` | `2.1979 km/h` | `5.9821 km/h` | `4.0681%` | Boy varsayımı değişse de performans kararlı |
| `SPEED-EXP-006B` locked | 156 video / 13 araç | leave-one-vehicle-out | `huber_features` | `2.7088 km/h` | `3.4750 km/h` | `2.1109 km/h` | `5.9034 km/h` | `4.0835%` | Bu faz için raporlanabilir yaklaşık hız adayı |

VS13 karşılaştırmasının yorumu:

* 006B sonucu yalnız 3 demo video üzerinde üretilmiş bir sonuç değildir; 13 araç paketli,
  156 videoluk kontrollü bilinen-hız benchmark sonucudur.
* İlk sanity check'teki `8.07 km/h` test MAE, geniş subset ve robust feature kalibrasyonu ile
  `2.7088 km/h` LOO MAE seviyesine düştü.
* RMSE `12.29 km/h` seviyesinden `3.4750 km/h` seviyesine indi. Bu, büyük hata piklerinin
  belirgin biçimde azaldığını gösterir.
* `ridge_features` ve `huber_features` birbirine çok yakındır. `huber_features`, daha düşük MAE
  ve median AE verdiği ve robust regression davranışı sağladığı için kilit model olarak seçildi.
* P90 hata hâlâ yaklaşık `5.90 km/h` seviyesindedir. Bu nedenle çıktı hukuki/cezai hız ölçümü
  değil, `dataset_calibrated_approximate_candidate` olarak korunur.

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
