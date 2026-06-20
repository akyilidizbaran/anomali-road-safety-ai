# Hız Kestirimi

## FTR Kapsam Notu

2026-06-13 FTR teslim dokümanı otomatik değerlendirme `results.json` şemasında hız alanı
istememektedir. Bu nedenle hız kestirimi FTR submission için zorunlu puanlanan çıktı değildir.

Hız modülü bundan sonra iki amaçla korunur:

1. `slalom` gibi hareket tabanlı sürücü/araç davranışı etiketlerine destek sinyali üretmek.
2. Proje raporunda risk/evidence zenginleştirme ve araştırma katkısı olarak anlatılmak.

Mevcut `SPEED-EXP-005A` çizgi grafiklerinde raw ve moving-average hız sinyalleri bbox jitter,
kadrajdan çıkış ve monoküler ölçek belirsizliği nedeniyle gürültülüdür. Bu durum araç/plaka
pipeline'ının yanlış olduğu anlamına gelmez; yalnızca kalibrasyonsuz bbox-geometry hız adayının
tek başına final mutlak km/s olarak kullanılamayacağını gösterir.

`SPEED-EXP-005D` ile mevcut hız fazı kapatılmıştır. Bu deney 004A relative, 002 plate-scale
ve 005A bbox-geometry adaylarını tek karar ağacında birleştirir. Sonuçlar:

* `video_1`: yaklaşık `2.64 km/h`, relative `normal`.
* `video_2`: yaklaşık `2.33 km/h`, relative `normal`.
* `video_3`: yaklaşık `15.06 km/h`, relative `fast`.

Bu değerler yalnız support/evidence sinyalidir; FTR `results.json` içine hız alanı olarak
yazılmayacaktır.

### Confidence Audit Sonucu

`SPEED-EXP-005D` sonrası ayrı bir confidence audit üretildi:

* Script: `scripts/benchmarks/plot_speed_confidence_audit.py`
* Rapor: `testing/reports/speed_exp_005d_confidence_audit.md`
* Audit JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-005D-candidate-fusion/speed_exp_005d_confidence_audit.json`
* Grafik klasörü: `runs/speed/SPEED-EXP-005D-candidate-fusion/plots/`

Bu audit sonucunda hız katmanlarının confidence anlamı şöyle sabitlendi:

| Katman | Confidence neyi ölçer? | Ne değildir? |
|---|---|---|
| `SPEED-EXP-004A` | Track/bbox geçmişinin kararlılığı ve göreli hareket sinyali kalitesi | Mutlak km/s doğruluğu |
| `SPEED-EXP-002` | Plaka ölçeği adayının düşük güvenli destek değeri | Tek başına hız ölçümü |
| `SPEED-EXP-005A` | Bbox geometry adayının iç stabilitesi, usable segment oranı ve moving-average kalitesi | Ground-truth hız başarımı |
| `SPEED-EXP-005D` | Bbox, plaka ve relative sinyallerinin birbirini destekleme skoru | Hukuki/kalibre edilmiş hız güveni |

Bu ayrım kritik: `video_1` ve `video_3` için `005D` confidence yüksek görünür, fakat bu yüksek
değer aday sinyallerin kendi içinde destekli olduğunu söyler. Ground-truth hız olmadığı için
“gerçek km/s doğru ölçüldü” iddiası kurulmaz.

### VS13 Known-Speed Kalibrasyon Deneyi

Mutlak km/s iddiasını büyütmeden önce bilinen hızlı dış videolarda sanity check yapılacaktır.
Bu amaçla `SPEED-EXP-006` notebook'u eklendi:

* Notebook: `notebooks/SPEED_EXP_006_VS13_Known_Speed_Calibration_Colab.ipynb`
* Veri kaynağı: VS13 known-speed video+annotation paketleri
* İlk paketler: `RenaultCaptur`, `KiaSportage`, `VWPassat`
* Ground-truth hız: paket seviyesinde değil, video dosya adındaki hız suffix'inden okunur
  (`RenaultCaptur_66.MP4` -> `66 km/h` gibi).
* Çıktı klasörü: `/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/speed/SPEED-EXP-006-VS13-known-speed-calibration/`

Bu deney yeni bir neural speed modeli eğitmez. Mevcut `YOLO + ByteTrack + bbox-geometry`
hız adayını bilinen hızlara karşı test eder ve şu parametreleri optimize eder:

* Global scale correction.
* Horizontal FOV varsayımı.
* Araç yükseklik prior'ı.
* Moving-average window.
* Segment outlier gate.

Split video/araç bazlıdır; frame bazlı split yapılmaz. İlk varsayılan split paket bazlıdır;
her paketten seçilen videolar düşük/orta/yüksek hızları kapsayacak şekilde dengeli seçilir:

| Araç paketi | GT hız kaynağı | Split |
|---|---|---|
| Renault Captur | Dosya adı suffix'i | train/calibration |
| Kia Sportage | Dosya adı suffix'i | validation |
| VW Passat | Dosya adı suffix'i | test |

Eğer test MAE makul çıkarsa hız modülü “dataset-calibrated approximate speed candidate”
olarak raporlanabilir. Test MAE yüksek veya tutarsız çıkarsa hız modülü yine
`relative/support evidence` olarak kalır.

## Kritik İlke

Gerçek km/s tahmini yalnız kamera sabitlenirse ve referans mesafe biliniyorsa savunulabilir. Kalibrasyon yoksa sistem mutlak hız iddiası üretmemelidir.

## Mevcut Karar

Demo gerçek yol kenarında ve sabit kamera ile yapılacak. Projenin hedefi mutlak km/s tahmini üretmektir. Eğer kalibrasyon veya görüntü koşulları yeterli olmazsa sistem göreli hız/risk sınıflandırmasına düşecektir.

Ground truth hız yaklaşımı, yerel sahada zorunlu doğrudan ölçüm yapmak yerine literatürdeki/internette yayımlanmış hız kestirimi çalışmalarından yöntem ve değerlendirme fikri türetmek olarak belirlenmiştir. Final raporda bu yaklaşım kaynaklandırılmalıdır.

Kalibrasyon denemesi **final scope** olarak tutulacaktır. MVP aşamasında hız modülü mutlak km/s iddiası kurmak yerine track tabanlı göreli hareket, ani hızlanma/yavaşlama ve motion anomaly sinyali üretebilir.

## Plate-Scale Monocular Speed Baseline

Plakanın göründüğü hedef araçlarda ayrı bir ara yöntem denenir: Türkiye uzun plaka boyutu
ön bilgisi (`0.52m x 0.11m`) ile plaka crop piksel boyutundan yaklaşık derinlik ve frame
arası range-rate/hız sinyali üretilir.

İlk deney:

* Deney adı: `SPEED-EXP-001 Plate-Scale Monocular Speed Baseline`
* Script: `scripts/benchmarks/run_plate_scale_speed_baseline.py`
* Kaynak: `POCR-EXP-005` plate detector crop'ları + `POCR-EXP-007` CCT-XS per-crop OCR çıktıları
* Çıktılar:
  * `models/benchmarks/artifacts/speed/SPEED-EXP-001-plate-scale/speed_exp_001_plate_scale_summary.json`
  * `models/benchmarks/artifacts/speed/SPEED-EXP-001-plate-scale/speed_exp_001_plate_scale_summary.csv`
  * `testing/reports/speed_exp_001_plate_scale_baseline.md`

Formül:

```text
Z_width   = fx * 0.52 / plate_width_px
Z_height  = fy * 0.11 / plate_height_px
Z_geomean = sqrt(Z_width * Z_height)
speed_kmh = abs(Z_t2 - Z_t1) / dt * 3.6
```

Bu yöntem ilk aşamada düşük güvenli araştırma baseline'ıdır. Çünkü mevcut crop-only
artefactlerde plakanın full-frame merkez koordinatı saklanmaz; bu nedenle lateral hareket
bileşeni hesaba katılamaz. Ayrıca crop aspect ratio standart uzun plaka oranından belirgin
saparsa mutlak km/s iddiası kurulmaz.

Sonraki iyileştirme için plate detector summary içine full-frame `plate_bbox_xyxy`, plate
center ve mümkünse plate corner bilgisi yazılmalıdır. Böylece `X/Y/Z` konum serisi veya
`solvePnP` tabanlı hız hesabı denenebilir.

## Full-Frame Plate BBox / XYZ Denemesi

`SPEED-EXP-002` kapsamında plate detector summary içine full-frame plaka bbox ve center
alanları eklendi. Böylece hız hesabı yalnız `abs(dZ)` range-rate hesabı olmaktan çıkıp,
full-frame plate center varsa yaklaşık `X/Y/Z` displacement moduna geçebilir:

```text
X = (u - cx) * Z / fx
Y = (v - cy) * Z / fy
speed_kmh = sqrt(dX^2 + dY^2 + dZ^2) / dt * 3.6
```

İlk `SPEED-EXP-002` sonuçları:

* `video_1` geomean median hız adayı: `3.7806 km/h`
* `video_2` geomean median hız adayı: `3.8768 km/h`
* `video_3` geomean median hız adayı: `12.8163 km/h`

Bu sonuçlar hâlâ düşük güvenlidir. Nedeni, median plaka bbox aspect ratio değerlerinin
standart uzun Türkiye plaka oranından (`4.73`) belirgin sapmasıdır. Sonraki geliştirme,
plaka bbox'ın gerçekten tüm plaka yüzeyini kapsayıp kapsamadığını manuel overlay ile
incelemek ve mümkünse plaka köşesi/perspektif düzeltmesi eklemektir.

## Vehicle Dimension Prior / Speed Fusion

Plaka ölçeği tek başına her senaryoda yeterli değildir. Bu nedenle hız modülüne ayrı bir
`Vehicle Dimension Prior` sinyali eklenir. Bu sinyal araç crop'undan gövde tipi veya
fine-grained araç etiketi çıkarır ve yaklaşık wheelbase/uzunluk ön bilgisi üretir.

İlk deney:

* Deney adı: `VATTR-EXP-001`
* Notebook: `notebooks/VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab.ipynb`
* Veri adayı: BoxCars116k
* İlk backbone: `MobileNetV3-Large`
* Amaç: `Speed Fusion Layer` için `body_type`, `wheelbase_m_mean`, confidence ve
  `use_for_speed_fusion` alanlarını üretmek.

Bu modül marka/model sonucunu kesin kanıt yapmaz. Confidence düşükse veya gövde tipi
belirsizse dimension-prior sinyali mutlak km/s hesabına katılmaz. Önerilen fusion:

```text
speed_candidate =
  plate_scale_signal +
  homography_track_signal +
  vehicle_dimension_prior_signal
```

Kalibrasyon veya güvenilir ölçek yoksa çıktı `speed_mode=relative` olarak kalır.

## Referans Mesafe Otomatik Ölçülebilir mi?

Tek kameradan, sahnede hiçbir bilinen ölçek yokken güvenilir gerçek mesafe otomatik çıkarılamaz. Monoküler görüntüde ölçek belirsizliği vardır; yani sistem piksel hareketini görür ama bu hareketin kaç metreye karşılık geldiğini bilmek için bir referansa ihtiyaç duyar.

Pratik seçenekler:

1. **Yarı otomatik kalibrasyon:** Kullanıcı görüntü üzerinde yol üzerindeki 4 noktayı seçer ve bilinen mesafeyi girer. Homografi bu bilgiyle kurulur.
2. **Sahaya referans marker koyma:** Yol kenarına veya güvenli alana iki görünür marker konur; aralarındaki mesafe bilinir.
3. **Bilinen şerit genişliği varsayımı:** Şerit genişliği yaklaşık ölçek olarak kullanılır. Daha az güvenilirdir, çünkü yol tipine ve kamera açısına bağlı hata üretir.
4. **Harita/GPS/IMU desteği:** Kamera konumu ve yol geometrisi biliniyorsa destekleyici ölçek sağlanabilir; MVP için karmaşıktır.
5. **Fallback:** Referans güvenilir değilse mutlak km/s yerine göreli hız sınıflandırması yapılır.

Final scope için önerilen tasarım: Kullanıcıya demo başlangıcında kısa bir kalibrasyon adımı sunmak. Kullanıcı iki veya dört referans noktası seçer; sistem homografi matrisini hesaplar ve hız kestirimini confidence ile birlikte verir.

MVP için önerilen tasarım: Kalibrasyon UI veya marker zorunlu tutulmaz. Track history üzerinden göreli hareket skoru ve risk etiketi üretilir; raporda bunun km/s tahmini olmadığı açıkça yazılır.

## Kalibre Edilmiş Mod

1. Kamera sabitlenir.
2. Yol üzerinde gerçek mesafesi bilinen noktalar seçilir.
3. Piksel koordinatları dünya düzlemine homografiyle dönüştürülür.
4. Hedef araç alt merkez noktası takip edilir.
5. Yer değiştirme / zaman farkı ile hız hesaplanır.
6. Temporal smoothing uygulanır.

## Kalibrasyonsuz Mod

* Göreli hız.
* Ani hızlanma/yavaşlama.
* Takip tabanlı hareket aykırılığı.
* Risk sınıfı.

## Rapor Cümlesi

> Kalibre edilmiş sabit kamera senaryosunda sistem gerçek km/s tahmini üretir. Kalibrasyonun yetersiz olduğu mobil veya serbest kamera senaryolarında ise mutlak hız iddiası üretmek yerine göreli hız ve hareket aykırılığı skoruyla risk değerlendirmesi yapar.

## Metrikler

MVP:

* Relative motion consistency.
* Motion anomaly event accuracy.
* Track continuity.
* Risk sınıfı doğruluğu.

Final scope:

* MAE.
* RMSE.
* km/s hata aralığı.
* Calibration confidence.
