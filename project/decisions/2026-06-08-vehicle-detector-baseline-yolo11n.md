# Vehicle Detector Baseline - YOLO11n

Tarih: 2026-06-08

Karar:

İlk ölçülebilir araç tespiti baseline modeli **YOLO11n** olacak.

Bu karar final model seçimi değildir. Final araç detektörü, aynı veri/split protokolüyle yapılacak Colab fine-tune sonuçları ve MacBook runtime benchmark sonrası belirlenecektir.

Gerekçe:

* Araç tespiti pipeline'ın kök modelidir; tracking, hedef araç seçimi, plate/OCR, evidence ve risk fusion bu çıktıya bağlıdır.
* YOLO11n küçük model boyutu ve pratik Ultralytics train/val/predict/export akışıyla hızlı iterasyon sağlar.
* İlk hedef en yüksek mAP değil, output contract, tracking başlangıcı, evidence crop ve MacBook runtime ölçümünü hızlıca kurmaktır.
* YOLO11n, YOLO11s/YOLOv10/YOLOv8/RT-DETR adayları için ortak benchmark zemini oluşturur.

Etkilenen Alanlar:

* `research/02_vehicle_detection/`
* `models/benchmarks/vehicle_detection_comparison.csv`
* `models/experiments/vehicle_detection_experiment_template.md`
* `architecture/contracts/model_output_contract.md`
* `architecture/contracts/event.schema.json`
* `architecture/contracts/mobile_overlay_response.schema.json`
* `docs/04_yapay_zeka/01_arac_tespiti_takip.md`

Alternatifler:

* YOLO11s ile başlamak: kalite potansiyeli daha yüksek, fakat ilk iterasyon maliyeti daha fazla.
* YOLOv10n/s ile başlamak: düşük latency avantajı olabilir, fakat proje stack'inde ölçülmeden varsayılmamalı.
* YOLOv8n ile başlamak: daha stabil fallback, fakat YOLO11n ile başlamak daha güncel ve pratik.
* RT-DETR-L ile başlamak: mimari challenger, fakat ilk MVP için daha riskli.

Geri Dönüş Planı:

YOLO11n MacBook latency, output contract, tracking/evidence crop veya lisans açısından uygun çıkmazsa YOLOv8n stabil fallback, YOLO11s kalite adayı veya YOLOv10n/s düşük latency challenger olarak yeniden değerlendirilir.

Durum: Accepted as initial baseline
