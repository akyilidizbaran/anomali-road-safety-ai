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

### Stage 0A - Local Dark Manual Smoke Test

Amaç: Mevcut 3 dark video üzerinde hazır YOLO11n modelinin pipeline içinde çalışıp çalışmadığını görmek.

Veri:

* `Test/video_1.mp4`
* `Test/video_2.mp4`
* `Test/video_3.mp4`

Koşul:

* Video dosyaları Git'e eklenmez.
* Bu set training verisi değildir.
* İlk condition profile `dark` olarak etiketlenir.
* Router başlangıçta `dark` modunu çağırabilir, fakat ayrı dark model henüz yoksa `general` YOLO11n detector fallback çalışır.
* Her benchmark sonrası video çıktısı manuel kontrol edilir.
* Accuracy ve failure case notları model/deney kaydıyla yazılır.
* Disk/memory yükü için video dosyaları benchmark turu sonrası silinebilir.

Çıktı:

* Manuel detection accuracy notu.
* False positive / false negative örnekleri.
* Dark profile için threshold/preprocessing ihtiyacı.
* Evidence crop usable / not usable kararı.
* Tracking başlatılabilir / başlatılamaz kararı.

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

Status: **Active next phase as of 2026-06-10.**

Bu aşama tamamlanmadan fine-tune aktif çalışmaya alınmayacak. Amaç, fine-tune öncesinde hangi pretrained model ailesinin pipeline için en uygun olduğunu ölçmektir.

### Stage 1 - Colab Fine-Tune Baseline

Amaç: Aynı veri/split üzerinde road-domain adaptation.

Status: **Deferred / TODO as of 2026-06-10.**

BDD100K Colab notebook ve mapping hazır tutulacak; ancak aktif sıra pretrained baseline benchmark ve tracking entegrasyonudur.

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

## Manual Review Accuracy

İlk dark video setinde ground truth annotation olmadığı için otomatik mAP üretmek doğru değildir.

Bu aşamada manuel review ile şu oranlar tutulur:

* görünür araç sayısı,
* doğru tespit edilen araç sayısı,
* kaçırılan araç sayısı,
* yanlış pozitif sayısı,
* doğru sınıf oranı,
* bbox kullanılabilirlik oranı,
* evidence crop kullanılabilirlik oranı.

Bu metrikler raporda "manual review score" olarak adlandırılmalı; public benchmark mAP gibi sunulmamalıdır.

## Benchmark CSV

Makine-okunur sonuçlar `models/benchmarks/vehicle_detection_comparison.csv` içinde tutulur.

Bu CSV'ye fake sayı girilmez. Her sonuç bir deney dosyası, kaynak veri ve commit SHA ile izlenebilir olmalıdır.
