# 3.1 Genel Sistem Mimarisi ve Veri Akış Şeması

## Resmi Beklenti

Mobil uygulama, sunucu, yapay zeka modeli ve dış API’lerin iletişimini gösteren sistem blok şeması verilmelidir. Canlı video verisinin sunucuya nasıl iletildiği, yapay zeka modeliyle nasıl işlendiği ve sonuçların kullanıcı arayüzüne hangi hız/protokol ile döndürüldüğü net anlatılmalıdır.

## Proje Mimarisi

Sistem beş katmanlı düşünülmelidir:

1. **Mobil Uygulama:** Android/Kotlin, login, Number Verification durumu, CameraX, canlı kamera, overlay, evidence ve ayarlar.
2. **Video Aktarım:** İlk MVP’de WebSocket/frame aktarımı veya aynı ağ stream; ileride düşük gecikmeli 5G/WebRTC seçeneği.
3. **Edge/Backend:** FastAPI tabanlı inference server, preprocessing, queue, event fusion.
4. **Yapay Zeka Pipeline:** Normal mod, kritik mod, uzman modeller, risk skoru.
5. **5G API ve Evidence:** Number Verification, riskli araç özelinde QoD adapter, event evidence store.

## Veri Akışı

1. Kullanıcı adı/şifre doğrulaması sonrası Number Verification API kullanıcı/cihaz/oturum eşleşmesini kontrol eder.
2. Doğrulama başarılıysa mobil kamera frame üretir.
3. Frame encode edilir ve edge/backend’e gönderilir.
4. Backend frame ID, timestamp ve kalite bilgisi ekler.
5. Normal mod önce ortam/sahne, hava, ışık ve görüş bağlamını üretir.
6. Araç tespiti, takip, hedef araç seçimi, genel yol durumu ve araç dışı kullanıcı/yaya durumu çıkarılır.
7. Risk ön değerlendirme skoru hesaplanır.
8. Riskli araç sinyali oluşursa QoD aday/request akışı tetiklenir.
9. Kritik eşik aşılırsa uzman model seçici çalışır.
10. Plaka/OCR, hız, şerit, araç dışı kullanıcı yakınlığı veya cabin risk modülleri ilgili ROI üzerinde çalışır.
11. Model sonuçları event JSON’da birleştirilir.
12. Evidence görseli ve metadata saklanır.
13. Mobil UI’ye overlay ve event bilgisi döner.

## Diyagramda Bulunması Gereken Bloklar

* Android CameraX
* Login/Auth
* Number Verification adapter
* Mobile UI screens
* Video uplink
* Edge inference server
* Normal mode pipeline
* Critical mode expert models
* QoD orchestration
* Event Evidence Store
* REST/WebSocket response

## Darboğaz Önleme Mantığı

Her model her frame’de çalıştırılmaz. Kamera preview 30 FPS hedeflerken, normal analiz hattı 15-30 FPS aralığında çalışabilir. Ortam/sahne analizi düşük frekanslı erken bağlam sinyali olarak çalışabilir. OCR, lane, araç dışı kullanıcı yakınlığı ve cabin risk gibi ağır veya ROI bağımlı görevler olay bazlı ya da düşük frekanslı çalıştırılır. Bu seçici çalışma sistemi edge kaynaklarını korur.

## Sorulacak Noktalar

* İlk canlı aktarım protokolü WebSocket mi WebRTC mi olacak?
* Demo edge cihazı kesin MacBook mu?
* 5G API gerçek bağlantı zamanı belli mi?
