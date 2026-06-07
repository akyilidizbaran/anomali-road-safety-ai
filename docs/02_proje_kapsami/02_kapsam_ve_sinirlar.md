# Kapsam ve Sınırlar

## Kapsam İçi

* Android mobil uygulama.
* Kullanıcı adı/şifre girişi.
* Number Verification API request/response akışı.
* CameraX mantığında canlı kamera akışı.
* Edge/backend video aktarımı.
* Ortam, hava, ışık ve görüş koşulu analizi.
* Araç tespiti.
* Araç takibi.
* Tek hedef araç seçimi.
* Genel yol durumu.
* Araç dışı kullanıcı/yaya durumu.
* Plaka tespiti ve OCR.
* Şerit veya road marking analizi.
* Kalibrasyon varsa hız kestirimi.
* Kalibrasyon yoksa göreli hız/risk skoru.
* Görünürlük yeterliyse sürücü/yolcu/cabin risk analizi.
* Normal mod ve kritik mod ayrımı.
* QoD adaylığı ve seçici aktivasyon.
* Number Verification için gerçek adapter ve geliştirme aşamasında mock yapı.
* Evidence package.
* Test metrikleri.

## Kapsam Dışı

* Otomatik ceza kesme.
* Hukuki kusur belirleme.
* Her koşulda mutlak hız garantisi.
* Her araç için tam uzman model analizi.
* QoD’nin her riskte otomatik açılması.
* KVKK izni olmayan kişisel veri saklama.

## Varsayımlar

* Edge cihaz ilk geliştirme döneminde MacBook olabilir.
* 5G API keyleri gelene kadar Number Verification ve QoD mock/stub çalışabilir.
* Gerçek API key sağlandığında login sonrası Number Verification request’i gerçek servise bağlanır.
* MVP single-target mode ile başlar.
* Multi-target mode ayarlardan açılabilecek genişletme olabilir.
* Cabin risk yalnız kontrollü ve görünürlüğü yeterli videolarda güvenilir gösterilebilir.

## Sorulacak Noktalar

* Sürücü/yolcu riskleri final kapsamına zorunlu mu, opsiyonel mi?
