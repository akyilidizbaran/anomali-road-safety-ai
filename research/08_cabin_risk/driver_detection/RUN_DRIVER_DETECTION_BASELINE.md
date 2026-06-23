# RUN - DRIVER-EXP-001 Driver Detection Baseline

Bu komut mevcut seçilmiş cabin summary dosyasını kullanarak driver detection event
alanını üretir.

```bash
python3 scripts/benchmarks/enrich_event_skeleton_with_driver_detection.py
```

Varsayılan girdiler:

```text
models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json
models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json
```

Varsayılan çıktılar:

```text
models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-driver-detection.json
models/benchmarks/artifacts/driver_detection/DRIVER-EXP-001-yunet_view_policy_driver_presence_v1/driver_exp_001_driver_detection_summary.json
testing/reports/driver_exp_001_driver_detection_summary.md
models/benchmarks/cabin/driver_detection_baseline_comparison.csv
```

Doğrulama:

```bash
python3 -m py_compile scripts/benchmarks/enrich_event_skeleton_with_driver_detection.py
python3 -m py_compile scripts/benchmarks/render_driver_detection_overlay.py
python3 -m json.tool models/benchmarks/artifacts/driver_detection/DRIVER-EXP-001-yunet_view_policy_driver_presence_v1/driver_exp_001_driver_detection_summary.json >/dev/null
```

## Görsel Overlay Üretimi

Driver'ın video üzerinde görülmesi için:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/render_driver_detection_overlay.py
```

Çıktılar:

```text
runs/driver_detection/DRIVER-EXP-001-yunet_view_policy_driver_presence_v1/annotated/video_1_driver_detection.mp4
runs/driver_detection/DRIVER-EXP-001-yunet_view_policy_driver_presence_v1/annotated/video_2_driver_detection.mp4
runs/driver_detection/DRIVER-EXP-001-yunet_view_policy_driver_presence_v1/annotated/video_3_driver_detection.mp4
```

Not: Bu modül sürücü eylemi üretmez. Çıktı yalnız sonraki
`telefonla_konusma`, `su_icme`, `sigara_icme`, `emniyet_kemeri_ihlali` gibi uzman
modüller için gate/evidence sinyalidir.
