# Condition Profile Classifier and Router Plan

## Karar Özeti

Evet, canlı frame'den kondisyon tahmini yapan ayrı bir `condition_profile` classifier/router çıkarmalıyız.

Sebep: VD-EXP-002 ile elde edilen condition bilgisi BDD100K metadata'sından türetildi; yani model canlı kamerada kendi başına "bu frame gece/düşük ışık/rain/fog" kararı vermiyor. Rapor ve demo tarafında condition-aware AI iddiasının savunulabilir olması için canlı frame üzerinde çalışan hafif bir kondisyon sınıflandırıcısı gerekir.

Bu modül, araç tespiti yerine geçmez. Görevi, detector ve evidence hattına bağlam sinyali vermektir.

## Mevcut Durum

| Bileşen | Durum | Not |
|---|---|---|
| BDD100K metadata tabanlı condition split | Var | VD-EXP-002 train/val/test ve specialist deneyleri için kullanıldı. |
| General fine-tuned YOLO11n detector | Var | Drive'da `VD-EXP-002-GENERAL-YOLO11N/weights/best.pt` olarak duruyor. |
| Night/rain specialist detector deneyleri | Var | Recall tarafında küçük artış var; mAP50-95 genel modelden iyi değil. |
| Canlı frame condition classifier | Yok | Bu dosyanın önerdiği sıradaki model kapsamı. |
| Runtime router config | Tasarım var | `condition_confidence`, temporal smoothing ve fallback kuralı gerçek config'e dönüştürülmeli. |

## Bu Modül Ne Üretmeli?

`ConditionProfileOutput` için önerilen contract:

```json
{
  "frame_id": 1842,
  "timestamp_utc": "2026-06-15T12:30:45.120Z",
  "condition_profile": "night_low_light",
  "condition_confidence": 0.82,
  "top_k": [
    {"label": "night_low_light", "score": 0.82},
    {"label": "low_light_transition", "score": 0.11},
    {"label": "day_clear", "score": 0.04}
  ],
  "profile_window_stability": 0.76,
  "routing_allowed": true,
  "fallback_used": false,
  "selected_detector_profile": "general",
  "routing_reason": "night specialist not promoted; general detector remains active"
}
```

Önemli nokta: `condition_profile=night_low_light` dönse bile specialist detector otomatik seçilmemeli. Specialist yalnız aynı condition benchmark'ında general modele göre kanıtlı daha iyiyse aktiflenir.

## Önerilen İlk Model

İlk MVP classifier:

* **MobileNetV3-Small veya MobileNetV3-Large**
* Girdi: canlı frame'den resize edilmiş RGB görüntü
* Çıkış: condition profile sınıfı + confidence
* Çalışma sıklığı: her frame değil, 1-2 Hz
* Runtime: MacBook CPU/MPS üzerinde düşük latency hedefi

Neden MobileNetV3?

* Mobil/edge cihazlar için tasarlanmış hafif CNN ailesidir.
* Bu projede condition classifier yalnız routing sinyali üretir; çok ağır ViT/CLIP tabanlı model ilk MVP için gereksiz latency üretebilir.
* Sınıf sayısı az olduğu için MobileNetV3 veya ResNet18 yeterli bir ilk baseline verir.

Challenger:

* **ResNet18**: Daha klasik, raporda açıklaması kolay, küçük veriyle sağlam bir baseline.
* **CLIP zero-shot**: Sadece ön smoke test / pseudo-label kontrolü için düşünülebilir; final router olarak kullanılmamalı.

## Condition Label Taksonomisi

İlk geniş taksonomi:

| Label | Anlam | İlk Faz Durumu |
|---|---|---|
| `day_clear` | Gündüz, açık/normal görüş | Aktif |
| `night_low_light` | Gece/düşük ışık | Aktif |
| `low_light_transition` | Alacakaranlık, geçiş ışığı | Aktif |
| `rain` | Yağmur/ıslak görüş koşulu | Aktif |
| `fog_low_visibility` | Sis/düşük görüş | Aday |
| `adverse_other` | Kar, fırtına, kum, ağır kötü hava | Aday |
| `tunnel_or_parking_dark` | Yol dışı özel karanlık ortam | Sinyal olarak izle |
| `unknown` | Güven düşük veya profil belirsiz | Fallback |

İlk eğitimde aşırı parçalamadan kaçınmak gerekir. Fog verisi VD-EXP-002 vehicle subset'inde çok az çıktığı için `fog_low_visibility` ayrı sınıf olarak eğitilecekse BDD100K dışı veriyle desteklenmelidir. Aksi durumda `adverse_other` veya `unknown` altında tutulmalıdır.

## Router Kuralı

Runtime kuralı:

```text
condition = condition_classifier(frame_sample)
stable_condition = temporal_smoother(condition, last_window)

if condition_confidence < threshold:
    selected_detector = general
    fallback_used = true
elif specialist[stable_condition].proven_better != true:
    selected_detector = general
    fallback_used = true
elif specialist[stable_condition].health != ok:
    selected_detector = general
    fallback_used = true
elif latency_budget_exceeded:
    selected_detector = general
    fallback_used = true
else:
    selected_detector = specialist[stable_condition]
```

Başlangıç threshold önerisi:

* `condition_confidence_threshold = 0.65`
* `profile_window_size = 5-15 sample`
* `routing_change_hysteresis = 2-3 stable sample`
* `unknown_or_low_confidence -> general`

## Temporal Smoothing

Canlı frame bazlı condition çıktısı tek frame'e göre değişmemeli. Önerilen yöntem:

1. Her 0.5-1 saniyede bir frame örnekle.
2. Son `N` örnekte softmax skorlarını ortala.
3. En yüksek sınıf confidence threshold'u geçerse stable condition kabul et.
4. Sınıf değişimi için en az 2-3 ardışık stable karar iste.
5. Hızlı profil değişimlerinde evidence içine `condition_unstable=true` yaz.

Bu sayede far/parlama, geçici kararma veya kamera otomatik pozlama değişimi router'ı zıplatmaz.

## Detection Pipeline ile Bağlantı

Condition classifier şu anda detector seçimi için gerekli ama yeterli değildir.

VD-EXP-002 sonucuna göre aktif detector:

* `vehicle_detector_general_yolo11n_bdd100k_v1`

Specialist modeller:

* `night_low_light`: candidate, active değil
* `rain`: candidate, active değil
* `fog_low_visibility`: veri yetersizliği nedeniyle skipped

Bu nedenle ilk canlı router şu davranışı göstermeli:

```text
classifier: night_low_light
router: general detector selected
reason: night specialist candidate did not outperform general on mAP50-95
```

Bu rapor açısından güçlüdür: sistem condition-aware olduğunu gösterir, ama zayıf specialist'i körlemesine aktifleyerek performans riski almaz.

## Eğitim ve Değerlendirme Planı

1. BDD100K image metadata'sından classification CSV üret:
   * image path
   * weather
   * timeofday
   * scene
   * condition_profile
2. Train/val/test split'i image/video leakage yaratmayacak şekilde kur.
3. MobileNetV3 baseline eğit.
4. ResNet18 challenger eğit.
5. Test metriklerini kaydet:
   * overall accuracy
   * macro-F1
   * per-class precision/recall/F1
   * confusion matrix
   * low-confidence rejection oranı
   * p50/p95 latency
6. 3 dark video üzerinde smoke test:
   * sampled frame sayısı
   * `night_low_light` oranı
   * unstable/unknown oranı
   * detector routing kararı

## Rapor Şablonuna Katkı

Bu modül FTR içinde şu sorulara doğrudan cevap verir:

* Ortam koşulu nasıl saptanıyor?
* Düşük ışık/yağmur/sis gibi durumlar sisteme nasıl yansıyor?
* Condition-aware model seçimi iddiası canlı sistemde nasıl gerçekleşiyor?
* Hatalı condition tahmininde güvenli fallback var mı?
* Specialist model neden her zaman çağrılmıyor?
* QoD/evidence kararına kondisyon nasıl sinyal veriyor?

Kullanılabilecek rapor cümlesi:

> Sistem, canlı video akışından düşük frekansta örneklenen kareler üzerinde hafif bir condition profile classifier çalıştırır. Bu sınıflandırıcı hava/ışık/görüş profilini ve güven skorunu üretir. Router, yalnız güven yüksekse ve ilgili specialist detector aynı condition benchmark'ında general detector'a göre kanıtlı avantaj sağlıyorsa specialist'i seçer; aksi durumda general detector güvenli fallback olarak korunur.

Kaçınılması gereken iddia:

* "Her koşulda doğru ortam tespiti yapar."
* "Gece/rain/fog specialist her zaman daha iyidir."
* "Condition router doğrudan risk kararı verir."

## İlk Uygulama Çıktıları

Önerilen yeni deney:

* Experiment ID: `COND-EXP-001`
* Notebook: `notebooks/COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab.ipynb`
* Dataset output: `datasets/bdd100k_condition_classifier/`
* Artifacts:
  * `models/benchmarks/artifacts/COND-EXP-001-condition-classifier-summary.json`
  * `testing/reports/cond_exp_001_condition_classifier_summary.md`
* Runtime config:
  * `models/registry/condition_profiles.yaml`
  * `models/registry/vehicle_detector_registry.yaml`
  * `models/registry/condition_routing.yaml`

## Kaynakça

* BDD100K dataset overview and split bilgisi: https://docs.voxel51.com/dataset_zoo/datasets/bdd100k.html
* BDD100K BAIR duyurusu, weather/time-of-day çeşitliliği: https://bair.berkeley.edu/blog/2018/05/30/bdd/
* BDD100K toolkit license: https://github.com/ucbdrive/bdd100k/blob/master/LICENSE
* MobileNetV3 paper: https://arxiv.org/abs/1905.02244
* timm MobileNetV3 dokümantasyonu: https://huggingface.co/docs/timm/en/models/mobilenet-v3
* ResNet paper: https://arxiv.org/abs/1512.03385
