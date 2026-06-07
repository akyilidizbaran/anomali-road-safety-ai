# 3.3 Çözüm Detayları

## Resmi Beklenti

Kullanılan derin öğrenme algoritmaları, sinir ağı mimarileri, ön işleme/son işleme adımları ve donanım/yazılım altyapısı teknik dille aktarılmalıdır.

## Detaylandırılacak Modüller

### Araç Tespiti

YOLO nano/small ailesi başlangıç modeli olarak seçilebilir. Sınıflar car, bus, truck, motorcycle olarak tutulabilir. Model gerçek zamanlı edge çıkarım hedefi nedeniyle hız/doğruluk dengesiyle seçilir.

### Takip

ByteTrack veya BoT-SORT, araç tespitlerini track ID’ye dönüştürür. Track stability, hedef araç seçimi, hız kestirimi ve evidence sürekliliği için kullanılır.

### Plaka/OCR

İki aşamalı mimari önerilir: vehicle ROI -> plate detector -> OCR. Türk plaka formatı regex/post-processing ile doğrulanır. OCR çıktısı temporal voting ile iyileştirilebilir.

### Hız

Sabit kamera ve referans mesafe varsa homografi + tracking ile km/s tahmini yapılır. Kalibrasyon yoksa mutlak hız iddiası yerine göreli hız/risk skoru verilir.

### Şerit

YOLOP/YOLOPv2 veya lane-specific modeller değerlendirilebilir. Hedef aracın alt merkez noktası ile şerit sınırları karşılaştırılır.

### Sahne/Hava/Görüş

ResNet18 baseline veya MobileNetV3/EfficientNet-lite gibi hafif sınıflandırıcılar kullanılabilir. Çıktı QoD ve uzman model seçimini etkiler.

### Cabin Risk

Görünürlük yeterliyse araç cam/ön bölge ROI’sinde sürücü, yolcu, telefon, sigara, kemer ve dikkat dağınıklığı sinyalleri aranır.

### Optimizasyon

* ONNX export.
* FP16/INT8 quantization.
* ROI inference.
* Frame skipping.
* Async inference.
* Model çalışma frekansı ayrıştırma.

## Sorulacak Noktalar

* Hangi runtime finalde kullanılacak: PyTorch, ONNX Runtime, TFLite?
* Edge cihaz değişebilir mi?
