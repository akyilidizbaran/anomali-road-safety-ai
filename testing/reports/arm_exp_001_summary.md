# ARM-EXP-001 Driver Arm-State Baseline

Tarih: 2026-06-14T16:37:41Z

`ViTPose-B observations -> forward/backward LK optical flow -> anatomical gate -> temporal arm-state voting`

Bu deney nesne tespit etmez ve risk üretmez. `hands_on_wheel_candidate` yalnız beklenen wheel zone geometrisidir; direksiyon teması değildir.

| Video | Evaluable | Available Rate | Flow-Recovered | Longest Miss s | Transitions | Identity Reset | Mean ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| video_3.mp4 | 134 | 0.9851 | 140 | 0.04 | 3 | 8 | 7.436 | 10.836 |

Manuel review: `testing/templates/manual_driver_arm_state_review.csv`
