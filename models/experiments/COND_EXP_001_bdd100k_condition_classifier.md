# COND-EXP-001 - BDD100K Condition Profile Classifier

## Experiment Metadata

* Experiment ID: `COND-EXP-001`
* Module: Condition Profile Classifier / Router
* Goal: Canlı frame'den hava/ışık/görüş profili üreten hafif classifier baseline kurmak.
* Training runtime: Google Colab GPU
* Inference/runtime target: MacBook local edge/backend; ileride mobil/edge için lightweight export
* Primary model: `MobileNetV3-Small`
* Optional challenger: `ResNet18`
* Starting weights: ImageNet-pretrained TorchVision weights
* Dataset: BDD100K image attributes (`weather`, `timeofday`, `scene`)
* Notebook: `notebooks/COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab.ipynb`

## Neden MobileNetV3-Small?

İlk condition classifier için MobileNetV3-Small varsayılan seçildi.

Gerekçeler:

* Condition classifier her frame'de ağır detection yapmaz; düşük frekansta sahne/koşul sinyali üretir.
* MobileNetV3 ailesi mobil/edge kullanım için daha hafiftir.
* `ResNet18`, raporlanabilir ve sağlam bir challenger olarak aynı notebook içinde opsiyonel tutulur.
* İlk hedef yüksek kapasiteli model değil, düşük latency ile güvenilir `condition_profile + confidence` üretmektir.

## Label Set

İlk label set:

| Label | Anlam |
|---|---|
| `day_clear` | Gündüz/normal görüş |
| `night_low_light` | Gece/düşük ışık |
| `low_light_transition` | Şafak/alacakaranlık |
| `rain` | Yağmur/ıslak görüş |
| `fog_low_visibility` | Sis/düşük görüş |
| `adverse_other` | Kar, fırtına, tünel/parking vb. |
| `unknown` | Belirsiz/eksik metadata |

BDD100K metadata öncelik sırası:

```text
fog_low_visibility > rain > night_low_light > low_light_transition > adverse_other > day_clear > unknown
```

## Notebook Tasarım Dersleri

Önceki VD-EXP-002 notebook'tan alınan dersler bu notebook'a uygulandı:

* Drive mount ilk hücrede yapılır.
* Büyük BDD100K arşivleri Drive'da kalır, local `/content/anomali-road-safety-ai-condition-work` altına kopyalanıp orada extract edilir.
* Drive içine 100.000 küçük image dosyası extract edilmeye zorlanmaz.
* `condition_metadata.csv` varsa ve kolonları sağlamsa yeniden üretilmez.
* Boş/bozuk metadata geçerli sayılmaz.
* `SMOKE_MODE` ve `MAX_IMAGES_PER_CLASS` ile küçük deneme yapılabilir.
* Model checkpointleri ve run çıktıları Drive `runs/condition_profile/COND-EXP-001/` altında tutulur.
* Ham veri, model ağırlığı ve görüntü çıktısı Git'e eklenmez.

## Output Contract

Runtime'da hedef çıktı:

```json
{
  "condition_profile": "night_low_light",
  "condition_confidence": 0.82,
  "top_k": [
    {"label": "night_low_light", "score": 0.82},
    {"label": "low_light_transition", "score": 0.11}
  ],
  "profile_window_stability": 0.76,
  "selected_detector_profile": "general",
  "fallback_used": true,
  "routing_reason": "night specialist is not promoted; general detector remains active"
}
```

## Metrics

Notebook şu metrikleri üretir:

* overall accuracy
* macro-F1
* weighted-F1
* per-class precision/recall/F1
* confusion matrix
* dark video condition smoke test summary
* router fallback decision

## Dataset Strategy

İlk koşu yalnız BDD100K ile yapılır.

ACDC, DAWN, ExDark ve IDD-AW şu aşamada ilk training merge'e alınmaz. Bu kaynaklar:

* `fog_low_visibility` sınıfı zayıfsa,
* `rain` sınıfı genelleme problemi gösterirse,
* düşük ışık smoke testinde classifier kararsız kalırsa

harici validation veya ikinci faz destek datası olarak açılır.

## Acceptance Criteria

* Notebook Colab'da Drive mount sonrası çalışır.
* BDD100K archive/metadata tekrar indirme zorlamadan kullanılır.
* `condition_metadata.csv` ve split CSV dosyaları üretilir.
* MobileNetV3-Small checkpoint ve summary JSON üretilir.
* Opsiyonel ResNet18 challenger aynı protokolle çalışabilir.
* 3 dark video Drive altında mevcutsa condition smoke test üretilir; yoksa temiz şekilde skip eder.
* Specialist detector router otomatik aktifleme yapmaz; `proven_better=false` ise general fallback kullanır.

## Output-Saved Run Review - 2026-06-15

`COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab_outputsaved.ipynb` çıktısı incelendi ve Drive artifactleri doğrulandı.

Doğrulanan checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/condition_profile/COND-EXP-001/train/COND-EXP-001-mobilenet_v3_small/best.pt
```

Ana test sonuçları:

| Metrik | Değer |
|---|---:|
| best epoch | 1 |
| best validation macro-F1 | 0.6578 |
| test accuracy | 0.7455 |
| test macro-F1 | 0.6582 |
| test weighted-F1 | 0.7444 |
| mean confidence | 0.7540 |

Sınıf bazlı önemli bulgular:

* `night_low_light` F1: `0.845`; düşük ışık/dark demo senaryosu için ilk baseline olarak anlamlı.
* `rain` F1: `0.770`; ilk baseline için kullanılabilir.
* `fog_low_visibility` F1: `0.200`, test support `10`; bu sınıf için FTR'de güçlü iddia kurulamaz.
* Dark video smoke test Drive `Test/` klasörü bulunmadığı için boş çıktı.

Notebook düzeltmeleri:

* Metadata duplicate riskine karşı dedup guard eklendi.
* Colab multiprocessing cleanup uyarılarını azaltmak için default `NUM_WORKERS=0` yapıldı.
* Dark video smoke test klasör adayları ve boş video durumu daha açık raporlanacak şekilde güncellendi.
* Ağır comparison run için `RUN_MOBILENETV3_SMALL=True` ve `RUN_RESNET18=True` default hale getirildi.
* Backbone seçimi `test_macro_f1` yerine `best_val_macro_f1` ile yapılacak şekilde düzeltildi; test metrikleri yalnız final raporlama için kullanılacak.

Karar: Bu koşu classifier'ın çalıştığını ve checkpoint ürettiğini kanıtlayan geçerli bir ilk baseline'dır; ancak final FTR kanıtı olarak kullanılmadan önce patch'li notebook tekrar koşulmalı ve 3 demo video üzerinde smoke test boş kalmamalıdır.

## Ağır Run Seçim Mantığı

Güncel notebook iki modeli aynı koşuda sırayla eğitir:

1. `mobilenet_v3_small`
2. `resnet18`

Her backbone için ayrı klasör ve checkpoint oluşur:

```text
runs/condition_profile/COND-EXP-001/train/COND-EXP-001-mobilenet_v3_small/best.pt
runs/condition_profile/COND-EXP-001/train/COND-EXP-001-resnet18/best.pt
```

Her model kendi içinde epoch bazında validation macro-F1'a göre en iyi checkpoint'i saklar. İki backbone arasındaki final seçim de `best_val_macro_f1` ile yapılır. `test_accuracy`, `test_macro_f1` ve `test_weighted_f1` değerleri karşılaştırma tablosuna yazılır; ancak model seçmek için kullanılmaz.

## İlişkili Notlar

Motorcycle/car karışıklığı bu deneyin hedefi değildir. Bu konu vehicle detector tarafında ayrı aksiyon dosyasında takip edilir:

* `testing/reports/vd_exp_002_motorcycle_class_confusion_action.md`

## Kaynaklar

* MobileNetV3 paper: https://arxiv.org/abs/1905.02244
* TorchVision MobileNetV3-Small weights dokümantasyonu: https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html
* ResNet paper: https://arxiv.org/abs/1512.03385
* TorchVision model loading/head replacement referansı: `/pytorch/vision` Context7, `torchvision.models.get_model(..., weights=..., num_classes=...)` ve model head replacement pattern.
