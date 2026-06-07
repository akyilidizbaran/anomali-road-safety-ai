# 3.2 Çözüm Mimarisi

## Resmi Beklenti

Ham videonun sisteme girişinden etiketlenmiş çıktıların üretilmesine kadar süreç mimari diyagramlar, bileşenler ve arayüz özetleriyle açıklanmalıdır.

## Kuşbakışı Akış

1. Mobil kamera ham video/frame üretir.
2. Frame edge/backend sistemine gönderilir.
3. Preprocess katmanı resize, normalize, timestamp ve frame ID üretir.
4. Normal mode pipeline araç tespiti, takip, hedef araç seçimi ve sahne analizi yapar.
5. Risk pre-decision skoru hesaplanır.
6. Kritik mod gerekiyorsa uzman modeller çağrılır.
7. Event fusion modeli tüm çıktıları tek event JSON’da birleştirir.
8. Evidence store görüntü ve metadata kaydeder.
9. Mobil UI overlay ve event sonuçlarını gösterir.

## Arayüz Özetleri

* `WS /stream`: Canlı frame gönderimi ve overlay response.
* `GET /events/recent`: Son evidence kartları.
* `GET /events/{event_id}`: Detay ve kanıt paketi.
* `POST /qod/request`: QoD adapter.
* `GET /system/status`: Pipeline sağlık bilgisi.

## Diyagram Notu

Diyagramda normal mod ve kritik mod ayrı renk veya bölümlerle gösterilmelidir. QoD, ana pipeline’dan ayrı ama karar noktasına bağlı adapter olarak çizilmelidir.

## Sorulacak Noktalar

* API endpoint isimleri kesinleşecek mi?
* LLM açıklama katmanı backend içinde mi ayrı servis mi olacak?
