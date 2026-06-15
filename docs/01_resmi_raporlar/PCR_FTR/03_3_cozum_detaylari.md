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

COND-EXP-001 kapsamında ilk canlı-frame kondisyon profili yaklaşımı MobileNetV3-Small ile kurulmuştur. Model araç tespiti yapmaz; ham/video frame'den düşük frekansta hava, ışık ve görüş profili üretir. Router bu çıktıyı detector seçimi ve evidence/QoD bağlam sinyali olarak kullanır.

Önerilen runtime davranışı:

```text
frame sample -> MobileNetV3 condition classifier
             -> condition_profile + confidence
             -> temporal smoothing
             -> detector router
             -> general detector fallback veya kanıtlanmış specialist detector
```

Router kuralı gereği `condition_profile=night_low_light` veya `rain` dönmesi tek başına specialist detector seçimi için yeterli değildir. Specialist detector yalnız ilgili condition benchmark'ında general detector'a göre kanıtlı üstünlük sağlarsa aktif edilir; aksi durumda general YOLO11n detector güvenli fallback olarak korunur.

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
