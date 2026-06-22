# CABIN-EXP-020A Local Video Smoke Test

## Scope

This smoke test runs the CABIN-EXP-020A cabin/driver visibility gate on the local road-facing demo videos. It does not detect driver actions; it only checks whether the frame should be routed into cabin/driver analysis.

Expected result for these exterior road videos: `not_cabin_view`.

## Summary

- Experiment: `CABIN-EXP-020A`
- Checkpoint: `models/checkpoints/cabin_driver/CABIN-EXP-020A/CABIN-EXP-020A-mobilenet_v3_large-best.pth`
- Backbone: `mobilenet_v3_large`
- Device: `mps`
- Sample every: `5` frame(s)
- Generated at UTC: `2026-06-22T15:07:45.548353+00:00`

| Video | Sampled frames | Expected-label ratio | Non-expected ratio | Max driver-cabin probability | Status | Output video |
|---|---:|---:|---:|---:|---|---|
| video_1.mp4 | 85 | 1.000 | 0.000 | 0.000 | pass | `runs/cabin/CABIN-EXP-020A-local-video-smoke/video_1_cabin020a_smoke.mp4` |
| video_2.mp4 | 92 | 1.000 | 0.000 | 0.000 | pass | `runs/cabin/CABIN-EXP-020A-local-video-smoke/video_2_cabin020a_smoke.mp4` |
| video_3.mp4 | 77 | 1.000 | 0.000 | 0.000 | pass | `runs/cabin/CABIN-EXP-020A-local-video-smoke/video_3_cabin020a_smoke.mp4` |

## Interpretation

- `pass` means at least 95% of sampled frames matched `not_cabin_view`.
- Any `driver_cabin_visible` prediction on these videos is treated as a cabin-gate false positive for manual review.
- This result should not be used as evidence that driver action recognition works; that belongs to the next cabin/action classifier stage.

## Artifacts

- Summary JSON: `models/benchmarks/artifacts/cabin_driver/CABIN-EXP-020A-local-video-smoke/cabin_exp_020a_local_video_smoke_summary.json`
- Per-frame CSV: `models/benchmarks/artifacts/cabin_driver/CABIN-EXP-020A-local-video-smoke/cabin_exp_020a_local_video_smoke_frames.csv`
- Video outputs directory: `runs/cabin/CABIN-EXP-020A-local-video-smoke`
