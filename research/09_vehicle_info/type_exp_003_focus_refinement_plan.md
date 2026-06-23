# TYPE-EXP-003 Focused Vehicle Type Refinement Plan

## Amaç

`TYPE-EXP-003`, `TYPE-EXP-002` ile üretilen FTR araç tipi modelini doğrudan değiştirmek yerine, zayıf ve karışmaya açık sınıfları hedefli bir veri eklemesiyle iyileştirme deneyidir.

Odak sınıflar:

```text
sedan, suv, hatchback, minibus
```

FTR tip etiketi yine değişmez:

```text
sedan, suv, hatchback, pickup, minibus, panelvan, kamyon
```

Bu deneyde `TYPE-EXP-002-efficientnet_b0-best.pth` başlangıç checkpoint olarak kullanılır. Amaç sıfırdan model eğitmek değil, mevcut modeli ek kaynaklarla kontrollü fine-tune etmektir.

## Neden EXP-003?

`TYPE-EXP-002` dataset-level olarak `kamyon`, `panelvan` ve `pickup` tarafını güçlendirdi. Ancak şu sorunlar devam ediyor:

- `sedan`, `suv`, `hatchback` ayrımı orta seviyede kaldı.
- `minibus` veri desteği çok düşük kaldı ve test F1 `0.0625` seviyesinde.
- 3 demo target ROI video testinde sonuç çoğunlukla `suv` olsa da frame-level `hatchback` ve birkaç ticari sınıf sapması görüldü.

Bu yüzden EXP-003, tüm sınıfları yeniden agresif şekilde karıştırmak yerine zayıf dört sınıfa ek veri ve ek loss/sampler ağırlığı verir.

## Ek Veri Kaynakları

| Kaynak | Kullanım amacı | Beklenen katkı | Risk |
|---|---|---|---|
| Vehicle Type Image Dataset / VTID2 | `sedan`, `suv`, `hatchback` odaklı ek image-classification verisi | Binek araç gövde tipi ayrımını güçlendirmek | `Seden` gibi yazım varyantları ve domain farkı mapping ile normalize edilmeli |
| Vehicle-10 | `minibus` sınıfı için ek destek | EXP-002'deki minibus veri açığını kapatmak | GPL-2.0 lisans ve generic internet-image domain farkı raporda açık belirtilmeli |
| TYPE-EXP-002 base sources | 7 sınıf kapsamını korumak | `pickup`, `panelvan`, `kamyon` regresyonunu azaltmak | Eski kaynaklardaki taxonomy gürültüsü aynen taşınabilir |
| Manual focus folders | Gerekirse hedefli veri eklemek | Türkiye/FTR formatına yakın örnek eklemek | Manuel etiket kalite kontrolü gerekir |

## Kaynak Bağlantıları

- Vehicle Type Image Dataset / VTID2 Kaggle: https://www.kaggle.com/datasets/sujaykapadnis/vehicle-type-image-dataset
- Vehicle-10 GitHub: https://github.com/yjzhai-cs/Vehicle-10
- Vehicle-10 zip: https://drive.google.com/file/d/1pNmm9RjcdTJVRl8_uv-Cs5-CahkROKHs/view?usp=sharing
- Vehicle-10 tar.gz: https://drive.google.com/file/d/1Z2LL-vcjKnpcX2rLyBkKG577mkPcYIpR/view?usp=sharing
- Car Body Type Kaggle: https://www.kaggle.com/datasets/ademboukhris/cars-body-type-cropped

## Notebook

Aktif notebook:

```text
notebooks/TYPE_EXP_003_Focus_Sedan_SUV_Hatchback_Minibus_Colab.ipynb
```

Drive dizinleri:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_003/
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_type/TYPE-EXP-003/
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/
```

Zorunlu başlangıç checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-002-efficientnet_b0-best.pth
```

## Manual Focus Folder Yapısı

Otomatik veri indirme başarısız olursa veya odak sınıflar yeterli çıkmazsa şu klasörlere veri eklenebilir:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_003/manual/sedan/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_003/manual/suv/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_003/manual/hatchback/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_003/manual/minibus/
```

## Mapping Kararları

| Kaynak etiketi | FTR etiketi | Not |
|---|---|---|
| `Seden`, `Sedan` | `sedan` | VTID2 yazım varyantı normalize edilir |
| `SUV` | `suv` | Doğrudan mapping |
| `Hatchback` | `hatchback` | Doğrudan mapping |
| `minibus` | `minibus` | Vehicle-10 içinde doğrudan sınıf |
| `bus` | skip | Generic bus, FTR `minibus` sayılmaz |
| `car` | skip | Çok geniş ve sedan/suv/hatchback ayrımı üretmez |

## Eğitim Stratejisi

EXP-003:

1. EXP-002 veri kaynaklarını korur.
2. VTID2 ve Vehicle-10 focus kaynaklarını ekler.
3. `TYPE-EXP-002-efficientnet_b0-best.pth` checkpoint'ini yükler.
4. EfficientNet-B0 üzerinden düşük learning rate ile fine-tune eder.
5. Loss ve sampler tarafında `sedan/suv/hatchback/minibus` sınıflarına ek ağırlık verir.
6. Model seçimini şu skorla yapar:

```text
selection_score = 0.45 * all_class_macro_f1 + 0.55 * focus_macro_f1
```

Bu sayede sadece minibus'u artırırken diğer sınıfları bozmak engellenmeye çalışılır.

## Kabul Kriterleri

EXP-003, EXP-002 yerine runtime baseline olabilmek için şunları sağlamalı:

1. Focus macro-F1, EXP-002 baseline değerlendirmesine göre artmalı.
2. Genel macro-F1 anlamlı düşmemeli.
3. `minibus` F1 açık şekilde iyileşmeli.
4. `sedan/suv/hatchback` confusion matrix'te daha okunabilir hale gelmeli.
5. 3 demo target ROI video smoke testte `suv` temporal/gated majority korunmalı.
6. Tek-frame top-1 değil, track-level gated temporal majority kullanılmalı.

## Başarısızlık Durumu

Şu durumlardan biri görülürse EXP-003 runtime'a alınmaz:

- `suv` demo track stabilitesi EXP-002'den kötüleşirse.
- `pickup/panelvan/kamyon` ciddi regresyona uğrarsa.
- `minibus` artışı yalnız dataset leakage veya domain bias gibi görünürse.
- Test macro-F1 artışı yalnız focus dışı sınıfları bozarak elde edilirse.

Bu durumda EXP-002 aktif baseline kalır; EXP-003 yalnız araştırma deneyi olarak raporlanır.

