# RUN VATTR-EXP-001 — BoxCars Vehicle Attribute / Dimension Prior

## Amaç

BoxCars116k üzerinden araç crop'ları için `Vehicle Dimension Prior` modeli hazırlamak. Bu model doğrudan hız ölçmez; `Speed Fusion Layer` içinde kullanılacak araç gövde tipi / fine-grained etiket / yaklaşık wheelbase ön bilgisi üretir.

## Drive Konumu

Notebook şu Drive klasörünü kullanır:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/boxcars/
```

Bu klasör Google Drive'da oluşturuldu:

```text
https://drive.google.com/drive/folders/12MIFpt_lN8J0KWbqSgsKRECdNKIkE22O
```

İndirme link notu Drive'a yüklendi:

```text
https://drive.google.com/file/d/1GVp0YY9H7bZyrj1dOhLd2Y73uCOjaduP/view?usp=drivesdk
```

## Direct Download

Birincil indirme URL'i:

```text
https://medusa.fit.vutbr.cz/traffic/data/BoxCars116k.zip
```

Notebook varsayılan olarak bu dosyayı şu hedefe indirmeyi dener:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/boxcars/BoxCars116k.zip
```

## Kaggle Fallback

Resmi host DNS veya erişim hatası verirse notebook Kaggle fallback kullanabilir:

```text
https://www.kaggle.com/datasets/igorlashkov/boxcars-dataset
```

Colab Secrets içinde şu alanlar tanımlı olmalı:

```text
KAGGLE_USERNAME
KAGGLE_KEY
```

Notebook config:

```python
AUTO_DOWNLOAD_BOXCARS = True
DOWNLOAD_METHOD = "direct"
ENABLE_KAGGLE_FALLBACK = True
KAGGLE_DATASET_SLUG = "igorlashkov/boxcars-dataset"
```

Eğer direct host sürekli hata verirse:

```python
DOWNLOAD_METHOD = "kaggle"
```

## İlk Koşu

İlk koşuda smoke mode açık kalsın:

```python
SMOKE_MODE = True
BACKBONES = ["mobilenet_v3_large"]
EPOCHS = 3
MAX_VEHICLES_PER_SPLIT = 800
MAX_INSTANCES_PER_VEHICLE = 2
```

Başarılı smoke run sonrası ağır run:

```python
SMOKE_MODE = False
BACKBONES = ["mobilenet_v3_large", "efficientnet_b0"]
EPOCHS = 20
MAX_VEHICLES_PER_SPLIT = None
MAX_INSTANCES_PER_VEHICLE = 4
```

## Beklenen Çıktılar

Drive altında:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_attribute/VATTR-EXP-001/
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_attribute/VATTR-EXP-001/
/content/drive/MyDrive/anomali-road-safety-ai/reports/vehicle_attribute/VATTR-EXP-001/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/boxcars_vehicle_attribute/metadata/
```

Önemli dosyalar:

```text
VATTR-EXP-001-*-best.pth
VATTR-EXP-001-label-map.json
VATTR-EXP-001-dimension-prior-table.json
vattr-exp-001_metrics.json
vattr-exp-001_summary.md
```

## Yorumlama

Bu modelin çıktısı kesin marka/model kanıtı değildir. Hız modülünde yalnız:

* confidence yeterliyse,
* track stabilse,
* araç görünümü ölçü prior'ı için uygunsa,
* diğer hız sinyalleriyle çelişmiyorsa

`use_for_speed_fusion=true` olarak kullanılmalıdır.
