# FTR Vehicle Detection Fine-Tune Plan

## Amaç

Bu dosya, Final Tasarım Raporu (FTR) formatındaki `Veriseti Oluşturulması`, `Yapay Zeka Çözümü` ve `Çözümün Sınanması` başlıklarına doğrudan taşınabilecek araç tespiti fine-tune planını tanımlar.

Bu aşamanın hedefi sıfırdan model eğitmek değildir. Hedef, COCO-pretrained YOLO11n ağırlıklarını BDD100K yol görüntüleriyle fine-tune ederek Anomali Road Safety AI için ölçülebilir, tekrar üretilebilir ve raporlanabilir bir `vehicle_detector_general` modeli hazırlamaktır.

Bu plan, önceki vehicle detection kararları ile `deep_research/condition_experts_deep_research_report.md` çıktılarının birleştirilmiş uygulama planıdır. Deep research tarafındaki ana sonuç korunur: önce güçlü general detector, sonra yalnız metrik üstünlüğü gösteren koşullar için sınırlı specialist detector.

## FTR Başlık Eşlemesi

| FTR Başlığı | Bu Çalışmada Üretilecek Kanıt |
|---|---|
| Proje Özeti | Araç tespitinin normal mod, tracking, risk, plate/OCR ve evidence hattındaki rolü |
| Veriseti Oluşturulması | BDD100K kaynak bilgisi, sınıf mapping, condition metadata, split, balancing, augmentation |
| Problemin Analizi | Düşük ışık, yağmur/sis, motion blur, uzak/küçük araç, occlusion, class imbalance |
| Çözüm Mimarisi | Raw frame -> preprocessing -> YOLO11n detector -> JSON output -> ByteTrack/evidence |
| Çözüm Detayları | Model mimarisi, input size, eğitim ayarları, post-processing, export, Colab/Drive altyapısı |
| Çözümün Sınanması | mAP, precision, recall, F1, class AP, condition breakdown, FPS/latency, manual dark video review |
| Kaynakça | BDD100K, Ultralytics YOLO11, COCO/pretrained kaynakları, ikincil dataset adayları |

## Nihai İlk Karar

* İlk fine-tune modeli: `YOLO11n`
* Eğitim ortamı: Google Colab GPU
* Veri depolama: Google Drive
* Ana dataset: BDD100K object detection labels
* İlk çıktı: `.pt` checkpoint
* Opsiyonel çıktı: ONNX export
* İlk hedef profil: `vehicle_detector_general`
* İlk sınıflar: `car`, `bus`, `truck`, `motorcycle`

ONNX export ilk FTR kabul kriteri değildir, ancak önerilir. `.pt` Colab eğitimi ve Ultralytics doğrulaması için yeterlidir. ONNX ise MacBook local edge/runtime, ileride backend entegrasyonu ve FTR'de dağıtım kabiliyeti göstermek için güçlü bir ek kanıttır. Bu yüzden plan: `.pt` zorunlu, ONNX opsiyonel ama notebook içinde tek hücreyle alınabilir şekilde tutulacak.

## Dataset Stratejisi

### 1. Ana Omurga - BDD100K

BDD100K ilk fine-tune için ana veri seti olarak seçilir.

Gerekçe:

* Yol ve sürüş sahnesi odaklıdır.
* Araç bbox anotasyonları içerir.
* `weather`, `timeofday`, `scene` gibi condition metadata alanlarıyla FTR'de veri dengesi ve koşul bazlı başarı analizi yapılabilir.
* `night_low_light`, `rain`, `fog_low_visibility`, `day_clear`, `low_light_transition` gibi proje condition profillerine kaynak sağlar.
* Colab/Drive içinde dönüştürülebilir ve YOLO formatına çevrilebilir.

Kullanım:

* Ana eğitim ve doğrulama seti olarak kullanılacak.
* Sınıflar dört MVP sınıfına indirgenecek.
* Condition metadata model sınıfı yapılmayacak; yalnız balancing, validation breakdown ve ileride specialist model kararı için tutulacak.

Kaynaklar:

* https://github.com/bdd100k/bdd100k
* https://github.com/ucbdrive/bdd100k/blob/master/doc/format.md
* https://openaccess.thecvf.com/content_CVPR_2020/papers/Yu_BDD100K_A_Diverse_Driving_Dataset_for_Heterogeneous_Multitask_Learning_CVPR_2020_paper.pdf
* Pratik Colab mirror: https://www.kaggle.com/datasets/solesensei/solesensei_bdd100k

Kaggle mirror kararı:

* Notebook `DOWNLOAD_METHOD = 'kaggle'` ve `KAGGLE_DATASET_SLUG = 'solesensei/solesensei_bdd100k'` olacak şekilde sabitlenmiştir.
* Bu mirror, Colab/Drive pratikliği için seçilmiştir; resmi kaynakça ve lisans değerlendirmesinde BDD100K resmi kaynakları esas alınır.
* İlk Colab koşusunda label path, image path ve `weather/timeofday/scene` metadata alanları doğrulanmadan training başlatılmamalıdır.

2026-06-13 Drive kontrolü:

* Drive'da `datasets/bdd100k` altında image verisi ve `solesensei_bdd100k.zip` görüldü.
* Drive aramasında `det_train.json`, `det_val.json`, `bdd100k_labels_images_train.json`, `bdd100k_labels_images_val.json` veya `Detection 2020 Labels` dosyası bulunmadı.
* Bu nedenle tüm image setini tekrar indirmek yerine yalnız BDD100K `Detection 2020 Labels` arşivi eklenmelidir.
* Notebook varsayılan olarak mevcut Drive image verisini kullanır; label arşivi `datasets/bdd100k/bdd100k_det_20_labels_trainval.zip` konumuna eklenirse otomatik açar.
* Label arşivi için pratik direct URL: https://dl.cv.ethz.ch/bdd100k/data/bdd100k_det_20_labels_trainval.zip
* Notebook artık bu URL'den yalnız label arşivini Drive'a indirebilir; image zip'lerini tekrar indirmez.

### 2. COCO'nun Rolü

COCO bu projede ayrı bir ana eğitim veri seti olarak eklenmeyecek. COCO'nun ilk rolü YOLO11n pretrained başlangıç ağırlığıdır.

Gerekçe:

* YOLO11n zaten genel nesne algılama bilgisini pretrained ağırlık üzerinden taşır.
* BDD100K ile doğrudan road-domain adaptation yapılması daha temiz ve FTR'de savunulabilir bir deney sağlar.
* COCO'yu ayrıca training merge içine eklemek sınıf mapping, domain farkı ve veri dengesi raporunu gereksiz karmaşıklaştırabilir.

COCO ancak şu durumda ayrıca ele alınır:

* BDD100K subseti çok küçük tutulursa,
* `motorcycle` gibi sınıflarda ciddi veri yetersizliği görülürse,
* class imbalance kontrolü için kontrollü ek veri gerekirse.

### 3. Specialist / Adverse Condition Adayları

Arkadaşının önerdiği dataset omurgası mantıklı bir araştırma yönü gösteriyor, ama ilk fine-tune'a hepsini aynı anda sokmak doğru değil. Doğru kullanım sırası:

1. Önce BDD100K ile `vehicle_detector_general`.
2. Sonra BDD100K condition breakdown ile zayıf koşulu bul.
3. Zayıflık kanıtlanırsa ilgili condition specialist datasetini ayrı deney olarak aç.
4. Specialist modelin general modele göre anlamlı kazanç getirdiği gösterilirse router'a bağla.

| Koşul | Aday Dataset | İlk Aşamadaki Rol | Not |
|---|---|---|---|
| `night_low_light` | BDD100K night | Ana training/validation kırılımı | İlk aşamada general model içinde kalır |
| `night_low_light` | ACDC night | Specialist/evaluation adayı | ACDC daha çok adverse semantic perception odaklıdır; bbox uygunluğu ayrıca kontrol edilmeli |
| `dark` | ExDark vehicle-only | Low-light robustness adayı | Road-domain değildir; yalnız vehicle subset ve lisans kontrolüyle kullanılmalı |
| `rain` | BDD100K rainy | Ana training/validation kırılımı | İlk aşamada yeterli |
| `rain` | ACDC rain / DAWN rain | Specialist/evaluation adayı | DAWN object detection odaklıdır; boyut küçük olabilir |
| `fog_low_visibility` | ACDC fog / DAWN fog | Specialist/evaluation adayı | İlk modelden sonra açılmalı |
| `fog_low_visibility` | Foggy Cityscapes / Foggy Zurich | External/synthetic fog adayı | Cityscapes lisans ve sentetik domain gap nedeniyle dikkatli kullanılmalı |

Kaynaklar:

* ACDC: https://acdc.vision.ee.ethz.ch/
* ACDC paper: https://openaccess.thecvf.com/content/ICCV2021/papers/Sakaridis_ACDC_The_Adverse_Conditions_Dataset_With_Correspondences_for_Semantic_Driving_ICCV_2021_paper.pdf
* DAWN paper: https://arxiv.org/abs/2008.05402
* ExDark official: https://github.com/cs-chan/Exclusively-Dark-Image-Dataset
* Cityscapes license: https://www.cityscapes-dataset.com/
* Foggy Cityscapes description: https://people.ee.ethz.ch/~csakarid/SFSU_synthetic/

## Arkadaş Önerisinin Değerlendirmesi

Ekteki önerinin güçlü tarafı, datasetleri `general`, `dark/night`, `rain`, `fog` koşullarına göre ayırmasıdır. Bu, bizim condition-aware mimarimizle uyumludur.

Ancak öneri ilk uygulama için fazla geniştir. Aynı anda BDD100K, COCO, ACDC, ExDark, DAWN, Foggy Cityscapes, Foggy Zurich ve sentetik türevleri birleştirmek şu riskleri üretir:

* Etiket formatları farklıdır.
* Lisans koşulları farklıdır.
* Bazıları semantic segmentation odaklıdır; doğrudan bbox training için ek dönüşüm gerekebilir.
* Bazıları road-domain değildir veya sentetiktir.
* Class mapping ve condition balancing FTR süresini gereksiz karmaşıklaştırır.
* İlk modelin neden iyi/kötü çalıştığını analiz etmek zorlaşır.

Bu yüzden öneriyi tamamen reddetmiyoruz; fazlara bölüyoruz:

* FTR ilk model: BDD100K + YOLO11n.
* FTR robustness analizi: BDD100K condition breakdown.
* Sonraki faz: ACDC/DAWN/ExDark/Foggy Cityscapes kaynak-lisans doğrulaması.
* Specialist faz: yalnız ihtiyaç kanıtlanırsa condition-specific fine-tune.
* Orta vade: Türkiye'ye özgü kontrollü yerel çekim + manuel etiketleme.

Türkiye'ye özgü, açık lisanslı, güçlü bbox yoğunluklu ve condition-etiketli bir veri setinin öne çıkmaması tespiti doğru kabul edilebilir. Ancak bu, ilk aşamada yerel veri toplamayı zorunlu yapmaz. Yerel çekim orta vadeli final acceptance ve domain validation için planlanmalıdır.

## Veri Hazırlama Planı

### Kaynak Yerleşimi

Colab/Drive hedef dizini:

```text
/content/drive/MyDrive/anomali-road-safety-ai/
  datasets/
    bdd100k/
      images/
      labels/
    bdd100k_vehicle_yolo/
      images/
      labels/
      splits/
      metadata/
  runs/
    vehicle_detection/
      VD-EXP-002/
```

Ham BDD100K dosyaları Git'e eklenmez. Drive üzerinde tutulur.

### Sınıf Mapping

| Kaynak Kategori | Hedef Sınıf |
|---|---|
| `car` | `car` |
| `bus` | `bus` |
| `truck` | `truck` |
| `motor`, `motorcycle`, `motorbike` | `motorcycle` |

Ignore:

* `person`
* `rider`
* `bike`
* `bicycle`
* `traffic light`
* `traffic sign`
* `train`
* `other vehicle`
* belirsiz veya bbox kalitesi düşük objeler

### Condition Mapping

Condition alanları model sınıfı değildir; metadata olarak saklanır.

| BDD100K Alanı | Proje Profili |
|---|---|
| `timeofday=daytime`, `weather=clear/overcast/partly cloudy` | `day_clear` |
| `timeofday=night` | `night_low_light` |
| `timeofday=dawn/dusk` | `low_light_transition` |
| `weather=rainy` | `rain` |
| `weather=foggy` | `fog_low_visibility` |
| `weather=snowy` | `adverse_other` |
| `scene=tunnel/parking lot` | `tunnel_or_parking_dark` |
| eksik/undefined | `unknown` |

### Split Politikası

İlk uygulanabilir split:

* Train: %70
* Validation: %15
* Test: %15

Önemli kurallar:

* Aynı sahne/video kaynağı train ve val/test arasında sızdırılmamalı.
* Test seti model seçimi için tekrar tekrar kullanılmamalı.
* Condition dağılımı raporlanmalı.
* Az örnekli condition profilleri için metrikler "sınırlı örnek" notuyla verilmelidir.

### Data Balancing

FTR'de şu tablolar üretilecek:

* sınıf başına bbox sayısı,
* split başına image sayısı,
* split başına bbox sayısı,
* condition başına image sayısı,
* condition başına bbox sayısı,
* class-condition çapraz dağılımı.

Dengesizlik varsa ilk çözüm aşırı veri karıştırmak değil:

* sampling ağırlığı,
* condition-aware split,
* augmentation,
* validation breakdown ile açık raporlama.

## Augmentation Planı

İlk güvenli augmentation seti:

* brightness/contrast jitter,
* hafif Gaussian blur,
* hafif motion blur,
* JPEG compression,
* scale/translate,
* sınırlı perspective,
* HSV augmentation.

Kontrollü kullanılacaklar:

* synthetic rain,
* synthetic fog,
* aggressive low-light transform,
* mosaic.

Validation/test setine augmentation uygulanmaz. Augmentation yalnız training tarafında kullanılır ve FTR'de açıkça belirtilir.

## Model Eğitim Planı

### VD-EXP-002 - YOLO11n BDD100K Fine-Tune

Notebook:

* `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`

Başlangıç config:

| Alan | Değer |
|---|---|
| Model | `yolo11n.pt` |
| Input size | 640 |
| Classes | 4 |
| Epoch | ilk koşu için 50, süreye göre 100'e çıkarılabilir |
| Batch | Colab GPU belleğine göre otomatik/manuel |
| Patience | 10-20 |
| Device | Colab GPU |
| Output | `.pt`, opsiyonel ONNX |

İlk koşuda amaç en yüksek skoru almak değil, pipeline'ın baştan sona doğru çalıştığını kanıtlamaktır.

### Model Karşılaştırması

İlk zorunlu model:

* YOLO11n

Opsiyonel challenger:

* YOLO11s

YOLO11s yalnız şu durumda açılmalı:

* YOLO11n recall düşük kalırsa,
* düşük ışıkta false negative yüksekse,
* MacBook runtime bütçesi YOLO11s'i kaldırabilecek görünürse.

## Değerlendirme Planı

### Otomatik Metrikler

FTR için temel metrikler:

* mAP@0.5,
* mAP@0.5:0.95,
* precision,
* recall,
* F1,
* class AP,
* confusion matrix,
* FPS,
* mean latency,
* p95 latency.

### Condition Breakdown

Her metric mümkünse şu kırılımlarda raporlanacak:

* `day_clear`
* `night_low_light`
* `rain`
* `fog_low_visibility`
* `low_light_transition`
* `adverse_other`
* `unknown`

Bu tablo, specialist detector gerekip gerekmediğinin ana kanıtı olacak.

### Local Dark Video Smoke Test

Mevcut 3 dark video training verisi değildir.

Kullanım:

* fine-tune sonrası local smoke/manual test,
* false negative gözlemi,
* bbox kullanılabilirlik kontrolü,
* ByteTrack'e giriş kalitesi kontrolü,
* evidence crop kullanılabilirliği.

Rapor dili:

* "manual qualitative review"
* "smoke test"
* "pipeline usability"

Bu sonuçlar ground-truth mAP gibi sunulmaz.

## Çıktılar

Colab/Drive üzerinde üretilecekler:

* YOLO formatlı dataset,
* `data.yaml`,
* split listeleri,
* condition metadata CSV,
* class distribution CSV,
* pretrained baseline metrics,
* fine-tuned metrics,
* condition breakdown metrics,
* confusion matrix,
* training curves,
* `.pt` checkpoint,
* opsiyonel ONNX export,
* FTR tablo/grafik görselleri.

Repo içinde tutulacak küçük kanıtlar:

* deney planı,
* dataset card,
* mapping YAML,
* küçük CSV/JSON özetler,
* model card,
* FTR uyumlu Markdown özet.

Repo dışında tutulacaklar:

* ham BDD100K verisi,
* lokal video,
* model ağırlıkları,
* run klasörleri,
* crop/overlay görselleri,
* kişisel veri içerebilecek evidence çıktıları.

## FTR'ye Yazılacak Ana İddia

Doğru iddia:

> Araç tespiti modülü, BDD100K yol görüntüleri üzerinde YOLO11n tabanlı olarak fine-tune edilmiş ve farklı çevresel koşullara göre ayrı validasyon kırılımlarıyla değerlendirilmiştir. Sistem, tek başına hukuki karar üretmez; tracking, risk analizi, QoD ve evidence package hattına bbox, sınıf, güven skoru ve frame metadata sağlar.

Kaçınılacak iddialar:

* her koşulda tüm araçları kesin yakalar,
* hukuki delil üretir,
* ceza kararı verir,
* Türkiye'deki tüm yol koşullarına genellenmiştir,
* hız/plaka/şerit problemleri araç tespitiyle tamamen çözülmüştür.

## Sonraki Aksiyonlar

1. Notebook config'i `YOLO11n`, `.pt mandatory`, `ONNX optional` olacak şekilde son kontrol et.
2. BDD100K download/placement akışını Colab + Drive için çalıştır.
3. BDD100K -> YOLO conversion hücresini küçük subset ile smoke test et.
4. Class/condition distribution tablolarını üret.
5. Pretrained YOLO11n validation çalıştır.
6. YOLO11n general fine-tune çalıştır.
7. General model için overall validation + condition breakdown çıkar.
8. Night/rain/fog specialist deneylerini varsayılan kapalı tut; yalnız general modelin zayıf kaldığı condition için sırayla aç.
9. Specialist açılırsa aynı train/val/test protokolünde general'e karşı karşılaştır.
10. En iyi `.pt` checkpoint'i Drive'da sakla.
11. 3 dark video üzerinde local runtime/manual smoke test yap.
12. FTR tablo/grafik/model card özetlerini repo içine küçük artifact olarak işle.
