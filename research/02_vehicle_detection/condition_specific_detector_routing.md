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
| `night_low_light` | İlk specialist adayı | `best_general` checkpoint -> night/low-light fine-tune | Mevcut `Test/video_1-3.mp4` ile smoke/manual benchmark |
| `rain` | İkinci specialist adayı | BDD100K rainy + ACDC/DAWN rainy subset | Yağmurlu koşul |
| `fog_low_visibility` | Üçüncü specialist adayı | ACDC fog + Foggy Cityscapes/Foggy Driving + DAWN fog | Sis/düşük görüş |
| `dark` | Ayrı detector değil | Başlangıçta `night_low_light` routing etiketi | Parking/tunnel/dark gibi alt koşulların izlenmesi |

Deep research sonucu, ilk aşamada `dark` profilinin ayrı detector olarak açılmamasını önerir. `dark`, `tunnel_or_parking_dark` ve benzeri alt koşullar önce condition profile katmanında izlenir; detector seçimi gerekiyorsa `night_low_light` uzmanına veya `general` fallback'e route edilir.

Koşul uzmanları `best_general` checkpoint'ten türetilmelidir. `best_general` seçilmeden ayrı specialist detector eğitilmez.

## Router Output Contract

Önerilen condition routing çıktısı:

```json
{
  "frame_id": "frame_000123",
  "condition_profile": "night_low_light",
  "condition_confidence": 0.86,
  "selected_detector": "vehicle_detector_yolo11n_general_v1",
  "fallback_detector": "vehicle_detector_yolo11n_general_v1",
  "routing_mode": "manual_review",
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

Night/low-light specialist eğitimi için 3 video yeterli kabul edilmez.

Night/low-light specialist fine-tune'a geçmek için önerilen minimumlar:

* farklı kamera açılarından video,
* farklı karanlık seviyeleri,
* araç tipleri dengeli dağılım,
* video-level train/val/test split,
* manuel bbox etiketi veya güvenilir açık dataset subset'i,
* en azından ayrı validation videosu.

Yeterli veri yoksa yapılacak doğru iş:

* general detector'ı dark/night videolarda ölçmek,
* failure case notlarını çıkarmak,
* threshold / confidence / preprocessing ayarı denemek,
* ileride `night_low_light` fine-tune için veri gereksinimini netleştirmek.

## Promotion Kuralı

Bir specialist detector routing'e aktif eklenmeden önce general modelle aynı condition validation setinde karşılaştırılır.

Minimum kabul önerisi:

* `mAP@0.5:0.95` en az +2.0 puan veya `AP@0.5` en az +3 puan,
* ya da recall/missed detection tarafında proje açısından anlamlı iyileşme,
* FP/min artışı kontrol altında,
* MacBook p95 latency bütçesi aşılmamış,
* yanlış route olabilecek mixed-condition sette general'e göre ciddi bozulma yok.

Bu koşullar sağlanmazsa specialist model eğitilmiş olsa bile `enabled=false` kalır ve general fallback kullanılır.

## Benchmark Kararı

Her condition profile için ayrı benchmark tutulmalıdır:

* `general_day`
* `dark`
* `rain`
* `fog_low_visibility`
* `night_low_light`

Final model kararı overall skorla değil, condition breakdown ile verilmelidir. Dark profili kötü çalışıyorsa genel mAP iyi olsa bile demo riski yüksektir.
