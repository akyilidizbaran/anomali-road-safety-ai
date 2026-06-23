# ARM-EXP-001 Driver Arm-State Baseline

Tarih: 2026-06-14T16:37:41Z

`ViTPose-B observations -> forward/backward LK optical flow -> anatomical gate -> temporal arm-state voting`

Bu deney nesne tespit etmez ve risk üretmez. `hands_on_wheel_candidate` yalnız beklenen wheel zone geometrisidir; direksiyon teması değildir.

| Video | Evaluable | Available Rate | Flow-Recovered | Longest Miss s | Transitions | Identity Reset | Mean ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| video_3.mp4 | 134 | 0.3209 | 53 | 0.94 | 0 | 8 | 7.289 | 11.127 |

Manuel review: `testing/templates/manual_driver_arm_state_review.csv`
