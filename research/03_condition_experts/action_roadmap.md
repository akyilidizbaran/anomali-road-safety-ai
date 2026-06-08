# Condition Experts Action Roadmap

## Karar Özeti

Bu proje için uygulanacak strateji:

**Önce genel road-domain vehicle detector, sonra yalnızca benchmark ile faydası kanıtlanan koşul uzmanları.**

Bu karar, condition expert fikrini iptal etmez. Tam tersine, condition expert'leri ölçülebilir ve savunulabilir hale getirir.

## Faz 0 - Mevcut Dark Smoke Test Review

Amaç: YOLO11n zero-fine-tune çıktılarının gerçek hata tiplerini görmek.

Girdiler:

* `Test/video_1.mp4`
* `Test/video_2.mp4`
* `Test/video_3.mp4`
* `runs/detect/runs/detect/VD-EXP-001-yolo11n-dark/`

Yapılacaklar:

* [ ] Her video için missed detection, false positive, wrong class ve bbox adequacy notlarını doldur.
* [ ] `testing/templates/manual_video_benchmark_review.csv` formatını kullan.
* [ ] Özellikle low-light kaynaklı hata örüntülerini çıkar.
* [ ] Bu üç videoyu training data olarak kullanma.

Çıkış:

* Dark smoke test manual review sonucu.
* Night specialist için hangi hata tiplerinin hedefleneceği.

## Faz 1 - Kaynak ve Lisans Doğrulama

Amaç: Veri setlerini indirmeden önce hukuki/teknik uygunluğu netleştirmek.

Yapılacaklar:

* [ ] BDD100K download ve license şartlarını kaydet.
* [ ] UA-DETRAC resmi download/license durumunu doğrula.
* [ ] ACDC non-commercial şartını kaydet.
* [ ] ExDark ticari kullanım notunu kaydet.
* [ ] NOD/DAWN/SHIFT veri erişimini ve lisansını doğrula.
* [ ] Her dataset için dataset card oluştur.

Çıkış:

* `dataset_source_checklist.md` tamamlanmış olur.
* Hangi veri setleri training, validation veya sadece research benchmark için kullanılacak netleşir.

## Faz 2 - General Road-Domain Detector

Amaç: Condition expert'lerin dallanacağı güçlü bir temel checkpoint üretmek.

Model adayları:

1. `YOLO11n`
2. `YOLOv10n`
3. `YOLO11s`

Veri:

* BDD100K road object subset
* UA-DETRAC fixed-camera subset

Sınıflar:

* `car`
* `bus`
* `truck`
* `motorcycle`

Yapılacaklar:

* [ ] COCO/BDD/UA-DETRAC sınıf mapping dosyası oluştur.
* [ ] Video-level train/val/test split yap.
* [ ] YOLO formatına dönüşüm scriptini hazırla.
* [ ] Colab notebook ile `general_yolo11n` fine-tune koş.
* [ ] Aynı split ile `general_yolov10n` ve `general_yolo11s` benchmark al.
* [ ] MacBook runtime benchmark ile p50/p95 latency ve FPS ölç.

Çıkış:

* `best_general` checkpoint kararı.
* General model card.
* Benchmark tablosu.

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

* [ ] `night_low_light` train/val/test split oluştur.
* [ ] `night_yolo11n_from_general` deneyini koş.
* [ ] Gerekirse `night_yolo11s_from_general` deneyini koş.
* [ ] General model ile aynı night validation set üzerinde karşılaştır.
* [ ] Mevcut 3 dark video üzerinde smoke test yap.

Promotion eşiği:

* `mAP@0.5:0.95` en az +2.0 puan veya `AP@0.5` en az +3 puan.
* Ya da missed detection/recall tarafında anlamlı iyileşme.
* FP/min artışı kabul edilebilir sınırda kalmalı.
* MacBook p95 latency bütçeyi aşmamalı.

Çıkış:

* `vehicle_detector_night_low_light_v1` enabled veya rejected kararı.

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

* [ ] `rain_yolo11n_from_general` deneyini koş.
* [ ] `fog_yolo11n_from_general` deneyini koş.
* [ ] Specialist'leri general modelle aynı condition validation setinde karşılaştır.
* [ ] Fog için sentetik data kullanımını ayrı ablation olarak tut.

Çıkış:

* `vehicle_detector_rain_v1` ve `vehicle_detector_fog_low_visibility_v1` için enable/reject kararı.

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

1. Manual review sonuçlarını doldur.
2. BDD100K ve UA-DETRAC kaynak/lisans kartlarını tamamla.
3. General detector Colab notebook skeleton'ını oluştur.
4. Dataset conversion planını yaz.
5. `best_general` olmadan specialist training'e geçme.
