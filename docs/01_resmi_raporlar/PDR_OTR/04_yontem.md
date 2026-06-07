# 4. Yöntem

## Resmi Beklenti

Yarışma aşamalarındaki görevler yerine getirilirken çalışma kurguları akış diyagramı ile anlatılmalıdır. Her aşama ayrı ele alınmalıdır.

## Önerilen Geliştirme Fazları

### Faz 1 - Temel Canlı Sistem

Çıktılar:

* Camera ekranı.
* Canlı görüntü alma.
* Edge bağlantısı.
* Araç bbox overlay.
* FPS/latency ölçümü.
* Temel event JSON.

### Faz 2 - Araç Takibi ve Hedef Araç

Çıktılar:

* Track ID.
* Target vehicle seçimi.
* Takip kararlılığı.
* Hedef araç overlay vurgusu.

### Faz 3 - Plaka Tespiti ve OCR

Çıktılar:

* Plaka kutusu.
* OCR metni.
* Karakter güvenleri.
* Türk plaka format doğrulama.
* Evidence kartı.

### Faz 4 - Evidence Sistemi

Çıktılar:

* Son 10 evidence kartı.
* Kanıt göster.
* Detay göster.
* Backend kayıtları.

### Faz 5 - Sahne/Hava/Yol Koşulu

Çıktılar:

* Weather/visibility etiketi.
* Güven skoru.
* Düşük görüşte QoD adaylığı.
* Uzman seçimine bağlamsal sinyal.

### Faz 6 - Şerit/Road Marking

Çıktılar:

* Şerit çizgisi overlay.
* Şerit yakınlığı.
* Şerit ihlali şüphesi.
* Risk sinyali.

### Faz 7 - Hız Kestirimi

Çıktılar:

* Kalibrasyon varsa km/s tahmini.
* Kalibrasyon yoksa göreli hız skoru.
* Hız hata metriği.

### Faz 8 - Sürücü/Yolcu ve Araç İçi Risk

Çıktılar:

* Sürücü görünür/görünmez.
* Yolcu sayısı.
* Telefon/sigara/kemer riski.
* Görüş yetersizse analiz güvenilir değil çıktısı.

## Sorulacak Noktalar

* Final demo için hangi fazlar zorunlu MVP kabul edilecek?
* Cabin risk fazı kontrollü demo olarak mı sunulacak?
