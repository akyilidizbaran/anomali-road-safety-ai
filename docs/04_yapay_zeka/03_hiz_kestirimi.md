# Hız Kestirimi

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
