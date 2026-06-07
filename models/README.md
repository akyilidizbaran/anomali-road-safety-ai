# Models Alanı

Bu klasör model geliştirme çıktıları için ayrılmıştır.

## Alt Klasörler

* `checkpoints`: Eğitim checkpointleri.
* `exports`: ONNX/TFLite gibi export dosyaları.
* `benchmarks`: Latency, FPS, model size sonuçları.
* `experiments`: Deney notları ve configler.

## Model Versiyonlama

Örnek isim:

```text
vehicle_yolo_v1
plate_ocr_v1
lane_model_v1
scene_resnet18_v1
```

Model versiyonu event JSON içinde görünmelidir.

## Template ve Benchmark Dosyaları

* `MODEL_CARD_TEMPLATE.md`
* `EXPERIMENT_TEMPLATE.md`
* `benchmarks/vehicle_detection_comparison.csv`
* `experiments/vehicle_detection_yolo_baseline.md`
