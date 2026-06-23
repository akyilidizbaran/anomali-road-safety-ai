# Driver Torso / Arm-State Handoff Baseline Review

Date: 2026-06-23

Source archive:

```text
handoff.zip
```

## Scope

This report records whether `driver_torso` and `driver_arm_state` baselines are
present in the imported handoff package and what can be reviewed on the current
three local videos.

The imported modules are not final driver-risk models. They are baseline
pipelines for manual review and for deciding whether a later fine-tune or
replacement model is required.

## Checkpoint Finding

No standalone trained checkpoint was found for either module:

| Module | Dedicated checkpoint in handoff | Interpretation |
|---|---:|---|
| `driver_torso` | No | Deterministic torso ROI pipeline anchored to cabin/face evidence. |
| `driver_arm_state` | No | Pose + LK tracking + temporal voting pipeline. |

Phone object specialists are the only new `.pt` weights found in `handoff.zip`.
They are documented separately in `models/checkpoint_registry_cabin_phone.md`.

## Driver Torso Baseline

Experiment:

```text
TORSO-EXP-001-yunet_face_anchored_deterministic_torso_v1
```

Summary artifact:

```text
models/benchmarks/artifacts/TORSO-EXP-001-yunet_face_anchored_deterministic_torso_v1-summary.json
```

Three-video outputs:

| Video | Status | Evaluable driver frames | Usable torso rate | Mean torso quality | Annotated video |
|---|---|---:|---:|---:|---|
| `video_1.mp4` | completed | 187 | 1.0000 | 0.9633 | `runs/driver_torso/torso_exp_001/annotated/video_1_yunet_face_anchored_deterministic_torso_v1.mp4` |
| `video_2.mp4` | completed | 209 | 1.0000 | 0.9688 | `runs/driver_torso/torso_exp_001/annotated/video_2_yunet_face_anchored_deterministic_torso_v1.mp4` |
| `video_3.mp4` | completed | 134 | 0.4254 | 0.8039 | `runs/driver_torso/torso_exp_001/annotated/video_3_yunet_face_anchored_deterministic_torso_v1.mp4` |

Comparison decision:

```text
models/benchmarks/cabin/driver_torso_baseline_comparison.csv
```

The current comparison row marks this baseline as:

```text
rejected_full_video_user_review
```

Reason recorded in the imported comparison table:

```text
Sampled frames looked plausible but full-video user review found discontinuities,
incorrect placement and materially inconsistent behavior across all three videos.
```

Project decision: keep the outputs and scripts as a baseline reference, but do
not promote deterministic torso geometry as an accepted driver-risk model.

## Driver Arm-State Baseline

Primary three-video branch:

```text
ARM-EXP-001-vitpose_b_lk_arm_tracker_v1
```

Summary artifact:

```text
models/benchmarks/artifacts/phone_call_baseline_v2/ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json
```

Three-video outputs:

| Video | Status | Available state rate | Dominant state rates | p95 arm latency | Annotated video |
|---|---|---:|---|---:|---|
| `video_1.mp4` | completed | 1.0000 | `hand_near_face=0.9679`, `hand_off_wheel_candidate=0.0160`, `hands_on_wheel_candidate=0.0160` | 6.540 ms | `runs/phone_call_baseline_v2/arm/arm_exp_001/annotated/video_1_vitpose_b_lk_arm_tracker_v1.mp4` |
| `video_2.mp4` | completed | 1.0000 | `hand_near_face=0.9856`, `hands_on_wheel_candidate=0.0144` | 6.259 ms | `runs/phone_call_baseline_v2/arm/arm_exp_001/annotated/video_2_vitpose_b_lk_arm_tracker_v1.mp4` |
| `video_3.mp4` | completed | 0.9851 | `hand_near_face=0.8881`, `hands_on_wheel_candidate=0.0970`, `unknown=0.0149` | 6.055 ms | `runs/phone_call_baseline_v2/arm/arm_exp_001/annotated/video_3_vitpose_b_lk_arm_tracker_v1.mp4` |

Standalone comparison outputs also exist for `video_3`:

| Branch | Available state rate | p95 arm latency | Annotated video |
|---|---:|---:|---|
| ViTPose-B + LK | 0.9851 | 10.836 ms | `runs/driver_arm_state/arm_exp_001/annotated/video_3_vitpose_b_lk_arm_tracker_v1.mp4` |
| YOLO11n-pose + LK | 0.3209 | 11.127 ms | `runs/driver_arm_state/arm_exp_001/annotated/video_3_yolo11n_pose_arm_focus_coco17_lk_arm_tracker_v1.mp4` |

Project decision: ViTPose + LK is the only branch worth manually reviewing
first. YOLO11n-pose arm focus is weaker as a continuous arm-state baseline.

Guardrail:

```text
risk_enabled=false
```

The high `hand_near_face` rate across all three videos is a warning sign, not a
success claim. It may reflect camera geometry, pose landmark bias, face/ear zone
geometry or missing negative validation. It must be manually reviewed before any
driver behavior inference is accepted.

## Manual Review Files

Use these templates:

```text
testing/templates/manual_driver_torso_review.csv
testing/templates/manual_driver_arm_state_review.csv
```

Review order:

1. `driver_torso` annotated videos, because torso ROI quality determines whether
   later cabin/driver crops are usable.
2. `driver_arm_state` ViTPose + LK three-video outputs.
3. Standalone `video_3` YOLO11n-pose arm-state comparison only if the ViTPose
   branch looks promising enough to need a lighter fallback.

## Next Technical Decision

If manual review confirms poor torso placement, do not tune the deterministic
geometry further as the main route. Replace it with a stronger cabin/driver ROI
strategy: face + upper-body/person detector, segmentation-assisted cabin crop, or
explicit driver-region labeling.

If manual review confirms arm-state false positives, do not treat arm-state as a
rule-only module. Open a supervised driver-action dataset path and train a
separate action classifier after cabin/driver ROI quality is acceptable.

## Reproduction Commands

Existing outputs are already available locally. To regenerate from current
summaries:

```bash
python3 scripts/benchmarks/run_driver_torso_baseline.py
```

```bash
python3 scripts/benchmarks/run_driver_arm_state_baseline.py \
  --pose-summary models/benchmarks/artifacts/phone_call_baseline_v2/POSE-EXP-010-vitpose_b_arm_focus_observations_v1-summary.json \
  --runs-root runs/phone_call_baseline_v2/arm
```

Clean regeneration from raw video may also require the missing YuNet ONNX file
referenced in the handoff docs:

```text
models/checkpoints/cabin/face_detection_yunet_2026may.onnx
```
