# Vehicle Detection Benchmark Plan

## Amaç

Araç tespiti modelini yalnız public benchmark skoruyla değil, proje pipeline'ı içindeki gerçek katkısıyla değerlendirmek.

## Benchmark Sorusu

Benchmark'ı yalnız yapılmış çalışmaların en iyi skorları üzerinden seçmeyeceğiz.

Doğru yaklaşım üç katmanlıdır:

1. **Public reference score:** Literatür/dokümantasyondaki COCO veya dataset skorları modelin kısa listeye girip girmeyeceğini belirler.
2. **Project validation score:** Aynı veri/split/protokol ile bizim Colab ortamımızda ölçülen detection başarımı model seçiminin teknik temelidir.
3. **Runtime pipeline score:** MacBook local edge runtime üzerinde p95 latency, FPS, export, JSON/evidence/tracking uyumu final kararı belirler.

Public skorlar tek başına final karar değildir; sadece aday seçimi ve önceliklendirme sağlar.

## Benchmark Aşamaları

### Stage 0 - Pretrained Zero Fine-Tune Baseline

Amaç: COCO-pretrained modelin proje domaininde fine-tune olmadan ne kadar çalıştığını görmek.

Modeller:

* YOLO11n
* YOLO11s
* YOLOv10n
* YOLOv10s
* YOLOv8n

Çıktı:

* İlk latency/FPS ölçümü.
* İlk JSON output uyumluluğu.
* Domain gap gözlemi.

### Stage 1 - Colab Fine-Tune Baseline

Amaç: Aynı veri/split üzerinde road-domain adaptation.

Veri:

* BDD100K 4 sınıf mapping.
* Video-level split.

Ölçüm:

* mAP@0.5
* mAP@0.5:0.95
* precision
* recall
* F1
* class AP
* confusion matrix

### Stage 2 - Fixed-Camera Adaptation / Test

Amaç: Göğüs yüksekliği/sabit yol kenarı kamera senaryosuna yaklaşmak.

Veri:

* UA-DETRAC selected subset.
* CityFlow selected subset, gerekiyorsa.

Ölçüm:

* Occlusion alt kümesi.
* Night/low-light alt kümesi.
* Multi-vehicle scene.
* Detection stability.
* Tracker-ready continuity.

### Stage 3 - MacBook Runtime Benchmark

Amaç: Demo ortamında çalışabilirlik.

Koşul:

* Android 720p source frame veya replay.
* MacBook local edge/backend.
* Model input resize 640 başlangıç.

Ölçüm:

* Mean latency.
* p95 latency.
* Pipeline FPS.
* CPU/GPU/RAM.
* Model load time.
* ONNX export success.
* Quantization attempt result, gerekiyorsa.
* Event JSON üretim süresi.
* Evidence crop usability.

## Karar Skoru

| Kategori | Ağırlık | İçerik |
|---|---:|---|
| Detection quality | 35 | mAP, precision, recall, F1, class AP |
| Real-time performance | 25 | FPS, mean latency, p95 latency, pipeline FPS |
| Deployment/export | 15 | ONNX/TFLite/NCNN/OpenVINO export, MacBook runtime uyumu |
| Robustness/domain generalization | 15 | gece, blur, yağmur, occlusion, fixed-camera, small-object |
| Fine-tune/maintenance practicality | 10 | Colab kolaylığı, dokümantasyon, ekip uygulanabilirliği |

## Minimum MVP Kabul Kriteri

Sayısal eşikler ilk benchmark turundan sonra sabitlenir. İlk kriterler:

* Detection output contract hatasız üretilmeli.
* `detections: []` durumu hata sayılmamalı.
* Evidence crop üretilecek bbox kalitesi sağlanmalı.
* Single-target senaryoda tracker başlatılabilir olmalı.
* MacBook p95 detection latency canlı pipeline bütçesini bozmamalı.
* Model seçiminde yalnız mAP değil, tracking/evidence katkısı da dikkate alınmalı.

## Benchmark CSV

Makine-okunur sonuçlar `models/benchmarks/vehicle_detection_comparison.csv` içinde tutulur.

Bu CSV'ye fake sayı girilmez. Her sonuç bir deney dosyası, kaynak veri ve commit SHA ile izlenebilir olmalıdır.
