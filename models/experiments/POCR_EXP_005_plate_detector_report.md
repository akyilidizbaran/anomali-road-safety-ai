# POCR-EXP-005 - YOLO11n Plate Detector Fine-Tune Report

Tarih: 2026-06-17

## Durum

`POCR-EXP-005-YOLO11N-PLATE-DETECTOR` Colab koşusu tamamlandı. Bu çalışma yalnız **plaka tespiti** içindir; OCR, plaka metni doğruluğu veya hukuki/cezai karar iddiası içermez.

Notebook çıktısı:

```text
notebooks/POCR_EXP_005_YOLO11N_Plate_Detector_Colab_outsaved.ipynb
```

## Amaç

Mevcut lokal/pretrained plate detector baseline'ını koruyarak daha kapsamlı bir `license_plate` detector üretmek:

* Başlangıç modeli: resmi Ultralytics `yolo11n.pt`
* Görev: tek sınıf `license_plate` object detection
* Eğitim yaklaşımı: pretrained YOLO11n ağırlığından fine-tune
* Karşılaştırma baseline'ı: `models/checkpoints/plate/license_plate_detector.pt`

## Veri Kaynakları

Notebook iki Roboflow kaynağını indirdi, sınıf adlarını `license_plate` olarak normalize etti, duplicate/near-duplicate kontrolünden geçirip deterministik train/val/test ayrımı oluşturdu.

| Kaynak | Roboflow proje | Versiyon | Raw train | Raw val | Raw test | Not |
|---|---|---:|---:|---:|---:|---|
| Turkish Number Plates | `plakatanima-vnt3k/turkish-number-plates` | 2 | 4,857 | 419 | 208 | Türkiye plaka geometrisine en yakın birincil kaynak |
| Roboflow LPR | `roboflow-universe-projects/license-plate-recognition-rxg4e` | 13 | 98,798 | 2,048 | 1,020 | Hacim desteği; kendi split/dedup zorunlu |

Normalize edilmiş metadata:

```text
metadata rows: 106,432
metadata columns: 13
```

Final split dağılımı:

| Split | Kaynak | Görüntü | BBox |
|---|---|---:|---:|
| train | Roboflow LPR | 80,707 | 84,199 |
| train | Turkish Number Plates | 4,332 | 4,566 |
| val | Roboflow LPR | 10,113 | 10,533 |
| val | Turkish Number Plates | 523 | 553 |
| test | Roboflow LPR | 10,159 | 10,591 |
| test | Turkish Number Plates | 598 | 629 |

Toplam YOLO split kontrolü:

| Split | Image | Label |
|---|---:|---:|
| train | 85,039 | 85,039 |
| val | 10,636 | 10,636 |
| test | 10,757 | 10,757 |

## Eğitim Konfigürasyonu

| Alan | Değer |
|---|---|
| Model ailesi | YOLO11n |
| Başlangıç ağırlığı | `yolo11n.pt` |
| Sınıf sayısı | 1 |
| Sınıf adı | `license_plate` |
| Image size | 640 |
| Epoch | 80 |
| Batch | 48 |
| Patience | 20 |
| Workers | 4 |
| Seed | 42 |
| AMP | enabled |
| Cache | false |
| Donanım | NVIDIA L4, 22.5 GB VRAM |
| Ultralytics | 8.4.68 |
| Python / Torch | Python 3.12.13 / torch 2.11.0+cu128 |
| Eğitim süresi | 67,512.44 sn, yaklaşık 18.75 saat |
| Parametre | 2,582,347 |
| FLOPs | 6.3 GFLOPs |

Not: Notebook konfigürasyonu A100 odaklı yazılmıştı, fakat çıktı L4 GPU üzerinde çalıştığını gösteriyor. Rapor metninde donanım sonucu **L4** olarak yazılmalıdır.

## Çıktı Artifactleri

Drive yolları:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-last.pt
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.onnx
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/plate_detection/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-summary.json
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/plate_detection/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-dataset-metadata.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/experiments/POCR_EXP_005_plate_detector_report.md
```

Drive dosya doğrulaması:

| Dosya | Drive URL |
|---|---|
| Best `.pt` | https://drive.google.com/file/d/1DnmlwCEfGXyx0XYgzixPErnvY9IvlIOd/view |
| Last `.pt` | https://drive.google.com/file/d/1XvnFubavg1wX4LjI9gLy4LFxHJWZLfrm/view |
| Best `.onnx` | https://drive.google.com/file/d/1I22hfJ93AxH4m2CJQoJKPrr-iTSs5ePv/view |
| Drive report | https://drive.google.com/file/d/1N3adcW_NGSaN2s0in37h1lI2ht-500Lu/view |

Yerel test için önerilen hedef path:

```text
models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt
```

Model ağırlığı Git'e eklenmemelidir.

## Metrikler

### Yeni Fine-Tuned Model

| Split | Images | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|---:|
| val | 10,636 | 11,086 | 0.9947 | 0.9891 | 0.9948 | 0.8569 |
| test | 10,757 | 11,220 | 0.9951 | 0.9907 | 0.9948 | 0.8543 |

### Mevcut Baseline

| Split | Images | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|---:|
| val | 10,636 | 11,086 | 0.9722 | 0.9576 | 0.9754 | 0.6097 |
| test | 10,757 | 11,220 | 0.9726 | 0.9586 | 0.9754 | 0.6089 |

### Baseline'a Göre Fark

| Split | Delta precision | Delta recall | Delta mAP@0.5 | Delta mAP@0.5:0.95 |
|---|---:|---:|---:|---:|
| val | +0.0224 | +0.0315 | +0.0193 | +0.2473 |
| test | +0.0225 | +0.0321 | +0.0194 | +0.2454 |

## UFPR External Benchmark Durumu

UFPR-ALPR dış benchmark koşmadı:

```json
{
  "status": "missing",
  "message": "UFPR zip/folder not found in Drive; external benchmark skipped."
}
```

Bu nedenle modelin domain dışı genelleme başarısı henüz kanıtlanmış değildir. FTR'de bu model için güçlü iddia kurulacaksa en azından:

* `Test/video_1-3.mp4` target ROI smoke/manual review,
* mümkünse UFPR-ALPR veya izinli farklı bir dış test seti,
* düşük ışık/uzak plaka failure-case incelemesi

tamamlanmalıdır.

## Değerlendirme

Bu koşu teknik olarak başarılıdır:

* Roboflow indirme ve split path sorunları çözülmüş.
* Raw dataset ağaçları Drive'a kopyalanmadığı için önceki Drive I/O hatası tekrarlanmamış.
* Büyük YOLO dataset local Colab runtime altında üretilmiş.
* 80 epoch tamamlanmış.
* `best.pt`, `last.pt`, ONNX, summary JSON ve Markdown report Drive'a yazılmış.
* Yeni model, aynı val/test split üzerinde mevcut baseline'dan özellikle `mAP@0.5:0.95` tarafında belirgin daha iyi çıkmıştır.

Fakat model henüz otomatik olarak runtime'a terfi ettirilmemelidir:

* Lokal 3 dark demo video üzerinde target-ROI smoke test yapılmadı.
* Manual plate bbox correctness sayımı yapılmadı.
* OCR metni veya Türk plaka format doğruluğu ölçülmedi.
* UFPR dış benchmark eksik.
* Roboflow kaynaklarında lisans ve olası dataset contamination notları final rapor öncesi tekrar doğrulanmalıdır.

## Karar

`POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt`, **aktif aday plate detector** olarak işaretlenir. Mevcut `license_plate_detector.pt` baseline korunur. Runtime/default detector değişimi, lokal target video smoke test ve manuel review sonrasında yapılacaktır.

## Sonraki Adım

1. `best.pt` dosyasını Drive'dan yerel path'e indir:

```text
models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt
```

2. 3 demo video üzerinde detector-only smoke test çalıştır:

```bash
python3 scripts/benchmarks/run_plate_detection_smoke.py \
  --models yolo \
  --plate-yolo-weights models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt \
  --runs-dir runs/plate_ocr/POCR-EXP-005-local-smoke \
  --report testing/reports/pocr_exp_005_local_smoke_summary.md
```

3. Annotated videolar ve plate crop'lar manuel incelenir.
4. Model POCR-EXP-001 baseline'a göre target video üzerinde de daha iyi ise OCR fazına geçilir.
