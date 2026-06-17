# Plate-Scale Monocular Speed Baseline

Tarih: 2026-06-17

## Amaç

Bu not, plakanın göründüğü hedef araçlarda Türkiye plaka boyutu standardını kullanarak
tek kamera üzerinden yaklaşık hız kestirimi denemesini tanımlar. Bu yöntem radar/hukuki
hız ölçümü değildir; kamera kalibrasyonu, plaka köşe tespiti ve saha ground truth'u
olmadan yalnız araştırma/evidence sinyali olarak değerlendirilmelidir.

## Literatür Karşılığı

Plaka geometrisini kullanarak tek kameradan mesafe/hız kestirimi yapılmış çalışmalar
vardır. Bu proje için doğrudan ilişkili başlıklar:

* `Real-Time Vehicle Speed Estimation Based on License Plate Tracking in Monocular Video Sequences`:
  sabit over-road tek kamera, plaka takibi, kamera tilt açısı, dikey görüş açısı ve plaka
  yüksekliği varsayımı ile hız kestirimi önerir.
  Kaynak: https://www.sensorsportal.com/HTML/DIGEST/february_2016/Vol_197/P_2802.pdf
* `Single-camera vehicle speed measurement using the geometry of license plates`:
  tek kamera görüntüsünde plaka geometrisi ile hız ölçümü fikrini ele alır.
  Kaynak: https://dl.acm.org/doi/abs/10.1007/s11042-020-08761-5
* `Vehicle Speed Estimation Based on License Plate Detection`:
  kalibre edilmiş kamera varsayımıyla plaka detection üzerinden hız kestirimi çalışır.
  Kaynak: https://lume.ufrgs.br/bitstream/handle/10183/234929/001136025.pdf?sequence=1
* Plaka boyutundan mesafe kestirimi pratik örneği:
  https://www.timetoact-group.at/en/techblog/techblog/license-plate-detection
* Tek kamera hız ölçümü genel bağlamı:
  https://www.nature.com/articles/s41598-025-87077-6

## Türkiye Plaka Boyutu Varsayımı

Karayolları Trafik Yönetmeliği'nde otomobil, kamyonet, minibüs, kamyon, çekici ve
otobüslerde ön plaka `11x52 cm`, arka plaka `11x52 cm` veya `21x32 cm`; plaka yeri
uygun değilse `15x30 cm` ölçüsü belirtilir.

Kaynak: https://www.aile.gov.tr/eyhgm/mevzuat/ulusal-mevzuat/yonetmelikler/karayollari-trafik-yonetmeligi/

İlk deneyde yalnız uzun plaka varsayımı kullanılır:

* `plate_width_m = 0.52`
* `plate_height_m = 0.11`
* standart oran: `0.52 / 0.11 = 4.727`

Crop aspect ratio bu orandan belirgin saparsa hız sonucu `low confidence` kabul edilir.

## SPEED-EXP-001 Deney Tasarımı

Script:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_plate_scale_speed_baseline.py
```

Girdiler:

* Plate detector summary:
  `models/benchmarks/artifacts/plate_detection/POCR-EXP-005-local-video-smoke-yolo-summary.json`
* CCT-XS per-crop OCR summary:
  `models/benchmarks/artifacts/plate_ocr/POCR-EXP-007-cct-xs-baseline-percrop/POCR-EXP-006-fast-plate-ocr-summary.json`

Çıktılar:

* `models/benchmarks/artifacts/speed/SPEED-EXP-001-plate-scale/speed_exp_001_plate_scale_summary.json`
* `models/benchmarks/artifacts/speed/SPEED-EXP-001-plate-scale/speed_exp_001_plate_scale_summary.csv`
* `testing/reports/speed_exp_001_plate_scale_baseline.md`

## Formül

Kamera yatay görüş açısı yaklaşık verilir:

```text
fx = image_width / (2 * tan(horizontal_fov / 2))
```

Dikey görüş açısı görüntü oranından türetilir ve `fy` hesaplanır.

Üç varyant birlikte denenir:

```text
Z_width   = fx * 0.52 / plate_width_px
Z_height  = fy * 0.11 / plate_height_px
Z_geomean = sqrt(Z_width * Z_height)
```

Frame arası hız:

```text
speed_kmh = abs(Z_t2 - Z_t1) / dt * 3.6
```

Bu ilk versiyon yalnız plaka ölçek değişimini kullanır. Mevcut crop-only artefactlerde
plakanın tam karedeki merkez koordinatı saklanmadığı için lateral hareket bileşeni henüz
hesaba katılmaz.

## İlk Sonuç

Default `horizontal_fov=70°` ve CCT-XS `stable_count=3` sonrası crop'larla:

| Video | Width median km/h | Height median km/h | Geomean median km/h | Güven Notu |
|---|---:|---:|---:|---|
| video_1.mp4 | 3.294 | 5.958 | 4.104 | düşük: crop aspect ratio standarttan sapıyor |
| video_2.mp4 | 3.114 | 5.706 | 3.312 | düşük: crop aspect ratio standarttan sapıyor |
| video_3.mp4 | 10.818 | 20.466 | 12.564 | düşük: crop aspect ratio standarttan sapıyor |

Bu sonuçlar mutlak km/s olarak kabul edilmemelidir. Ancak plaka yaklaşma/uzaklaşma ölçeği
temelli bir `range-rate` sinyali üretildiğini gösterir.

## Neden Düşük Güvenli?

Mevcut plaka crop'larının median aspect ratio değerleri `3.20-3.39` aralığında, standart
uzun plaka oranı `4.73` civarındadır. Bu fark şunlardan kaynaklanabilir:

* detector crop'un tüm plakayı değil karakter bölgesini veya dikeyde fazla alanı kapsaması,
* perspektif/yaw etkisi,
* motion blur ve low-light kaynaklı bbox sınır hatası,
* plaka çerçevesi/araç yüzeyi ile detector bbox karışması,
* standart dışı veya farklı tip plaka geometrisi.

## Sonraki Matematiksel İyileştirme

1. Plate detector summary içine full-frame `plate_bbox_xyxy` ve plate center yazılmalı.
2. Plaka crop yerine full-frame bbox üzerinden `u, v, w, h` serisi çıkarılmalı.
3. Depth-only hız yerine yaklaşık 3D nokta serisi denenmeli:

```text
X = (u - cx) * Z / fx
Y = (v - cy) * Z / fy
Z = depth
speed = sqrt((X2-X1)^2 + (Y2-Y1)^2 + (Z2-Z1)^2) / dt
```

4. Plaka 4 köşesi çıkarılabilirse `solvePnP` denenmeli.
5. Demo alanında en az bir saha kalibrasyon ölçüsüyle scale/fov doğrulanmalı.

## Rapor Dili

Kullanılacak ifade:

> Plaka görünür hedef araçlarda Türkiye uzun plaka boyutu ön bilgisi kullanılarak tek kamera
> üzerinde yaklaşık range-rate/hız sinyali üretilmiştir. Kamera FOV ve plaka bbox geometrisi
> kalibre edilmediği için bu aşama mutlak km/s iddiası değil, kalibre edilebilir bir hız
> baseline'ı olarak değerlendirilmiştir.

Kaçınılacak ifade:

* kesin hız ölçümü
* hukuki kanıt
* radar alternatifi
* kalibrasyonsuz doğru km/s
