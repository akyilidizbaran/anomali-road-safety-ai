# Araştırma 11 - Model Optimizasyonu ve Deployment

## Amaç

30 FPS preview ve 1 saniye altı uçtan uca gecikme hedefi için model ve sistem optimizasyonunu planlamak.

İlk canlı inference çalışma ortamı MacBook üzerinde local edge/backend olacaktır. Google Colab eğitim/fine-tune ortamıdır; Android cihaz ilk aşamada kamera ve UI istemcisi olarak değerlendirilir.

## Alt Başlıklar

* ONNX ve kullanım nedeni.
* PyTorch -> ONNX export.
* ONNX Runtime.
* TensorFlow Lite.
* NNAPI.
* GPU delegate.
* Android odaklı yaklaşım.
* Edge’de TensorRT/OpenVINO/ONNX Runtime.
* MacBook üzerinde uygun runtime.
* FP16 quantization.
* INT8 quantization.
* Quantization-aware training.
* Pruning.
* Knowledge distillation.
* Model boyutu vs doğruluk.
* Latency benchmark.
* Frame skipping.
* Async inference.
* Pipeline profiling.

## Çıktı

MacBook edge runtime kararı, Android client varsayımı ve benchmark planı.
