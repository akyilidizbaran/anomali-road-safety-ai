# Araştırma 5 - Hız Kestirimi

## Amaç

Tek kamera görüntüsünden otomatik/yaklaşık hız adayları üretmek, bu adayların güvenini
ölçmek ve güvenilirlik yetersizse göreli hız/risk yaklaşımına düşmek.

Güncel ana plan:

* `automatic_speed_estimation_redesign_2026_06_20.md`

## Alt Başlıklar

* Otomatik monocular speed candidate üretimi.
* Bbox-track + araç boyutu prior tabanlı otomatik sahne geometri tahmini.
* FARSEC-lite depth + track + average vehicle length yaklaşımı.
* Plate-scale v2 fallback/sanity-check.
* Homografi tabanlı hız tahmini. Opsiyonel fallback/doğrulama olarak korunur.
* Sabit kamera gereksinimi.
* Referans mesafe ölçümü. Zorunlu runtime girdisi değil; yalnız doğrulama/fallback olarak kullanılır.
* Pikselden dünya koordinatına dönüşüm.
* Araç merkez noktası veya alt orta nokta takibi.
* Zaman farkı ile hız hesaplama.
* Temporal smoothing.
* Kalibrasyon yoksa göreli hız/risk.
* Monocular speed estimation literatürü.
* Optical flow tabanlı yöntemler.
* BrnoCompSpeed, AI City Challenge.
* MAE/RMSE km/s metrikleri.
* MVP için göreli hız / motion anomaly metriği.
* Final scope için kalibrasyon ve kontrollü hız videosu denemesi.

## Çıktı

MVP çıktısı: otomatik approximate km/s adayları + göreli hareket/risk metriği + fallback gerekçesi.

Final scope çıktısı: otomatik adayların ground-truth veya kontrollü sürüşle hata metriği; manuel homografi
yalnız opsiyonel doğrulama protokolü olarak kalır.
