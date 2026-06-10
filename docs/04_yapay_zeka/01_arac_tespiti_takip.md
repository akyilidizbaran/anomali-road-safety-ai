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

## Tracking Baseline Kararı

İlk tracking baseline **ByteTrack** olacaktır. İkinci alternatif **BoT-SORT** olarak tutulur ve ilk karşılaştırmada ReID kapalı çalıştırılır.

Gerekçe:

* Mevcut ihtiyaç, araç detection çıktılarının kararlı `track_id` değerlerine bağlanmasıdır.
* Kısa false negative ve 2-3 frame class flicker davranışları önce track-level class voting ve confidence smoothing ile ele alınmalıdır.
* Sabit yol kenarı kamera demo senaryosunda ReID ilk MVP için zorunlu değildir.
* ByteTrack düşük confidence detection'ları association sürecinde kullanması nedeniyle dark/low-light smoke test için pratik ilk adaydır.

Tracking çıktıları:

* `track_id`
* `track_age_frames`
* `bbox_history`
* `center_history`
* `stable_class`
* `class_votes`
* `track_stability`
* `pixel_displacement`
* `best_frame_id`
* `best_crop_ref`

Araştırma ve karar dosyaları:

* `research/03_tracking/deep_research/deep_research_report.md`
* `research/03_tracking/benchmark_plan.md`
* `research/03_tracking/decision_tracking_baseline_v1.md`

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
* HOTA
* MOTA
* MOTP
* ID switch
* Track fragmentation
* Track stability

## Açık Sorular

* ByteTrack ve BoT-SORT dark test videolarında kaç ID switch üretecek?
* BoT-SORT ReID kapalı mod ByteTrack'e göre anlamlı avantaj sağlayacak mı?
