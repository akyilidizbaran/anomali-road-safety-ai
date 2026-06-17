# Experiments

Deney notları, configler ve küçük özet sonuçlar burada tutulabilir. Eğitim run çıktıları ve model ağırlıkları `runs/` altında lokal kalmalıdır.

## Aktif Deney Kartları

* `VD_EXP_002_bdd100k_yolo11n.md`: BDD100K tabanlı fine-tuned general YOLO11n vehicle detector ve specialist karşılaştırmaları.
* `VD_EXP_006_motorcycle_focus_yolo11n.md`: VD-EXP-002 üzerinde doğrulanan düşük ışık motorcycle/car confusion için targeted iyileştirme deney kartı.
* `COND_EXP_001_bdd100k_condition_classifier.md`: BDD100K metadata tabanlı MobileNetV3-Small condition profile classifier ve opsiyonel ResNet18 challenger.
* `POCR_EXP_001_plate_detector_baseline.md`: Mevcut lokal `license_plate_detector.pt` pretrained plate detector baseline kartı.
* `POCR_EXP_005_plate_detector_report.md`: Colab koşusu sonrası Drive'da üretilecek YOLO11n plate detector fine-tune raporu.
