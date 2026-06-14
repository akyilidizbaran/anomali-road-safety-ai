# VD-EXP-002 Fine-Tuned General Vehicle Detector Summary

## Kapsam

Bu rapor, `VD-EXP-002` Colab/Drive koşusundan çıkan fine-tuned YOLO11n vehicle detector durumunu özetler. Amaç, FTR raporundaki "Araç Tespiti / Veri Seti / Model Eğitimi / Test Sonuçları / Kondisyon Profili" bölümleri için izlenebilir kısa kanıt üretmektir.

Bu rapor final saha performansı iddiası değildir. Colab üzerinde BDD100K tabanlı model geliştirme sonucudur; lokal MacBook edge runtime ve 3 dark video smoke test ayrıca koşulmalıdır.

## Fine-Tuned Model Var mı?

Evet. General fine-tuned YOLO11n checkpoint Drive üzerinde mevcut.

| Alan | Değer |
|---|---|
| Experiment | `VD-EXP-002-GENERAL-YOLO11N` |
| Model ailesi | YOLO11n |
| Eğitim ortamı | Google Colab GPU |
| Dataset | BDD100K 4-class vehicle subset |
| Sınıflar | `car`, `bus`, `truck`, `motorcycle` |
| Drive checkpoint | `/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/VD-EXP-002/train/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt` |
| Drive file | https://drive.google.com/file/d/1bRBN58HyQYufsfKxVp87AEwAAZYAPnkr/view |
| Modified time | `2026-06-14T20:19:53.105Z` |
| Drive summary | https://drive.google.com/file/d/1XLLjbQPEcy-JEUyBa3ljoMIXXhOxbe0J |
| Local repo status | Checkpoint Git'e eklenmemiştir; `.pt` dosyaları ignore edilir. |

Lokal kullanım için checkpoint şu path'e kopyalanmalıdır:

```text
models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

## Dataset Özeti

VD-EXP-002 çıktısına göre BDD100K vehicle subset dağılımı:

| Split | Image | Vehicle BBox |
|---|---:|---:|
| train | 23055 | 251753 |
| val | 4918 | 54124 |
| test | 4931 | 54026 |

Condition profile kırılımı:

| Profile | Train | Val | Test |
|---|---:|---:|---:|
| `general` | 23055 | 4918 | 4931 |
| `night_low_light` | 10116 | 2220 | 2103 |
| `rain` | 1625 | 335 | 360 |
| `fog_low_visibility` | 28 | 3 | 11 |

Fog verisi bu splitte çok azdır; fog specialist eğitimi veya performans iddiası için yeterli değildir.

## General Fine-Tuned YOLO11n Metrikleri

| Split | mAP50 | mAP50-95 | Precision | Recall |
|---|---:|---:|---:|---:|
| validation | 0.488905 | 0.322091 | 0.647045 | 0.425098 |
| test | 0.506167 | 0.332283 | 0.632970 | 0.455739 |

Bu değerler FTR için kullanılabilir, ancak şu ifadeyle verilmelidir:

> BDD100K vehicle subset üzerinde fine-tune edilen YOLO11n general detector, test splitinde `mAP50=0.5062` ve `mAP50-95=0.3323` üretmiştir. Bu sonuçlar saha iddiası değil, veri seti tabanlı model geliştirme çıktısıdır.

## Specialist Deneylerinden Çıkan Karar

| Specialist | General baseline on same test | Specialist test | Karar |
|---|---:|---:|---|
| `night_low_light` | mAP50-95 0.318208, recall 0.460183 | mAP50-95 0.299556, recall 0.486511 | Candidate; active değil |
| `rain` | mAP50-95 0.318531, recall 0.385243 | mAP50-95 0.315180, recall 0.400426 | Candidate; active değil |
| `fog_low_visibility` | Yetersiz veri | Yetersiz veri | Skipped |

Night/rain specialist modelleri recall tarafında küçük artış gösterse de mAP50-95 tarafında general modele göre net avantaj üretmedi. Bu nedenle runtime/demo için aktif detector seçimi general fine-tuned YOLO11n olmalıdır.

## Condition Router Kararı

Condition-aware yaklaşım korunmalıdır, fakat ilk canlı runtime şu şekilde davranmalıdır:

```text
Condition classifier: profile tahmini üretir.
Router: specialist proven_better değilse general detector seçer.
Evidence: condition_profile, routing_reason ve fallback_used alanlarını kaydeder.
```

Bu karar raporda şu açıdan önemlidir:

* Sistem canlı frame'den ortam profilini saptamaya hazırlanır.
* Specialist model çağırma fikri korunur.
* Benchmark ile doğrulanmamış specialist model canlı sistemde körlemesine kullanılmaz.

## 3 Dark Video Deneme Durumu

Lokal 3 video denemesi şu anda **pending** durumdadır.

Neden:

* Fine-tuned `best.pt` Drive'da var, fakat lokal repo altında yok.
* Lokal Python ortamında `ultralytics` kurulu değil.
* Ağır annotated video çıktıları Git'e eklenmemelidir.

Tekrar üretilebilir koşu için script eklendi:

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_vehicle_detection_video_smoke.py \
  --weights models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

Script şunları üretir:

* JSON: `models/benchmarks/artifacts/VD-EXP-002-general-yolo11n-dark-smoke-summary.json`
* Rapor: `testing/reports/vd_exp_002_dark_video_smoke_test_summary.md`
* Annotated video: `runs/vehicle_detection/VD-EXP-002-dark-smoke/`

## FTR'ye Aktarılabilecek Net Bilgiler

* Kullanılan ana veri seti: BDD100K vehicle subset.
* Model ailesi: YOLO11n.
* Eğitim ortamı: Google Colab GPU.
* Runtime hedefi: MacBook local edge/backend.
* Class mapping: `car`, `bus`, `truck`, `motorcycle`.
* Condition-aware split üretildi.
* General model active baseline seçildi.
* Night/rain specialist deneyleri yapıldı ama aktif modele terfi ettirilmedi.
* Fog specialist veri yetersizliği nedeniyle ertelendi.
* Canlı frame condition classifier/router ayrı modül olarak sıradaki iş olmalı.

## Kaçınılması Gereken İddialar

* "Model saha ortamında kesin doğrulukla araç tespit eder."
* "Night/rain specialist general modelden daha iyidir."
* "Fog modeli eğitildi ve hazır."
* "Pretrained YOLO11n ile fine-tuned YOLO11n sayısal olarak doğrudan kıyaslandı."

Pretrained baseline konusunda özel not: COCO pretrained `yolo11n.pt` class ID'leri ile BDD 4-class label ID'leri bire bir aynı olmadığı için, eski pretrained mAP çıktıları final model kıyası olarak kullanılmamalıdır.

## Sonuç

Fine-tuned general YOLO11n modeli mevcuttur ve aktif vehicle detector baseline olarak kullanılmalıdır. Ancak FTR'deki "kondisyon profili ve saptanması" adımını tam cevaplamak için sıradaki model, canlı frame'den çalışan `condition_profile` classifier/router olmalıdır.
