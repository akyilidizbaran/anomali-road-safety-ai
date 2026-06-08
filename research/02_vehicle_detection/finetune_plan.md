# Vehicle Detection Fine-Tune Plan

## Amaç

Araç tespiti için Colab üzerinde tekrar üretilebilir fine-tune deneyi tasarlamak.

## Genel Yaklaşım

* Büyük modeli sıfırdan eğitmek yok.
* Public/pretrained ağırlıklar kullanılacak.
* İlk veri BDD100K 4 sınıf mapping olacak.
* Her deney aynı split ve aynı metrik protokolüyle karşılaştırılacak.
* MacBook runtime benchmark, Colab validation sonucundan ayrı tutulacak.

## İlk Deney Sırası

| Deney | Model | Veri | Img size | Amaç |
|---|---|---|---:|---|
| VD-EXP-001 | YOLO11n pretrained | küçük replay/test subset | 640 | Zero fine-tune baseline ve JSON output |
| VD-EXP-002 | YOLO11n fine-tune | BDD100K 4-class | 640 | İlk road-domain baseline |
| VD-EXP-003 | YOLO11s fine-tune | BDD100K 4-class | 640 | Quality gain ölçümü |
| VD-EXP-004 | YOLOv10n fine-tune | BDD100K 4-class | 640 | NMS-free latency kıyası |
| VD-EXP-005 | YOLOv10s fine-tune | BDD100K + selected UA-DETRAC | 640 | Low-latency challenger |
| VD-EXP-006 | YOLOv8n fine-tune | BDD100K 4-class | 640 | Stable fallback |
| VD-EXP-007 | RT-DETR-L pilot | BDD100K small pilot | 640 | Transformer challenger |

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
* BDD100K validation sonucu kayıt altına alınmalı.
* MacBook runtime benchmark'a taşınabilecek export üretmeli.
* Failure cases görsel/metadata olarak repo dışında saklanmalı, repo içinde yalnız özetlenmeli.
