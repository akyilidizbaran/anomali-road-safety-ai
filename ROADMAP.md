# Roadmap

## FTR Submission Target

The first working target is now the official FTR submission package:

1. Root-level `Dockerfile`.
2. Automatic `main.py` entrypoint.
3. Read `/app/data/input/video.mp4`.
4. Write `/app/data/output/results.json`.
5. Produce `arac_bilgisi.tip`, `arac_bilgisi.plaka`, `arac_bilgisi.renk`, `arac_bilgisi.confidence_score`.
6. Produce timed `tespitler[]` entries for `sofor_eylemi`, `nesneler`, and `yolcular`.
7. Keep every JSON key and label ASCII-safe, lower-case and exact-match with the FTR document.
8. Run under Tesla T4, 4 vCPU, 16 GB RAM, 2 GB SHM, max 8 GB image and 10-minute runtime constraints.

The wider Android/live edge/QoD/evidence architecture stays in the project, but it is no longer the
first acceptance target for FTR scoring.

## Near-Term Technical Order

1. Implement FTR `results.json` schema validator.
2. Implement `ftr_output_adapter` that maps internal model outputs to `arac_bilgisi` and `tespitler`.
3. Add root Dockerfile, `main.py`, `src/predict.py`, `src/utils.py` submission skeleton.
4. Wire existing vehicle detection/tracking + plate OCR into `arac_bilgisi.plaka`.
5. Add vehicle type mapping to FTR labels: `sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan`, `kamyon`.
6. Add vehicle color model or strong ROI color heuristic for `renk`.
7. Start cabin/action/object/passenger pipeline for FTR labels.
8. Add `slalom` candidate from tracking/lateral motion, but only if confidence is defensible.
9. Run local smoke test that writes a valid `results.json`.
10. Run Docker smoke test and check image size/runtime.

## Deferred Model Training Backlog

Fine-tune is only useful if it improves one of the required FTR outputs.

1. Vehicle type classifier/mapping quality.
2. Plate OCR robustness.
3. Vehicle color classification.
4. Cabin driver action labels.
5. Object/passenger labels.

Speed and homography experiments are now research/support signals, not the main FTR scoring path.

## Report Order

1. PDR/OTR draft.
2. System architecture figure.
3. AI module selection rationale.
4. Dataset/license inventory.
5. Test and evidence metric tables.
6. FTR delivery contract compliance checklist.
