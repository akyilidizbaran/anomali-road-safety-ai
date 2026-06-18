# SPEED-EXP-004 Speed Fusion Layer Implementation Plan

## Yönetici Özeti

Speed Fusion Layer, tek kameradan gelen hız sinyallerini tek bir kesin hız ölçümü gibi değil, `speed_mode`, hız adayı, güven skoru ve fallback gerekçesi üreten karar destek katmanı olarak tasarlanacaktır.

İlk sürüm üç mod üretmelidir:

```text
absolute_candidate
relative
unavailable
```

Mutlak km/s yalnız sabit kamera, geçerli FPS, güvenilir yol düzlemi ölçeği/homografi veya ölçülü referans, yeterli track uzunluğu ve sinyaller arası tutarlılık varsa üretilecektir. Aksi halde sistem göreli hız / motion anomaly üretir.

## Sinyal Önceliği

V1 için sinyal önceliği:

1. `homography_track`
   * Varsa birincil `absolute_candidate` kaynağı.
   * Track bottom-center noktası dünya düzlemine projekte edilir.
2. `bbox_bottom_center_relative`
   * Her koşulda relative speed ana kaynağı.
   * Kalibrasyon gerektirmez.
3. `bbox_scale_dynamics`
   * En hızlı eklenebilir ek sinyal.
   * Bbox height/area değişiminden yaklaşma/uzaklaşma ve motion anomaly üretir.
4. `plate_scale`
   * Plaka netse auxiliary absolute candidate ve sanity-check.
   * Tek başına mutlak hız için yeterli kabul edilmez.
5. `vehicle_dimension_prior`
   * VATTR çıktısı ile wheelbase/araç boyutu prior üretir.
   * V1'de confidence adjuster ve range sanity-check olarak kullanılır.

## Aşama 1 — Speed Candidate Contract

Her hız adayı aynı contract ile temsil edilecek:

```json
{
  "source": "homography_track",
  "speed_kmh": 48.7,
  "speed_range_kmh": [43.2, 54.5],
  "relative_score": null,
  "confidence": 0.78,
  "quality_flags": ["track_len_ok", "homography_ok", "low_jitter"],
  "failure_flags": []
}
```

Gerekli dosya:

```text
architecture/contracts/speed_fusion_contract.md
```

## Aşama 2 — Relative Speed Baseline

Ground truth veya kalibrasyon gerektirmeyen ilk uygulanabilir hız sinyali budur.

Girdi:

* `track_id`
* `bbox_history`
* `center_history`
* `frame_id`
* `timestamp`
* `fps`

Hesaplanacak feature'lar:

```text
pixel_speed_px_s
bottom_center_velocity_px_s
bbox_height
bbox_area
d_bbox_height_dt
d_log_bbox_area_dt
scale_normalized_speed = pixel_speed / bbox_height
```

Çıktı:

```text
relative_speed_score
relative_speed_label = normal / slightly_fast / fast / motion_anomaly
```

İlk deney:

```text
SPEED-EXP-004A-relative-track-motion
```

## Aşama 3 — Quality Gates

Hız sinyali üretmeden önce kalite kapıları çalışmalıdır:

```text
track_length_frames >= threshold
fps_valid = true
id_switch_suspected = false
bbox_jitter_score <= threshold
occlusion_score <= threshold
vehicle_bbox_height >= threshold
```

Başarısızsa:

```json
{
  "speed_mode": "unavailable",
  "fallback_reason": "track_too_short_or_occluded"
}
```

## Aşama 4 — Plate-Scale Sanity Check

Mevcut `SPEED-EXP-002` çıktısı V1 fusion içine auxiliary signal olarak bağlanır.

Kullanılacak alanlar:

* full-frame `plate_bbox_xyxy`
* `plate_width_px`
* `plate_height_px`
* `plate_center_xy`
* OCR/plate confidence
* plate aspect ratio quality

Kural:

* Plate-scale tek başına `absolute_candidate` üretmez.
* Homography yoksa `weak_absolute_candidate` gibi ayrı mod açılmayacak; sonuç `relative` kalır.
* Plate-scale yalnız hız aralığı ve candidate disagreement kontrolünde kullanılır.

## Aşama 5 — Vehicle Dimension Prior

`VATTR-EXP-001` çıktısı şu alanları sağlayacak:

```json
{
  "label": "sedan_or_fine_grained_class",
  "confidence": 0.82,
  "body_type_prior": "sedan",
  "wheelbase_m_mean": 2.75,
  "wheelbase_m_min": 2.55,
  "wheelbase_m_max": 3.0,
  "use_for_speed_fusion": true
}
```

Kural:

* Confidence düşükse kullanılmaz.
* Araç çok küçük/uzaksa kullanılmaz.
* Viewpoint uygun değilse wheelbase speed adayı üretilmez.
* V1'de birincil hız kaynağı değil, `confidence adjuster` ve `range sanity-check` olur.

İlk deney:

```text
SPEED-EXP-004B-vehicle-dimension-prior-fusion
```

## Aşama 6 — Homography Track Absolute Candidate

Mutlak km/s için birincil yol budur.

Girdi:

* sabit kamera
* FPS/timestamp
* yol düzleminde 4 nokta veya ölçülü iki referans çizgisi
* track bottom-center history

Hesap:

```text
pixel bottom-center -> world XY
distance_m = ||XY_t2 - XY_t1||
speed_kmh = distance_m / dt * 3.6
```

Kural:

```text
absolute_candidate = homography exists
                  and calibration_quality >= threshold
                  and track quality ok
                  and candidate disagreement acceptable
```

İlk deney:

```text
SPEED-EXP-004C-homography-track-candidate
```

## Aşama 7 — Fusion Decision

V1'de karmaşık weighted average yerine güvenli karar ağacı kullanılacak:

```text
if homography_track confidence high:
    speed_mode = absolute_candidate
    primary_source = homography_track
    plate_scale and vehicle_prior = sanity-check
elif track_relative confidence high:
    speed_mode = relative
    primary_source = bbox_bottom_center_relative
else:
    speed_mode = unavailable
```

Candidate disagreement kuralı:

```text
if absolute candidates disagree too much:
    speed_mode = relative
    fallback_reason = candidate_disagreement_high
```

## Evidence JSON Alanları

Önerilen alanlar:

```json
{
  "speed_mode": "absolute_candidate",
  "speed_kmh_candidate": 47.8,
  "speed_range_kmh": [42.5, 53.6],
  "relative_speed_score": 1.72,
  "relative_speed_label": "fast",
  "fusion_confidence": 0.76,
  "primary_speed_source": "homography_track",
  "candidate_speeds": [],
  "track_quality": {},
  "geometry_quality": {},
  "plate_quality": {},
  "vehicle_dimension_prior": {},
  "decision_flags": [
    "not_for_legal_enforcement",
    "risk_decision_support_only"
  ],
  "fallback_reason": null
}
```

## Manuel Review

Ground truth yoksa MAE/RMSE raporlanmaz. İlk manuel metrikler:

```text
speed_mode_distribution
candidate_availability_rate
candidate_disagreement_rate
relative_only_rate
unavailable_rate
manual_pairwise_ranking_accuracy
```

Track review rubriği:

```text
A: speed signal güvenilir
B: göreli hız güvenilir, mutlak hız zayıf
C: belirsiz ama motion var
D: track bozuk / occlusion fazla
E: speed unavailable olmalıydı
```

## Uygulama Sırası

1. `SPEED-EXP-004A`: Relative track/bbox speed baseline.
2. `SPEED-EXP-004B`: Plate-scale ve VATTR dimension-prior sanity-check bağlantısı.
3. `SPEED-EXP-004C`: Semi-manual homography calibration ve absolute candidate.
4. `SPEED-EXP-004D`: Event/evidence JSON enrichment.
5. Kontrollü yerel hız videosu ile engineering validation.

## Rapor Dili

Kullanılacak ifadeler:

* hız adayı
* göreli hız skoru
* hareket aykırılığı
* kalibre edilmiş sabit kamera
* karar destek sinyali
* denetlenebilir evidence

Kaçınılacak ifadeler:

* kesin hız ölçümü
* hukuki hız kanıtı
* ceza tespiti
* her koşulda km/s doğruluğu

## Kaynak Omurgası

* BrnoCompSpeed: https://arxiv.org/abs/1702.06441
* Sochor 3D bbox calibration: https://arxiv.org/abs/1702.06451
* Robust monocular speed estimation: https://openaccess.thecvf.com/content/ICCV2021/papers/Revaud_Robust_Automatic_Monocular_Vehicle_Speed_Estimation_for_Traffic_Surveillance_ICCV_2021_paper.pdf
* ByteTrack: https://arxiv.org/abs/2110.06864
* BoxCars: https://arxiv.org/abs/1703.00686
