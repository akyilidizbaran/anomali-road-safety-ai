# Condition Profile Classifier Dataset Candidates

## Amaç

Canlı frame'den `condition_profile` tahmini yapan classifier için kullanılabilecek veri setlerini, görev uyumu ve lisans riski açısından özetlemek.

Bu dosya condition-specific vehicle detector dataset listesinden farklıdır. Buradaki hedef bbox üretmek değil, frame/sahne seviyesinde hava, ışık ve görüş profilini sınıflandırmaktır.

## Önerilen Veri Omurgası

İlk uygulanabilir omurga:

1. **BDD100K**: Ana eğitim ve ilk test kaynağı.
2. **ACDC**: Harici adverse condition doğrulama ve sınıf güçlendirme.
3. **DAWN**: Rain/fog/snow/sandstorm gibi zor hava koşulları için yardımcı test/fine-tune adayı.
4. **ExDark**: Düşük ışık davranışını güçlendirmek için auxiliary low-light kaynak.
5. **IDD-AW**: Domain genelleme için opsiyonel adverse-weather validation.

İlk MVP'de tek başına BDD100K ile MobileNetV3 baseline çıkarmak yeterlidir. ACDC/DAWN/ExDark, özellikle `fog_low_visibility`, `rain` ve low-light hataları belirginleşirse eklenmelidir.

## Aday Veri Setleri

| Dataset | Condition Bilgisi | Görüntü Tipi | İlk Rol | Lisans / Risk | Not |
|---|---|---|---|---|---|
| BDD100K | `weather`, `scene`, `timeofday` metadata | 720p dashcam / road scene | Ana train/val/test | Toolkit BSD-3; dataset terms ayrıca download portalında kontrol edilmeli | Canlı yol sahnesine en yakın ilk kaynak. |
| ACDC | Fog, nighttime, rain, snow | Adverse driving scene | Harici adverse validation + sınıf destek | Non-commercial kullanım şartları var | Rapor için güçlü adverse condition kaynağı; üretim/ticari iddialarda dikkat. |
| DAWN | Fog, rain, snow, sandstorm | Real-world traffic image | Rain/fog external test veya ek eğitim | Kaggle/Mendeley lisansı ayrıca doğrulanmalı | BDD100K'daki az fog/rain örneklerini destekleyebilir. |
| ExDark | 10 low-light condition | Low-light generic object image | Low-light auxiliary | Resmi repo BSD-3; ticari kullanım için yazar iletişim notu var | Road-specific değildir; classifier low-light robustness için yardımcı olabilir. |
| IDD-AW | Rain/fog/lowlight/night gibi adverse scene | Driving scene | Opsiyonel external validation | Resmi terms doğrulanmalı | Türkiye'ye değil farklı ülke/domain'e ait; genelleme testi için iyi olabilir. |
| Foggy Cityscapes / Foggy Driving | Sentetik/gerçek fog | Driving scene | Fog-only research benchmark | Cityscapes terms ve redistribution kısıtları | Fog classifier için sadece dikkatli research/eval adayı. |
| SHIFT | Controlled weather/time | Synthetic autonomous driving | Ablation / synthetic support | Resmi lisans doğrulanmalı | Domain gap nedeniyle ilk eğitim omurgası olmamalı. |

## BDD100K Mapping Önerisi

BDD100K metadata alanları condition profile'a şu şekilde indirgenebilir:

| BDD Alanları | Önerilen `condition_profile` |
|---|---|
| `timeofday=daytime`, `weather=clear/partly cloudy/overcast`, visibility normal | `day_clear` |
| `timeofday=night` | `night_low_light` |
| `timeofday=dawn/dusk` | `low_light_transition` |
| `weather=rainy` | `rain` |
| `weather=foggy` | `fog_low_visibility` |
| `weather=snowy` veya nadir adverse koşul | `adverse_other` |
| Metadata eksik/çelişkili | `unknown` |

Not: `rain` ve `night_low_light` aynı frame'de kesişebilir. İlk MVP'de tek label istenecekse öncelik sırası tanımlanmalıdır:

```text
fog_low_visibility > rain > night_low_light > low_light_transition > day_clear > adverse_other > unknown
```

İleri fazda multi-label classifier daha doğru olabilir:

```json
{
  "timeofday": "night",
  "weather": "rain",
  "visibility": "low"
}
```

Ancak ilk MVP için tek `condition_profile` router kararı daha basit ve raporlanabilir olur.

## Veri Dengesi Riski

VD-EXP-002 vehicle subset'inde condition dağılımı dengesiz çıktı:

| Profile | Train | Val | Test |
|---|---:|---:|---:|
| `general` | 23055 | 4918 | 4931 |
| `night_low_light` | 10116 | 2220 | 2103 |
| `rain` | 1625 | 335 | 360 |
| `fog_low_visibility` | 28 | 3 | 11 |

Bu dağılım vehicle detector subset'i içindir; classifier için full BDD metadata daha geniş olabilir. Yine de fog sınıfı kritik risk taşır. Fog için:

* BDD100K tek başına yeterli görülmemeli.
* ACDC fog ve DAWN fog ile external validation yapılmalı.
* Fog specialist detector eğitimi, classifier doğruluğu ve detector verisi birlikte yeterli olana kadar ertelenmeli.

## İlk Eğitim Stratejisi

MVP classifier için önerilen seçenek:

```text
Model: MobileNetV3-Small
Input: 224x224 RGB
Labels: day_clear, night_low_light, low_light_transition, rain, adverse_other, unknown
Fog: yeterli veri yoksa adverse_other/unknown altında tutulur
Loss: weighted cross entropy veya focal loss
Augmentation: brightness/contrast, blur, noise, rain/fog light simulation as ablation
Metric: macro-F1 + per-class recall
```

Alternatif:

```text
Model: ResNet18
Rol: challenger / sanity baseline
Gerekçe: Klasik, raporda açıklaması kolay, küçük veriyle stabil
```

## Manual Dark Video Smoke Test

3 lokal dark video için condition classifier smoke test şu şekilde kaydedilmeli:

| Alan | Açıklama |
|---|---|
| `video` | `Test/video_1.mp4` gibi kaynak |
| `sampled_frames` | Classifier'ın kaç frame örneklediği |
| `dominant_profile` | En sık stable profile |
| `dominant_confidence_mean` | Ortalama güven |
| `night_low_light_ratio` | Örneklerin kaçında gece/düşük ışık çıktığı |
| `unknown_ratio` | Güven düşük/kararsız oran |
| `routing_decision` | general veya specialist adayı |
| `fallback_reason` | Specialist aktif değilse neden |

Bu test final classifier accuracy değil, canlı router kullanılabilirliği smoke testidir.

## Kaynakça

* BDD100K dataset zoo açıklaması: https://docs.voxel51.com/dataset_zoo/datasets/bdd100k.html
* BDD100K BAIR duyurusu: https://bair.berkeley.edu/blog/2018/05/30/bdd/
* BDD100K download page: https://bdd-data.berkeley.edu/download.html
* ACDC resmi site: https://acdc.vision.ee.ethz.ch/
* ACDC paper: https://arxiv.org/html/2104.13395v4
* ACDC license/terms: https://acdc.vision.ee.ethz.ch/license
* DAWN Kaggle dataset page: https://www.kaggle.com/datasets/shuvoalok/dawn-dataset
* DAWN paper: https://arxiv.org/abs/2008.05402
* DAWN Mendeley data page: https://data.mendeley.com/datasets/766ygrbt8y/3
* ExDark official repository: https://github.com/cs-chan/Exclusively-Dark-Image-Dataset
* ExDark paper: https://arxiv.org/abs/1805.11227
* IDD-AW official page: https://iddaw.github.io/
