# Araştırma 2 - Araç Tespiti ve Tek Hedef Araç Seçimi

## Amaç

Projenin ilk yapay zeka çekirdeği olan araç tespitini ve hedef araç seçimini netleştirmek.

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
