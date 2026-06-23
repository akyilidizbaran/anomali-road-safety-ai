# TYPE-EXP-004 Controlled Minibus Repair Plan

## Amaç

`TYPE-EXP-002` araç tipi modeli aktif demo/runtime baseline olarak korunuyor; fakat dataset-level raporda `minibus` F1 skoru `0.0625` olduğu için bu sınıf raporlanabilir seviyede değil.

`TYPE-EXP-003`, `Vehicle-10` ekleyerek minibus F1'i dataset split üzerinde ciddi artırdı; ancak aynı checkpoint lokal target ROI video smoke testlerinde `minibus` false mode üretti. Bu nedenle `TYPE-EXP-004`, EXP-003'ü agresif şekilde tekrarlamaz. Ana hedef:

```text
minibus F1 yükselsin, fakat suv/panelvan/sedan/hatchback sınıfları minibus'a kaymasın.
```

## Notebook

Aktif notebook:

```text
notebooks/TYPE_EXP_004_T4_Controlled_Minibus_Repair_Colab.ipynb
```

Colab donanım hedefi:

```text
T4 GPU yeterli olacak şekilde tasarlandı.
```

Başlangıç checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-002-efficientnet_b0-best.pth
```

## Neden TYPE-EXP-003 Freeze Edilmedi?

EXP-003 dataset-level olarak güçlüydü:

| Metrik | Değer |
|---|---:|
| Test macro-F1 | 0.8763 |
| Focus macro-F1 | 0.8466 |
| Minibus F1 | 0.9237 |

Ancak lokal target ROI video smoke testte aktif demo aracını `minibus` olarak fazla tahmin etti:

| Test | TYPE-EXP-002 | TYPE-EXP-003 |
|---|---:|---:|
| Video raw `suv` count | 808 / 975 | 504 / 975 |
| Video raw `minibus` count | 9 / 975 | 382 / 975 |
| Video gated majority `video_2` | `suv` | `minibus` |
| Video gated majority `video_3` | `suv` | `minibus` |

Bu sonuç, EXP-003'ün minibus sınıfını dataset split üzerinde iyileştirirken bizim karanlık target ROI dağılımımızda domain bias oluşturduğunu gösteriyor.

## Veri Stratejisi

EXP-004 yine aynı 7 FTR tip etiketini kullanır:

```text
sedan, suv, hatchback, pickup, minibus, panelvan, kamyon
```

Kullanılan kaynaklar:

| Kaynak | Rol |
|---|---|
| Stanford Cars | konservatif binek araç tipi sinyali |
| Car Body Type | sedan / suv / hatchback / pickup / panelvan desteği |
| MIO-TCD classification subset | pickup / panelvan / kamyon desteği |
| VTID2 | sedan / suv / hatchback guard desteği |
| Vehicle-10 | kontrollü minibus desteği |
| Manual folders | gerekirse hedefli veri ekleme |

## Kontrollü Minibus Ayarları

EXP-004'te minibus tarafı özellikle sınırlandırılır:

| Ayar | Değer | Gerekçe |
|---|---:|---|
| `MAX_MINIBUS_TOTAL` | 900 | EXP-003'teki 1686 minibus örneğine göre daha kontrollü |
| `MAX_MINIBUS_FROM_VEHICLE10` | 650 | tek kaynaklı Vehicle-10 baskısını azaltır |
| `MAX_MINIBUS_RATIO` | 0.075 | split içinde minibus oranı aşırı büyümez |
| `MINIBUS_LOSS_MULTIPLIER` | 1.15 | minibus öğrenilir ama agresif weight verilmez |
| `MINIBUS_SAMPLER_MULTIPLIER` | 1.10 | sampler minibus'u görür ama baskınlaştırmaz |
| `CLASS_WEIGHT_CLIP_MAX` | 1.35 | düşük support sınıf ağırlıkları patlamaz |

## Guard Sınıflar

Minibus'a en çok karışabilecek sınıflar ayrıca izlenir:

```text
sedan, suv, hatchback, panelvan
```

Bu sınıflar seçim skorunda `guard_macro_f1` ile korunur. Amaç yalnız minibus recall artırmak değil, minibus false-positive üretmeden FTR tip ayrımını iyileştirmektir.

## Model Seçim Skoru

EXP-003'te selection ağırlığı focus macro-F1'a fazla yaslanıyordu. EXP-004 seçim skoru şu mantıkla değiştirildi:

```text
selection_score =
  0.35 * macro_f1
+ 0.25 * guard_macro_f1
+ 0.20 * minibus_f1
+ 0.10 * minibus_precision
+ 0.10 * accuracy
- 0.35 * minibus_false_positive_rate
```

Bu skor özellikle şunu engeller:

```text
minibus recall artsın ama model her şeyi minibus'a çeksin
```

## Promotion Kriterleri

Notebook içi dataset-level adaylık:

| Kontrol | Eşik |
|---|---:|
| `test_macro_f1` | >= 0.68 |
| `minibus_f1` | >= 0.30 |
| `minibus_precision` | >= 0.30 |
| `minibus_false_positive_rate` | <= 0.08 |

Ancak bu eşikler tek başına freeze için yeterli değildir.

Final runtime promotion için ayrıca local smoke test zorunludur:

1. Checkpoint Drive'dan local'e indirilecek.
2. `runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames` üzerinde crop smoke çalışacak.
3. `runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/clips` üzerinde video overlay smoke çalışacak.
4. Üç demo target track'te gated majority `suv` kalmalı.
5. `minibus` false mode tekrar oluşursa checkpoint runtime'a alınmayacak.

## Beklenen Çıktılar

Drive çıktıları:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_type/TYPE-EXP-004/
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-004-efficientnet_b0-best.pth
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-004-label-map.json
```

Ana dosyalar:

```text
TYPE-EXP-004-summary.json
TYPE-EXP-004-test_classification_report.csv
TYPE-EXP-004-test_confusion_matrix.csv
TYPE-EXP-004-test_confusion_matrix.png
TYPE-EXP-004-test_predictions.csv
TYPE-EXP-004-run_summary.md
```

## Başarı Durumu

Başarılı kabul edilecek senaryo:

- Minibus F1, EXP-002'deki `0.0625` seviyesinden anlamlı şekilde çıkar.
- Dataset macro-F1, EXP-002 seviyesinin altına anlamsız düşmez.
- Minibus precision ve false-positive oranı kabul edilebilir kalır.
- Local target ROI smoke testlerinde EXP-003'teki minibus baskınlığı tekrar oluşmaz.

## Başarısızlık Durumu

Başarısız kabul edilecek senaryo:

- Minibus F1 artar ama `suv/panelvan` örnekleri minibus'a kayar.
- Local smoke testte `video_2` veya `video_3` gated majority yine `minibus` olur.
- Dataset metrikleri iyi görünür ama demo/evidence pipeline dağılımı bozulur.

Bu durumda aktif runtime baseline yine `TYPE-EXP-002` kalır.
