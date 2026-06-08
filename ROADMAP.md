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

Runtime assumption: Android captures live 720p frames/stream, MacBook runs the local edge/backend inference server, and Colab is used for model research/fine-tune.

## Near-Term Technical Order

1. Finalize `architecture/contracts`.
2. Prepare vehicle detection research comparison table.
3. Create Colab baseline experiment notebook plan.
4. Add backend stub with health, stream and recent events endpoints.
5. Connect mobile camera screen to backend stub.

## Report Order

1. PDR/OTR draft.
2. System architecture figure.
3. AI module selection rationale.
4. Dataset/license inventory.
5. Test and evidence metric tables.
