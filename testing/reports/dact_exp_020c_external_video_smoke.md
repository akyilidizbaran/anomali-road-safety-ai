# DACT-EXP-020C External Video Smoke Test

Tarih: 2026-06-24T05:11:31Z

## Amaç

DACT-EXP-020B iç-kabin State Farm görüntüleriyle eğitildi. Bu test, modelin yol dış-kamera videolarında doğrudan sürücü eylemi olarak kullanılıp kullanılamayacağını kontrol eden domain-transfer smoke testtir.

## Karar Politikası

* Bu testte `should_emit_driver_action=false` sabittir.
* Dış kamera görüntüsünde classifier skorları final eylem kararı değildir.
* `telefonla_konusma` ve `su_icme` yalnız driver/cabin görünürlük + temporal gate sonrası event'e taşınabilir.
* `arkaya_bakma_candidate` final `arkaya_bakma` değildir; head/torso yönü gerekir.

## Genel Karar

* Karar: `do_not_emit_driver_action_from_exterior_smoke`
* Gerekçe: DACT-EXP-020B State Farm iç-kabin görüntüleriyle eğitildi; test videoları ise yol/dış-kamera domain'inde. Bu nedenle pozitif aksiyon skorları cabin/driver visibility ve temporal gate olmadan final event/evidence kararı olarak yazılmayacak.

## Özet Tablo

| Video | Mode | Samples | Temporal vote | Vote rate | Mean conf | Top-1 counts | Positive candidates |
|---|---|---:|---|---:|---:|---|---|
| video_1.mp4 | full_frame | 35 | arkaya_bakma_candidate | 0.6571 | 0.7057 | arkaya_bakma_candidate:23, phone_use_non_call:12 | arkaya_bakma_candidate=8/35 (0.2286) |
| video_1.mp4 | target_vehicle | 35 | arkaya_bakma_candidate | 0.4 | 0.5971 | passenger_interaction_candidate:7, arkaya_bakma_candidate:14, other_distraction_hard_negative:11, phone_use_non_call:3 | arkaya_bakma_candidate=7/35 (0.2) |
| video_1.mp4 | cabin_candidate | 35 | arkaya_bakma_candidate | 0.3143 | 0.5406 | safe_or_no_event:7, passenger_interaction_candidate:9, phone_use_non_call:4, arkaya_bakma_candidate:11, other_distraction_hard_negative:2, telefonla_konusma:2 | arkaya_bakma_candidate=9/35 (0.2571) |
| video_2.mp4 | full_frame | 35 | arkaya_bakma_candidate | 0.8286 | 0.7545 | arkaya_bakma_candidate:29, phone_use_non_call:6 | arkaya_bakma_candidate=16/35 (0.4571) |
| video_2.mp4 | target_vehicle | 35 | arkaya_bakma_candidate | 0.3429 | 0.6103 | passenger_interaction_candidate:11, other_distraction_hard_negative:7, arkaya_bakma_candidate:12, safe_or_no_event:2, phone_use_non_call:3 | arkaya_bakma_candidate=9/35 (0.2571) |
| video_2.mp4 | cabin_candidate | 35 | passenger_interaction_candidate | 0.4857 | 0.4809 | passenger_interaction_candidate:17, safe_or_no_event:2, arkaya_bakma_candidate:15, telefonla_konusma:1 | arkaya_bakma_candidate=7/35 (0.2) |
| video_3.mp4 | full_frame | 29 | phone_use_non_call | 0.5172 | 0.6171 | phone_use_non_call:15, arkaya_bakma_candidate:13, su_icme:1 | arkaya_bakma_candidate=7/29 (0.2414) |
| video_3.mp4 | target_vehicle | 29 | arkaya_bakma_candidate | 0.7931 | 0.5354 | arkaya_bakma_candidate:23, other_distraction_hard_negative:4, safe_or_no_event:1, phone_use_non_call:1 | - |
| video_3.mp4 | cabin_candidate | 29 | arkaya_bakma_candidate | 0.931 | 0.5211 | arkaya_bakma_candidate:27, other_distraction_hard_negative:2 | - |

## Çıktılar

* Summary JSON: `models/benchmarks/artifacts/cabin_driver/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/dact_exp_020c_external_video_smoke_summary.json`
* Summary CSV: `models/benchmarks/artifacts/cabin_driver/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/dact_exp_020c_external_video_smoke_summary.csv`
* Frame CSV: `models/benchmarks/artifacts/cabin_driver/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/dact_exp_020c_external_video_smoke_frames.csv`

## Annotated Video Çıktıları

* `video_1.mp4` / `full_frame`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_1_full_frame_dact020c.mp4`
* `video_1.mp4` / `target_vehicle`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_1_target_vehicle_dact020c.mp4`
* `video_1.mp4` / `cabin_candidate`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_1_cabin_candidate_dact020c.mp4`
* `video_2.mp4` / `full_frame`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_2_full_frame_dact020c.mp4`
* `video_2.mp4` / `target_vehicle`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_2_target_vehicle_dact020c.mp4`
* `video_2.mp4` / `cabin_candidate`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_2_cabin_candidate_dact020c.mp4`
* `video_3.mp4` / `full_frame`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_3_full_frame_dact020c.mp4`
* `video_3.mp4` / `target_vehicle`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_3_target_vehicle_dact020c.mp4`
* `video_3.mp4` / `cabin_candidate`: `runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/video_3_cabin_candidate_dact020c.mp4`

## Not

Bu test, State Farm iç-kabin modelinin dış-kamera verisine doğrudan transfer edilmesinin risklerini ölçmek içindir. Pozitif candidate çıksa bile bu aşamada event/evidence JSON'a final driver action olarak yazılmaz.
