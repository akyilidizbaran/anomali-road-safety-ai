# POCR-EXP-005 — YOLO11n Plate Detector Fine-Tune Colab Runbook

Tarih: 2026-06-15

## Amaç

Bu çalışma smoke test değildir. Amaç, mevcut lokal plate detector baseline'ını koruyup daha kapsamlı bir plate detection modeli üretmektir:

```text
Baseline: models/checkpoints/plate/license_plate_detector.pt
Yeni deney: POCR-EXP-005-YOLO11N-PLATE-DETECTOR
```

Notebook:

```text
notebooks/POCR_EXP_005_YOLO11N_Plate_Detector_Colab.ipynb
```

## Kullanılacak Veri Kaynakları

### 1. Birincil Veri

```text
Turkish Number Plates
Roboflow workspace: plakatanima-vnt3k
Roboflow project: turkish-number-plates
Version: 2
Format: yolov8
License: CC BY 4.0 olarak listeleniyor
```

Kaynak:

```text
https://universe.roboflow.com/plakatanima-vnt3k/turkish-number-plates
```

### 2. Hacim Destek Verisi

```text
License Plate Recognition
Roboflow workspace: roboflow-universe-projects
Roboflow project: license-plate-recognition-rxg4e
Version: 13
Format: yolov8
License: CC BY 4.0 olarak listeleniyor
```

Kaynak:

```text
https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e
```

Not: Bu veri için reported Roboflow metrikleri final kanıt sayılmayacak. Notebook kendi duplicate kontrolünü, class normalization adımını ve train/val/test split üretimini yapar.

### 3. External Benchmark

```text
UFPR-ALPR
Kullanım: external benchmark / generalization check
Training: hayır
```

Kaynak:

```text
https://github.com/raysonlaroca/ufpr-alpr-dataset
https://web.inf.ufpr.br/vri/databases/ufpr-alpr/
```

UFPR otomatik indirilmeyecek. Resmi koşullar akademik/non-commercial erişim ve lisans onayı istediği için, zip dosyası izinli şekilde elde edilip Drive'a elle konulmalıdır.

## Colab'da Senin Yapman Gerekenler

1. Runtime olarak **A100 GPU** seç.
   * A100 yoksa L4 çalışır.
   * T4 ile de çalışır ama batch'i düşürmek gerekir.
2. Colab Secrets içine şunu ekle:

```text
ROBOFLOW_API_KEY
```

3. Notebook'u aç:

```text
notebooks/POCR_EXP_005_YOLO11N_Plate_Detector_Colab.ipynb
```

4. `Run all` çalıştır.

5. Eğer Roboflow otomatik indirme başarısız olursa, Roboflow UI'dan YOLOv8 export zip'lerini indirip Drive'da şu klasöre koy:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/plate_detection/raw/manual_zips/
```

Beklenen manuel zip adları:

```text
turkish_number_plates_yolov8.zip
roboflow_lpr_yolov8.zip
```

6. UFPR-ALPR için izinli zip elde edilirse şu yola koy:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/plate_detection/raw/manual_zips/ufpr_alpr.zip
```

Alternatif olarak extracted klasör:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/plate_detection/raw/ufpr_alpr/
```

## Notebook'un Çalışma Mantığı

Önceki BDD100K sorunlarından çıkarılan derslerle notebook şu şekilde tasarlandı:

* Google Drive mount edilir ama ağır eğitim lokal `/content/anomali-road-safety-ai-work/` altında yapılır.
* Roboflow verileri önce local path'e iner.
* Drive yalnız kalıcı cache ve final artifact alanı olarak kullanılır.
* Veri seti yoksa net hata verir; boş split üretip eğitime başlamaz.
* Raw Roboflow split'lerine kör güvenmez; tüm kayıtlar merge edilir, class `license_plate` olarak normalize edilir.
* Exact SHA1 ve conservative pHash duplicate kontrolü yapılır.
* Deterministik `80/10/10` train/val/test split üretilir.
* Mevcut `license_plate_detector.pt` baseline olarak değerlendirilir.
* UFPR varsa external benchmark, yoksa skipped olarak raporlanır.

## 2026-06-16 Crash Teşhisi ve Düzeltme

`POCR_EXP_005_YOLO11N_Plate_Detector_Colab_outcrashed.ipynb` çıktısına göre problem API key değildir.

Gözlenen durum:

* `Roboflow key present: True`
* `turkish_number_plates` dataset'i indirildi ve extract edildi.
* `roboflow_lpr` dataset'i indirildi ve extract edildi.
* Crash Cell 5'te oluştu:

```text
RuntimeError: No labeled images found. Check Roboflow download/export format.
```

Kök neden:

* Roboflow `data.yaml` dosyaları bazı exportlarda `../train/images`, `../valid/images` gibi relative path yazıyor.
* Önceki notebook yalnız tek relative path çözümü kullandığı için gerçek `train/images`, `valid/images`, `test/images` klasörlerini bulamadı.
* Bu nedenle `split_counts: {'train': 0, 'val': 0, 'test': 0}` göründü.

Düzeltme:

* Cell 5 artık Roboflow'un farklı export yapılarını destekler:
  * `train/images`
  * `valid/images`
  * `val/images`
  * `test/images`
  * `../train/images`
  * root altında fallback `images` discovery
* `images -> labels` eşlemesi daha dayanıklı hale getirildi.
* Hiç kayıt bulunmazsa klasör ağacı preview basar; böylece boş split yerine teşhis üretir.

Tekrar çalıştırma:

* Düzeltilmiş notebook'u aç.
* `Run all` çalıştırabilirsin.
* Veriler Drive cache'e kopyalandığı için Cell 4 büyük ihtimalle yeniden indirme yapmadan `[drive cache -> local]` veya `[local exists]` çıktısı verir.
* Eğer hâlâ aynı Colab runtime açıksa, güncellenmiş Cell 5 kodunu içeren notebook ile Cell 5'ten itibaren devam etmek de yeterlidir.

## 2026-06-16 İkinci Crash Teşhisi ve Düzeltme

`POCR_EXP_005_YOLO11N_Plate_Detector_Colab_crashed.ipynb` çıktısına göre ikinci problem de API key veya Roboflow indirme problemi değildir.

Gözlenen durum:

* `turkish_number_plates` Drive cache'ten local'e alınmış.
* `roboflow_lpr` Roboflow API ile yeniden indirilmiş ve extract edilmiş.
* Crash Cell 4'te oluşmuş:

```text
shutil.Error: [Errno 5] Input/output error
```

Kök neden:

* Notebook `roboflow_lpr` klasörünü local runtime'dan Google Drive raw cache'e kopyalamaya çalışıyordu.
* Bu dataset yaklaşık `200k+` küçük image/label dosyası çıkarıyor.
* Google Drive mount, bu kadar çok küçük dosyanın tek tek kopyalanmasında kırılgan; `[Errno 5] Input/output error` üretebiliyor.

Düzeltme:

* Raw Roboflow image/label ağaçları artık Drive'a kopyalanmaz.
* `USE_DRIVE_RAW_TREE_CACHE=False`
* `SAVE_RAW_TREE_TO_DRIVE=False`
* Drive'da yalnız küçük download manifestleri, metadata CSV, final checkpoint, summary JSON ve rapor tutulur.
* Drive'da daha önce oluşmuş partial raw cache klasörleri marker dosyası olmadığı için yok sayılır:

```text
.roboflow_tree_cache_complete.json
```

Tekrar çalıştırma:

* Aynı runtime hâlâ açıksa Cell 4'ten itibaren tekrar çalıştır.
* Yeni runtime açıldıysa `Run all` yap; `roboflow_lpr` yeniden indirilebilir ama artık Drive raw-tree kopyası yapılmadığı için aynı I/O hatası tekrarlanmamalı.
* Cell 4'te beklenen yeni çıktı:

```text
[skip raw tree Drive copy] roboflow_lpr - using local runtime dataset; final artifacts will persist to Drive
```

## Drive Girdi/Çıktı Yolları

### Raw / Cache

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/plate_detection/raw/
```

### YOLO Metadata

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/plate_detection_yolo/data.yaml
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/plate_detection/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-dataset-metadata.csv
```

Varsayılan olarak full image/label split Drive'a kopyalanmaz; eğitim local runtime'da yapılır. Bunun nedeni Drive I/O yavaşlığıdır. Notebook içinde `COPY_SPLIT_DATASET_TO_DRIVE=True` yapılırsa full split Drive'a da kopyalanabilir.

### Eğitim Run Çıktısı

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/plate_detection/POCR-EXP-005/
```

### Checkpoint Çıktısı

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.pt
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-last.pt
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/plate/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-best.onnx
```

ONNX export opsiyoneldir; başarısız olursa `.pt` çıktısı yeterli kabul edilir.

### Metrik / Rapor

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/plate_detection/POCR-EXP-005-YOLO11N-PLATE-DETECTOR-summary.json
/content/drive/MyDrive/anomali-road-safety-ai/models/experiments/POCR_EXP_005_plate_detector_report.md
```

## Başarı Kriterleri

Minimum başarılı koşu için:

* Roboflow iki veri seti indirilmeli veya manual zip fallback ile bulunmalı.
* Merge sonrası train/val/test split boş olmamalı.
* `best.pt` üretilmeli.
* Trained model val/test metrikleri JSON'a yazılmalı.
* Existing `license_plate_detector.pt` baseline ile karşılaştırma yapılmalı veya baseline eksikse neden skipped olduğu raporlanmalı.
* UFPR yoksa notebook fail etmemeli; `ufpr_status=missing` yazmalı.

## OCR'a Geçiş Kriteri

OCR'a bu notebook biter bitmez otomatik geçilmeyecek. Önce:

1. Yeni model POCR-EXP-001 baseline'a göre daha iyi plate recall / mAP / usable crop rate vermeli.
2. 3 dark video üzerinde manual plate bbox review yapılmalı.
3. Target track başına en az bir kullanılabilir plate crop oranı ölçülmeli.
4. False positive plate bbox kabul edilebilir seviyeye inmeli.

Bu sağlanırsa POCR-EXP-006/007 kapsamında OCR + temporal voting tekrar ele alınır.
