# Driver / Cabin / Phone Çalışmaları - Ana Handoff Dosyası

Tarih: 2026-06-23
Proje kökü: `/Users/elifgungen/Downloads/5G Teknofest`

Bu dosya, şimdiye kadar Codex ile üstüne ekleyerek yürütülen sürücü/kabin/telefon
çalışmalarını tek yerde toplar. Amaç ekip arkadaşlarıyla çalışmaları birleştirirken
neyin hazır, neyin provisional, neyin sadece araştırma/deney çıktısı olduğunu açık
tutmaktır.

## 1. Kısa Sonuç

Telefon konusu dahil olmak üzere şu anki teknik durum:

| Alan | Durum | Ana karar |
|---|---|---|
| Cabin visibility / face | Kullanılabilir baseline seçildi | OpenCV YuNet + visibility gate |
| Driver torso / skeleton | Kullanılabilir baseline seçildi | ViTPose-B torso/shoulder freeze |
| Driver arm state | Risk kararı kapalı, metadata/reference | Kol pozisyonundan doğrudan risk üretmiyoruz |
| Seatbelt | Deferred / unknown | Mevcut model baseline değil |
| Phone object | Specialist smoke model eğitildi, final baseline değil | Görünür telefon için destekleyici kanıt |
| Phone-call behavior | Demo/entegrasyon için provisional baseline | `phone_risk=null`, final risk baseline değil |

En kritik telefon kuralı:

`phone_object_detected=false`, “telefonla konuşmuyor” anlamına gelmez.

Telefon net görünmediğinde sistem, el-kulak geometrisi, pose sürekliliği ve temporal
hysteresis üzerinden `phone_call_status` üretebilir. Ancak final kabul seti
tamamlanmadığı için bu sinyal şimdilik risk skorunu yükseltmez.

## 2. Sabitlenen / Dondurulan Kararlar

### 2.1 Cabin visibility ve face baseline

Seçilen baseline:

* `CABIN-EXP-004 = OpenCV YuNet 2026may`
* Checkpoint: `models/checkpoints/cabin/face_detection_yunet_2026may.onnx`
* Karar dokümanı: `research/08_cabin_risk/decision_cabin_baseline_v1.md`

Kabul edilen kullanım:

* driver face anchor,
* occupant metadata,
* cabin ROI/visibility kalite gate'i,
* `good/limited/poor/not_visible` kalite ayrımı.

Kabul edilmeyen kullanım:

* `poor/not_visible` karelerden doğrudan ihlal/risk üretmek,
* ikinci occupant var diye risk artırmak.

### 2.2 Driver pose / torso baseline

Seçilen baseline:

* `POSE-EXP-009 = vitpose_b_final_torso_baseline_v1`
* Karar dokümanı: `research/08_cabin_risk/upper_body_pose/decision_driver_skeleton_freeze_v1.md`

Kabul edilen kullanım:

* omuz/torso sürekliliği,
* specialist ROI üretimi,
* face-anchored sürücü bölgesi,
* telefon/sigara gibi küçük nesneler için yardımcı context.

Kabul edilmeyen kullanım:

* bilek/dirsek keypointlerinden tek başına telefon/sigara kararı,
* “kol direksiyonda / havada / off-wheel” gibi final davranış sınıfları,
* düşük görünürlükten risk artırmak.

### 2.3 Driver arm state

`ARM-EXP-001` ve VLM denemeleri referans olarak tutuldu. Final sürüş riski
üretmiyorlar.

Sebep: kol/dirsek/bilek evidence'i bazı videolarda faydalı ama üç video ve zor
görüş koşullarında action-grade stabil değil.

## 3. Telefon Konusu: Ne Elde Ettik?

### 3.1 Hazır modellerden çıkan sonuç

Hazır modeller doğrudan baseline olmadı.

Denenen ana hazır/domain modeller:

* COCO `cell phone` detector: mevcut windshield kamera açısında çok düşük recall.
* StateFarm distraction YOLO26s classifier: domain transfer başarısız.
* AI City 2024 X3D action modelleri: mevcut kamera açısı için ayrıştırıcı değil.

Sonuç: “hazır modeli indirip koyduk, baseline oldu” seviyesinde güvenilir bir model
bulunamadı.

### 3.2 Kendi phone object modelimiz

YOLO26s phone specialist smoke eğitimi yapıldı:

* `PHONE-EXP-003 = yolo26s_p2_phone_windshield_seed_smoke`
* `PHONE-EXP-004 = yolo26s_phone_windshield_seed_smoke`

Önemli çıktılar:

* P2 best weights:
  `runs/phone/training/phone_exp_003_yolo26s_p2_seed_smoke/weights/best.pt`
* Standard best weights:
  `runs/phone/training/phone_exp_004_yolo26s_seed_smoke/weights/best.pt`
* Training result:
  `runs/phone/training/phone_specialist_training_results.json`
* Dataset:
  `runs/phone/specialist_datasets/phone_windshield_seed_v1/`

Bu eğitim çalışıyor ve pipeline’ı doğruluyor; ancak dataset küçük ve aynı domain
üzerinden smoke olduğu için final baseline kanıtı değildir.

### 3.3 Phone-call behavior provisional baseline

Dondurulan demo/entegrasyon stack'i:

`PHONE-CALL-PROVISIONAL-BASELINE = PHONE-CALL-EXP-002 + PHONE-CALL-EXP-007`

Bileşenler:

* `PHONE-CALL-EXP-002`: YOLO26s phone object + ViTPose/LK arm evidence + ear-zone
  temporal fusion.
* `PHONE-CALL-EXP-007`: pose reliability guardrail.
* `PHONE-EXP-004`: görünür telefon için destekleyici object kanıtı.

Şu davranış statüleri üretilebilir:

* `handheld_call_likely`
* `candidate`
* `not_detected`
* `not_evaluable`

Güncel event sonucu:

| Video | Status | Pose reliability | Risk |
|---|---|---|---|
| `video_1.mp4` | `candidate` | `usable_borderline` | `phone_risk=null` |
| `video_2.mp4` | `handheld_call_likely` | `decision_usable` | `phone_risk=null` |
| `video_3.mp4` | `candidate` | `usable_borderline` | `phone_risk=null` |

Bu şu anlama geliyor:

* Manuel olarak pozitif gördüğümüz `video_2` yakalanıyor.
* Telefon görünmeyen/belirsiz durumlarda sistem tamamen “yok” demiyor, `candidate`
  bırakabiliyor.
* Ama final risk baseline değil; çünkü negatif/hard-negative veri yok.

Final baseline'a geçmek için gereken minimum kapı:

* en az 3 pozitif session,
* en az 5 negatif session,
* en az 2 hard-negative session,
* en az 1 occluded-positive session,
* event recall `>=0.80`,
* specificity `>=0.90`,
* hard-negative specificity `>=0.90`.

Şu an kabul durumu:

* `baseline_accepted=false`
* `recall=0.5`
* `specificity=null`
* `hard_negative_specificity=null`

## 4. Üretilen Ana Dosya / Artifact Haritası

### 4.1 Karar ve araştırma dokümanları

Gönderilmesi gereken ana doküman klasörü:

* `research/08_cabin_risk/`

Özellikle önemli dosyalar:

* `research/08_cabin_risk/CABIN_DRIVER_FINETUNE_HANDOFF.md`
* `research/08_cabin_risk/decision_cabin_baseline_v1.md`
* `research/08_cabin_risk/phone/decision_phone_call_baseline_v2.md`
* `research/08_cabin_risk/phone/phone_call_provisional_baseline.md`
* `research/08_cabin_risk/phone/generalization_strategy.md`
* `research/08_cabin_risk/phone/phone_call_data_collection_plan.md`
* `research/08_cabin_risk/upper_body_pose/decision_driver_skeleton_freeze_v1.md`
* `research/08_cabin_risk/arm_state/decision_arm_state_baseline_v1.md`
* `research/08_cabin_risk/seatbelt/decision_seatbelt_baseline_v1.md`

### 4.2 Scriptler

Gönderilmesi gereken script klasörü:

* `scripts/benchmarks/`

Telefon için kritik scriptler:

* `scripts/benchmarks/run_phone_baseline.py`
* `scripts/benchmarks/run_phone_call_behavior_fusion.py`
* `scripts/benchmarks/evaluate_phone_call_behavior.py`
* `scripts/benchmarks/enrich_event_skeleton_with_phone.py`
* `scripts/benchmarks/summarize_phone_call_events.py`
* `scripts/benchmarks/prepare_phone_finetune_samples.py`
* `scripts/benchmarks/prepare_phone_specialist_yolo_dataset.py`
* `scripts/benchmarks/train_phone_specialist_challengers.py`
* `scripts/benchmarks/prepare_phone_call_segment_review.py`
* `scripts/benchmarks/train_phone_call_temporal_head.py`
* `scripts/benchmarks/analyze_phone_call_pose_reliability.py`

Cabin/driver için kritik scriptler:

* `scripts/benchmarks/run_cabin_visibility_baseline.py`
* `scripts/benchmarks/enrich_event_skeleton_with_cabin.py`
* `scripts/benchmarks/run_driver_pose_baseline.py`
* `scripts/benchmarks/run_driver_torso_baseline.py`
* `scripts/benchmarks/run_driver_arm_state_baseline.py`

### 4.3 Test ve raporlar

Gönderilmesi gereken test/rapor klasörü:

* `testing/`

Özellikle:

* `testing/templates/`
* `testing/reports/`
* `testing/reports/phone_call_baseline_v2/`
* `testing/test_phone_event_enrichment.py`
* `testing/test_evaluate_phone_call_behavior.py`
* `testing/test_train_phone_call_temporal_head.py`
* `testing/test_prepare_phone_call_segment_review.py`

### 4.4 Benchmark tabloları

Gönderilmesi gereken benchmark klasörleri:

* `models/benchmarks/cabin/`
* `models/benchmarks/artifacts/`

Özellikle:

* `models/benchmarks/cabin/cabin_baseline_comparison.csv`
* `models/benchmarks/cabin/driver_pose_baseline_comparison.csv`
* `models/benchmarks/cabin/driver_torso_baseline_comparison.csv`
* `models/benchmarks/cabin/driver_arm_state_comparison.csv`
* `models/benchmarks/cabin/phone_baseline_comparison.csv`
* `models/benchmarks/cabin/phone_call_behavior_comparison.csv`
* `models/benchmarks/artifacts/phone_call_baseline_v2/`
* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-phone-call.json`

### 4.5 Contract / entegrasyon dosyaları

Gönderilmesi gereken contract klasörü:

* `architecture/contracts/`

Özellikle:

* `architecture/contracts/model_output_contract.md`
* `architecture/contracts/event.schema.json`
* `architecture/contracts/mobile_overlay_response.schema.json`

## 5. AirDrop İçin Net Paket Önerisi

### Paket A - Küçük paket: kod + karar + artifact

Ekip sadece ne yaptığımızı okuyacak, kodu inceleyecek ve kendi ana dosyasına
merge edecekse bu yeterli.

Gönder:

* `research/08_cabin_risk/`
* `scripts/benchmarks/`
* `testing/`
* `models/benchmarks/cabin/`
* `models/benchmarks/artifacts/`
* `architecture/contracts/`

Yaklaşık boyut:

* `research/08_cabin_risk`: 244 KB
* `scripts/benchmarks`: 1.5 MB
* `testing`: 744 KB
* `models/benchmarks`: 51 MB
* `architecture/contracts`: 76 KB

Bu paket küçük ve ana çalışma dosyası oluşturmak için en mantıklı ilk pakettir.

### Paket B - Demo-runnable paket

Ekip videolu overlayleri, review segmentlerini ve local çıktıların çoğunu da görmek
istiyorsa Paket A'ya ek olarak bunları gönder:

* `Test/`
* `runs/phone_call_baseline_v2/`
* `runs/phone_call_review/segment_review_v1/`
* `runs/phone/training/`
* `runs/phone/specialist_datasets/`
* `models/checkpoints/cabin/`

Yaklaşık ek boyut:

* `Test`: 44 MB
* `runs/phone_call_baseline_v2`: 457 MB
* `runs/phone_call_review`: 37 MB
* `runs/phone`: 207 MB
* `models/checkpoints/cabin`: 1.1 GB

Bu paket local yeniden çalışma ve demo için daha uygundur.

### Paket C - Full görsel kanıt paketi

Ekip tüm driver/cabin/pose/arm overlaylerini de beraber kontrol edecekse Paket B'ye
ek olarak bunları gönder:

* `runs/cabin/`
* `runs/cabin_pose/`
* `runs/driver_torso/`
* `runs/driver_arm_state/`

Yaklaşık ek boyut:

* `runs/cabin`: 295 MB
* `runs/cabin_pose`: 317 MB
* `runs/driver_torso`: 24 MB
* `runs/driver_arm_state`: 39 MB

Bu paket en büyük pakettir; yalnız görsel review gerekecekse gönderilmeli.

## 6. AirDrop İçin Pratik Komutlar

Küçük paket için:

```bash
zip -r 5g_teknofest_cabin_phone_handoff_small.zip \
  research/08_cabin_risk \
  scripts/benchmarks \
  testing \
  models/benchmarks/cabin \
  models/benchmarks/artifacts \
  architecture/contracts
```

Demo-runnable paket için:

```bash
zip -r 5g_teknofest_cabin_phone_handoff_demo.zip \
  research/08_cabin_risk \
  scripts/benchmarks \
  testing \
  models/benchmarks/cabin \
  models/benchmarks/artifacts \
  architecture/contracts \
  Test \
  runs/phone_call_baseline_v2 \
  runs/phone_call_review/segment_review_v1 \
  runs/phone/training \
  runs/phone/specialist_datasets \
  models/checkpoints/cabin
```

Full görsel kanıt paketi için:

```bash
zip -r 5g_teknofest_cabin_phone_handoff_full.zip \
  research/08_cabin_risk \
  scripts/benchmarks \
  testing \
  models/benchmarks/cabin \
  models/benchmarks/artifacts \
  architecture/contracts \
  Test \
  runs/phone_call_baseline_v2 \
  runs/phone_call_review/segment_review_v1 \
  runs/phone/training \
  runs/phone/specialist_datasets \
  models/checkpoints/cabin \
  runs/cabin \
  runs/cabin_pose \
  runs/driver_torso \
  runs/driver_arm_state
```

## 7. Ekip Arkadaşına Söylenecek Teknik Özet

Kısa mesaj olarak şu yazılabilir:

> Cabin/driver tarafında YuNet face + ViTPose-B torso baseline donduruldu.
> Telefon tarafında hazır modeller yeterli olmadı; YOLO26s phone specialist smoke
> eğitildi ama final baseline değil. Phone-call için object + pose/LK + ear-zone
> temporal fusion provisional demo baseline olarak bağlandı. `video_2` telefonla
> konuşmayı yakalıyor; görünmeyen telefonlarda `candidate` bırakıyor. Negatif ve
> hard-negative session olmadığı için `phone_risk` hâlâ `null`, final risk baseline
> değil.

## 8. Sıradaki Net İş

Telefonu gerçek baseline yapmak için yapılacak iş model aramaktan çok veri kapısını
kapatmaktır:

1. En az 3 pozitif session.
2. En az 5 negatif session.
3. En az 2 hard-negative session:
   * el yanakta,
   * yüz kaşıma,
   * saç/gözlük düzeltme,
   * yolcu telefonu,
   * sigara/benzer küçük obje,
   * cam/trim yansıması.
4. En az 1 görünmeyen veya kısmi görünür telefon pozitif session.
5. `runs/phone_call_review/segment_review_v1/manual_phone_call_segments_review.csv`
   formatıyla segment label'larının doldurulması.
6. Aynı harness ile `train_phone_call_temporal_head.py` ve
   `evaluate_phone_call_behavior.py` tekrar koşturulması.

Şu anda sistem mimarisi doğru yöne bağlandı; eksik olan kabul edilebilir
session-disjoint veri ve hard-negative coverage.
