# Phone-Call Pose Reliability Diagnostic

Bu rapor davranış etiketi üretmez; el-kulak kararının pose kanıtı açısından
ne kadar güvenilir olduğunu ölçer.

| Video | Reliability | Evaluable | Complete arm | Optical-flow pts | Mean kp conf | Borderline | Policy |
|---|---|---:|---:|---:|---:|---|---|
| video_1.mp4 | usable_borderline | 0.5468 | 0.877 | 0.057 | 0.5646 | evaluable_rate=0.5468<0.55 | allow_pose_temporal_decision_but_require_temporal_consistency |
| video_2.mp4 | decision_usable | 0.6129 | 0.933 | 0.0367 | 0.6486 | - | allow_pose_temporal_decision |
| video_3.mp4 | usable_borderline | 0.4702 | 0.7985 | 0.1007 | 0.6038 | evaluable_rate=0.4702<0.55, optical_flow_wrist_rate=0.3252>0.3, identity_reset_count=8>5 | allow_pose_temporal_decision_but_require_temporal_consistency |

Guardrail: pose kanıtı sınırlı olduğunda sistem negatif üretmemeli;
`not_evaluable` veya düşük riskli `candidate` durumunda kalmalıdır.
