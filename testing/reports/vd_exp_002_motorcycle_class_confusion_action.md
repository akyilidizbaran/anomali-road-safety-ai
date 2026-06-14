# VD-EXP-002 Motorcycle / Car Class Confusion Action Note

## Gözlem

`VD-EXP-002` fine-tuned general YOLO11n smoke testinde `Test/video_3.mp4` için otomatik özet:

| Video | Frame | Detection | Class dağılımı |
|---|---:|---:|---|
| `Test/video_3.mp4` | 383 | 617 | `car:611`, `motorcycle:6` |

Kullanıcı manuel gözlemine göre sahnede normalde 1 araba + 1 motosiklet vardır. Buna rağmen model motosikleti büyük ölçüde `car` olarak tahmin ediyor.

Bu durum final accuracy iddiası değildir; manual review ile doğrulanması gereken class-level hata örüntüsüdür.

## Bu Problem Ne Değildir?

Bu, `condition_profile` classifier problemi değildir.

Condition classifier yalnız frame'in hava/ışık/görüş profilini üretir:

```text
night_low_light, rain, fog_low_visibility, day_clear, ...
```

Motorcycle/car karışıklığı ise vehicle detector sınıf ayrımı problemidir.

## Muhtemel Nedenler

* BDD100K vehicle subset içinde `car` sınıfı `motorcycle` sınıfından çok daha baskın olabilir.
* Mevcut 3 dark video düşük ışık içerdiği için motosiklet silueti ve far/parlama etkisi car sınıfına kayabilir.
* Motosiklet bbox'ı küçük, kısmi görünür veya motion blur içeriyor olabilir.
* YOLO11n nano ölçeği class ayrımı için yeterli temsil gücünü her koşulda sağlayamayabilir.
* Tracking/class voting aşamasında kısa süreli `motorcycle` tahminleri stable class içinde `car` oyları tarafından bastırılabilir.

## Hemen Yapılacak Manual Review

`video_3` için frame-level manuel sayım yapılmalı:

| Alan | Açıklama |
|---|---|
| `motorcycle_visible_frames` | Motosikletin gerçekten göründüğü frame sayısı |
| `motorcycle_detected_as_motorcycle` | Doğru sınıfla yakalanan frame sayısı |
| `motorcycle_detected_as_car` | Yanlış `car` sınıfıyla yakalanan frame sayısı |
| `motorcycle_missed` | Hiç yakalanmayan frame sayısı |
| `bbox_adequate` | Yanlış sınıf olsa bile bbox aracı kapsıyor mu |
| `low_light_or_blur_reason` | Hatanın düşük ışık/blur/parlama ile ilişkisi |

Bu sayım yapılmadan "motorcycle recall" veya "motorcycle accuracy" iddiası kurulmayacak.

## Kısa Vadeli Sistem Kararı

Risk/evidence MVP için class ayrımı yerine önce "vehicle present + track continuity" güvenceye alınabilir.

Bu nedenle ilk rapor dili:

> Model, düşük ışık test videosunda araç varlığını yakalayabilmektedir; ancak motosiklet sınıf ayrımı manuel review gerektiren bir hata örüntüsü göstermiştir.

Kaçınılması gereken ifade:

> Model car/motorcycle ayrımını karanlık ortamda güvenilir biçimde yapmaktadır.

## Model İyileştirme Aksiyonları

1. BDD100K train metadata içinde `motorcycle` örnek sayısı ve condition kırılımı çıkarılacak.
2. `motorcycle_focus` validation subset oluşturulacak.
3. `VD-EXP-006-MOTORCYCLE-FOCUS` deney ailesi açılacak:
   * general checkpoint'ten devam,
   * motorcycle class oversampling,
   * class-weight veya focal loss ablation,
   * low-light motorcycle augmentation,
   * aynı 3 dark video üzerinde manual review.
4. Eğer YOLO11n class ayrımı yeterli değilse YOLO11s challenger veya targeted specialist değerlendirilecek.
5. Runtime tarafında class label düşük güvenliyse event içinde `stable_class_confidence_low=true` ve `class_review_required=true` yazılacak.

## Condition Classifier ile İlişki

Condition classifier yine gereklidir, çünkü bu hata düşük ışık profiliyle ilişkili olabilir.

Ancak router şu şekilde davranmalıdır:

```text
condition_profile = night_low_light
selected_detector = general
routing_reason = night specialist not promoted
class_warning = motorcycle/car confusion observed in manual smoke test
```

Yani condition classifier hatayı tek başına çözmez; yalnız hangi koşulda hata oluştuğunu açıklanabilir hale getirir.
