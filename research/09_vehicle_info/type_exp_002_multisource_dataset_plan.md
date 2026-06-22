# TYPE-EXP-002 Multi-source FTR Vehicle Type Plan

## Amaç

`TYPE-EXP-002`, FTR `arac_bilgisi.tip` alanı için aşağıdaki 7 resmi sınıfı doğrudan hedefleyen ikinci araç tipi deneyidir:

```text
sedan, suv, hatchback, pickup, minibus, panelvan, kamyon
```

Bu deney, `TYPE-EXP-001` sonucunda görülen iki temel problemi düzeltmek için açılmıştır:

1. `kamyon` sınıfında eğitim/evaluation support `0` kaldı.
2. Stanford Cars model isimlerinden tek kaynaklı mapping, özellikle `suv/hatchback/panelvan` ayrımında lokal ROI smoke testte kararsız çıktı.

## Ana Veri Omurgası

EXP-002 tek veri setine bağlı kalmayacak. Ana strateji, her FTR sınıfını en güçlü kaynaktan besleyen çok kaynaklı bir eğitim seti kurmaktır.

| Kaynak | EXP-002 rolü | FTR sınıflarına katkı | Not |
|---|---|---|---|
| Stanford Cars | Fine-grained otomobil model isimlerinden konservatif gövde tipi mapping | `sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan` | `coupe`, `convertible`, `wagon` gibi belirsiz sınıflar zorla map edilmez. |
| Car Body Type Kaggle | Doğrudan body-style klasörlerinden otomobil gövde tipi | `sedan`, `suv`, `hatchback`, `pickup`, `panelvan` | `van` sınıfı panelvan için kullanılabilir ama manuel review gerekir. |
| MIO-TCD classification subset/mirror | Trafik kamera domaininde coarse sınıflar | `pickup`, `panelvan`, `kamyon` | `work van`, `pickup truck`, `single unit truck`, `articulated truck` sınıfları EXP-001 eksiklerini kapatır. |
| Manual FTR folders | Eksik/zayıf sınıf tamamlama | Tüm sınıflar | Özellikle `kamyon`, `minibus`, `panelvan` ayrımı için kritik fallback. |

## Neden Bu Sıralama?

`TYPE-EXP-001` Stanford ağırlıklı olduğu için otomobil gövde tiplerinde makul bir başlangıç verdi fakat FTR'nin ticari/servis araç sınıflarını kapatamadı. MIO-TCD, araç sınıflandırma challenge'ında `pickup truck`, `work van`, `single unit truck` ve `articulated truck` gibi FTR açısından daha yararlı sınıflar sağladığı için EXP-002'nin ana tamamlayıcı kaynağıdır.

Car Body Type Kaggle kaynakları, sedan/SUV/hatchback/pickup tarafını daha doğrudan body-style etiketiyle güçlendirmek için kullanılır. Bu kaynaklar final rapora alınmadan önce her datasetin Kaggle lisans alanı ayrıca kaydedilmelidir.

## Notebook

Aktif notebook:

```text
notebooks/TYPE_EXP_002_Multisource_FTR_Vehicle_Type_Classifier_Colab.ipynb
```

Drive dizinleri:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_type/TYPE-EXP-002/
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/
```

Manual ek veri klasörleri:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/manual/sedan/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/manual/suv/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/manual/hatchback/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/manual/pickup/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/manual/minibus/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/manual/panelvan/
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_002/manual/kamyon/
```

## Mapping Kuralları

Mapping tarafında `needle in string` yaklaşımı kullanılmaz. Örneğin `van` token'ı `vantage` içinde eşleşirse coupe/convertible araçlar yanlışlıkla `panelvan` olur. Bu yüzden EXP-002 notebook token/phrase boundary match kullanır.

Temel mapping:

| Kaynak sınıfı / token | FTR tipi |
|---|---|
| `sedan`, `saloon` | `sedan` |
| `suv`, `crossover`, SUV model adları | `suv` |
| `hatchback`, `hatch` | `hatchback` |
| `pickup`, `pickup truck`, `regular cab`, `crew cab` | `pickup` |
| `minivan`, `microbus`, `minibus` | `minibus` |
| `work van`, `cargo van`, `panel van`, `sprinter`, `savana` | `panelvan` |
| `single unit truck`, `articulated truck`, `box truck`, `truck` | `kamyon` |

Belirsiz örnekler:

| Kaynak etiketi | Karar |
|---|---|
| `coupe` | Skip |
| `convertible` | Skip |
| `wagon` | Skip |
| generic `car` | Skip |
| generic `bus` | Varsayılan olarak skip; `minibus` sayılmaz |

## Kabul Kriterleri

EXP-002 modeli FTR runtime'a ancak şu koşullar sağlanırsa aday olur:

1. Her FTR sınıfında yeterli eğitim ve test support olmalı.
2. Test macro-F1 hedefi en az `0.75`.
3. Her sınıf için F1 hedefi en az `0.60`; `kamyon`, `panelvan`, `minibus` ayrıca manuel incelenmeli.
4. Target ROI smoke testte aynı track içinde temporal majority kararlı olmalı.
5. `Test/video_1-3.mp4` üzerinde overlay/manual review yapılmalı.
6. Model checkpoint, label map, classification report ve confusion matrix Drive altında saklanmalı.

## İlk Çalıştırma Notu

Önce notebook'un dataset coverage hücresindeki tablo kontrol edilir. Eğer herhangi bir sınıf `MIN_IMAGES_PER_CLASS` altındaysa eğitim başlatılmaz. Bu durumda ilgili sınıf için manual klasöre veri eklenir veya ilgili dataset erişimi düzeltilir.

## Kaynaklar

- MIO-TCD official challenge page: https://tcd.miovision.com/challenge/dataset.html
- MIO-TCD homepage: https://tcd.miovision.com/
- Kaggle Car Body Types Images Dataset: https://www.kaggle.com/datasets/ademboukhris/cars-body-type-cropped
- Kaggle Stanford Cars Dataset mirror: https://www.kaggle.com/datasets/eduardo4jesus/stanford-cars-dataset
- Stanford Cars overview: https://ai.stanford.edu/~jkrause/cars/car_dataset.html

