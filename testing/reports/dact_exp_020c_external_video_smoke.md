# DACT-EXP-020C External Video Smoke Test

Tarih: 2026-06-24T05:18:16Z

## Amaç

DACT-EXP-020B iç-kabin State Farm görüntüleriyle eğitildi. Bu test, modelin yol dış-kamera videolarında doğrudan sürücü eylemi olarak kullanılıp kullanılamayacağını kontrol eden domain-transfer smoke testtir.

## Karar Politikası

* Bu testte `should_emit_driver_action=false` sabittir.
* Dış kamera görüntüsünde classifier skorları final eylem kararı değildir.
* `telefonla_konusma` ve `su_icme` yalnız driver/cabin görünürlük + temporal gate sonrası event'e taşınabilir.
* `arkaya_bakma_candidate` final `arkaya_bakma` değildir; head/torso yönü gerekir.
* Dış kamera videosunda sürücü/telefon görünmüyorsa modelden gerçek `telefonla_konusma` kanıtı beklenmez; bu koşuda amaç görünmeyen eylemi tespit etmek değil, yanlış-domain skorlarını ölçmektir.
* `sample_every > 1` kullanıldığında annotated videolar hızlandırılmaz; sampled kareler `input_fps / sample_every` ile yazılarak zaman çizgisi korunur.

## Genel Karar

* Karar: `do_not_emit_driver_action_from_exterior_smoke`
* Gerekçe: DACT-EXP-020B State Farm iç-kabin görüntüleriyle eğitildi; test videoları ise yol/dış-kamera domain'inde. Bu nedenle pozitif aksiyon skorları cabin/driver visibility ve temporal gate olmadan final event/evidence kararı olarak yazılmayacak.

## Özet Tablo

| Video | Mode | Samples | Temporal vote | Vote rate | Mean conf | Top-1 counts | Positive candidates |
|---|---|---:|---|---:|---:|---|---|
| video_1.mp4 | full_frame | 344 | arkaya_bakma_candidate | 0.657 | 0.7057 | arkaya_bakma_candidate:226, phone_use_non_call:118 | arkaya_bakma_candidate=82/344 (0.2384) |
| video_1.mp4 | target_vehicle | 344 | arkaya_bakma_candidate | 0.4186 | 0.5997 | passenger_interaction_candidate:61, arkaya_bakma_candidate:144, other_distraction_hard_negative:107, safe_or_no_event:1, phone_use_non_call:31 | arkaya_bakma_candidate=71/344 (0.2064) |
| video_1.mp4 | cabin_candidate | 344 | arkaya_bakma_candidate | 0.3459 | 0.5276 | safe_or_no_event:48, passenger_interaction_candidate:87, phone_use_non_call:45, other_distraction_hard_negative:32, arkaya_bakma_candidate:119, telefonla_konusma:13 | arkaya_bakma_candidate=76/344 (0.2209) |
| video_2.mp4 | full_frame | 344 | arkaya_bakma_candidate | 0.811 | 0.7501 | arkaya_bakma_candidate:279, phone_use_non_call:65 | arkaya_bakma_candidate=150/344 (0.436) |
| video_2.mp4 | target_vehicle | 344 | arkaya_bakma_candidate | 0.3663 | 0.6024 | passenger_interaction_candidate:112, other_distraction_hard_negative:70, safe_or_no_event:7, arkaya_bakma_candidate:126, phone_use_non_call:29 | arkaya_bakma_candidate=78/344 (0.2267) |
| video_2.mp4 | cabin_candidate | 344 | passenger_interaction_candidate | 0.4651 | 0.504 | passenger_interaction_candidate:160, safe_or_no_event:29, arkaya_bakma_candidate:151, telefonla_konusma:2, su_icme:1, phone_use_non_call:1 | arkaya_bakma_candidate=85/344 (0.2471) |
| video_3.mp4 | full_frame | 287 | phone_use_non_call | 0.5575 | 0.6278 | phone_use_non_call:160, arkaya_bakma_candidate:118, su_icme:9 | arkaya_bakma_candidate=74/287 (0.2578) |
| video_3.mp4 | target_vehicle | 287 | arkaya_bakma_candidate | 0.8014 | 0.5221 | arkaya_bakma_candidate:230, passenger_interaction_candidate:1, other_distraction_hard_negative:39, safe_or_no_event:2, phone_use_non_call:15 | - |
| video_3.mp4 | cabin_candidate | 287 | arkaya_bakma_candidate | 0.8746 | 0.5327 | arkaya_bakma_candidate:251, passenger_interaction_candidate:4, safe_or_no_event:4, other_distraction_hard_negative:28 | - |

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
