# 3.3 Yazılım Mimari Tasarımı

## Resmi Beklenti

Mobil uygulama ve sunucu bileşenleri tanımlanmalı; canlı video aktarımı, yapay zeka entegrasyonu, kullanıcı arayüzü ve eşzamanlı istek yönetimi açıklanmalıdır.

## Mobil Katman

* Dil: Kotlin.
* UI: Jetpack Compose / Material 3.
* Kamera: CameraX.
* Canlı sonuç: WebSocket.
* Evidence detay: REST.
* Giriş: Kullanıcı adı/şifre + Number Verification durumu.

Mobil ekranlar:

* **Login:** Kullanıcı adı/şifre, Number Verification pending/verified/rejected durumları.
* **Camera:** Canlı görüntü, bbox overlay, hedef araç, risk seviyesi, ortam/hava/ışık/görüş etiketi, genel yol ve araç dışı kullanıcı/yaya durumu, FPS/latency, QoD durumu.
* **Evidence:** Son 10 olay, kanıt göster, detay göster.
* **System:** Kamera, edge, model, backend, QoD ve evidence storage sağlığı.
* **Settings:** Risk threshold, OCR threshold, model modu, QoD mock, frame skipping, endpoint.

## Backend/Edge Katman

* Dil: Python.
* API: FastAPI.
* Stream: WebSocket.
* AI Runtime: PyTorch/ONNX Runtime.
* Storage: JSON metadata + image/crop/screenshot files.
* Queue: Asenkron frame ve inference kuyruğu.

## Eşzamanlılık

Backend canlı frame akışını alırken normal mod inference sürekli çalışır. Normal modda ortam/sahne bağlamı, araç tespiti/takip, genel yol durumu ve araç dışı kullanıcı/yaya sinyali birlikte değerlendirilir. Kritik olay penceresinde QoD aday/request akışı ve uzman modeller ayrı görevler olarak tetiklenir. Böylece tek bir ağır model çağrısı tüm sistemi kilitlemez.

## Sorulacak Noktalar

* Storage ilk etapta dosya sistemi mi SQLite mı?
* Mobil uygulama gerçek Android projesi olarak ne zaman başlayacak?
* API contract hangi sprintte sabitlenecek?
