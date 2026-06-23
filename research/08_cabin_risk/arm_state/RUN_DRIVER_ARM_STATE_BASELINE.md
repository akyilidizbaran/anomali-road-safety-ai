# Driver Arm-State Baseline Çalıştırma

```bash
source .venv-yolo/bin/activate
```

Önce arm-focus pose gözlemlerini üret:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-010 \
  --allow-model-download
```

Ardından hybrid arm-state benchmarkını çalıştır:

```bash
python scripts/benchmarks/run_driver_arm_state_baseline.py
```

Yalnız `video_3` smoke testi:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-010 \
  --videos Test/video_3.mp4 \
  --allow-model-download

python scripts/benchmarks/run_driver_arm_state_baseline.py \
  --videos Test/video_3.mp4
```

Çıktılar:

* `models/benchmarks/artifacts/POSE-EXP-010-*-summary.json`
* `models/benchmarks/artifacts/ARM-EXP-001-*-summary.json`
* `testing/reports/pose_exp_010_pose_summary.md`
* `testing/reports/arm_exp_001_summary.md`
* `runs/driver_arm_state/arm_exp_001/annotated/`

## VLM / Llama Challenger

Local Ollama veya uyumlu runtime hazırsa, Llama/VLM adayını örnek karelerde
ölçmek için:

```bash
python scripts/benchmarks/run_driver_vlm_arm_state_challenger.py \
  --model <LOCAL_VISION_MODEL_NAME> \
  --videos Test/video_3.mp4 \
  --frames 150 175 200 225 240 \
  --crop-source vehicle
```

Bu deney pose baseline yerine geçmez; yalnız structured JSON arm-state challenger
ve audit sinyali üretir.
