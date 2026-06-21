# Model-First Cabin / Driver Baseline Plan v1

Tarih: 2026-06-21

`CABIN-EXP-012` heuristik ROI/visibility denemesi manuel kontrolde baseline kalitesinde
görülmediği için kaldırıldı. Yeni başlangıç noktası model-first olacaktır: önce sürücü eylemi
sınıflandırma baseline'ı, ardından küçük nesne specialist detector ve yolcu/koltuk konumu
modeli.

## Neden Model-First?

Heuristik cabin ROI yaklaşımı dış kameradan çekilen karanlık/yan görüş videolarda güvenilir
görünmedi. Bu nedenle önce modelin doğrudan sürücü eylemi ve küçük nesne sinyallerini öğrenmesi
daha savunulabilir.

Bu karar şu kaynaklarla uyumludur:

* State Farm Distracted Driver Detection, 10 sınıflı driver action sınıflandırma problemi sunar:
  `safe driving`, `texting`, `talking on the phone`, `drinking`, `reaching behind`, vb.
  Kaynak: https://www.kaggle.com/competitions/state-farm-distracted-driver-detection/data
* AUC Distracted Driver Dataset, farklı ülkelerden 44 katılımcı ile distracted driver verisi
  sağlar. Kaynak: https://heshameraqi.github.io/distraction_detection
* Drive&Act, 12 saatten fazla ve 9.6 milyon frame içeren çok modlu fine-grained driver behavior
  benchmark'ıdır; büyük ve karmaşık olduğu için ilk baseline değil, sonraki araştırma/fine-tune
  kaynağıdır. Kaynak: https://driveandact.com/
* Phone gibi küçük nesneler için Roboflow Universe tarafında phone/mobile-phone detection veri
  setleri ve pretrained model seçenekleri bulunur. Kaynak:
  https://universe.roboflow.com/search?q=class%3Amobile-phone

## Yeni Deney Sırası

### CABIN-EXP-020A: Cabin / Driver View Baseline

Amaç:

Doğrudan eylem sınıflandırmasına geçmeden önce frame/crop içinde cabin ve sürücü görünür mü
sorusunu model tabanlı cevaplamak.

İlk sınıflar:

```text
driver_cabin_visible
not_cabin_view
```

Önerilen ilk model:

```text
MobileNetV3-Large ve EfficientNet-B0 binary image classifier
```

Veri:

* Pozitif: State Farm Distracted Driver Detection görüntüleri.
* Negatif: mevcut BDD100K dış/yol görüntüleri veya Drive altında manuel
  `datasets/cabin_exp_020a/negatives/not_cabin_view/` klasörü.

İlk notebook:

```text
notebooks/CABIN_EXP_020A_Cabin_Driver_View_Baseline_Colab.ipynb
```

Beklenen çıktı:

```text
models/checkpoints/cabin_driver/CABIN-EXP-020A/
models/benchmarks/artifacts/cabin_driver/CABIN-EXP-020A/
testing/reports/cabin_exp_020a_driver_view_baseline.md
```

### CABIN-EXP-020B: Driver Action Classifier Baseline

Amaç:

FTR `sofor_eylemi` etiketleri için ilk çalışır classifier baseline'ı kurmak.

Önerilen ilk model:

```text
MobileNetV3-Large veya EfficientNet-B0 image classifier
```

Gerekçe:

* Colab'da hızlı fine-tune edilir.
* MacBook runtime için hafiftir.
* Önceki condition/VATTR çalışmalarındaki notebook yapımıza benzer.
* State Farm / AUC gibi classification veri setleriyle uyumludur.

İlk label mapping:

| Kaynak sınıf | FTR etiketi |
|---|---|
| talking on phone left/right | `telefonla_konusma` |
| texting left/right | `telefonla_konusma` veya `telefon_kullanimi_candidate` internal |
| drinking | `su_icme` |
| reaching behind | `arkaya_bakma` candidate |
| talking to passenger | `etrafa_bakinma` / `passenger_interaction_candidate` |
| safe driving | no event |

Not: `esneme`, `sigara_icme`, `emniyet_kemeri_ihlali` State Farm ile tam kapanmaz; bunlar
ayrı specialist veya ek dataset ister.

İlk notebook:

```text
notebooks/CABIN_EXP_020B_Driver_Action_Classifier_Colab.ipynb
```

Beklenen çıktı:

```text
models/checkpoints/cabin_driver/CABIN-EXP-020B-driver-action-classifier-best.pth
models/benchmarks/artifacts/CABIN-EXP-020B-driver-action-classifier-summary.json
testing/reports/cabin_exp_020b_driver_action_classifier.md
```

### CABIN-EXP-021: Small-Object Specialist Baseline

Amaç:

Driver action classifier çıktısını destekleyecek veya çürütecek küçük nesne detector kurmak.

İlk hedef sınıflar:

```text
phone
cigarette
bottle_or_cup
laptop_or_computer
```

Önerilen ilk model:

```text
YOLO11s veya YOLO26s-P2
```

Gerekçe:

* Phone/cigarette gibi küçük nesnelerde object detector, action classifier'dan daha açıklanabilir
  evidence üretir.
* FTR `nesneler` için `bilgisayar` sınıfı object detector tarafında daha doğal çözülür.
* P2/small-object head seçeneği phone gibi küçük bbox'larda avantaj sağlayabilir; standart
  modelle karşılaştırılmalıdır.

İlk notebook:

```text
notebooks/CABIN_EXP_021_Small_Object_Specialist_Colab.ipynb
```

### CABIN-EXP-022: Passenger / Seat-Region Baseline

Amaç:

FTR `yolcular` etiketlerini üretmek:

```text
on_koltuk
arka_koltuk_1
arka_koltuk_2
```

Bu aşama phone/smoking/nesne specialist sonrası açılmalıdır. Dış kameradan koltuk konumu zor
olduğu için ilk yaklaşım weakly-supervised/manual review destekli olmalıdır.

## İlk Teknik Adım

İlk yapılacak iş `CABIN-EXP-020A` Colab notebook'u olmalıdır.

Notebook işlevleri:

1. Kaggle/Drive üzerinden State Farm dataset kontrolü.
2. Negatif sınıf için BDD100K veya manuel `not_cabin_view` klasörü kontrolü.
3. Train/val/test split'i sürücü/session leakage olmayacak şekilde kurma.
4. MobileNetV3-Large ve EfficientNet-B0 kıyaslama.
5. `driver_cabin_visible` / `not_cabin_view` confusion matrix ve per-class F1 üretme.
6. Checkpoint export.
7. Lokal 3 video için smoke inference artifact üretme.

## State Farm Veri Erişim Notu

State Farm veri seti Kaggle competition endpoint'i üzerinden geldiği için yalnız API key'in
tanımlı olması yeterli değildir. Aynı Kaggle hesabında competition/data terms kabul edilmiş
olmalıdır.

Kontrol:

```text
https://www.kaggle.com/competitions/state-farm-distracted-driver-detection/data
```

Notebook `KAGGLE_USERNAME` / `KAGGLE_KEY` ve küçük harfli `kaggle_username` / `kaggle_key`
Colab Secret adlarını destekler. Buna rağmen `kaggle competitions download` exit code `1`
dönerse kullanıcı:

1. Aynı hesapla Kaggle data sayfasında Join/Accept Rules adımını tamamlamalı.
2. Kaggle API token'ını yenilemeli.
3. Colab Secrets değerlerini güncellemeli.
4. Hâlâ engel varsa `imgs.zip` veya extracted `imgs/train/c0..c9` yapısını Drive altında
   `datasets/cabin_exp_020a/state_farm/` klasörüne manuel koymalıdır.

## Kabul Kriteri

`CABIN-EXP-020A` baseline kabulü için:

* Validation/test per-class metrikleri raporlanmalı.
* `driver_cabin_visible` false positive ve false negative davranışı ayrı izlenmeli.
* Model sadece accuracy ile değil confusion matrix ile değerlendirilmeli.
* FTR etkisi açıkça yazılmalı: `not_cabin_view` ise `sofor_eylemi` yazılmamalı.
* Lokal 3 videoda kesin iddia kurulmadan smoke inference yapılmalı.
* Domain farkı açıkça yazılmalı: public driver datasets genelde araç içi kameradır, bizim demo
  dış kamera/yan cam görüşüdür.

## Neyi Yapmayacağız?

* Heuristik `CABIN-EXP-012` üstünden devam etmeyeceğiz.
* Seatbelt'i görünmüyor diye `emniyet_kemeri_ihlali` saymayacağız.
* Phone/smoking/object için tek kare detection'ı doğrudan FTR event yapmayacağız.
* Pozitif-only küçük seti benchmark olarak raporlamayacağız.

## Sıradaki Dosya

Bir sonraki implementation işi:

```text
notebooks/CABIN_EXP_020A_Cabin_Driver_View_Baseline_Colab.ipynb
```

Bu notebook, önceki BDD100K/condition/VATTR notebooklarında yaşanan Drive/cache/path sorunlarını
dikkate alarak local Colab çalışma alanı + Drive output cache yapısıyla tasarlanmalıdır.
