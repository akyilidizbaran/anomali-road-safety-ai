# Condition Experts Action Roadmap

## Karar Özeti

Bu proje için uygulanacak strateji:

**Önce genel road-domain vehicle detector, sonra yalnızca benchmark ile faydası kanıtlanan koşul uzmanları.**

Bu karar, condition expert fikrini iptal etmez. Tam tersine, condition expert'leri ölçülebilir ve savunulabilir hale getirir.

2026-06-15 güncellemesi: `VD-EXP-002` Colab koşusu tamamlandı. General fine-tuned YOLO11n aktif baseline olarak seçildi. Night/rain specialist deneyleri candidate olarak tutulacak; mAP50-95 tarafında general modelden iyi olmadıkları için runtime routing'e aktif alınmayacak. Sıradaki zorunlu adım, canlı frame'den `condition_profile` üreten ayrı classifier/router kurmaktır.

## Faz 0 - Mevcut Dark Smoke Test Review

Amaç: YOLO11n zero-fine-tune çıktılarının gerçek hata tiplerini görmek.

Girdiler:

* `Test/video_1.mp4`
* `Test/video_2.mp4`
* `Test/video_3.mp4`
* `runs/detect/runs/detect/VD-EXP-001-yolo11n-dark/`

Yapılacaklar:

* [x] Qualitative review ile genel araç yakalamanın kullanılabilir olduğu doğrulandı.
* [ ] Her video için missed detection, false positive, wrong class ve bbox adequacy sayısal notlarını doldur.
* [ ] `testing/templates/manual_video_benchmark_review.csv` formatını kullan.
* [ ] Özellikle low-light kaynaklı hata örüntülerini çıkar.
* [ ] Bu üç videoyu training data olarak kullanma.

Çıkış:

* Dark smoke test manual review sonucu.
* Night specialist için hangi hata tiplerinin hedefleneceği.

## Faz 1 - Kaynak ve Lisans Doğrulama

Amaç: Veri setlerini indirmeden önce hukuki/teknik uygunluğu netleştirmek.

Yapılacaklar:

* [x] BDD100K download ve kaynak şartlarını ilk seviye kaydet.
* [ ] UA-DETRAC resmi download/license durumunu doğrula.
* [x] ACDC non-commercial şartını kaynakça seviyesinde kaydet.
* [x] ExDark ticari kullanım notunu kaynakça seviyesinde kaydet.
* [ ] NOD/SHIFT veri erişimini ve lisansını doğrula.
* [x] DAWN veri erişim kaynaklarını kaynakça seviyesinde kaydet.
* [ ] Her dataset için dataset card oluştur.

Çıkış:

* `dataset_source_checklist.md` tamamlanmış olur.
* Hangi veri setleri training, validation veya sadece research benchmark için kullanılacak netleşir.

## Faz 2 - General Road-Domain Detector

Amaç: Condition expert'lerin dallanacağı güçlü bir temel checkpoint üretmek.

Bu faz doğrudan araç detection fine-tune fazıdır. Condition profile modeli veya specialist detector bu faz için blocker değildir.

`general` burada "yalnız gündüz/normal model" anlamına gelmez. General detector, night/rain/fog örneklerini condition metadata ile gören ve tüm koşullarda çalışması beklenen ana detektördür.

Model adayları:

1. `YOLO11n`
2. `YOLOv10n`
3. `YOLO11s`

Veri:

* BDD100K road object subset
* UA-DETRAC fixed-camera subset
* Condition metadata korunmuş night/rain/fog/day splitleri

Sınıflar:

* `car`
* `bus`
* `truck`
* `motorcycle`

Yapılacaklar:

* [x] BDD100K -> 4-class vehicle mapping oluştur.
* [x] Train/val/test split ve condition dağılımını üret.
* [x] YOLO formatına dönüşüm notebook hattını çalıştır.
* [x] Colab notebook ile `general_yolo11n` fine-tune koş.
* [ ] Aynı split ile `general_yolov10n` ve `general_yolo11s` benchmark al.
* [x] Overall metriklerle birlikte `night_low_light`, `rain`, `fog_low_visibility` kırılımlarını raporla.
* [ ] MacBook runtime benchmark ile p50/p95 latency ve FPS ölç.

Çıkış:

* `best_general`: `VD-EXP-002-GENERAL-YOLO11N/weights/best.pt`.
* General model card ve summary: `testing/reports/vd_exp_002_finetuned_general_detector_summary.md`.
* Dark video smoke test pending: `testing/reports/vd_exp_002_dark_video_smoke_test_runbook.md`.

## Faz 3 - İlk Specialist: Night / Low-Light

Amaç: Mevcut test materyaline en yakın koşulda specialist modelin gerçekten fayda sağlayıp sağlamadığını ölçmek.

Başlangıç checkpoint:

* `best_general`

Veri:

* BDD100K night subset
* ACDC nighttime
* UA-DETRAC night veya low-light subset varsa
* ExDark/NOD yardımcı veri, sınıf mapping uygunluğu doğrulanırsa

Yapılacaklar:

* [x] `night_low_light` train/val/test split oluştur.
* [x] `night_yolo11n_from_general` deneyini koş.
* [ ] Gerekirse `night_yolo11s_from_general` deneyini koş.
* [x] General model ile aynı night validation/test set üzerinde karşılaştır.
* [ ] Mevcut 3 dark video üzerinde smoke test yap.

Promotion eşiği:

* `mAP@0.5:0.95` en az +2.0 puan veya `AP@0.5` en az +3 puan.
* Ya da missed detection/recall tarafında anlamlı iyileşme.
* FP/min artışı kabul edilebilir sınırda kalmalı.
* MacBook p95 latency bütçeyi aşmamalı.

Çıkış:

* `vehicle_detector_night_low_light_v1` candidate olarak tutulur; aktif runtime model değildir.
* Gerekçe: recall küçük artış gösterdi, ancak mAP50-95 general modelden düşük kaldı.

## Faz 4 - Rain ve Fog Specialist

Amaç: Night specialist fayda sağlarsa aynı yaklaşımı diğer güçlü condition'lara genişletmek.

Rain veri:

* BDD100K rainy
* ACDC rain
* DAWN rain
* UA-DETRAC rainy varsa

Fog veri:

* ACDC fog
* Foggy Cityscapes / Foggy Driving
* DAWN fog
* WEDGE fog yalnız research-only destek

Yapılacaklar:

* [x] `rain_yolo11n_from_general` deneyini koş.
* [x] Fog için veri yetersizliğini kaydet; eğitim koşma.
* [x] Rain specialist'i general modelle aynı condition test setinde karşılaştır.
* [ ] Fog için sentetik data kullanımını ayrı ablation olarak tut.

Çıkış:

* `vehicle_detector_rain_v1` candidate olarak tutulur; aktif runtime model değildir.
* `vehicle_detector_fog_low_visibility_v1` skipped; veri artırımı olmadan eğitilmemeli.

## Faz 4.5 - Live Condition Profile Classifier

Amaç: BDD metadata'sına bağımlı kalmadan canlı frame'den kondisyon profili üretmek.

Model adayları:

1. `MobileNetV3-Small`
2. `MobileNetV3-Large`
3. `ResNet18`

Yapılacaklar:

* [ ] BDD100K metadata'dan classification CSV üret.
* [ ] `day_clear`, `night_low_light`, `low_light_transition`, `rain`, `adverse_other`, `unknown` ilk label setini oluştur.
* [ ] Fog'u veri yeterliyse ayrı sınıf, değilse `adverse_other/unknown` altında tut.
* [ ] MobileNetV3 baseline eğit.
* [ ] ResNet18 challenger eğit.
* [ ] Macro-F1, per-class recall, confusion matrix ve p95 latency raporla.
* [ ] 3 dark video üzerinde frame sampling smoke test yap.

Çıkış:

* `condition_profile_classifier_v1`
* `condition_profile`, `condition_confidence`, `profile_window_stability`, `routing_reason` alanları.
* Detay plan: `condition_profile_classifier_router_plan.md`.

## Faz 5 - Runtime Routing ve Registry

Amaç: Model seçimini "hangi model var?" mantığından "hangi model kanıtlı ve aktif?" mantığına taşımak.

Yapılacaklar:

* [ ] `vehicle_detector_registry.yaml` oluştur.
* [ ] `condition_profiles.yaml` oluştur.
* [ ] `condition_routing.yaml` oluştur.
* [ ] Condition confidence threshold ekle.
* [ ] Temporal smoothing/hysteresis ekle.
* [ ] Health check ve fallback kuralı ekle.
* [ ] Kritik modda dual-run seçeneği ekle.

Runtime kuralı:

```text
if condition_confidence < threshold:
    use general
elif specialist.proven_better != true:
    use general
elif specialist.health != ok:
    use general
elif latency_budget_exceeded:
    use general
else:
    use specialist
```

Çıkış:

* Açıklanabilir detector seçimi.
* Event/evidence içinde `detector_selected`, `routing_reason`, `fallback_used` alanları.

## Faz 6 - Demo ve Rapor Entegrasyonu

Amaç: Sistemi TEKNOFEST raporunda savunulabilir hale getirmek.

Yapılacaklar:

* [ ] PDR/ÖTR için model geliştirme yaklaşımını Strateji 1 olarak yaz.
* [ ] PCR/FTR için benchmark metriklerini condition breakdown ile ver.
* [ ] Mobil dashboard/evidence ekranında kullanılan detector ve routing reason göster.
* [ ] QoD'nin yalnız riskli/uncertain durumda active olduğunu belirt.
* [ ] Video/evidence görsellerinde kişisel veri riskini yönet.

## Hemen Sonraki Net Adımlar

1. Drive'daki `best.pt` checkpoint'i lokal `models/checkpoints/vehicle_detection/` altına al.
2. `run_vehicle_detection_video_smoke.py` ile 3 dark video üzerinde fine-tuned general detector smoke test'i koş.
3. Manual review sonuçlarını doldur.
4. `COND-EXP-001` condition profile classifier notebook'unu oluştur.
5. Classifier/router sonuçlarını event/evidence contractına bağla.

## Güncel Colab Başlangıcı

İlk Colab hattı hazırlandı:

* `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`

Bu notebook BDD100K metadata'sını koruyarak `vehicle_detector_general` fine-tune eder ve condition breakdown metriklerini üretir. Güncel koşuda night/rain specialist deneyleri de çalıştırılmıştır; ancak specialist modeller aktif runtime modeline terfi ettirilmemiştir.

Notebook artık tek dosyada şunları yürütür:

* BDD100K download/Drive placement,
* BDD100K -> YOLO dönüşümü,
* pretrained baseline validation,
* fine-tune training,
* optional challenger runs,
* baseline-delta comparison,
* condition breakdown validation.
