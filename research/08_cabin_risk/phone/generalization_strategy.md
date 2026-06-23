# Phone-Call Genelleme Stratejisi (v1)

Tarih: 2026-06-20

## Amaç ve Kısıt

Hedef, herhangi bir araç / sürücü / aydınlık koşulunda çalışan bir sistemdir:
"generalization by construction". Buna bağlı en sert kısıt:

* **Teknofest `video_1/2/3` = HELD-OUT TEST.** Üzerinde eğitim YOK, threshold tuning
  YOK. Yalnız son smoke / kabul kontrolü için kullanılır.
* Bir modeli/eşiği bu üç videoya göre ayarlamak, raporlanan başarının genelleme
  değil ezber olduğu anlamına gelir. En büyük genelleme riski budur.

## Domain Zorluğu

Dış / ön-cam görünüm: sürücü az piksel kaplar, cam yansıması ve düşük aydınlık var.
İç-kabin public veri setleri (State Farm, AI City Track 3, DMD, 100-Driver) bu açıyı
temsil etmez. Bu yüzden appearance tabanlı transfer başarısız oldu (bkz.
`decision_phone_call_baseline_v2.md` EXP-003/004). Sonuç: genelleme appearance'tan
değil, **anatomi + göreli geometri**den gelmeli.

## Genelleyen Mimari (ne KULLANILACAK)

Katmanlar, genelleme gücüne göre sıralı:

1. **Person + pose** (ViTPose / YOLO-pose) — büyük ve çeşitli veride pretrained,
   anatomiyi genelleştirir. **Asıl darboğaz burada: bu zor görünümde keypoint
   güvenilirliği.** Yatırım önceliği: detection crop -> upscale -> pose, test-time
   augmentation, düşük-confidence -> `not_evaluable` kapısı.
2. **Phone object** (YOLO26s specialist + COCO cell phone) — yalnız destekleyici
   kanıt, asla veto. Görünmeyen telefon negatif demek değildir.
3. **Geometric + temporal karar kuralı** (el-kulak zonu, süre, taraf sürekliliği) —
   tasarım gereği domain-agnostic. Literatür doğruluyor: el+kulak ROI + pose/landmark
   geometrisi, dış/frontal sürücü telefon tespitinde yerleşik ve genelleyen
   yaklaşımdır (CVPR 2016 multi-scale Faster-RCNN windshield; ScienceDirect el-kulak
   HOG %93.86).

## Eşikler Nereden Gelecek (KRİTİK)

Eşikler test videosuna fit EDİLMEZ; fizyolojik önceliklerden türetilir:

* **Süre:** gerçek çağrı >= ~1.5-2 sn sürer; kaşıma / dokunma kısadır.
* **Tek taraf:** çağrı tek kulakta kalır (yüksek `dominant_side_rate`); kaşıma gezinir.
* **Kulak zonu:** el kulak bölgesinde olmalı, ağız/burun değil (sigara/yeme ayrımı).

Bu öncelikler her araç/sürücüde geçerli olduğu için genelleşir. Teknofest videosu bu
eşiklerin makul olduğunu yalnız DOĞRULAR (smoke); onları kalibre etmez.

## Genelleme Nasıl DOĞRULANIR (test'e dokunmadan)

Per-component validation + held-out:

* **Pose / person:** çeşitli public veride (COCO vb.) bilinen genelleme + Teknofest
  videolarında stres testi (etiketle değil; keypoint güvenilirliği ve `not_evaluable`
  oranıyla).
* **Phone detection:** dış-görünüm public phone veri setlerinde (ör. Roboflow
  Universe) genelleme metriği.
* **Behavior (el-kulak):** domain-agnostic geometri argümanı + mümkünse çok kaynaklı
  klipler. Dürüst kısıt: serbestçe kullanılabilir dış-görünüm DAVRANIŞ veri seti azdır;
  bu yüzden iddia, component-wise generalization + geometry-by-construction'a dayanır.
* **Teknofest 3 videosu:** yalnız son held-out smoke.

## Pose Güvenilirlik Stres Testi (EXP-007)

`PHONE-CALL-EXP-007 = phone_call_pose_reliability_diagnostic_v1` eklendi. Bu
adım davranış etiketi üretmez; pose kanıtının telefon-konuşma kararı için ne kadar
güvenilir olduğunu ölçer.

Komut:

```bash
.venv-yolo/bin/python scripts/benchmarks/analyze_phone_call_pose_reliability.py
```

Mevcut Teknofest smoke sonucu:

| Video | Pose durumu | Kritik not |
|---|---|---|
| `video_1.mp4` | `usable_borderline` | evaluable rate 0.5468 ile sınırda |
| `video_2.mp4` | `decision_usable` | en temiz pose kanıtı |
| `video_3.mp4` | `usable_borderline` | evaluable rate 0.4702, optical-flow wrist 0.3252, identity reset 8 |

Karar politikası:

* `decision_usable`: pose-temporal karar verilebilir.
* `usable_borderline`: karar verilebilir ama daha güçlü temporal süreklilik istenir;
  negatif karar pose yokluğundan çıkarılmamalı.
* `pose_limited`: `not_evaluable` veya düşük riskli `candidate`; negatif üretme.

Çıktılar:

* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-007-pose_reliability.json`
* `testing/reports/phone_call_baseline_v2/pose_reliability.md`

## Öğrenilmiş Temporal Head (EXP-005) — Deprioritize

5 session'dan öğrenilmiş bir head "herhangi araç/sürücü"ye genelleşmez; domain-overfit
olur. Yalnız büyük + çeşitli + dış-görünüm bir davranış veri seti ortaya çıkarsa
revisit edilir. O zamana kadar generalizable core = pretrained pose + phone +
geometric/temporal kural.

## Kabul Protokolü (güncel)

* Held-out test = Teknofest 3 video; üzerinde tuning yasak.
* Dev / validation seti DIVERSE ve çok kaynaklı olmalı (tek kayıt/kişi değil).
* `evaluate_phone_call_behavior.py` kapıları (session-based kapsama, hard-negative
  specificity, occluded-positive) dev set üzerinde geçilmeli; test yalnız doğrular.

## Eski Planın Düzeltmesi

* "3 videoda LOSO threshold sweep" -> İPTAL (test'e fit olur). Eşikler priors'tan gelir.
* "30 session kendi verini topla + head eğit" -> opsiyonel/ikincil; generalization için
  zorunlu değil. Öncelik pose robustluğu + geometrik kuralın domain-agnostic kalması.

## Kaynaklar

* Le et al., "Multiple Scale Faster-RCNN Approach to Driver's Cell-Phone Usage and
  Hands on Steering Wheel Detection", CVPR 2016 Workshops:
  <https://openaccess.thecvf.com/content_cvpr_2016_workshops/w3/papers/Le_Multiple_Scale_Faster-RCNN_CVPR_2016_paper.pdf>
* "Detection of driver manual distraction via image-based hand and ear recognition",
  Accident Analysis & Prevention:
  <https://www.sciencedirect.com/science/article/abs/pii/S0001457519309029>
