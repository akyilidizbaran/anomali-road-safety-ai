# SPEED-EXP-002 Plate-Scale Monocular Speed Baseline

Tarih: `2026-06-17T11:43:09Z`

## Amaç

Türkiye uzun plaka boyutu varsayımı (`0.52m x 0.11m`) ile plaka crop piksel ölçülerinden yaklaşık derinlik ve frame'ler arası göreli/mutlak hız adayları üretmek. Bu çalışma radar/hukuki hız ölçümü değildir; kalibrasyon gerektiren bir matematiksel baseline denemesidir.

## Formül

* `fx = image_width / (2 * tan(horizontal_fov / 2))`
* `fy` yatay FOV ve görüntü oranından türetilen dikey FOV ile hesaplanır.
* Width yöntemi: `Z = fx * 0.52 / plate_width_px`
* Height yöntemi: `Z = fy * 0.11 / plate_height_px`
* Geomean yöntemi: `Z = sqrt(Z_width * Z_height)`
* Full-frame plate center varsa: `X=(u-cx)*Z/fx`, `Y=(v-cy)*Z/fy`
* Hız: full-frame center varsa `sqrt(dX^2+dY^2+dZ^2)/dt*3.6`, yoksa `abs(dZ)/dt*3.6`

## Konfigürasyon

* Horizontal FOV varsayımı: `70.0` derece
* Minimum OCR confidence: `0.75`
* Smooth window: `7`
* Max speed outlier gate: `220.0` km/s

## Özet

| Video | Variant | Full BBox | Measurements | Aspect Median | Width px | Height px | Median km/h | Mean km/h | Outliers | Note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| video_1.mp4 | width | True | 201 | 3.3519 | 302.42 | 90.97 | 3.0973 | 3.6521 | 0 | low_plate_crop_aspect_differs_from_standard_width |
| video_1.mp4 | height | True | 201 | 3.3519 | 302.42 | 90.97 | 4.5422 | 4.7046 | 0 | low_plate_crop_aspect_differs_from_standard_height |
| video_1.mp4 | geomean | True | 201 | 3.3519 | 302.42 | 90.97 | 3.7806 | 4.0178 | 0 | low_plate_crop_aspect_differs_from_standard_geomean |
| video_2.mp4 | width | True | 190 | 3.3939 | 318.08 | 93.735 | 3.2847 | 3.3165 | 0 | low_plate_crop_aspect_differs_from_standard_width |
| video_2.mp4 | height | True | 190 | 3.3939 | 318.08 | 93.735 | 4.3888 | 5.5965 | 0 | low_plate_crop_aspect_differs_from_standard_height |
| video_2.mp4 | geomean | True | 190 | 3.3939 | 318.08 | 93.735 | 3.8768 | 4.2688 | 0 | low_plate_crop_aspect_differs_from_standard_geomean |
| video_3.mp4 | width | True | 178 | 3.2069 | 184.56 | 50.56 | 12.0596 | 14.7163 | 0 | low_plate_crop_aspect_differs_from_standard_width |
| video_3.mp4 | height | True | 178 | 3.2069 | 184.56 | 50.56 | 14.5751 | 19.9879 | 0 | low_plate_crop_aspect_differs_from_standard_height |
| video_3.mp4 | geomean | True | 178 | 3.2069 | 184.56 | 50.56 | 12.8163 | 15.9842 | 0 | low_plate_crop_aspect_differs_from_standard_geomean |

## Yorum

* Bu ilk deneme yalnız plaka görünür hedefler içindir.
* Crop aspect ratio standart `4.73` değerinden belirgin saparsa sonuç düşük güvenli kabul edilir.
* Kamera FOV ve plaka köşe/pose bilgisi gerçek kalibrasyonla doğrulanmadan mutlak km/s iddiası kurulmaz.
* Sonraki iyileştirme: plaka 4 köşe tespiti + `solvePnP` veya saha kalibrasyon noktaları ile ölçek doğrulaması.
