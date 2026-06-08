# Event JSON Şeması

Ana teknik schema kaynağı `architecture/contracts/event.schema.json` dosyasıdır. Bu dosya rapor ve ekip içi açıklama için okunabilir örnek event yapısını gösterir.

Önerilen event yapısı:

```json
{
  "event_id": "evt_2026_000001",
  "timestamp_utc": "2026-06-07T13:45:21Z",
  "frame_id": "frame_000123",
  "source": {
    "device_id": "android_demo_001",
    "session_id": "session_001",
    "camera_mode": "live",
    "resolution": "1280x720",
    "fps": 30,
    "calibration_profile_id": "roadside_demo_calib_001"
  },
  "system": {
    "mode": "critical",
    "qod_status": "candidate",
    "number_verification_status": "mock_verified",
    "latency_ms": 420,
    "pipeline_fps": 24.8
  },
  "target_vehicle": {
    "status": "selected",
    "track_id": "TRK-17",
    "vehicle_type": "car",
    "bbox": [320, 180, 760, 540],
    "confidence": 0.93,
    "track_stability": 0.91,
    "selection_score": 0.84,
    "selection_reasons": ["track_stable", "near_lane_boundary", "plate_visible"]
  },
  "plate": {
    "status": "detected",
    "detected": true,
    "bbox": [455, 410, 610, 455],
    "ocr_status": "read",
    "ocr_text": "34ABC123",
    "format_valid": true,
    "confidence": 0.87
  },
  "speed": {
    "status": "ok",
    "mode": "homography_kmh",
    "estimated_kmh": 54.2,
    "relative_motion_score": null,
    "confidence": 0.72
  },
  "lane": {
    "status": "ok",
    "lane_status": "near_lane_boundary",
    "lane_risk": "medium",
    "confidence": 0.76
  },
  "driver_cabin": {
    "status": "not_run",
    "visibility": "limited",
    "driver_detected": null,
    "passenger_count": null,
    "phone_risk": null,
    "seatbelt_status": "unknown",
    "failure_reason": "not_in_mvp_scope"
  },
  "scene": {
    "status": "ok",
    "weather": "clear",
    "lighting": "day",
    "visibility": "good",
    "confidence": 0.91
  },
  "road_context": {
    "surface_condition": "dry",
    "lane_marking_visibility": "medium",
    "roadside_activity": "pedestrian_present",
    "confidence": 0.78
  },
  "external_users": [
    {
      "type": "pedestrian",
      "bbox": [120, 240, 180, 410],
      "confidence": 0.84,
      "relative_position": "roadside",
      "risk_relation": "near_target_vehicle"
    }
  ],
  "risk": {
    "risk_score": 0.68,
    "risk_level": "medium",
    "reasons": [
      "lane_boundary_proximity",
      "plate_readable",
      "target_vehicle_stable",
      "external_user_near_target_vehicle"
    ]
  },
  "routing_decision": {
    "experts_called": [
      "plate_ocr",
      "lane_road_marking",
      "speed_estimation",
      "evidence_generation"
    ],
    "routing_reasons": [
      "target_vehicle_stable",
      "lane_boundary_proximity",
      "plate_visible"
    ],
    "qod_reason": "plate_and_lane_evidence_quality_may_improve"
  },
  "models": {
    "vehicle_detector": "vehicle_yolo_v1",
    "tracker": "bytetrack_v1",
    "plate_detector": "plate_yolo_v1",
    "ocr": "plate_ocr_v1",
    "lane": "lane_model_v1",
    "scene": "scene_resnet18_v1"
  },
  "evidence": {
    "status": "created",
    "original_frame_uri": "/evidence/evt_2026_000001_frame.jpg",
    "overlay_image_uri": "/evidence/evt_2026_000001_overlay.jpg",
    "target_vehicle_crop_uri": "/evidence/evt_2026_000001_vehicle.jpg",
    "plate_crop_uri": "/evidence/evt_2026_000001_plate.jpg",
    "json_uri": "/evidence/evt_2026_000001.json",
    "evidence_quality_score": 0.81
  },
  "explanation": {
    "user_level_summary": "Sistem hedef aracı şerit sınırına yakın ve iz sürekliliği yüksek olduğu için orta riskli olarak işaretlemiştir.",
    "technical_summary": "Plate OCR, lane expert and speed estimation were called based on target stability, lane proximity and sufficient plate visibility.",
    "llm_used": false,
    "template_fallback_used": true,
    "source": "template"
  }
}
```
