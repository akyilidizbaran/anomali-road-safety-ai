# Decision - Vehicle Detector v1

Tarih: 2026-06-08

## Karar Durumu

Status: **Provisional baseline selected**

Bu dosya final model seçimi değildir. İlk ölçülebilir baseline kararını kaydeder.

## Seçilen İlk Baseline

İlk deney modeli: **YOLO11n**

## Gerekçe

YOLO11n:

* hızlı Colab iterasyonu sağlar,
* küçük model boyutuyla MacBook runtime benchmark için uygundur,
* Ultralytics train/val/predict/export akışıyla hızlı prototipleme sağlar,
* ilk amaç olan output contract + tracking/evidence pipeline uyumluluğunu hızlı test etmeye uygundur.

## Final Karar İçin Yarışacak Modeller

* YOLO11n
* YOLO11s
* YOLOv10n
* YOLOv10s
* YOLOv8n
* RT-DETR-L
* NanoDet-Plus-m veya YOLOv6Lite-M, yalnız on-device fallback ihtiyacı güçlenirse

## Karar Verme Yöntemi

Final seçim public benchmark skoruna göre yapılmayacak.

Final seçim şu birleşimle yapılacak:

1. Public reference score.
2. Bizim Colab validation/test sonuçlarımız.
3. MacBook runtime p95 latency ve FPS.
4. Output contract uyumu.
5. Tracking başlatma ve target selection katkısı.
6. Evidence crop kullanılabilirliği.
7. Export ve lisans riski.

## Lisans Notu

Ultralytics tabanlı modeller AGPL-3.0 / Enterprise lisans riskleri nedeniyle ürünleşme aşamasında yeniden değerlendirilecektir. Yarışma prototipi için kullanılacak model ve ağırlıkların lisans durumu ayrıca doğrulanmadan final raporda kesin ticari uygunluk iddiası kurulmaz.

## Yeniden Karar Koşulları

YOLO11n aşağıdaki durumlardan biri gerçekleşirse baseline olmaktan çıkar:

* BDD100K/UA-DETRAC validation sonuçları belirgin düşük kalır.
* MacBook p95 latency hedefi aşılır.
* Output contract dönüşümü kırılgan çıkar.
* Tracking ve evidence crop kalitesi yetersiz olur.
* Lisans değerlendirmesi kullanım amacına uygun bulunmaz.

## Sonraki Aksiyonlar

* `benchmark_plan.md` uygulanacak.
* `finetune_plan.md` içindeki VD-EXP-001 ve VD-EXP-002 hazırlanacak.
* `models/benchmarks/vehicle_detection_comparison.csv` gerçek sonuçlar için genişletilecek.
* `architecture/contracts/model_output_contract.md` VehicleDetectionOutput alanları güncellenecek.
