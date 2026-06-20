# SPEED-EXP-006 VS13 Outhealth Review

Bu rapor, `notebooks/SPEED_EXP_006_VS13_Known_Speed_Calibration_Colab_outhealth.ipynb`
çıktılarının teknik değerlendirmesidir.

## Çalışma Sağlığı

Notebook bu koşuda tamamlandı. Önceki crash sebebi olan `.MP4` büyük harfli dosya uzantısı
ve boş manifest problemi çözülmüş görünüyor.

Başarılı noktalar:

* VS13 zip paketleri Drive cache üzerinden bulundu; tekrar indirme yapılmadı.
* `RenaultCaptur`, `KiaSportage`, `VWPassat` paketlerinden toplam `18` video çıkarıldı.
* Ground-truth hız video dosya adından doğru okundu (`*_30.MP4`, `*_100.MP4` vb.).
* Splitler araç/paket bazlı oluştu:
  * train: `RenaultCaptur`, 6 video, `30-102 km/h`
  * validation: `KiaSportage`, 6 video, `31-105 km/h`
  * test: `VWPassat`, 6 video, `30-100 km/h`
* YOLO + ByteTrack tracking her videoda `ok` döndü.
* `vs13_subset_manifest.csv`, `vs13_base_speed_candidates.csv`,
  `vs13_calibration_grid_metrics.csv`, `vs13_best_calibrated_predictions.csv`,
  summary JSON, Markdown rapor ve plotlar üretildi.

## Tablo Formatı Değerlendirmesi

Manifest tablosu doğru formatta:

| Alan | Durum |
|---|---|
| `video_path` | Var |
| `video_name` | Var |
| `vehicle` | Var |
| `gt_speed_kmh` | Var ve dosya adından okunuyor |
| `split` | Var |

Base candidate tablosu çalışır durumda; şu alanlar yeterli:

| Alan | Durum |
|---|---|
| `track_status` | Tüm videolarda `ok` |
| `selected_observation_count` | Var |
| `base_estimated_raw_kmh` | Var |
| `base_confidence` | Var ama mevcut koşuda saturate oldu |
| `base_speed_cv` | Var ve kalite analizi için kullanılabilir |

Grid metrics tablosu teknik olarak yeterli ama çok geniş. Aktif notebook patch'i sonrası
özet display, yalnız ana tuning kolonlarını gösterecek şekilde daraltıldı.

## Metrikler

En iyi global-scale koşu:

```json
{
  "horizontal_fov_deg": 70.0,
  "vehicle_height_m": 1.45,
  "moving_average_window": 15,
  "max_segment_speed_kmh": 180.0,
  "global_scale_alpha": 1.3317851476,
  "train_mae_kmh": 3.43,
  "val_mae_kmh": 5.19,
  "test_mae_kmh": 8.07,
  "test_rmse_kmh": 12.29,
  "test_mean_rel_error_pct": 12.67
}
```

Bu sonuç, mevcut bbox-geometry hız adayının VS13 üzerinde anlamlı bir hız sinyali taşıdığını
gösterir. Ancak test setinde hatalar hâlâ büyük dalgalanıyor:

| Video | GT | Kalibre tahmin | Hata |
|---|---:|---:|---:|
| `VWPassat_30.MP4` | 30 | 29.49 | 0.51 |
| `VWPassat_49.MP4` | 49 | 53.47 | 4.47 |
| `VWPassat_61.MP4` | 61 | 82.28 | 21.28 |
| `VWPassat_72.MP4` | 72 | 92.77 | 20.77 |
| `VWPassat_85.MP4` | 85 | 85.46 | 0.46 |
| `VWPassat_100.MP4` | 100 | 100.92 | 0.92 |

Yorum: düşük ve yüksek uçlarda sonuç iyi, orta hızlarda ciddi over-estimation var.
Bu dağılım tek global scale ile tam otomatik mutlak hızın kapanmadığını gösterir.

## Confidence Bulgusu

Mevcut outhealth koşusunda `candidate_confidence` tüm videolarda `0.75` tavanına vurdu.
Bu nedenle confidence-vs-error grafiği anlamlı ayrım üretmiyor.

Aktif notebook patch'i sonrası confidence formülü değiştirildi:

* `coverage_quality`
* `valid_ratio`
* `cv_quality`
* `mean_detection_confidence`
* `det_conf_quality`
* `estimate_available`

alanlarıyla daha ayrıştırıcı skor üretilecek. Bu nedenle sonraki Colab koşusunda Cell 8
sonrasının yeniden çalıştırılması gerekir.

## Tuning ile İyileştirme Şansı

Kısa yanıt: Evet, fakat bu neural model eğitimi değil, kalibrasyon/tuning iyileştirmesidir.

Mevcut çıktılardan görülen olası iyileştirmeler:

1. **Lineer kalibrasyon:** `speed = a * raw_speed + b` global alpha'ya göre küçük ama gerçek
   iyileştirme potansiyeli gösteriyor. Yerel hesapla test MAE yaklaşık `8.07 -> 7.59 km/h`,
   test RMSE yaklaşık `12.29 -> 10.43 km/h` seviyesine inebilir.
2. **Segment seçimi:** Araç görüntünün giriş/çıkış uçlarında bbox geometry daha kırılgan.
   Merkez geçiş segmenti, stabil bbox-height ve düşük speed-CV pencereleri seçilmeli.
3. **Tüm paket kullanımı:** 6 video/araç sadece hızlı sanity için yeterli. Gerçek karar için
   her paketten daha fazla video kullanılmalı.
4. **Leave-one-vehicle-out validasyon:** Tek bir train araç + tek val araç + tek test araç
   küçük bir kurulum. Daha güvenilir sonuç için araç bazlı çapraz validasyon gerekir.
5. **Kalibrasyon modeli karşılaştırması:** `global_alpha`, `linear_raw`, robust regression,
   piecewise speed-bin correction ve confidence-weighted calibration kıyaslanmalı.

## Full Otomatik İçin Karar

Bu sonuçla “tam otomatik mutlak km/s hız modeli bitti” denmemeli.

Söylenebilir iddia:

> VS13 bilinen hızlı videolarda mevcut bbox-geometry hız adayı, basit kalibrasyonla
> yaklaşık hız sinyali üretebilmiştir; ancak bazı hız aralıklarında yüksek hata gözlendiği
> için modül bu aşamada karar destek/evidence sinyali olarak tutulmalıdır.

Tam otomatik mutlak hız için daha iyi yol:

1. `SPEED-EXP-006B`: tüm VS13 subset + lineer/robust/piecewise kalibrasyon kıyası.
2. `SPEED-EXP-006C`: track segment selector; yalnız stabil merkez geçiş segmentlerinden hız.
3. `SPEED-EXP-006D`: confidence calibration; confidence gerçekten düşük hatayla korele mi?
4. Eğer hâlâ test MAE yüksekse, FTR kapsamında hız `relative/support evidence` olarak kalmalı.

## Son Karar

Mevcut run istediğimiz çıktıları üretti ve pipeline sağlıklı çalıştı. Ancak sonuçlar mutlak
km/s modelini kapatmaya yetmez. Hiperparametre/kalibrasyon iyileştirmesi yapılabilir; en
yakın adım, patch'li notebook ile Cell 8 sonrası tekrar koşup lineer kalibrasyon ve yeni
confidence skorlarını değerlendirmektir.
