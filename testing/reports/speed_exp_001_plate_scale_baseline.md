# SPEED-EXP-001 Plate-Scale Monocular Speed Baseline

Tarih: `2026-06-17T10:51:26Z`

## Amaç

Türkiye uzun plaka boyutu varsayımı (`0.52m x 0.11m`) ile plaka crop piksel ölçülerinden yaklaşık derinlik ve frame'ler arası göreli/mutlak hız adayları üretmek. Bu çalışma radar/hukuki hız ölçümü değildir; kalibrasyon gerektiren bir matematiksel baseline denemesidir.

## Formül

* `fx = image_width / (2 * tan(horizontal_fov / 2))`
* `fy` yatay FOV ve görüntü oranından türetilen dikey FOV ile hesaplanır.
* Width yöntemi: `Z = fx * 0.52 / plate_width_px`
* Height yöntemi: `Z = fy * 0.11 / plate_height_px`
* Geomean yöntemi: `Z = sqrt(Z_width * Z_height)`
* Hız: `speed_kmh = abs(Z_t2 - Z_t1) / dt * 3.6`

## Konfigürasyon

* Horizontal FOV varsayımı: `70.0` derece
* Minimum OCR confidence: `0.75`
* Smooth window: `7`
* Max speed outlier gate: `220.0` km/s

## Özet

| Video | Variant | Measurements | Aspect Median | Width px | Height px | Median km/h | Mean km/h | Outliers | Note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| video_1.mp4 | width | 201 | 3.3483 | 303.0 | 91.0 | 3.294 | 3.2229 | 0 | low_plate_crop_aspect_differs_from_standard_width |
| video_1.mp4 | height | 201 | 3.3483 | 303.0 | 91.0 | 5.958 | 5.4054 | 0 | low_plate_crop_aspect_differs_from_standard_height |
| video_1.mp4 | geomean | 201 | 3.3483 | 303.0 | 91.0 | 4.104 | 4.072 | 0 | low_plate_crop_aspect_differs_from_standard_geomean |
| video_2.mp4 | width | 190 | 3.3906 | 318.5 | 93.5 | 3.114 | 3.0786 | 0 | low_plate_crop_aspect_differs_from_standard_width |
| video_2.mp4 | height | 190 | 3.3906 | 318.5 | 93.5 | 5.706 | 5.7714 | 0 | low_plate_crop_aspect_differs_from_standard_height |
| video_2.mp4 | geomean | 190 | 3.3906 | 318.5 | 93.5 | 3.312 | 3.9451 | 0 | low_plate_crop_aspect_differs_from_standard_geomean |
| video_3.mp4 | width | 178 | 3.2038 | 184.0 | 50.0 | 10.818 | 13.3743 | 0 | low_plate_crop_aspect_differs_from_standard_width |
| video_3.mp4 | height | 178 | 3.2038 | 184.0 | 50.0 | 20.466 | 22.8272 | 0 | low_plate_crop_aspect_differs_from_standard_height |
| video_3.mp4 | geomean | 178 | 3.2038 | 184.0 | 50.0 | 12.564 | 16.3343 | 0 | low_plate_crop_aspect_differs_from_standard_geomean |

## Yorum

* Bu ilk deneme yalnız plaka görünür hedefler içindir.
* Crop aspect ratio standart `4.73` değerinden belirgin saparsa sonuç düşük güvenli kabul edilir.
* Kamera FOV ve plaka köşe/pose bilgisi gerçek kalibrasyonla doğrulanmadan mutlak km/s iddiası kurulmaz.
* Sonraki iyileştirme: plaka 4 köşe tespiti + `solvePnP` veya saha kalibrasyon noktaları ile ölçek doğrulaması.
