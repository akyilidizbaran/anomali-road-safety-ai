# 3.1 Genel Sistem Mimarisi ve Veri Akış Şeması

## Resmi Beklenti

Mobil uygulama, sunucu, yapay zeka modeli ve dış API’lerin iletişimini gösteren sistem blok şeması verilmelidir. Canlı video verisinin sunucuya nasıl iletildiği, yapay zeka modeliyle nasıl işlendiği ve sonuçların kullanıcı arayüzüne hangi hız/protokol ile döndürüldüğü net anlatılmalıdır.

## Proje Mimarisi

Sistem beş katmanlı düşünülmelidir:

1. **Mobil Uygulama:** Android/Kotlin, CameraX, canlı kamera, overlay, evidence ve ayarlar.
2. **Video Aktarım:** İlk MVP’de WebSocket/frame aktarımı veya aynı ağ stream; ileride düşük gecikmeli 5G/WebRTC seçeneği.
3. **Edge/Backend:** FastAPI tabanlı inference server, preprocessing, queue, event fusion.
4. **Yapay Zeka Pipeline:** Normal mod, kritik mod, uzman modeller, risk skoru.
5. **5G API ve Evidence:** Number Verification, QoD adapter, event evidence store.

## Veri Akışı

1. Mobil kamera frame üretir.
2. Frame encode edilir ve edge/backend’e gönderilir.
3. Backend frame ID, timestamp ve kalite bilgisi ekler.
4. Normal mod araç tespiti, takip, hedef araç seçimi ve sahne analizi yapar.
5. Risk ön değerlendirme skoru hesaplanır.
6. Kritik eşik aşılırsa uzman model seçici çalışır.
7. Plaka/OCR, hız, şerit veya cabin risk modülleri ilgili ROI üzerinde çalışır.
8. Model sonuçları event JSON’da birleştirilir.
9. Evidence görseli ve metadata saklanır.
10. Mobil UI’ye overlay ve event bilgisi döner.

## Diyagramda Bulunması Gereken Bloklar

* Android CameraX
* Mobile UI screens
* Video uplink
* Edge inference server
* Normal mode pipeline
* Critical mode expert models
* QoD orchestration
* Number Verification adapter
* Event Evidence Store
* REST/WebSocket response

## Darboğaz Önleme Mantığı

Her model her frame’de çalıştırılmaz. Kamera preview 30 FPS hedeflerken, normal analiz hattı 15-30 FPS aralığında çalışabilir. OCR, scene classification, lane ve cabin risk gibi ağır görevler olay bazlı veya düşük frekanslı çalıştırılır. Bu seçici çalışma sistemi edge kaynaklarını korur.

## Sorulacak Noktalar

* İlk canlı aktarım protokolü WebSocket mi WebRTC mi olacak?
* Demo edge cihazı kesin MacBook mu?
* 5G API gerçek bağlantı zamanı belli mi?
