# Roadmap

## MVP Target

The first working MVP will focus on:

1. Android live camera preview.
2. Edge frame streaming.
3. Vehicle detection.
4. Target vehicle tracking.
5. Plate detection/OCR.
6. Lightweight frame-quality / environment context metadata.
7. Evidence card generation.
8. Basic system health screen.

Lane analysis, calibrated speed estimation, full scene/weather modeling, external road users, cabin risk and real QoD integration will be added progressively.

Runtime assumption: Android captures live 720p frames/stream, MacBook runs the local edge/backend inference server, and Colab is used later for model research/fine-tune. The active model phase is pretrained zero-fine-tune benchmarking.

## Near-Term Technical Order

1. Run pretrained zero-fine-tune challengers on `Test/video_1-3.mp4`: `VD-EXP-008` YOLO11s, `VD-EXP-009` YOLOv10n, `VD-EXP-010` YOLOv8n.
2. Record manual review counts and qualitative notes for `VD-EXP-001`, `VD-EXP-008`, `VD-EXP-009` and `VD-EXP-010`.
3. Select the first vehicle detector baseline using recall feel, bbox usability, class flicker, latency/FPS, evidence crop usability and license/export risk.
4. Add ByteTrack-style tracking, track-level class voting and confidence smoothing on top of the selected pretrained baseline.
5. Add single target / risk candidate selection and first event/evidence JSON generation.
6. Add backend stub with health, stream and recent events endpoints.
7. Connect mobile camera screen to backend stub.

## Deferred Model Training Backlog

Fine-tune is intentionally deferred until the pretrained baseline and tracking/evidence pipeline are measurable.

1. Select BDD100K download mode in `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`.
2. Run BDD100K -> YOLO conversion.
3. Train condition-aware general vehicle detector.
4. Compare baseline vs fine-tuned delta.
5. Start `night_low_light` specialist only after the general baseline and tracking pipeline justify it.

## Report Order

1. PDR/OTR draft.
2. System architecture figure.
3. AI module selection rationale.
4. Dataset/license inventory.
5. Test and evidence metric tables.
