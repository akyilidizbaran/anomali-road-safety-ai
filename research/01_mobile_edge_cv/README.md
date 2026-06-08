# Araştırma 1 - Gerçek Zamanlı Mobil-Edge Computer Vision Mimarisi

## Amaç

Telefon kamerasından alınan canlı görüntünün edge bilgisayara nasıl aktarılacağı, edge üzerinde yapay zeka çıkarımının nasıl çalışacağı ve sonuçların mobil uygulamaya nasıl düşük gecikmeyle döneceği araştırılır.

## Alt Başlıklar

* Android CameraX canlı frame alma.
* ImageAnalysis pipeline.
* Frame encode/decode maliyeti.
* WebSocket ile frame gönderimi.
* WebRTC/WHIP ile düşük gecikmeli video akışı.
* REST’in canlı video için neden tek başına yeterli olmayabileceği.
* Aynı Wi-Fi/local ağ demosu.
* Public domain/backend üzerinden demo.
* FastAPI + WebSocket mimarisi.
* Edge bilgisayarda Python inference server.
* MacBook üzerinde local edge/backend runtime.
* Mobil overlay için anlık JSON response.
* 720p source frame/stream ve model input resize maliyeti.
* FPS/latency ölçümü.
* 1 saniye altı uçtan uca gecikme hedefi.
* 30 FPS preview, düşük frekanslı uzman model yaklaşımı.
* API key gelene kadar mock Number Verification/QoD entegrasyonu.

## Çıktı

Karar tablosu: WebSocket mi WebRTC mi, local edge mi cloud backend mi, frame mi stream mi?

## Sorulacak Nokta

İlk MVP için canlı aktarım protokolü kesin seçilecek mi?
