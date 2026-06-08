# Araç Tespiti ve Takip

## Amaç

Canlı görüntüde araçları tespit etmek, sınıflandırmak, takip ID’si vermek ve hedef araç seçimi için kararlı çıktı üretmek.

## Araç Tespiti

Aday modeller:

* YOLO11n: ilk ölçülebilir baseline.
* YOLO11s: dengeli kalite adayı.
* YOLOv10n/s: düşük latency ve NMS-free challenger.
* YOLOv8n: stabil fallback.
* RT-DETR-L: transformer challenger.
* NanoDet-Plus veya YOLOv6Lite: yalnız on-device fallback ihtimali güçlenirse.

Sınıflar:

* car
* bus
* truck
* motorcycle

## İlk Baseline Kararı

İlk araç tespiti deneyi **YOLO11n** ile başlatılır. Bu final model seçimi değildir. Final karar:

* Colab fine-tune sonuçları,
* MacBook runtime benchmark,
* output contract uyumu,
* tracking/evidence katkısı,
* export başarısı,
* lisans değerlendirmesi

sonrasında verilir.

Araştırma ve karar dosyaları:

* `research/02_vehicle_detection/model_candidates.md`
* `research/02_vehicle_detection/dataset_candidates.md`
* `research/02_vehicle_detection/benchmark_plan.md`
* `research/02_vehicle_detection/finetune_plan.md`
* `research/02_vehicle_detection/decision_vehicle_detector_v1.md`

## Takip

Aday tracker:

* ByteTrack.
* BoT-SORT.
* DeepSORT.
* OC-SORT.

## Metrikler

Araç tespiti:

* mAP@0.5
* mAP@0.5:0.95
* Precision
* Recall
* F1
* Class AP
* Mean latency
* P95 latency
* Pipeline FPS
* Evidence crop usability
* Tracking initialization usability

Takip:

* IDF1
* MOTA
* ID switch
* Track stability

## Açık Sorular

* Takip için ByteTrack mi BoT-SORT mu seçilecek?
