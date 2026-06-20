# Phone Specialist Fine-Tune Plan v1

Tarih: 2026-06-20

Bu plan `CABIN_DRIVER_FINETUNE_HANDOFF.md` ve `CABIN-EXP-012` runtime foundation sonucuna
dayanır. Amaç, FTR `sofor_eylemi=telefonla_konusma` etiketi için çalışabilir ve ölçülebilir
bir phone specialist hattı kurmaktır.

## Neden İlk Aktif Specialist Phone?

Handoff'a göre hazır COCO `cell phone` baseline, driver-phone ROI üzerinde false-negative
üretmiştir. Özellikle `video_2` pozitif senaryosunda telefon tespiti alınamamıştır. Bu nedenle
telefon, cabin tarafındaki en net aktif fine-tune hedefidir.

## Girdi Contract

Phone specialist doğrudan full frame üzerinde çalışmamalıdır. Girdi sırası:

```text
target_vehicle_event
-> cabin ROI
-> visibility gate
-> face/driver/torso candidate
-> face-near / upper-body phone ROI
-> phone detector
-> temporal persistence
-> driver association
-> FTR adapter
```

`poor` veya `not_visible` cabin frame'lerinde phone risk kararı kapalı kalır.

## Başlangıç Modelleri

| Deney | Model | Amaç |
|---|---|---|
| `PHONE-EXP-003` | YOLO26s-P2 | Küçük nesne head katkısını test eden primary challenger. |
| `PHONE-EXP-004` | standard YOLO26s | P2 katkısını izole eden kontrol modeli. |
| `PHONE-EXP-005` | YOLO26m-P2 | Veri büyürse accuracy challenger. |

Bu modeller aynı veri, aynı augmentasyon, aynı seed, aynı `imgsz=960` ve aynı evaluation split
ile karşılaştırılmalıdır.

## Veri Kapısı

Pozitif-only küçük crop seti baseline olarak kabul edilmeyecektir. Minimum veri kapısı:

| Veri tipi | Minimum |
|---|---:|
| Pozitif phone crop | 200-500 |
| Negatif/hard-negative | Pozitifin 2-3 katı |
| Held-out session/video | En az 1 tamamen ayrık session |
| View çeşitliliği | side window + front LHD |
| Zorluk çeşitliliği | low-light, reflection, phone near face, hand near face without phone |

Hard-negative örnekleri:

* El yanakta ama telefon yok.
* Yolcu telefonu.
* Cam/trim yansıması.
* Koyu renk iç trim.
* Kısmi görünen yüz/baş desteği.
* Telefon benzeri küçük parlak yüzeyler.

## Label Set

İlk aşama tek sınıf:

```text
phone
```

Gelecekte gerekirse:

```text
phone_in_driver_hand
phone_near_driver_face
passenger_phone
```

Ancak ilk FTR adapter için tek bbox + temporal/driver association yeterlidir.

## Metrikler

| Metrik | Neden |
|---|---|
| Precision | False alarm FTR skoru ve güvenilirlik için kritik. |
| Recall | Telefonu kaçırmamak için kritik. |
| F1 | Precision/recall dengesi. |
| False positive per minute | Video bazlı manuel review için daha okunur. |
| Time-to-first-detection | Event başlangıcını değerlendirmek için. |
| Temporal persistence pass rate | Tek kare false positive'i engellemek için. |
| Driver association pass rate | Yolcu telefonu / arka plan karışmasını engellemek için. |

## Temporal Gate

Tek frame phone detection `telefonla_konusma` olarak yazılmamalıdır.

Önerilen ilk gate:

```text
min_detection_count = 3
window_s = 1.0
min_confidence = 0.25 smoke / TBD final
driver_roi_overlap_or_distance_required = true
visibility_status in {good, limited}
```

Gate geçerse FTR adapter şu çıktıyı yazabilir:

```json
{
  "kategori": "sofor_eylemi",
  "etiket": "telefonla_konusma",
  "confidence_score": 0.0
}
```

Confidence daha sonra validation split ve threshold sweep ile belirlenecektir.

## İlk Uygulama Adımı

1. `CABIN-EXP-012` overlayleri manuel kontrol edilir.
2. Phone ROI export scripti yazılır:
   ```text
   scripts/benchmarks/prepare_phone_specialist_dataset.py
   ```
3. Pozitif + hard-negative dataset YOLO formatına çevrilir.
4. Colab notebook hazırlanır:
   ```text
   notebooks/PHONE_EXP_003_004_YOLO26S_Phone_Specialist_Colab.ipynb
   ```
5. `PHONE-EXP-003` ve `PHONE-EXP-004` aynı koşullarda eğitilir.
6. Lokal 3 video üzerinde overlay ve CSV/JSON summary üretilir.
7. FTR adapter'a yalnız temporal gate geçen event yazılır.

## Kabul Kriteri

Phone specialist bir sonraki faza geçmek için:

* Held-out video/session üzerinde manuel review pass almalı.
* Pozitif-only smoke sonucu ile raporlanmamalı.
* False positive örnekleri açıkça listelenmeli.
* `results.json` contract'ına schema-valid çıktı verebilmeli.
* Runtime süresi Docker 10 dakika limitini zorlamamalı.

## Riskler

* Dış kameradan cabin görünürlüğü düşük olabilir.
* Telefon çok küçük ve karanlık olabilir.
* El/yüz/cam yansıması false positive üretebilir.
* Yolcu telefonu driver telefonu gibi algılanabilir.
* Yetersiz veriyle fine-tune model yalnız 3 videoya overfit olabilir.

Bu riskler nedeniyle phone çıktısı başlangıçta `support/evidence` olarak tutulmalı, final FTR
confidence threshold'u validation ve manuel review sonrası sabitlenmelidir.
