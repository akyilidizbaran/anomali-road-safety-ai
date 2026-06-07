# Backend API Contract

Bu dosya mobil uygulama ile edge/backend arasındaki teknik contract için tek kaynak olarak tutulur. `docs/03_sistem_mimarisi/04_api_contract_ozeti.md` bu dosyanın özetidir.

## `POST /auth/login`

Kullanıcı adı/şifre doğrulamasını ve Number Verification eşleşmesini başlatır.

Request:

```json
{
  "username": "demo_user",
  "password": "********",
  "device_id": "android_demo_001",
  "phone_number_hint": "+90**********"
}
```

Response:

```json
{
  "session_id": "session_001",
  "auth_status": "authenticated",
  "number_verification_status": "number_verified",
  "access_token": "mock_or_real_token",
  "expires_in_seconds": 1800
}
```

## `WS /stream`

Mobil cihazdan frame/stream gönderir ve canlı overlay response alır.

Input metadata:

```json
{
  "session_id": "session_001",
  "frame_id": "frame_000123",
  "timestamp_utc": "2026-06-07T12:00:00Z",
  "image_format": "jpeg",
  "resolution": "1280x720"
}
```

Output schema:

* `architecture/contracts/mobile_overlay_response.schema.json`

## `GET /events/recent`

Son evidence kartlarını döndürür.

## `GET /events/{event_id}`

Tek event için detay ve evidence metadata döndürür.

## `GET /system/status`

Kamera, edge, model, QoD, storage ve latency durumunu döndürür.

## `POST /qod/request`

Riskli araç özelinde QoD kalite talebi başlatır. API key yoksa mock response üretir.
