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
  "detections": [],
  "target_vehicle": null,
  "risk": {
    "risk_score": 0.12,
    "risk_level": "low"
  }
}
```

## REST

### `GET /events/recent`

Son evidence kartlarını döndürür.

### `GET /events/{event_id}`

Tek event için detay ve evidence metadata döndürür.

### `GET /system/status`

Kamera, edge, model, QoD, storage ve latency durumunu döndürür.

### `POST /qod/request`

QoD adapter üzerinden kalite talebi başlatır. API key yoksa mock response üretir.

## Sorulacak Noktalar

* Frame taşıma binary WebSocket ile mi multipart ile mi yapılacak?
* Mobil uygulama önce REST mock ile mi başlayacak?
