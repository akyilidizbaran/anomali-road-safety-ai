# Cabin / Driver Baseline Çalıştırma Kılavuzu

Tarih: 2026-06-12

Bu komutlar uzun video/model işlemleridir ve MacBook terminalinde kullanıcı tarafından
çalıştırılmalıdır.

## 1. Ortamı Kur

```bash
cd "/Users/elifgungen/Downloads/5G Teknofest"

UV_CACHE_DIR=.uv-cache uv venv \
  --python /Users/elifgungen/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin/python3.11 \
  --seed \
  .venv-yolo

UV_CACHE_DIR=.uv-cache uv pip install \
  --python .venv-yolo/bin/python \
  -r scripts/benchmarks/requirements.txt
```

Kurulumu doğrula:

```bash
source .venv-yolo/bin/activate
python -c "import cv2, torch, ultralytics, paddleocr, easyocr, mediapipe; print('benchmark environment OK')"
python -c "import lap; print('ByteTrack lap dependency OK')"
python -m pytest testing/test_cabin_utils.py testing/test_cabin_event_enrichment.py -q
```

## 2. BlazeFace Modellerini İndir

```bash
mkdir -p models/checkpoints/cabin

curl -L \
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_full_range/float16/latest/blaze_face_full_range.tflite" \
  -o models/checkpoints/cabin/blaze_face_full_range.tflite

curl -L \
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite" \
  -o models/checkpoints/cabin/blaze_face_short_range.tflite
```

## 3. CABIN-EXP-001 Full-Range

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_cabin_visibility_baseline.py \
  --experiment CABIN-EXP-001
```

Çıktılar:

* `models/benchmarks/artifacts/CABIN-EXP-001-blazeface_full_range-summary.json`
* `testing/reports/cabin_exp_001_cabin_summary.md`
* `runs/cabin/cabin_exp_001/`

## 4. CABIN-EXP-002 Short-Range

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_cabin_visibility_baseline.py \
  --experiment CABIN-EXP-002
```

Çıktılar:

* `models/benchmarks/artifacts/CABIN-EXP-002-blazeface_short_range-summary.json`
* `testing/reports/cabin_exp_002_cabin_summary.md`
* `runs/cabin/cabin_exp_002/`

## 5. Hızlı Tek Video Kontrolü

```bash
python scripts/benchmarks/run_cabin_visibility_baseline.py \
  --experiment CABIN-EXP-001 \
  --videos Test/video_3.mp4 \
  --frame-stride 10 \
  --video-scale 0.35
```

## 6. CABIN-EXP-004 YuNet

Resmi OpenCV Zoo modelini indir:

```bash
curl -L \
  "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2026may.onnx" \
  -o models/checkpoints/cabin/face_detection_yunet_2026may.onnx
```

Önce `video_3` smoke testi:

```bash
python scripts/benchmarks/run_cabin_visibility_baseline.py \
  --experiment CABIN-EXP-004 \
  --videos Test/video_3.mp4
```

Smoke testi umut vericiyse üç video:

```bash
python scripts/benchmarks/run_cabin_visibility_baseline.py \
  --experiment CABIN-EXP-004
```

## 7. Manuel Review

`testing/templates/manual_cabin_review.csv` alanlarına göre:

* Cabin ROI cam/occupant bölgesini doğru kapsıyor mu?
* Visibility gate yansıma ve karanlığı doğru reddediyor mu?
* Yüz sayısı doğru mu?
* `front_lhd` ve `side_driver_window` driver ataması doğru mu?
* Tek kare false positive temporal final karara taşınıyor mu?

## 8. CABIN-EXP-003 Event Enrichment

Seçilen YuNet baseline:

```bash
python scripts/benchmarks/enrich_event_skeleton_with_cabin.py \
  --cabin-summary models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json
```

Eski BlazeFace deneylerini yeniden üretmek gerekirse full-range:

```bash
python scripts/benchmarks/enrich_event_skeleton_with_cabin.py \
  --cabin-summary models/benchmarks/artifacts/CABIN-EXP-001-blazeface_full_range-summary.json
```

Short-range:

```bash
python scripts/benchmarks/enrich_event_skeleton_with_cabin.py \
  --cabin-summary models/benchmarks/artifacts/CABIN-EXP-002-blazeface_short_range-summary.json
```

Ardından event schema doğrulaması:

```bash
python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator

schema = json.loads(Path("architecture/contracts/event.schema.json").read_text())
data = json.loads(Path(
    "models/benchmarks/artifacts/"
    "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin.json"
).read_text())
validator = Draft202012Validator(schema)
for event in data["events"]:
    validator.validate(event)
print(f"schema OK: {len(data['events'])} events")
PY
```
