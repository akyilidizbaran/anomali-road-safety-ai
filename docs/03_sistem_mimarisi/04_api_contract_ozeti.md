# API Contract Özeti

Bu dosya, mobil uygulama ile edge/backend arasında planlanan temel arayüzleri özetler.

## WebSocket

### `WS /stream`

Amaç: Mobil cihazdan frame/stream göndermek ve canlı overlay response almak.

Mobil gönderir:

```json
{
  "session_id": "session_001",
  "frame_id": "frame_000123",
  "timestamp_utc": "2026-06-07T12:00:00Z",
  "image_format": "jpeg",
  "resolution": "1280x720"
}
```

Backend döndürür:

```json
{
  "frame_id": "frame_000123",
  "mode": "normal",
  "latency_ms": 86,
  "scene": {
    "weather": "clear",
    "lighting": "day",
    "visibility": "good",
    "confidence": 0.91
  },
  "road_context": {
    "surface_condition": "dry",
    "lane_marking_visibility": "medium",
    "roadside_activity": "none",
    "confidence": 0.78
  },
  "detections": [],
  "external_users": [],
  "target_vehicle": null,
  "risk": {
    "risk_score": 0.12,
    "risk_level": "low"
  },
  "qod": {
    "status": "not_needed",
    "reason": "low_risk"
  }
}
```

## REST

### `POST /auth/login`

Kullanıcı adı/şifre doğrulamasını başlatır. Başarılı credential kontrolünden sonra backend Number Verification adapter üzerinden kullanıcı/cihaz/oturum eşleşmesini doğrular.

Mobil gönderir:

```json
{
  "username": "demo_user",
  "password": "********",
  "device_id": "android_demo_001",
  "phone_number_hint": "+90**********"
}
```

Backend döndürür:

```json
{
  "session_id": "session_001",
  "auth_status": "authenticated",
  "number_verification_status": "number_verified",
  "access_token": "mock_or_real_token",
  "expires_in_seconds": 1800
}
```

### `GET /events/recent`

Son evidence kartlarını döndürür.

### `GET /events/{event_id}`

Tek event için detay ve evidence metadata döndürür.

### `GET /system/status`

Kamera, edge, model, QoD, storage ve latency durumunu döndürür.

### `POST /qod/request`

QoD adapter üzerinden kalite talebi başlatır. API key yoksa mock response üretir.

QoD request, riskli araç özelinde tetiklenir. Her riskte otomatik aktif olmak zorunda değildir; backend QoD’nin karar güveni veya kanıt kalitesini artırıp artırmayacağını değerlendirir.

## Sorulacak Noktalar

* Frame taşıma binary WebSocket ile mi multipart ile mi yapılacak?
* Mobil uygulama önce REST mock ile mi başlayacak?
