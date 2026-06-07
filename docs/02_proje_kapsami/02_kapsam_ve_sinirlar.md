# Kapsam ve Sınırlar

## Kapsam İçi

* Android mobil uygulama.
* CameraX mantığında canlı kamera akışı.
* Edge/backend video aktarımı.
* Araç tespiti.
* Araç takibi.
* Tek hedef araç seçimi.
* Plaka tespiti ve OCR.
* Sahne/hava/görüş koşulu analizi.
* Şerit veya road marking analizi.
* Kalibrasyon varsa hız kestirimi.
* Kalibrasyon yoksa göreli hız/risk skoru.
* Görünürlük yeterliyse sürücü/yolcu/cabin risk analizi.
* Normal mod ve kritik mod ayrımı.
* QoD adaylığı ve seçici aktivasyon.
* Number Verification için adapter/mock yapı.
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
* MVP single-target mode ile başlar.
* Multi-target mode ayarlardan açılabilecek genişletme olabilir.
* Cabin risk yalnız kontrollü ve görünürlüğü yeterli videolarda güvenilir gösterilebilir.

## Sorulacak Noktalar

* Final demo kesin canlı kamera mı olacak, kontrollü video da kabul edilecek mi?
* Sürücü/yolcu riskleri final kapsamına zorunlu mu, opsiyonel mi?
