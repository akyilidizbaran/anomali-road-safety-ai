# Event JSON Şeması

Önerilen event yapısı:

```json
{
  "event_id": "evt_2026_000001",
  "timestamp_utc": "2026-06-07T13:45:21Z",
  "source": {
    "device_id": "android_demo_001",
    "camera_mode": "live",
    "resolution": "1280x720",
    "fps": 30
  },
  "system": {
    "mode": "critical",
    "qod_status": "candidate",
    "number_verification_status": "mock_verified",
    "latency_ms": 420,
    "pipeline_fps": 24.8
  },
  "target_vehicle": {
    "track_id": 7,
    "vehicle_type": "car",
    "bbox": [320, 180, 760, 540],
    "confidence": 0.93
  },
  "plate": {
    "detected": true,
    "bbox": [455, 410, 610, 455],
    "ocr_text": "34ABC123",
    "format_valid": true,
    "confidence": 0.87
  },
  "speed": {
    "available": true,
    "mode": "homography_tracking",
    "estimated_kmh": 54.2,
    "confidence": 0.72
  },
  "lane": {
    "available": true,
    "lane_status": "near_lane_boundary",
    "risk": "medium",
    "confidence": 0.76
  },
  "driver_cabin": {
    "visibility": "limited",
    "driver_detected": true,
    "passenger_count": 1,
    "phone_risk": 0.61,
    "seatbelt_status": "unknown"
  },
  "scene": {
    "weather": "clear",
    "lighting": "day",
    "visibility": "good",
    "confidence": 0.91
  },
  "risk": {
    "risk_score": 0.68,
    "risk_level": "medium",
    "reasons": [
      "lane_boundary_proximity",
      "plate_readable",
      "target_vehicle_stable"
    ]
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
    "image_uri": "/evidence/evt_2026_000001.jpg",
    "crop_uri": "/evidence/evt_2026_000001_crop.jpg",
    "json_uri": "/evidence/evt_2026_000001.json"
  }
}
```
