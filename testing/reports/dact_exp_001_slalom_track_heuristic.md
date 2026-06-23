# DACT-EXP-001 Slalom Track Heuristic Baseline

Date: 2026-06-23T18:48:05Z

## Purpose

This experiment estimates a `slalom` driver-action candidate from the existing target vehicle track.
It does not train a model and does not claim legal or final driving-behavior truth.

## Inputs

* Timeseries: `models/benchmarks/artifacts/speed/SPEED-EXP-005A-bbox-geometry-auto/speed_exp_005a_bbox_geometry_timeseries.csv`
* Events: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed005d.json`

## Method

1. Read target-track bottom-center and bbox geometry from SPEED-EXP-005A.
2. Fit a low-degree lateral trend to bottom-center x over time.
3. Subtract the trend and normalize residuals by median bbox width.
4. Smooth the normalized residual curve.
5. Count meaningful lateral direction changes and score residual amplitude.
6. Write `candidate`, `review`, `not_detected`, or `not_evaluable` into event/evidence JSON.

## Results

| Video | Status | Score | Confidence | Direction changes | Normalized amplitude | Track duration | Plot | Overlay |
|---|---|---:|---:|---:|---:|---:|---|---|
| video_1.mp4 | not_detected | 0.457 | 0.775 | 3 | 0.167 | 6.86s | `runs/driver_action/slalom_exp_001/plots/video_1_slalom_residual_plot.png` | `runs/driver_action/slalom_exp_001/annotated/video_1_slalom_track_heuristic.mp4` |
| video_2.mp4 | not_detected | 0.467 | 0.773 | 3 | 0.175 | 6.86s | `runs/driver_action/slalom_exp_001/plots/video_2_slalom_residual_plot.png` | `runs/driver_action/slalom_exp_001/annotated/video_2_slalom_track_heuristic.mp4` |
| video_3.mp4 | candidate | 0.932 | 0.903 | 4 | 0.458 | 5.72s | `runs/driver_action/slalom_exp_001/plots/video_3_slalom_residual_plot.png` | `runs/driver_action/slalom_exp_001/annotated/video_3_slalom_track_heuristic.mp4` |

## Interpretation

* `candidate` means the current heuristic found repeated lateral oscillation with enough normalized amplitude.
* `review` means direction changes exist but amplitude is below the candidate threshold.
* `not_detected` means the thresholds were not met.
* `not_evaluable` means the track quality or duration was insufficient.
* `confidence` is confidence in the heuristic status decision, not ground-truth slalom accuracy.

Default candidate gate:

```text
track_duration >= 2.0s
valid_frame_ratio >= 0.70
direction_change_count >= 2
normalized_lateral_amplitude >= 0.30
normalized_lateral_rms >= 0.08
```

This is a first smoke baseline. The output must be checked visually with the residual plots and overlay videos.

## Limitations

* No lane-line ground truth is used.
* No human slalom annotation is used.
* Perspective effects are reduced by trend removal and bbox-width normalization, but not fully solved.
* Normal lane changes or curved-road camera geometry may still require manual review.
