# Phone-Call Provisional Baseline Event Summary

* Baseline: `PHONE-CALL-PROVISIONAL-BASELINE`
* Final accepted: `False`
* Event count: `3`
* Status counts: `{'candidate': 2, 'handheld_call_likely': 1}`
* Pose reliability counts: `{'usable_borderline': 2, 'decision_usable': 1}`
* `phone_risk` all null: `True`

| Video | Phone object | Call status | Confidence | Evidence | Pose | Risk | Overlay |
|---|---|---|---:|---|---|---|---|
| video_1.mp4 | not_detected | candidate | 0.898 | pose_temporal | usable_borderline | None | `runs/phone_call_baseline_v2/phone_call_exp_002/annotated/video_1_phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2.mp4` |
| video_2.mp4 | candidate | handheld_call_likely | 1.0 | object_pose_temporal | decision_usable | None | `runs/phone_call_baseline_v2/phone_call_exp_002/annotated/video_2_phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2.mp4` |
| video_3.mp4 | not_detected | candidate | 0.7654 | pose_temporal | usable_borderline | None | `runs/phone_call_baseline_v2/phone_call_exp_002/annotated/video_3_phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2.mp4` |

Not: Bu rapor entegrasyon/demo çıktısıdır. Final kabul kapısı geçilmediği
için `phone_risk=null` korunur.
