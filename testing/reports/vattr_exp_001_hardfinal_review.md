# VATTR-EXP-001 Hard Final Review

## Özet

`VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab_outhardfinal.ipynb` çıktısı incelendi.

Sonuç: Bu koşu **gerçek full hard run** olarak kabul edilebilir. Önceki smoke/yanlış hard koşulardaki temel sorunlar çözülmüş görünmektedir:

* Full train split kullanılmıştır.
* İki backbone denenmiştir.
* 20 epoch eğitim yapılmıştır.
* Best backbone `efficientnet_b0` olarak seçilmiştir.
* `mpv/suv/van` sınıfları artık F1 `0.0` değildir.
* Test macro-F1 `0.8579` seviyesine çıkmıştır.

Bu model, `Speed Fusion Layer` içinde `vehicle_dimension_prior` sinyalinin ilk gerçek adayı olarak kullanılabilir. Yine de doğrudan mutlak hız kanıtı değildir; yalnız confidence-aware sanity-check / prior sinyali olarak kullanılmalıdır.

## Runtime ve Config Kontrolü

Runtime:

```text
Python: 3.12.13
Torch: 2.11.0+cu128
Torchvision: 0.26.0+cu128
GPU: NVIDIA L4
```

Config çıktısı:

```text
SMOKE_MODE: False
BACKBONES: ['mobilenet_v3_large', 'efficientnet_b0']
```

Notebook source içinde:

```python
RUN_MODE = "heavy"
FREEZE_BACKBONE = False
MAX_VEHICLES_PER_SPLIT = None
MAX_INSTANCES_PER_VEHICLE = 4
USE_CLASS_WEIGHTS = True
USE_BALANCED_SAMPLER = True
```

## Dataset ve Split Kontrolü

Seçilen split:

```text
body
```

Kayıt üretimi:

```text
train vehicles: 13432
val vehicles: 771
test vehicles: 12650
records: 87132
```

Image-backed split:

```text
train: 44694
val: 2563
test: 39875
```

Bu, önceki hatalı hard koşusundan farklıdır. Önceki koşuda train yalnız `1600` image idi ve `SMOKE_MODE=True` kalmıştı.

Train class dağılımı:

```text
combi: 17513
hatchback: 11416
mpv: 2299
sedan: 7112
suv: 2142
van: 4212
```

Class weights:

```text
combi: 0.6522
hatchback: 0.8078
mpv: 1.8000
sedan: 1.0234
suv: 1.8648
van: 1.3299
```

## Backbone Karşılaştırması

### MobileNetV3-Large

En iyi validation macro-F1:

```text
0.8941 civarı
```

Not: Validation metrikleri yüksek, ancak son epoch'larda train macro-F1 `0.99` seviyesine çıkmıştır. Bu yüzden overfit riski izlenmelidir.

### EfficientNet-B0

En iyi validation macro-F1:

```text
0.8991726130690852
```

Best model:

```text
efficientnet_b0
```

EfficientNet-B0, validation macro-F1 ile MobileNetV3-Large'tan az farkla daha iyi seçilmiştir.

## Test Sonucu

Final test metrics:

```text
loss: 0.5669611452
accuracy: 0.8897805643
macro_f1: 0.8578943696
```

Class bazlı sonuç:

```text
combi      precision 0.94 | recall 0.88 | f1 0.91 | support 15313
hatchback  precision 0.83 | recall 0.92 | f1 0.87 | support 12021
mpv        precision 0.67 | recall 0.69 | f1 0.68 | support 1673
sedan      precision 0.92 | recall 0.93 | f1 0.92 | support 5014
suv        precision 0.93 | recall 0.74 | f1 0.82 | support 1568
van        precision 0.97 | recall 0.92 | f1 0.94 | support 4286
```

Macro average:

```text
precision: 0.87
recall: 0.85
f1-score: 0.86
```

Weighted average:

```text
precision: 0.89
recall: 0.89
f1-score: 0.89
```

## Drive Artefactleri

Best checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_attribute/VATTR-EXP-001/VATTR-EXP-001-efficientnet_b0-best.pth
```

Drive URL:

```text
https://drive.google.com/file/d/1tQVq24gKbbhODVqBYG7fG9g-0GYZgHt9/view?usp=drivesdk
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

Training history:

```text
https://drive.google.com/file/d/1wjBIZ3hWL6BhigNYCn8oN5JD-d5xa85e/view?usp=drivesdk
```

## Amaca Uygunluk

### Uygun Kısımlar

* `Speed Fusion Layer` için gövde tipi / dimension bucket sinyali üretecek ilk güçlü aday model oluştu.
* Minority class sorunu büyük ölçüde çözüldü.
* `mpv`, `suv`, `van` artık tamamen kaçırılmıyor.
* Test macro-F1 yeterli başlangıç seviyesinde.
* EfficientNet-B0 checkpoint Drive'a yazıldı.

### Kalan Eksikler

* Opsiyonel crop smoke inference çalışmadı:

```text
POCR-EXP-001-target-roi-crops missing
```

Bu nedenle model henüz bizim 3 demo videosundaki target crop'lar üzerinde test edilmedi.

* BoxCars split aynı dataset ailesi içindedir; gerçek lokal/demo domain için ayrıca smoke test gerekir.
* Araç boyutu prior'ı mutlak hız kaynağı değildir; yalnız confidence/range sanity-check olarak kullanılmalıdır.

## Karar

Bu koşu:

```text
dataset access = başarılı
hard run = başarılı
model quality = ilk speed fusion adayı için yeterli
runtime promotion = yalnız vehicle_dimension_prior sinyali olarak evet
absolute speed source = hayır
```

`SPEED-EXP-004B` aşamasına geçmek için yeterlidir, ancak önce lokal/demo target crop smoke test yapılmalıdır.

## Sonraki Adım

1. `VATTR-EXP-001-efficientnet_b0-best.pth` checkpoint'ini lokal model manifestine veya runtime config'e referansla.
2. Mevcut 3 test videosundan target vehicle crop çıkar veya mevcut ROI crop yolunu düzelt.
3. VATTR modelini 3 video target crop'larında çalıştır.
4. Çıktıları event/evidence JSON'a doğrudan yazmadan önce şu alanlarla raporla:

```text
track_id
predicted_body_type
confidence
wheelbase_prior_m_mean
use_for_speed_fusion
failure_reason
```

5. Sonra `SPEED-EXP-004B` plate-scale + VATTR sanity-check entegrasyonuna geç.

## Geçiş Kriteri

Sonraki aşamaya geçiş için koşul:

```text
BoxCars hard run metrikleri yeterli: evet
local demo crop sanity-check: henüz eksik
```

Bu yüzden karar:

```text
SPEED-EXP-004B hazırlığına geçilebilir.
Ancak event/evidence runtime'a bağlamadan önce local VATTR crop smoke test yapılmalıdır.
```
