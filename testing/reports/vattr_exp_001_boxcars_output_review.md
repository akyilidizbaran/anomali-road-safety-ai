# VATTR-EXP-001 BoxCars Output Review

## Özet

`VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab_outputsaved.ipynb` çıktıları incelendi.

Sonuç: Notebook **erişim, veri hazırlama, smoke training ve Drive export** açısından başarılıdır. Ancak üretilen model **Speed Fusion Layer içinde aktif/default vehicle dimension prior modeli olarak kullanılacak kalitede değildir**. Bu koşu smoke-run kanıtı olarak saklanmalıdır; ağır run öncesi notebook class imbalance düzeltmesiyle güncellenmiştir.

## Çalışma Ortamı

* Runtime: Google Colab
* GPU: NVIDIA L4
* Python: `3.12.13`
* Torch: `2.11.0+cu128`
* Torchvision: `0.26.0+cu128`

## Veri Erişimi

Birincil direct URL başarısız oldu:

```text
https://medusa.fit.vutbr.cz/traffic/data/BoxCars116k.zip
```

Hata tipi:

```text
Name or service not known
curl exit status 6
wget exit status 4
```

Kaggle fallback başarılı oldu:

```text
igorlashkov/boxcars-dataset
```

Drive'a indirilen arşiv:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/boxcars/boxcars-dataset.zip
```

Arşiv boyutu:

```text
6.46 GB
```

Drive doğrulaması:

```text
https://drive.google.com/file/d/1ylvHiSvm8j8m8CcxTd0aF62K-8ha7_kS/view?usp=drivesdk
```

## Dataset ve Split

Notebook şu dosyaları buldu:

```text
dataset.pkl
classification_splits.pkl
atlas.pkl
```

Seçilen split:

```text
body
```

Sınıf haritası:

```text
combi
hatchback
mpv
sedan
suv
van
```

Üretilen kayıt sayıları:

```text
train: 1600 image
val:   1542 image
test:  1600 image
```

Class dağılımı dengesizdir:

```text
train combi:     790
train hatchback: 334
train mpv:        22
train sedan:     358
train suv:        58
train van:        38
```

Bu dengesizlik smoke-run sonucunun ana zayıflığıdır.

## Eğitim Sonucu

Backbone:

```text
mobilenet_v3_large
```

Epoch:

```text
3
```

Validation macro-F1:

```text
epoch 1: 0.1032
epoch 2: 0.1282
epoch 3: 0.1830
```

Test sonucu:

```text
accuracy: 0.49
macro_f1: 0.1915
```

Class bazlı sonuç:

```text
combi     f1: 0.61
hatchback f1: 0.41
mpv       f1: 0.00
sedan     f1: 0.13
suv       f1: 0.00
van       f1: 0.00
```

## Drive Çıktıları

Checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_attribute/VATTR-EXP-001/VATTR-EXP-001-mobilenet_v3_large-best.pth
```

Drive URL:

```text
https://drive.google.com/file/d/1uj1IXiVd_0wlj-Ff2uj8UbEEhl8v66Ix/view?usp=drivesdk
```

Label map:

```text
https://drive.google.com/file/d/1Iw98DOd0ddNye0Xr0zLrJgO0R6ZAD0fW/view?usp=drivesdk
```

Dimension prior table:

```text
https://drive.google.com/file/d/1oi32KV1vGqieVKhCQtWQELKnQruGyFuC/view?usp=drivesdk
```

Metrics:

```text
https://drive.google.com/file/d/19reuXX839mB37SIt-3C4L83-frgC7kR3/view?usp=drivesdk
```

Confusion matrix:

```text
https://drive.google.com/file/d/1_CVAG28AIKr6w3hqVZZ4nC-63j87FKdj/view?usp=drivesdk
```

Summary:

```text
https://drive.google.com/file/d/1l47byaD7AcLxtTVVeEAy2BX_BV1nHFwI/view?usp=drivesdk
```

## İstenen Amaca Uygunluk

### Başarılı Kısımlar

* BoxCars verisine Kaggle fallback üzerinden erişildi.
* Local runtime'a extract edildi.
* `body` split doğru seçildi.
* Image-backed record üretildi.
* Model eğitimi tamamlandı.
* Checkpoint, label map, metrics, confusion matrix ve summary Drive'a yazıldı.
* Speed Fusion contract için dimension-prior çıktısı üretildi.

### Yetersiz Kısımlar

* Smoke mode yalnız 3 epoch ve küçük subset ile koşuldu.
* Dataset class imbalance çok yüksek.
* `mpv`, `suv`, `van` sınıflarında F1 `0.0`.
* Optional local target crop smoke inference çalışmadı; Drive'da `POCR-EXP-001-target-roi-crops` bulunamadı.
* Bu checkpoint runtime/default model olarak kullanılmamalıdır.

## Alınan Düzeltmeler

Aktif notebook güncellendi:

* `WeightedRandomSampler` eklendi.
* Class-weighted cross entropy eklendi.
* `USE_CLASS_WEIGHTS=True`
* `USE_BALANCED_SAMPLER=True`
* `CLASS_WEIGHT_POWER=0.5`
* `combi` için `wagon` prior mapping eklendi.
* `mpv` için ayrı dimension prior mapping eklendi.

Bu düzeltmeler output-saved notebook'a değil, aktif notebook'a işlendi:

```text
notebooks/VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab.ipynb
```

## Sonuç Kararı

Bu koşu:

```text
dataset access + pipeline smoke test = başarılı
model quality for speed fusion = yetersiz
runtime promotion = hayır
```

Bir sonraki koşu ağır run olmalıdır:

```python
SMOKE_MODE = False
BACKBONES = ["mobilenet_v3_large", "efficientnet_b0"]
EPOCHS = 20
MAX_VEHICLES_PER_SPLIT = None
MAX_INSTANCES_PER_VEHICLE = 4
USE_CLASS_WEIGHTS = True
USE_BALANCED_SAMPLER = True
```

## Sonraki Adım

1. Güncel aktif notebook ile heavy run çalıştır.
2. Macro-F1 ve minority class F1 değerlerini kontrol et.
3. `mpv/suv/van` hâlâ düşükse:
   * body class merge stratejisi değerlendir,
   * `car_like_small / car_like_large / van_mpv` gibi daha az sınıflı dimension bucket'a geç,
   * veya VATTR modelini yalnız coarse dimension bucket için yeniden tasarla.
4. Hız tarafında paralel olarak `SPEED-EXP-004A` relative track/bbox baseline script'i uygulanabilir.
