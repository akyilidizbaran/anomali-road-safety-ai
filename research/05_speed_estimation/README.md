# Araştırma 5 - Hız Kestirimi

## Amaç

Tek kamera görüntüsünden otomatik/yaklaşık hız adayları üretmek, bu adayların güvenini
ölçmek ve güvenilirlik yetersizse göreli hız/risk yaklaşımına düşmek.

Güncel ana plan:

* `automatic_speed_estimation_redesign_2026_06_20.md`

Güncel kapanış durumu:

* `SPEED-EXP-005D` mevcut hız sinyallerini birleştirerek hız modülünü FTR ana yolunu
  bloklamayacak şekilde kapatır.
* `testing/reports/speed_exp_005d_candidate_fusion.md`
* `models/benchmarks/artifacts/speed/SPEED-EXP-005D-candidate-fusion/speed_exp_005d_candidate_fusion_summary.json`

## Alt Başlıklar

* Otomatik monocular speed candidate üretimi.
* Bbox-track + araç boyutu prior tabanlı otomatik sahne geometri tahmini.
* FARSEC-lite depth + track + average vehicle length yaklaşımı. Bu faz artık zorunlu
  sıradaki iş değil; FTR ana modülleri tamamlandıktan sonra future/support olarak ele alınabilir.
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

Mevcut çıktı: `SPEED-EXP-005D` ile otomatik approximate km/s adayları + göreli hareket/risk metriği
+ fallback gerekçesi.

Final/future scope çıktısı: otomatik adayların ground-truth veya kontrollü sürüşle hata metriği; manuel
homografi yalnız opsiyonel doğrulama protokolü olarak kalır.
