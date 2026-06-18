# VATTR-EXP-001 Outhard Review

## Özet

`VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab_outhard.ipynb` çıktısı incelendi.

Sonuç: Bu koşu **gerçek heavy run değildir**. Config hücresinde hâlâ `SMOKE_MODE=True` kaldığı için notebook tekrar smoke subset üzerinde çalışmıştır. Bu nedenle bu çıktı sonraki aşamaya geçmek için yeterli değildir.

## Config Kontrolü

Notebook çıktısında görülen aktif config:

```python
SMOKE_MODE = True
BACKBONES = ["mobilenet_v3_large"]
EPOCHS = 3
MAX_VEHICLES_PER_SPLIT = 800
MAX_INSTANCES_PER_VEHICLE = 2
FREEZE_BACKBONE = True
USE_CLASS_WEIGHTS = True
USE_BALANCED_SAMPLER = True
```

Bu ayarlar heavy run değil, class-weighted smoke run'dır.

## Veri Hazırlama Kontrolü

Seçilen split:

```text
body
```

Kullanılan kayıt sayıları:

```text
train: 1600
val:   1542
test:  1600
```

Bu değerler yine smoke sınırlarının aktif olduğunu gösterir. Gerçek heavy run'da `MAX_VEHICLES_PER_SPLIT=None` olmalı ve train kayıt sayısı 1600'den anlamlı şekilde büyük olmalıdır.

## Eğitim Sonucu

Backbone:

```text
mobilenet_v3_large
```

Epoch sayısı:

```text
3
```

Test sonucu:

```text
accuracy: 0.260625
macro_f1: 0.133885
```

Class bazlı sonuç:

```text
combi     f1: 0.18
hatchback f1: 0.43
mpv       f1: 0.00
sedan     f1: 0.19
suv       f1: 0.00
van       f1: 0.00
```

Class weighting ve balanced sampler train macro-F1'i yükseltmiş görünse de validation/test tarafında genelleme yeterli değildir. Özellikle `mpv/suv/van` hâlâ yakalanmamaktadır.

## Karar

Bu koşu:

```text
dataset access = başarılı
heavy run = hayır
model quality = yetersiz
next stage readiness = hayır
runtime promotion = hayır
```

Bu checkpoint `Speed Fusion Layer` içinde güvenilir `vehicle_dimension_prior` modeli olarak kullanılmamalıdır.

## Aktif Notebook Düzeltmesi

Aktif notebook güncellendi:

```python
RUN_MODE = "heavy"
SMOKE_MODE = False
BACKBONES = ["mobilenet_v3_large", "efficientnet_b0"]
EPOCHS = 20
FREEZE_BACKBONE = False
MAX_VEHICLES_PER_SPLIT = None
MAX_INSTANCES_PER_VEHICLE = 4
USE_CLASS_WEIGHTS = True
USE_BALANCED_SAMPLER = True
```

Bu nedenle bir sonraki koşu için aktif notebook tekrar kullanılmalıdır:

```text
notebooks/VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab.ipynb
```

## Bir Sonraki Koşuda Beklenen Kontrol Noktaları

Gerçek heavy run başladığında şu değerler görülmelidir:

```text
RUN_MODE: heavy
SMOKE_MODE: False
BACKBONES: ['mobilenet_v3_large', 'efficientnet_b0']
EPOCHS: 20
FREEZE_BACKBONE: False
MAX_VEHICLES_PER_SPLIT: None
MAX_INSTANCES_PER_VEHICLE: 4
```

Cell 5 çıktısında:

```text
Building records for train: vehicles=800
```

görülmemelidir. Train vehicle sayısı 800 ile sınırlıysa hâlâ smoke config çalışıyordur.

## Sonraki Aşamaya Geçiş Kriteri

VATTR modeliyle `SPEED-EXP-004B` aşamasına geçmek için önerilen minimum beklenti:

* Macro-F1 smoke seviyesinin belirgin üstüne çıkmalı.
* `mpv/suv/van` sınıflarında F1 `0.0` kalmamalı.
* En azından coarse body-type / dimension-bucket düzeyinde güvenilir çıktı üretmeli.

Bu sağlanmazsa `body` sınıfları yeniden gruplanmalıdır:

```text
compact_car: hatchback
car_like: sedan / combi
large_car_like: suv / mpv / van
```

Bu durumda VATTR modeli fine-grained gövde tipinden çok dimension bucket modeli olarak yeniden tasarlanmalıdır.
