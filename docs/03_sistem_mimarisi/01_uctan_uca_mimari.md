# Uçtan Uca Sistem Mimarisi

## Ana Bileşenler

1. **Mobile Client:** Kamera, UI, overlay, evidence ekranları.
2. **Transport Layer:** Frame/stream aktarımı.
3. **Edge Inference Server:** AI modellerinin çalıştığı backend.
4. **Mode Orchestrator:** Normal/kritik mod karar mantığı.
5. **Expert Models:** OCR, speed, lane, cabin risk gibi uzman modüller.
6. **QoD/5G Adapter:** Number Verification ve QoD servis entegrasyonu.
7. **Evidence Store:** Görsel kesit, screenshot ve JSON metadata.
8. **Explanation Layer:** Structured JSON çıktısından insan okunur açıklama.

## Veri Akışı

```mermaid
flowchart TD
  A["Android CameraX"] --> B["Frame/Stream Transport"]
  B --> C["Edge Preprocess"]
  C --> D["Normal Mode: Vehicle Detection + Tracking + Scene"]
  D --> E["Target Vehicle Selection"]
  E --> F["Risk Pre-Decision"]
  F -->|Low Risk| G["Live Overlay Response"]
  F -->|High Risk| H["Critical Mode Expert Selector"]
  H --> I["Plate OCR / Speed / Lane / Cabin"]
  I --> J["Event Fusion JSON"]
  J --> K["QoD Decision"]
  J --> L["Evidence Store"]
  K --> L
  L --> M["Mobile Evidence UI"]
  G --> N["Mobile Camera UI"]
```

## Darboğaz Kontrolü

* Araç tespiti ve tracking normal modda önceliklidir.
* OCR ve cabin risk her frame’de çalışmaz.
* Scene analysis düşük frekanslı olabilir.
* Evidence sadece olay bazlı üretilir.
* QoD yalnız aday olduğunda çağrılır.

## Ana Tasarım Kararı

Edge/backend tarafı ağır çıkarımı üstlenir; mobil taraf kamera, kullanıcı deneyimi ve sonuç gösterimini üstlenir. Bu ayrım mobil cihaz kaynaklarını korur.
