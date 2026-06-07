# Architecture Alanı

Bu klasör sistem mimarisi için diyagram, contract ve akış dosyalarını barındırır.

## Alt Klasörler

* `diagrams`: Mermaid, draw.io veya görsel diyagram kaynakları.
* `contracts`: API, event JSON, model input/output contract dosyaları.
* `flows`: Login/Number Verification, normal/kritik mod, evidence, riskli araçta QoD ve mobil akışlar.

## Ana Akış

* `flows/auth_normal_qod_flow.md`: Kullanıcı doğrulama, ortam analizi, normal detection, riskli araç, QoD ve evidence uçtan uca akışı.
* `flows/live_inference_flow.md`: Canlı inference akışı.
* `flows/evidence_generation_flow.md`: Evidence üretim akışı.

## Ana Contractlar

* `contracts/backend_api.md`
* `contracts/event.schema.json`
* `contracts/mobile_overlay_response.schema.json`
* `contracts/qod_status_enum.md`
