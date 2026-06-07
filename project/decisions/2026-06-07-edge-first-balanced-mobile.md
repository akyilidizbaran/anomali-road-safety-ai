# Decision: Edge First, Balanced Mobile

## Date

2026-06-07

## Decision

Mobil cihaz kamera, UI ve overlay sorumluluğunu üstlenir; ağır yapay zeka çıkarımı edge/backend tarafında çalışır.

## Rationale

Mobil cihaz kaynaklarını korumak, model çeşitliliğini artırmak ve 5G/QoD anlatısını güçlendirmek için edge-first mimari daha uygundur.

## Impact

* Backend API contractları kritik hale gelir.
* Mobil uygulama inference server yanıtlarını görselleştirir.
* Model export ve latency benchmark edge hedefiyle değerlendirilir.
