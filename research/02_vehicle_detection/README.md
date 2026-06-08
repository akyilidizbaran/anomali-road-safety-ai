# Araştırma 2 - Araç Tespiti ve Tek Hedef Araç Seçimi

## Amaç

Projenin ilk yapay zeka çekirdeği olan araç tespitini ve hedef araç seçimini netleştirmek.

## Güncel Karar

İlk ölçülebilir baseline **YOLO11n** olarak seçilmiştir. Bu final model seçimi değildir; final karar Colab fine-tune sonuçları, MacBook runtime benchmark, output contract uyumu, tracking/evidence katkısı ve lisans değerlendirmesi sonrası verilecektir.

Deep research raporu `deep_research/deep_research_report.md` altında tutulur. Uygulama ve karar takibi aşağıdaki aksiyon dosyalarıyla yapılır.

## Alt Başlıklar

* YOLOv8/v9/v10/v11 nano/small karşılaştırması.
* RT-DETR edge uygunluğu.
* COCO, BDD100K, KITTI, UA-DETRAC veri setleri.
* Car, bus, truck, motorcycle sınıfları.
* Tek hedef araç seçimi.
* Ekran merkezi, bbox büyüklüğü, confidence, track stability, plate visibility skorları.
* Çok araçlı trafik ama single-target inference.
* Araç ROI çıkarımı.
* Araç tespitinin plaka, hız, sürücü, şerit modüllerine girdi olması.
* mAP, precision, recall, F1.
* Model boyutu, FPS, latency.
* YOLO formatı, COCO formatı, veri dönüşümü.
* 720p source frame -> model input resize politikası.
* Colab fine-tune metrikleri ile MacBook runtime metriklerinin ayrı tutulması.

## Çıktı

Başlangıç araç detektörü, sınıf listesi, hedef araç skoru ve benchmark tablosu.

## Aksiyon Dosyaları

* `model_candidates.md`: model kısa listesi, roller ve lisans riskleri.
* `dataset_candidates.md`: veri seti adayları, kullanım rolü ve sınıf mapping.
* `benchmark_plan.md`: public skor, Colab benchmark ve MacBook runtime benchmark planı.
* `finetune_plan.md`: Colab deney sırası ve kayıt standardı.
* `condition_specific_detector_routing.md`: dark/rain/fog gibi koşullara göre detector profile seçimi.
* `decision_vehicle_detector_v1.md`: ilk baseline kararı ve yeniden karar koşulları.
* `deep_research/`: derin araştırma raporu ve kaynak listesi.
