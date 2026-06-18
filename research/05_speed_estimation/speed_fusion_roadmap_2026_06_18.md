# Speed Fusion Roadmap — 2026-06-18

## Amaç

Bu yol haritası, Anomali Road Safety AI projesindeki hız kestirimi modülünü tek kamera, sabit yol kenarı kamera ve mevcut model omurgası koşullarına göre aşamalı olarak geliştirmek için hazırlanmıştır.

Hız modülü hukuki hız ölçüm sistemi değildir. İlk sürüm, kesin km/s iddiası yerine:

* hız adayı,
* göreli hız skoru,
* hareket aykırılığı,
* güven skoru,
* fallback gerekçesi,
* evidence JSON alanları

üreten karar destek katmanı olacaktır.

## Ana İlke

Tek kamerada hız kestiriminin asıl problemi hız formülü değil, piksel hareketinin metre karşılığını güvenilir şekilde bulmaktır. Bu yüzden sistem üç modla çalışmalıdır:

```text
speed_mode = absolute_candidate
speed_mode = relative
speed_mode = unavailable
```

* `absolute_candidate`: Sadece sabit kamera, geçerli FPS, güvenilir homografi/ölçülü referans ve yeterli track kalitesi varsa üretilir.
* `relative`: Kalibrasyon yok ama track hareketi güvenilirse üretilir.
* `unavailable`: Track, görüntü, FPS veya sinyal kalitesi hız yorumu için yetersizse üretilir.

## Genel Sinyal Omurgası

Speed Fusion Layer şu sinyalleri kullanacaktır:

1. `bbox_bottom_center_relative`
   * Kalibrasyon gerektirmeyen ana relative speed sinyali.
   * Araç track geçmişinden bottom-center hareketi çıkarılır.
2. `bbox_scale_dynamics`
   * Bbox yüksekliği/alanı zaman içinde değişiyorsa yaklaşma/uzaklaşma sinyali üretir.
   * En hızlı uygulanabilecek ek sinyaldir.
3. `plate_scale`
   * Plaka bbox, plaka genişliği/yüksekliği ve Türkiye plaka ölçüsü üzerinden yardımcı ölçek sinyali üretir.
   * Tek başına mutlak hız kanıtı değildir.
4. `vehicle_dimension_prior`
   * VATTR modeliyle araç tipi/fine-grained sınıf ve yaklaşık wheelbase/uzunluk ön bilgisi üretir.
   * V1'de confidence adjuster ve sanity-check olarak kullanılır.
5. `homography_track`
   * Kalibre edilmiş sabit kamera varsa birincil absolute candidate kaynağıdır.

## 1. SPEED-EXP-004A — Relative Track/BBox Speed Baseline

### Amaç

Kalibrasyon gerektirmeyen ilk hız sinyalini üretmek. Bu aşama, dış veri seti veya ground truth gerektirmez. Mevcut ByteTrack ve bbox geçmişi üzerinden göreli hız / motion anomaly sinyali çıkarır.

### Girdiler

* `track_id`
* `frame_id`
* `timestamp` veya FPS
* `bbox_history`
* `center_history`
* `track_stability`
* `stable_class`
* `condition_profile`

### Hesaplanacak Özellikler

```text
bottom_center_x
bottom_center_y
pixel_velocity_px_s
bbox_height
bbox_area
d_bbox_height_dt
d_log_bbox_area_dt
scale_normalized_speed = pixel_velocity_px_s / bbox_height
```

### Kalite Kapıları

```text
track_length_frames >= min_track_length
fps_valid = true
id_switch_suspected = false
bbox_jitter_score <= threshold
vehicle_bbox_height >= min_bbox_height
```

### Çıktılar

```json
{
  "speed_mode": "relative",
  "relative_speed_score": 1.72,
  "relative_speed_label": "fast",
  "primary_speed_source": "bbox_bottom_center_relative",
  "fusion_confidence": 0.71,
  "fallback_reason": "no_reliable_metric_calibration"
}
```

### Beklenen Rapor Dili

Bu aşama km/s üretmez. Çıktı göreli hız ve hareket aykırılığı sinyalidir.

## 2. SPEED-EXP-004B — Plate-Scale + VATTR Sanity-Check

### Amaç

Mevcut plate-scale hız adayını ve VATTR vehicle dimension prior çıktısını relative speed sonucunun sanity-check katmanı olarak kullanmak.

### Girdiler

Plate/OCR tarafından:

* `plate_bbox_xyxy`
* `plate_width_px`
* `plate_height_px`
* `plate_confidence`
* `ocr_confidence`
* `plate_aspect_ratio_quality`

VATTR tarafından:

* `label`
* `body_type_prior`
* `wheelbase_m_mean`
* `wheelbase_m_min`
* `wheelbase_m_max`
* `vehicle_attribute_confidence`
* `use_for_speed_fusion`

### Kural

Plate-scale ve vehicle dimension prior, homografi yokken doğrudan kesin km/s üretmeyecek. Bu sinyaller:

* hız adayı aralığını daraltmak,
* tutarsız sonuçları yakalamak,
* confidence artırmak veya düşürmek,
* `candidate_disagreement_high` fallback gerekçesi üretmek

için kullanılacaktır.

### Çıktılar

```json
{
  "candidate_speeds": [
    {
      "source": "plate_scale",
      "speed_kmh": 45.1,
      "confidence": 0.54,
      "quality_flags": ["plate_detected"],
      "failure_flags": ["plate_angle_medium"]
    },
    {
      "source": "vehicle_dimension_prior",
      "speed_kmh": null,
      "confidence": 0.41,
      "quality_flags": ["vehicle_type_available"],
      "failure_flags": ["model_prior_weak"]
    }
  ]
}
```

### Beklenen Rapor Dili

Bu aşamada plaka ve araç boyutu sinyalleri hız hesabını destekleyen/çürüten yardımcı evidence olarak anlatılmalıdır.

## 3. SPEED-EXP-004C — Semi-Manual Homography Absolute Candidate

### Amaç

Sabit kamera ve ölçülü referans varsa gerçek km/s adayı üretmek. Bu aşama mutlak hız için en savunulabilir yoldur.

### Girdiler

* Sabit kamera görüntüsü
* Yol düzleminde 4 nokta veya bilinen iki referans mesafe
* FPS/timestamp
* Track bottom-center history
* Road ROI

### Hesap

```text
pixel bottom-center -> world XY
distance_m = ||XY_t2 - XY_t1||
speed_kmh = distance_m / dt * 3.6
```

### Kalite Kapıları

```text
camera_static = true
homography_available = true
calibration_quality >= threshold
bottom_center inside road_roi
track_length_frames >= threshold
candidate_disagreement <= threshold
```

### Çıktılar

```json
{
  "speed_mode": "absolute_candidate",
  "speed_kmh_candidate": 47.8,
  "speed_range_kmh": [42.5, 53.6],
  "primary_speed_source": "homography_track",
  "fusion_confidence": 0.76,
  "decision_flags": [
    "not_for_legal_enforcement",
    "risk_decision_support_only"
  ]
}
```

### Beklenen Rapor Dili

Bu çıktı kalibre edilmiş sabit kamera koşulunda üretilen hız adayıdır. Hukuki hız ölçümü değildir.

## 4. SPEED-EXP-004D — Event/Evidence JSON Enrichment

### Amaç

Speed Fusion çıktısını event/evidence JSON içine denetlenebilir şekilde işlemek.

### Yazılacak Alanlar

```json
{
  "speed_mode": "relative",
  "speed_kmh_candidate": null,
  "speed_range_kmh": null,
  "relative_speed_score": 2.31,
  "relative_speed_label": "motion_anomaly",
  "fusion_confidence": 0.69,
  "primary_speed_source": "bbox_bottom_center_relative",
  "candidate_speeds": [],
  "track_quality": {},
  "geometry_quality": {},
  "plate_quality": {},
  "vehicle_dimension_prior": {},
  "fallback_reason": "no_reliable_metric_calibration",
  "decision_flags": [
    "not_for_legal_enforcement",
    "risk_decision_support_only"
  ]
}
```

### Evidence İlkeleri

* Her hız sinyali kaynak adıyla yazılmalı.
* Düşük güvenli candidate silinmemeli; `failure_flags` ile saklanmalı.
* Hız yoksa sistem susmalı ve `unavailable` döndürmeli.
* Kalibrasyon yoksa km/s alanı boş kalmalı.

## Uygulama Sırası

1. `SPEED-EXP-004A` relative speed script'i yaz.
2. Mevcut `TRK-EXP-001` track/event skeleton üzerinden 3 video için çalıştır.
3. Manual review için CSV/JSON/Markdown raporu üret.
4. `VATTR-EXP-001` notebook'u smoke run ile çalıştır.
5. `SPEED-EXP-004B` içinde VATTR + plate-scale sanity-check bağla.
6. Demo için yarı manuel homografi noktaları belirlenirse `SPEED-EXP-004C` aç.
7. `SPEED-EXP-004D` ile event/evidence JSON'u zenginleştir.

## İlk Aktif Notebook

Hız yol haritasındaki ilk teknik adım `SPEED-EXP-004A` olsa da bu adım Colab notebook değil, lokal script olarak uygulanmalıdır.

Kullanıcının Colab'da aktif çalıştırması gereken ilk notebook:

```text
notebooks/VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab.ipynb
```

Bu notebook `SPEED-EXP-004B` için gerekli vehicle dimension prior modelini üretir. İlk koşu `SMOKE_MODE=True` ile yapılmalıdır.

## Riskler

* Ground truth hız yokken MAE/RMSE raporlanmamalıdır.
* Plate-scale tek başına mutlak hız iddiası için yeterli değildir.
* VATTR marka/model veya gövde tipi yanılırsa wheelbase prior yanlış hız ölçeği üretir.
* Homografi yoksa `absolute_candidate` üretilmemelidir.
* Kalibrasyonun sahne dışına taşması özellikle uzak araçlarda ciddi hata üretebilir.

## Başarı Kriterleri

`SPEED-EXP-004A` için:

* 3 test videosunda her target track için relative speed sinyali üretilmeli.
* Kötü track varsa `unavailable` dönebilmelidir.
* Manual review için speed-mode dağılımı ve feature tabloları üretilmelidir.

`VATTR-EXP-001` için:

* BoxCars dataset erişimi doğrulanmalı.
* Smoke mode eğitim tamamlanmalı.
* Checkpoint, label map, dimension-prior table ve summary üretilmelidir.

`SPEED-EXP-004B` için:

* Plate-scale ve VATTR sonuçları aynı event/track altında toplanmalıdır.
* Çelişkili sinyaller `candidate_disagreement_high` olarak işaretlenmelidir.

`SPEED-EXP-004C` için:

* Homografi kalite metriği olmadan `absolute_candidate` üretilmemelidir.
