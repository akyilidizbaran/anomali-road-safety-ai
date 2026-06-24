# DACT-EXP-021 Phone-Call Driver ROI / Head-Shoulder Smoke Test

Tarih: 2026-06-24T05:35:37Z

## Amaç

Bu deney `DACT-EXP-020B` driver-action classifier'ını dış kamera videolarında daha sıkı crop stratejileriyle dener: hedef araç, driver ROI ve head-shoulder ROI. Amaç final `telefonla_konusma` kararı üretmek değil, crop stratejisinin sinyal taşıyıp taşımadığını manuel videolarla kontrol etmektir.

## Karar

* Genel karar: `roi_smoke_only_do_not_emit_driver_action`
* Gerekçe: Telefonla konusma dis-kamera acisinda gorunurluk ve domain gap nedeniyle dogrudan aksiyon karari olarak kullanilamaz; bu kosu yalniz crop stratejisi karsilastirmasi ve manuel review icindir.
* `should_emit_driver_action=false` tüm modlar için sabittir.

## Özet Tablo

| Video | Mode | Samples | Vote | Vote rate | phone mean | phone p95 | phone >= threshold | Top-1 phone | Candidate gate |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| video_1.mp4 | target_vehicle | 344 | arkaya_bakma_candidate | 0.4157 | 0.0249 | 0.0645 | 0.0 | 0.0 | False |
| video_1.mp4 | driver_roi | 344 | arkaya_bakma_candidate | 0.8459 | 0.06 | 0.204 | 0.0116 | 0.0116 | False |
| video_1.mp4 | head_shoulder_roi | 344 | arkaya_bakma_candidate | 0.814 | 0.027 | 0.0942 | 0.0 | 0.0 | False |
| video_2.mp4 | target_vehicle | 344 | arkaya_bakma_candidate | 0.3663 | 0.0238 | 0.0608 | 0.0 | 0.0 | False |
| video_2.mp4 | driver_roi | 344 | arkaya_bakma_candidate | 0.9041 | 0.0203 | 0.1155 | 0.0 | 0.0 | False |
| video_2.mp4 | head_shoulder_roi | 344 | arkaya_bakma_candidate | 0.9884 | 0.0083 | 0.0356 | 0.0 | 0.0 | False |
| video_3.mp4 | target_vehicle | 287 | arkaya_bakma_candidate | 0.8014 | 0.0228 | 0.0397 | 0.0 | 0.0 | False |
| video_3.mp4 | driver_roi | 287 | arkaya_bakma_candidate | 0.8955 | 0.0589 | 0.1712 | 0.0 | 0.0 | False |
| video_3.mp4 | head_shoulder_roi | 287 | arkaya_bakma_candidate | 0.9094 | 0.0225 | 0.0945 | 0.0 | 0.0 | False |

## Annotated Video Çıktıları

* `video_1.mp4`: `runs/driver_action/DACT-EXP-021-phone_call_driver_roi_head_shoulder_smoke_v1/annotated/video_1_dact021_phone_roi_compare.mp4`
* `video_2.mp4`: `runs/driver_action/DACT-EXP-021-phone_call_driver_roi_head_shoulder_smoke_v1/annotated/video_2_dact021_phone_roi_compare.mp4`
* `video_3.mp4`: `runs/driver_action/DACT-EXP-021-phone_call_driver_roi_head_shoulder_smoke_v1/annotated/video_3_dact021_phone_roi_compare.mp4`

## Artefactler

* Summary JSON: `models/benchmarks/artifacts/cabin_driver/DACT-EXP-021-phone_call_driver_roi_head_shoulder_smoke_v1/dact_exp_021_phone_call_roi_smoke_summary.json`
* Summary CSV: `models/benchmarks/artifacts/cabin_driver/DACT-EXP-021-phone_call_driver_roi_head_shoulder_smoke_v1/dact_exp_021_phone_call_roi_smoke_summary.csv`
* Frame CSV: `models/benchmarks/artifacts/cabin_driver/DACT-EXP-021-phone_call_driver_roi_head_shoulder_smoke_v1/dact_exp_021_phone_call_roi_smoke_frames.csv`

## Yorum

Eger head-shoulder ROI'da `telefonla_konusma` skoru stabil artmiyorsa, mevcut State Farm classifier dis-kamera domain'i icin yeterli sayilmaz. Bu durumda sonraki adim, gorunur driver ROI crop'lari uzerinden yeni/focused bir model veya daha uygun dis kamera/driver dataset'i ile fine-tune calismasidir.
