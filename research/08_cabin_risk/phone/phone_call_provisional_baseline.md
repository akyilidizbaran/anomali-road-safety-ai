# Phone-Call Provisional Baseline

Tarih: 2026-06-20

## Karar

`PHONE-CALL-PROVISIONAL-BASELINE` entegrasyon ve demo için donduruldu.

Bu **final kabul edilmiş risk baseline'ı değildir**. Final kabul kapıları hâlâ
geçilmediği için `phone_risk=null` kalır.

## Stack

Provisional baseline şu stack'tir:

1. `PHONE-CALL-EXP-002 = phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2`
   * phone object branch,
   * ViTPose/LK arm evidence,
   * el-kulak zone,
   * dominant side consistency,
   * temporal window + hysteresis.
2. `PHONE-CALL-EXP-007 = phone_call_pose_reliability_diagnostic_v1`
   * pose güvenilirlik guardrail'i,
   * `decision_usable`, `usable_borderline`, `pose_limited` ayrımı.
3. `PHONE-EXP-004 = yolo26s_phone_windshield_seed_smoke`
   * yalnız destekleyici object kanıtı.

## Çıktı Contract'ı

Sistem şu davranış statülerini üretebilir:

* `handheld_call_likely`
* `candidate`
* `not_detected`
* `not_evaluable`

Önemli kurallar:

* `phone_object_detected=false`, “telefonla konuşmuyor” demek değildir.
* Telefon görünmüyorsa karar yükü pose-temporal kanıta geçer.
* Pose güvenilirliği `usable_borderline` ise daha güçlü süreklilik gerekir.
* Pose `pose_limited` ise negatif karar üretilmez; `candidate` veya
  `not_evaluable` tercih edilir.
* `phone_risk` final acceptance geçene kadar `null` kalır.

Event/evidence entegrasyonunda şu alanlar yazılır:

* `driver_cabin.phone_call_status`
* `driver_cabin.phone_call_confidence`
* `driver_cabin.phone_call_evidence_source`
* `driver_cabin.phone_call_baseline_id`
* `driver_cabin.phone_call_pose_reliability`
* `driver_cabin.phone_call_pose_policy`
* `models.phone_call_provisional_baseline`
* `evidence.phone_call_final_baseline_accepted=false`

## Güncel Held-Out Smoke Sonucu

| Video | Label | Status | Pose | Not |
|---|---|---|---|---|
| `video_1.mp4` | positive | candidate | usable_borderline | recall kaybı; hard-negative olmadan eşik düşürülmedi |
| `video_2.mp4` | positive | handheld_call_likely | decision_usable | doğru pozitif |
| `video_3.mp4` | unknown | candidate | usable_borderline | güvenilir label yok |

Event/demo özeti:

* Status counts: `candidate=2`, `handheld_call_likely=1`
* Pose reliability: `usable_borderline=2`, `decision_usable=1`
* `phone_risk` tüm eventlerde `null`
* Rapor: `testing/reports/phone_call_baseline_v2/provisional_baseline_event_summary.md`

Güncel evaluation:

* `baseline_accepted=false`
* `recall=0.5`
* `specificity=null`
* `hard_negative_specificity=null`

Blocker:

* `positive_sessions=2<3`
* `negative_sessions=0<5`
* `hard_negative_sessions=0<2`

## Neden Provisional?

Hazır modeller bu kamera açısında yeterli domain transfer sağlamadı. Kendi temporal
head'imiz çalışıyor ama veri çok az olduğu için final baseline olamaz. Buna rağmen
EXP-002 + EXP-007 stack'i doğru mimariyi ve güvenlik guardrail'lerini içeriyor:

* object yokluğunu veto olarak kullanmıyor,
* pose zayıfsa negatif üretmiyor,
* hard-negative verisi gelmeden risk üretmiyor.

Bu nedenle entegrasyon/demo için provisional baseline olarak dondurulmuştur.

## Final Baseline'a Geçiş Şartı

Final kabul için aynı evaluation harness ile şunlar aynı anda geçmelidir:

* en az 3 pozitif session,
* en az 5 negatif session,
* en az 2 hard-negative session,
* en az 1 occluded-positive session,
* recall `>=0.80`,
* genel specificity `>=0.90`,
* hard-negative specificity `>=0.90`.

## Artifactler

* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-PROVISIONAL-BASELINE.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-PROVISIONAL-BASELINE-event-summary.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-002-phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2-summary.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-002-evaluation.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-007-pose_reliability.json`
* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-phone-call.json`
* `testing/reports/phone_call_baseline_v2/provisional_baseline_event_summary.md`
