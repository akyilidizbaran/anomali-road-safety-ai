# Model Output Contract

Bu dosya runtime AI pipeline içindeki modüllerin standart output sözleşmesini tanımlar. Amaç backend, mobile overlay, event fusion, evidence package ve rapor dokümanlarının aynı alan adlarıyla konuşmasıdır.

Genel kurallar:

* Her output `frame_id` veya ilişkili `track_id` ile izlenebilir olmalıdır.
* Her model output içinde `model_version` bulunmalıdır.
* Her modül `status` alanı taşımalıdır.
* Bilinmeyen veya çalışmamış modüller `unknown`, `not_run`, `not_available`, `not_visible` gibi açık state değerleriyle temsil edilmelidir.
* Confidence değerleri 0-1 aralığında tutulmalıdır.

## FramePreprocessOutput

### Purpose

Ham frame verisini model inputları için normalize eder ve frame metadata’sını standardize eder.

### Required Fields

* `frame_id`
* `timestamp_utc`
* `source_resolution`
* `processed_resolution`
* `image_format`
* `status`

### Optional Fields

* `rotation`
* `crop_region`
* `calibration_profile_id`
* `preprocess_latency_ms`

### Confidence Fields

Bu modülde confidence yerine kalite metrikleri kullanılır.

### Failure / Unknown States

* `ok`
* `decode_failed`
* `unsupported_format`
* `missing_metadata`

### Example

```json
{
  "frame_id": "frame_000123",
  "timestamp_utc": "2026-06-08T10:30:12Z",
  "source_resolution": "1920x1080",
  "processed_resolution": "1280x720",
  "image_format": "jpeg",
  "status": "ok",
  "preprocess_latency_ms": 6.4
}
```

## SceneVisibilityOutput

### Purpose

Hava, ışık, görüş ve temel yol bağlamını model güveni, QoD adaylığı ve uzman routing kararları için üretir.

### Required Fields

* `frame_id`
* `status`
* `weather`
* `lighting`
* `visibility`
* `confidence`

### Optional Fields

* `road_surface`
* `glare`
* `rain_level`
* `fog_level`
* `quality_flags`
* `model_version`

### Confidence Fields

* `confidence`
* `weather_confidence`
* `lighting_confidence`
* `visibility_confidence`

### Failure / Unknown States

* `ok`
* `unknown`
* `not_run`
* `low_confidence`

### Example

```json
{
  "frame_id": "frame_000123",
  "status": "ok",
  "weather": "rain",
  "lighting": "low_light",
  "visibility": "limited",
  "road_surface": "wet",
  "confidence": 0.82,
  "model_version": "scene_visibility_v1"
}
```

## VehicleDetectionOutput

### Purpose

Frame içindeki araçları bulur. Pipeline’ın kök model çıktısıdır.

### Required Fields

* `frame_id`
* `status`
* `detections`
* `model_version`

### Optional Fields

* `timestamp_utc`
* `source_resolution`
* `processed_resolution`
* `input_size`
* `source_frame_ref`
* `confidence_threshold`
* `inference_latency_ms`
* `postprocess_latency_ms`
* `nms_threshold`
* `iou_threshold`
* `class_filter`

### Confidence Fields

Her detection içinde:

* `confidence`
* `detection_quality_score`

bulunmalıdır. `confidence` tek başına risk kararı veya hedef araç kararı için yeterli değildir; tracking stability, scene/visibility context ve evidence quality ile birlikte yorumlanmalıdır.

### Detection Object Fields

Her detection objesi aşağıdaki alanları taşımalıdır:

* `detection_id`
* `class_name`
* `class_id`
* `bbox_xyxy`
* `bbox_xywh`
* `area_px`
* `confidence`
* `detection_quality_score`

Opsiyonel detection alanları:

* `center_xy`
* `source_crop_ref`
* `is_target_candidate`
* `quality_flags`

### Bounding Box Convention

* `bbox_xyxy`: `[x1, y1, x2, y2]`. Evidence crop ve overlay üretimi için ana koordinattır.
* `bbox_xywh`: `[center_x, center_y, width, height]`. Tracking, hız/motion anomaly ve hedef araç seçimi için yardımcı koordinattır.
* Koordinatlar source frame koordinat sisteminde tutulmalıdır. Model input resize sonrası üretilen bbox tekrar source frame'e ölçeklenmelidir.

### Failure / Unknown States

* `ok`
* `not_run`
* `no_vehicle_detected`
* `low_quality_frame`
* `model_error`

`no_vehicle_detected` hata değildir. Bu durumda `detections: []` dönülür ve pipeline normal şekilde devam eder.

### Example

```json
{
  "frame_id": "frame_000123",
  "timestamp_utc": "2026-06-08T10:30:12Z",
  "status": "ok",
  "model_version": "vehicle_detector_yolo11n_v1",
  "source_resolution": "1280x720",
  "processed_resolution": "640x640",
  "input_size": 640,
  "confidence_threshold": 0.25,
  "nms_threshold": 0.7,
  "class_filter": ["car", "bus", "truck", "motorcycle"],
  "detections": [
    {
      "detection_id": "det_000123_001",
      "class_name": "car",
      "class_id": 0,
      "bbox_xyxy": [320, 180, 760, 540],
      "bbox_xywh": [540, 360, 440, 360],
      "center_xy": [540, 360],
      "area_px": 158400,
      "confidence": 0.93,
      "detection_quality_score": 0.9,
      "is_target_candidate": true,
      "quality_flags": []
    }
  ],
  "inference_latency_ms": 31.2,
  "postprocess_latency_ms": 4.1
}
```

### Empty Detection Example

```json
{
  "frame_id": "frame_000124",
  "status": "no_vehicle_detected",
  "model_version": "vehicle_detector_yolo11n_v1",
  "source_resolution": "1280x720",
  "processed_resolution": "640x640",
  "detections": [],
  "inference_latency_ms": 29.8
}
```

## TrackingOutput

### Purpose

Araç detection çıktılarını zamansal track ID’lere bağlar.

### Required Fields

* `frame_id`
* `status`
* `tracks`
* `tracker_version`

### Optional Fields

* `lost_tracks`
* `new_tracks`
* `track_history_length`
* `tracking_latency_ms`

### Confidence Fields

* `track_confidence`
* `track_stability`

### Failure / Unknown States

* `ok`
* `not_run`
* `no_active_track`
* `unstable_tracks`
* `tracker_error`

### Example

```json
{
  "frame_id": "frame_000123",
  "status": "ok",
  "tracker_version": "bytetrack_v1",
  "tracks": [
    {
      "track_id": "TRK-17",
      "bbox": [320, 180, 760, 540],
      "class_name": "car",
      "track_confidence": 0.89,
      "track_stability": 0.91,
      "history_frames": 42
    }
  ]
}
```

## TargetVehicleOutput

### Purpose

Normal modda izlenen araçlar arasından ağır uzman modeller için hedef/riskli aracı seçer.

### Required Fields

* `frame_id`
* `status`
* `target_track_id`
* `target_score`
* `selection_reasons`

### Optional Fields

* `candidate_tracks`
* `target_bbox`
* `target_roi`
* `pre_risk_score`

### Confidence Fields

* `target_score`
* `selection_confidence`

### Failure / Unknown States

* `selected`
* `no_target`
* `not_run`
* `ambiguous`
* `low_confidence`

### Example

```json
{
  "frame_id": "frame_000123",
  "status": "selected",
  "target_track_id": "TRK-17",
  "target_score": 0.84,
  "selection_confidence": 0.8,
  "selection_reasons": ["track_stable", "near_lane_boundary", "plate_visible"],
  "target_bbox": [320, 180, 760, 540]
}
```

## PlateDetectionOutput

### Purpose

Hedef araç ROI içinde plaka bölgesini tespit eder.

### Required Fields

* `frame_id`
* `track_id`
* `status`
* `detected`
* `model_version`

### Optional Fields

* `plate_bbox`
* `plate_crop_uri`
* `visibility`
* `failure_reason`

### Confidence Fields

* `confidence`
* `visibility_confidence`

### Failure / Unknown States

* `detected`
* `not_detected`
* `not_run`
* `blurred`
* `not_visible`
* `low_light`

### Example

```json
{
  "frame_id": "frame_000123",
  "track_id": "TRK-17",
  "status": "detected",
  "detected": true,
  "plate_bbox": [455, 410, 610, 455],
  "confidence": 0.86,
  "visibility": "limited",
  "model_version": "plate_detector_v1"
}
```

## OcrOutput

### Purpose

Tespit edilen plaka crop’ından metin okur.

### Required Fields

* `frame_id`
* `track_id`
* `status`
* `ocr_text`
* `confidence`
* `model_version`

### Optional Fields

* `format_valid`
* `char_confidences`
* `normalized_text`
* `failure_reason`

### Confidence Fields

* `confidence`
* `char_confidences`

### Failure / Unknown States

* `read`
* `not_read`
* `not_run`
* `low_confidence`
* `blurred`
* `not_visible`

### Example

```json
{
  "frame_id": "frame_000123",
  "track_id": "TRK-17",
  "status": "read",
  "ocr_text": "34ABC123",
  "normalized_text": "34ABC123",
  "format_valid": true,
  "confidence": 0.87,
  "model_version": "plate_ocr_v1"
}
```

## LaneOutput

### Purpose

Hedef aracın şerit/road marking ilişkisini ve şerit riski sinyalini üretir.

### Required Fields

* `frame_id`
* `track_id`
* `status`
* `lane_status`
* `confidence`
* `model_version`

### Optional Fields

* `lane_visibility`
* `boundary_distance_px`
* `lane_risk`
* `failure_reason`

### Confidence Fields

* `confidence`
* `lane_visibility_confidence`

### Failure / Unknown States

* `ok`
* `not_run`
* `marking_not_visible`
* `low_visibility`
* `unknown`

### Example

```json
{
  "frame_id": "frame_000123",
  "track_id": "TRK-17",
  "status": "ok",
  "lane_status": "near_lane_boundary",
  "lane_risk": "medium",
  "lane_visibility": "limited",
  "confidence": 0.76,
  "model_version": "lane_model_v1"
}
```

## SpeedOutput

### Purpose

Hedef araç hareketinden hız veya göreli hareket anomalisi üretir.

### Required Fields

* `frame_id`
* `track_id`
* `status`
* `mode`
* `confidence`

### Optional Fields

* `estimated_kmh`
* `relative_motion_score`
* `motion_anomaly`
* `calibration_profile_id`
* `window_frames`
* `failure_reason`
* `model_version`

### Confidence Fields

* `confidence`
* `calibration_confidence`

### Failure / Unknown States

* `ok`
* `not_run`
* `not_available`
* `insufficient_track_history`
* `calibration_missing`
* `low_confidence`

### Example

```json
{
  "frame_id": "frame_000123",
  "track_id": "TRK-17",
  "status": "ok",
  "mode": "relative_motion",
  "relative_motion_score": 0.72,
  "motion_anomaly": "fast_approach_suspected",
  "confidence": 0.68,
  "window_frames": 45
}
```

## CabinRiskOutput

### Purpose

Sürücü/yolcu veya araç içi risk sinyallerini yalnız görünürlük yeterliyse üretir.

### Required Fields

* `frame_id`
* `track_id`
* `status`
* `visibility`
* `confidence`

### Optional Fields

* `driver_detected`
* `passenger_count`
* `phone_risk`
* `seatbelt_status`
* `failure_reason`
* `model_version`

### Confidence Fields

* `confidence`
* `visibility_confidence`
* `phone_risk`

### Failure / Unknown States

* `ok`
* `not_run`
* `not_visible`
* `visibility_poor`
* `unknown`

### Example

```json
{
  "frame_id": "frame_000123",
  "track_id": "TRK-17",
  "status": "not_visible",
  "visibility": "not_visible",
  "confidence": 0.0,
  "failure_reason": "external_camera_cannot_see_cabin"
}
```

## ExternalUserOutput

### Purpose

Yaya, bisikletli, motosikletli veya yol kenarı insanlarını ve hedef araca yakınlıklarını temsil eder.

### Required Fields

* `frame_id`
* `status`
* `external_users`

### Optional Fields

* `proximity_to_target`
* `roadside_activity`
* `model_version`

### Confidence Fields

Her external user içinde `confidence` bulunmalıdır.

### Failure / Unknown States

* `ok`
* `not_run`
* `none_detected`
* `low_confidence`

### Example

```json
{
  "frame_id": "frame_000123",
  "status": "ok",
  "external_users": [
    {
      "type": "pedestrian",
      "bbox": [120, 240, 180, 410],
      "confidence": 0.84,
      "relative_position": "roadside",
      "risk_relation": "near_target_vehicle"
    }
  ],
  "model_version": "external_user_detector_v1"
}
```

## RiskFusionOutput

### Purpose

Normal/critical mode sinyallerini tek risk skoruna ve uzman çağırma kararına dönüştürür.

### Required Fields

* `frame_id`
* `status`
* `risk_score`
* `risk_level`
* `risk_reasons`
* `mode`

### Optional Fields

* `experts_called`
* `qod_status`
* `qod_reason`
* `routing_reasons`
* `thresholds`

### Confidence Fields

* `risk_score`
* `fusion_confidence`

### Failure / Unknown States

* `ok`
* `not_run`
* `insufficient_signal`
* `unknown`

### Example

```json
{
  "frame_id": "frame_000123",
  "status": "ok",
  "mode": "critical",
  "risk_score": 0.74,
  "risk_level": "high",
  "risk_reasons": ["sudden_lateral_motion", "low_visibility", "plate_blur"],
  "experts_called": ["plate_ocr", "lane", "evidence_quality"],
  "qod_status": "candidate",
  "qod_reason": "evidence_quality_may_improve",
  "fusion_confidence": 0.78
}
```

## EvidenceOutput

### Purpose

Event için görsel ve metadata referanslarını üretir.

### Required Fields

* `event_id`
* `status`
* `json_uri`
* `created_at_utc`

### Optional Fields

* `original_frame_uri`
* `overlay_image_uri`
* `target_vehicle_crop_uri`
* `plate_crop_uri`
* `technical_view_uri`
* `storage_backend`

### Confidence Fields

Evidence modülü confidence yerine completeness/quality kullanır:

* `evidence_quality_score`
* `metadata_completeness_score`

### Failure / Unknown States

* `created`
* `partial`
* `not_created`
* `storage_failed`
* `media_unavailable`

### Example

```json
{
  "event_id": "evt_2026_000001",
  "status": "created",
  "created_at_utc": "2026-06-08T10:30:14Z",
  "original_frame_uri": "/evidence/evt_2026_000001_frame.jpg",
  "overlay_image_uri": "/evidence/evt_2026_000001_overlay.jpg",
  "target_vehicle_crop_uri": "/evidence/evt_2026_000001_vehicle.jpg",
  "plate_crop_uri": "/evidence/evt_2026_000001_plate.jpg",
  "json_uri": "/evidence/evt_2026_000001.json",
  "evidence_quality_score": 0.81,
  "metadata_completeness_score": 0.92
}
```
