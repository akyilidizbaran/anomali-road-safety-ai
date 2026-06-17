# COND-EXP-001 Local Dark Video Smoke Test

## Scope

This is a local qualitative smoke test for the selected condition-profile classifier checkpoint. It is not ground-truth accuracy.

## Model

* Checkpoint: `/Users/baran/Desktop/5G Teknofest/models/checkpoints/condition_profile/COND-EXP-001-mobilenet_v3_small-best.pt`
* Backbone: `mobilenet_v3_small`
* Selection source: `COND-EXP-001 best_val_macro_f1 selected checkpoint`
* Device: `mps`

## Results

| Video | Sampled frames | Dominant profile | Dominant confidence | Mean confidence | Router decision |
|---|---:|---|---:|---:|---|
| `video_1.mp4` | 28 | `night_low_light` | 0.769 | 0.769 | night_low_light specialist is not promoted; general detector remains active |
| `video_2.mp4` | 30 | `night_low_light` | 0.743 | 0.729 | night_low_light specialist is not promoted; general detector remains active |
| `video_3.mp4` | 25 | `night_low_light` | 0.723 | 0.708 | night_low_light specialist is not promoted; general detector remains active |

## Interpretation

* Expected behavior for the current dark/low-light local videos is a dominant `night_low_light` or low-light-adjacent profile.
* The router still falls back to the general detector because condition specialists are not promoted yet.
* Manual review is still required; this smoke test only checks pipeline usability and qualitative profile consistency.
