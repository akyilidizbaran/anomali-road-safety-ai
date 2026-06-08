# Condition-Specific Vehicle Detector Routing

## Amaç

Araç tespiti modelinin ortam koşuluna göre farklı uzman detector profilleriyle çalışmasını tasarlamak.

Kullanıcı hedefi:

* Karanlık ortamda dark profile / dark detector çağrılsın.
* Yağmurlu havada rainy profile / rainy detector çağrılsın.
* Sis, düşük görüş, normal gündüz gibi koşullarda uygun detector veya fallback profile seçilsin.

## Kritik Ayrım

Her frame için model yeniden eğitilmez.

Doğru çalışma:

1. Frame veya kısa frame penceresi alınır.
2. Lightweight scene/condition classifier ortamı belirler.
3. Router `condition_profile` üretir.
4. Önceden eğitilmiş veya fine-tune edilmiş uygun detector çağrılır.
5. Eğer condition confidence düşükse general detector fallback çalışır veya iki model karşılaştırmalı çalıştırılır.

## Başlangıç Profilleri

| Profile | Status | Model Kaynağı | Kullanım |
|---|---|---|---|
| `general` | MVP baseline | COCO-pretrained YOLO11n, sonra road-domain fine-tune | Varsayılan detector |
| `dark` | İlk test profile | Başlangıçta YOLO11n general; ileride low-light/dark fine-tune | Mevcut `Test/video_1-3.mp4` ile manuel benchmark |
| `rain` | Future profile | BDD100K rainy subset / ilgili açık veri | Yağmurlu koşul |
| `fog_low_visibility` | Future profile | fog/low visibility subset | Sis/düşük görüş |
| `night_low_light` | Future profile | BDD100K night + dark test expansion | Gece/düşük ışık |

İlk aşamada `dark` profili ayrı eğitilmiş model olmak zorunda değildir. Router dark modunu çağırdığında başlangıçta general YOLO11n çalıştırılır ve dark-condition performansı ölçülür. Yeterli veri oluşunca dark-specific fine-tune yapılır.

## Router Output Contract

Önerilen condition routing çıktısı:

```json
{
  "frame_id": "frame_000123",
  "condition_profile": "dark",
  "condition_confidence": 0.86,
  "selected_detector": "vehicle_detector_yolo11n_general_v1",
  "fallback_detector": "vehicle_detector_yolo11n_general_v1",
  "routing_mode": "single_profile",
  "routing_reason": "low_brightness_and_limited_visibility"
}
```

## Routing Modes

| Mode | Açıklama | Ne Zaman |
|---|---|---|
| `single_profile` | Yalnız seçili detector çalışır | Condition confidence yüksek |
| `general_fallback` | Condition detector başarısızsa general detector çalışır | Specialist düşük confidence dönerse |
| `dual_compare` | General + condition detector birlikte denenir | Yeni specialist doğrulanırken |
| `manual_review` | Çıktı manuel etiket/hata incelemesine gider | İlk dark video testlerinde |

## Dark Test Kararı

Mevcut test seti:

* `Test/video_1.mp4`
* `Test/video_2.mp4`
* `Test/video_3.mp4`

Bu videolar:

* training set değildir,
* model seçimi için tek başına yeterli değildir,
* ilk dark-condition smoke test ve manuel benchmark materyalidir,
* benchmark sonrası disk/memory yükü nedeniyle silinebilir.

## Fine-Tune İçin Veri Eşiği

Dark-specific detector eğitimi için 3 video yeterli kabul edilmez.

Dark profile fine-tune'a geçmek için önerilen minimumlar:

* farklı kamera açılarından video,
* farklı karanlık seviyeleri,
* araç tipleri dengeli dağılım,
* video-level train/val/test split,
* manuel bbox etiketi veya güvenilir açık dataset subset'i,
* en azından ayrı validation videosu.

Yeterli veri yoksa yapılacak doğru iş:

* general detector'ı dark videolarda ölçmek,
* failure case notlarını çıkarmak,
* threshold / confidence / preprocessing ayarı denemek,
* ileride dark fine-tune için veri gereksinimini netleştirmek.

## Benchmark Kararı

Her condition profile için ayrı benchmark tutulmalıdır:

* `general_day`
* `dark`
* `rain`
* `fog_low_visibility`
* `night_low_light`

Final model kararı overall skorla değil, condition breakdown ile verilmelidir. Dark profili kötü çalışıyorsa genel mAP iyi olsa bile demo riski yüksektir.
