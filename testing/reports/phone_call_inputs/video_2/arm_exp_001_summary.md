# ARM-EXP-001 Driver Arm-State Baseline

Tarih: 2026-06-17T18:45:02Z

`ViTPose-B observations -> forward/backward LK optical flow -> anatomical gate -> temporal arm-state voting`

Bu deney nesne tespit etmez ve risk üretmez. `hands_on_wheel_candidate` yalnız beklenen wheel zone geometrisidir; direksiyon teması değildir.

| Video | Evaluable | Available Rate | Flow-Recovered | Longest Miss s | Transitions | Identity Reset | Mean ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| video_2.mp4 | 209 | 1.0 | 73 | 0.0 | 1 | 1 | 4.669 | 6.171 |

Manuel review: `testing/templates/manual_driver_arm_state_review.csv`
