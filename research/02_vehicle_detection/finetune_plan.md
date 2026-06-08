# Vehicle Detection Fine-Tune Plan

## Amaç

Araç tespiti için Colab üzerinde tekrar üretilebilir fine-tune deneyi tasarlamak.

## Genel Yaklaşım

* Büyük modeli sıfırdan eğitmek yok.
* Public/pretrained ağırlıklar kullanılacak.
* İlk veri BDD100K 4 sınıf mapping olacak.
* Her deney aynı split ve aynı metrik protokolüyle karşılaştırılacak.
* MacBook runtime benchmark, Colab validation sonucundan ayrı tutulacak.
* Dark/rain/fog gibi koşula özel detector profilleri, yeterli condition-specific veri oluşmadan ayrı model olarak eğitilmeyecek.
* `general` detector yalnız normal/gündüz model anlamına gelmez; night/rain/fog gibi koşullar general training ve validation breakdown içinde korunur.
* Mevcut 3 dark video yalnız manuel benchmark ve failure-case analizi içindir.

## General Detector ve Condition Kapsamı

İlk fine-tune doğrudan araç detection üzerinde yapılacaktır. Bu aşamada ayrı condition detector veya ayrı condition-specific vehicle detector eğitimi beklenmeyecektir.

Bu karar `night_low_light`, `rain` ve `fog_low_visibility` kapsamlarının dışarıda bırakıldığı anlamına gelmez. Doğru yorum:

* General detector tüm koşulları gören tek ana araç detektörüdür.
* Dataset split ve validation sonuçları condition breakdown ile tutulur.
* BDD100K gibi veri setlerindeki `timeofday`, `weather`, `scene` metadata korunur.
* Eğitim setinde clear/day örnekleriyle birlikte night/rain/fog örnekleri de dengeli biçimde bulunur.
* Validation raporu yalnız overall mAP değil, `day_clear`, `night_low_light`, `rain`, `fog_low_visibility` gibi alt kırılımlarla verilir.
* Bir condition kırılımında general model anlamlı zayıf kalırsa specialist branch için gerekçe oluşur.

Bu nedenle ilk aşamada "condition detect + fine-tune" yerine "condition-aware general vehicle detection fine-tune" yapılır.

## İlk Deney Sırası

| Deney | Model | Veri | Img size | Amaç |
|---|---|---|---:|---|
| VD-EXP-001 | YOLO11n pretrained | `Test/video_1-3.mp4` dark manual set | 640 | Zero fine-tune baseline, dark routing smoke test ve JSON output |
| VD-EXP-002 | YOLO11n fine-tune | BDD100K 4-class, condition-aware split | 640 | İlk condition-aware road-domain baseline |
| VD-EXP-003 | YOLO11s fine-tune | BDD100K 4-class, same split | 640 | Quality gain ölçümü |
| VD-EXP-004 | YOLOv10n fine-tune | BDD100K 4-class, same split | 640 | NMS-free latency kıyası |
| VD-EXP-005 | YOLOv10s fine-tune | BDD100K + selected UA-DETRAC | 640 | Low-latency challenger |
| VD-EXP-006 | YOLOv8n fine-tune | BDD100K 4-class | 640 | Stable fallback |
| VD-EXP-007 | RT-DETR-L pilot | BDD100K small pilot | 640 | Transformer challenger |

## VD-EXP-002 Colab Hattı

Notebook:

* `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`

Mapping ve dataset card:

* `data/README_assets/bdd100k_vehicle_detection_mapping.yaml`
* `data/README_assets/bdd100k_vehicle_detection_dataset_card.md`

Notebook görevleri:

1. BDD100K Drive path'lerini doğrular.
2. BDD JSON detection label formatını YOLO label formatına çevirir.
3. `car`, `bus`, `truck`, `motorcycle` sınıf mapping'ini uygular.
4. `weather`, `timeofday`, `scene` metadata'sından condition profile üretir.
5. `data.yaml`, train/val split listeleri ve condition validation listeleri oluşturur.
6. `YOLO11n` fine-tune çalıştırır.
7. Overall validation ve condition breakdown validation sonuçlarını üretir.
8. `.pt` ve ONNX export çıktısını Drive altında saklar.

## Condition-Specific Fine-Tune Planı

Koşul profilleri:

* `general`
* `dark`
* `rain`
* `fog_low_visibility`
* `night_low_light`

İlk aşamada yalnız `general` detector eğitilir/ölçülür. Router, dark videolarda `dark` veya `night_low_light` profile çağırsa bile ayrı specialist model yoksa `general` detector fallback çalışır.

General modelin condition kapsamı:

| Condition | General Fine-Tune'daki Rol | Specialist'e Geçiş Şartı |
|---|---|---|
| `day_clear` | Ana normal koşul | Specialist yok |
| `night_low_light` | General training/validation içinde korunur | General düşük ışıkta zayıf kalırsa ilk specialist |
| `rain` | General training/validation içinde korunur | Night specialist fayda sağladıktan ve rain split yeterli olduktan sonra |
| `fog_low_visibility` | Mümkünse validation/external test içinde korunur | Fog subset ve benchmark yeterliyse |
| `dark` | Ayrı detector değil, low-light alt etiketi | Başlangıçta `night_low_light` veya general fallback |

Dark/rain/fog specialist detector eğitimine geçiş için:

* condition-specific public dataset subset'i bulunmalı,
* yeterli video çeşitliliği sağlanmalı,
* video-level split yapılmalı,
* ayrı validation/test set ayrılmalı,
* general detector'a göre anlamlı kazanım gösterilmeli.

Yeterli veri olmadan 3 video ile specialist model eğitimi yapılmayacaktır; aksi halde model ezberler ve raporda savunulamaz sonuç üretir.

## Augmentation İlkeleri

Kullanılabilir:

* brightness/contrast
* hafif motion blur
* Gaussian blur
* JPEG compression artifact
* random scale
* sınırlı perspective
* düşük ışık/yağmur/sis simülasyonu, kontrollü

Dikkat:

* Aşırı mosaic ve sert random crop plaka/ROI istatistiğini bozabilir.
* Küçük/uzak araçlar için augmentation sonrası bbox kalitesi kontrol edilmelidir.
* Validation setine augmentation uygulanmamalıdır.

## Colab Kayıt Standardı

Her deneyde kaydedilecekler:

* experiment_id
* repo commit SHA
* model name / version
* pretrained weight source
* dataset source and license note
* split id
* class mapping version
* image size
* epochs
* batch size
* optimizer/lr
* augmentation config
* training duration
* validation metrics
* test metrics
* export status
* notes and failure cases

## Export Planı

İlk hedef:

* PyTorch `.pt`
* ONNX

Sonraki hedefler:

* OpenVINO, MacBook CPU performansı için gerekirse.
* TFLite/NCNN yalnız Android on-device ihtimali güçlenirse.
* FP16/INT8 denemesi yalnız baseline kararlı hale geldikten sonra.

## Başarı Tanımı

İlk fine-tune başarılı sayılması için:

* Model 4 sınıf output üretmeli.
* Output contract ile uyumlu JSON'a çevrilebilmeli.
* BDD100K validation sonucu overall ve condition breakdown olarak kayıt altına alınmalı.
* MacBook runtime benchmark'a taşınabilecek export üretmeli.
* Failure cases görsel/metadata olarak repo dışında saklanmalı, repo içinde yalnız özetlenmeli.
