# ARM-EXP-001 Driver Arm-State Baseline

Tarih: 2026-06-18T10:29:34Z

`ViTPose-B observations -> forward/backward LK optical flow -> anatomical gate -> temporal arm-state voting`

Bu deney nesne tespit etmez ve risk üretmez. `hands_on_wheel_candidate` yalnız beklenen wheel zone geometrisidir; direksiyon teması değildir.

| Video | Evaluable | Available Rate | Flow-Recovered | Longest Miss s | Transitions | Identity Reset | Mean ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| video_1.mp4 | 187 | 1.0 | 101 | 0.0 | 2 | 2 | 4.601 | 6.54 |
| video_2.mp4 | 209 | 1.0 | 73 | 0.0 | 1 | 1 | 4.625 | 6.259 |
| video_3.mp4 | 134 | 0.9851 | 140 | 0.04 | 3 | 8 | 4.66 | 6.055 |

Manuel review: `testing/templates/manual_driver_arm_state_review.csv`
