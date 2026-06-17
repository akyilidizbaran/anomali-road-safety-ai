# VD-EXP-002 Motorcycle / Car Class Confusion Action Note

## Güncel Karar - 2026-06-15

Durum: **Motorcycle özel fine-tune ertelendi**

Kullanıcı manuel review kararına göre mevcut kısa vadeli sistem odağı motorcycle
ayrımı değil, ana araç / `car` tespitinin stabil şekilde çalışmasıdır.

Aktif runtime kararı:

* Aktif detector: `VD-EXP-002-GENERAL-YOLO11N`
* Aktif checkpoint: `models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt`
* Runtime/demo confidence threshold: `TBD after threshold sweep`
* Current manual-review candidate false-positive pruning gate: `0.60`
* Ana araç: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4` içinde her frame'de yakalanıyor.
* BBox: ana araç için stabil.
* False positive: düşük threshold'da gözleniyor; `confidence >= 0.60` ile gözlenen false positive problemi bu manual review kapsaminda kalmıyor. Bu değer final threshold değildir.

`VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N` denemesi BDD100K tabanlı motorcycle
iyileştirmede beklenen sonucu vermediği için runtime'a terfi ettirilmedi.
Bu nedenle bu dosyadaki motorcycle aksiyonları aktif çalışma değil, ileri faz
teknik borç / deferred improvement olarak ele alınmalıdır.

## Gözlem

`VD-EXP-002` fine-tuned general YOLO11n smoke testinde `Test/video_3.mp4` için otomatik özet:

| Video | Frame | Detection | Class dağılımı |
|---|---:|---:|---|
| `Test/video_3.mp4` | 383 | 617 | `car:611`, `motorcycle:6` |

Kullanıcı manuel gözlemine göre sahnede normalde 1 araba + 1 motosiklet vardır. Buna rağmen model motosikleti büyük ölçüde `car` olarak tahmin ediyor.

Bu durum final accuracy iddiası değildir; manual review ile doğrulanması gereken class-level hata örüntüsüdür.

2026-06-15 güncel manuel review:

* Ana araç her frame'de doğru tespit ediliyor.
* Arka planda çok karanlıkta görünen motosiklet, görünür olduğu karelerde sistematik biçimde `car` olarak sınıflandırılıyor.
* Bu hata birkaç frame'lik flicker değil, sistematik motorcycle/car confusion olarak ele alınmalıdır.
* Ancak bu gözlem, runtime tarafında per-video override olarak kullanılmayacaktır. Detector `car` diyorsa event/evidence tarafına `car` etiketi taşınacaktır.
* Manuel review yapılandırılmış kayıt dosyası: `testing/manual_reviews/vd_exp_002_dark_video_manual_review.json`

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

## Manual Review Durumu

İlk manuel değerlendirme tamamlandı ve hata örüntüsü doğrulandı. Sayısal frame-level ground truth hâlâ yoktur; bu nedenle aşağıdaki alanlar ileride daha hassas sayım için korunur:

| Alan | Açıklama |
|---|---|
| `motorcycle_visible_frames` | Motosikletin gerçekten göründüğü frame sayısı |
| `motorcycle_detected_as_motorcycle` | Doğru sınıfla yakalanan frame sayısı |
| `motorcycle_detected_as_car` | Yanlış `car` sınıfıyla yakalanan frame sayısı |
| `motorcycle_missed` | Hiç yakalanmayan frame sayısı |
| `bbox_adequate` | Yanlış sınıf olsa bile bbox aracı kapsıyor mu |
| `low_light_or_blur_reason` | Hatanın düşük ışık/blur/parlama ile ilişkisi |

Bu sayım yapılmadan "motorcycle recall" veya "motorcycle accuracy" iddiası kurulmayacak. Mevcut ifade yalnız `manual qualitative review` olarak kullanılmalıdır.

## Kısa Vadeli Sistem Kararı

Risk/evidence MVP için class ayrımı yerine önce "vehicle present + track continuity" güvenceye alınabilir.

Bu nedenle ilk rapor dili:

> Model, düşük ışık test videosunda araç varlığını yakalayabilmektedir; ancak motosiklet sınıf ayrımı manuel review gerektiren bir hata örüntüsü göstermiştir.

Kaçınılması gereken ifade:

> Model car/motorcycle ayrımını karanlık ortamda güvenilir biçimde yapmaktadır.

Runtime politikası:

* Raw detector class count korunur.
* Detector `car` diyorsa event/evidence tarafında `car` etiketi taşınır.
* Bu 3 video için özel kural yazılmaz.
* Gözlem yalnız model geliştirme failure-case'i olarak kullanılır.
* Model düzeltmesi `VD-EXP-006-MOTORCYCLE-FOCUS` kapsamında denendi ancak başarısız/regresyon kabul edildi; yeni motorcycle çalışması ileri faza ertelendi.

## Model İyileştirme Aksiyonları

Bu aksiyonlar **aktif sprint dışına alınmıştır**:

1. BDD100K train metadata içinde `motorcycle` örnek sayısı ve condition kırılımı çıkarılacak.
2. `motorcycle_focus` validation subset oluşturulacak.
3. BDD100K dışı, motorcycle açısından daha uygun açık veri setleri ayrıca araştırılacak.
4. Eğer YOLO11n class ayrımı yeterli değilse YOLO11s challenger veya targeted specialist değerlendirilecek.
5. Runtime tarafında class confidence/quality metadata yazılabilir; ancak detector `car` diyorsa event/evidence sınıf etiketi `car` olarak taşınacak, sample-specific override yapılmayacak.

Aktif sprintte yapılacak:

1. `VD-EXP-002-GENERAL-YOLO11N` detector modelini aktif model olarak koru; confidence threshold değerini threshold sweep + manual review sonrası seç.
2. Tracking, plate/OCR, relative speed ve risk/evidence fusion kapsamlarına geç.
3. Heavy vehicle detection tune yalnız `car` detection stabilitesinde yeni bir sorun çıkarsa yeniden açılsın.

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

## Güncel Kısa Vadeli Kod Durumu

`run_vehicle_detection_video_smoke.py` manual review dosyasını okuyarak her video için `class_quality` alanı üretir. Bu alan raw sınıfı bastırmaz; yalnız model geliştirme notunu taşır. `video_3` için beklenen kısa vadeli çıktı:

```json
{
  "class_review_required": false,
  "raw_detector_class_counts_are_final": true,
  "class_reliability": "raw_detector_prediction_used",
  "recommended_event_label": "car",
  "event_policy": "carry the detector class as predicted in event/evidence"
}
```
