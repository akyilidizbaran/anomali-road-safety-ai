# Driver Cabin Baseline Registry

Date: 2026-06-23

This registry records the `driver_torso` and `driver_arm_state` modules imported
from `handoff.zip`.

Important: `handoff.zip` does not contain standalone trained `.pt`, `.pth`,
`.onnx` or `.engine` checkpoints for `driver_torso` or `driver_arm_state`.
These modules are baseline pipelines built from existing cabin/pose summaries,
deterministic geometry, optical flow tracking and temporal voting.

## Module Registry

| Module | Experiment | Implementation | Checkpoint status | Current role |
|---|---|---|---|---|
| Driver torso ROI | `TORSO-EXP-001` | YuNet face anchored deterministic torso geometry | No dedicated torso checkpoint | ROI/context baseline only; not direct risk. |
| Driver arm state | `ARM-EXP-001` | ViTPose arm observations + Lucas-Kanade tracker + temporal voting | No dedicated arm-state checkpoint | Manual-review baseline; risk disabled. |
| Driver arm state alternative | `ARM-EXP-001` | YOLO11n-pose COCO17 observations + LK tracker | No dedicated arm-state checkpoint | Rejected/auxiliary comparison; weaker availability. |

## Required Inputs

| Module | Required input artifact | Present in repo | Notes |
|---|---|---:|---|
| Driver torso | `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json` | Yes | Contains cabin/face per-frame evidence used by the deterministic torso script. |
| Driver arm state | `models/benchmarks/artifacts/POSE-EXP-010-vitpose_b_arm_focus_observations_v1-summary.json` | Yes | Pose observation summary used by arm-state script. |
| Driver arm state alternative | `models/benchmarks/artifacts/POSE-EXP-011-yolo11n_pose_arm_focus_coco17-summary.json` | Yes | Lower availability than ViTPose branch. |
| Clean rerun from raw video | `models/checkpoints/cabin/face_detection_yunet_2026may.onnx` | No | Referenced by handoff docs, not included in `handoff.zip`. Needed only if recreating cabin face summaries from scratch. |

## Local Review Outputs

These outputs are intentionally under ignored `runs/` directories and are not
tracked by Git.

### Driver Torso

```text
runs/driver_torso/torso_exp_001/annotated/video_1_yunet_face_anchored_deterministic_torso_v1.mp4
runs/driver_torso/torso_exp_001/annotated/video_2_yunet_face_anchored_deterministic_torso_v1.mp4
runs/driver_torso/torso_exp_001/annotated/video_3_yunet_face_anchored_deterministic_torso_v1.mp4
runs/driver_torso/torso_exp_001/rois/
```

### Driver Arm State

Three-video ViTPose + LK outputs are preserved under the phone-call baseline v2
run context:

```text
runs/phone_call_baseline_v2/arm/arm_exp_001/annotated/video_1_vitpose_b_lk_arm_tracker_v1.mp4
runs/phone_call_baseline_v2/arm/arm_exp_001/annotated/video_2_vitpose_b_lk_arm_tracker_v1.mp4
runs/phone_call_baseline_v2/arm/arm_exp_001/annotated/video_3_vitpose_b_lk_arm_tracker_v1.mp4
```

Standalone `driver_arm_state` comparison outputs currently cover `video_3`:

```text
runs/driver_arm_state/arm_exp_001/annotated/video_3_vitpose_b_lk_arm_tracker_v1.mp4
runs/driver_arm_state/arm_exp_001/annotated/video_3_yolo11n_pose_arm_focus_coco17_lk_arm_tracker_v1.mp4
```

## Summary Artifacts

| Artifact | Purpose |
|---|---|
| `models/benchmarks/artifacts/TORSO-EXP-001-yunet_face_anchored_deterministic_torso_v1-summary.json` | Per-frame torso ROI evidence and annotated output paths. |
| `models/benchmarks/artifacts/phone_call_baseline_v2/ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json` | Three-video arm-state baseline summary used for manual review. |
| `models/benchmarks/artifacts/ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json` | Standalone video_3 ViTPose arm-state comparison. |
| `models/benchmarks/artifacts/ARM-EXP-001-yolo11n_pose_arm_focus_coco17-lk_arm_tracker_v1-summary.json` | Standalone video_3 YOLO11n-pose arm-state comparison. |
| `models/benchmarks/cabin/driver_torso_baseline_comparison.csv` | Human decision table for torso baseline. |
| `models/benchmarks/cabin/driver_arm_state_comparison.csv` | Human decision table for arm-state baseline. |

## Current Interpretation

`driver_torso` and `driver_arm_state` are integrated as reviewable baseline
pipelines, not accepted final models.

The current comparison table marks deterministic torso as rejected after full
video review. It remains useful for understanding where a future torso/cabin
model should improve, but it should not be promoted as the selected risk
baseline.

The ViTPose + LK arm-state branch has high temporal availability on the three
videos, but it is not a fine-tuned behavior classifier and `risk_enabled=false`
is preserved. It can support manual review and future labeling, not final driver
risk decisions.
