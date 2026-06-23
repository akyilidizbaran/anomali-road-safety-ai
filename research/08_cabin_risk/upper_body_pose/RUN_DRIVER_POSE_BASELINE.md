# Driver Upper-Body / Pose Baseline Çalıştırma Kılavuzu

Tarih: 2026-06-13

Uzun video/model koşuları MacBook terminalinde kullanıcı tarafından çalıştırılmalıdır.

## 1. Ortam

```bash
cd "/Users/elifgungen/Downloads/5G Teknofest"
source .venv-yolo/bin/activate
python -c "import cv2, torch, ultralytics, mediapipe; print('pose environment OK')"
python -m pytest testing/test_driver_pose_utils.py -q
```

## 2. `POSE-EXP-001` YOLO11n-pose

Model ilk kullanımda Ultralytics tarafından indirilebilir. İndirmeyi açıkça yapmak:

```bash
python -c "from ultralytics import YOLO; YOLO('yolo11n-pose.pt'); print('yolo11n-pose ready')"
```

Önce `video_3` smoke testi:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-001 \
  --videos Test/video_3.mp4
```

Overlay uygun görünürse üç video full-rate:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-001
```

## 3. `POSE-EXP-002` MediaPipe Full

Modeli indir:

```bash
mkdir -p models/checkpoints/cabin
curl -L \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task" \
  -o models/checkpoints/cabin/pose_landmarker_full.task
```

Önce `video_3`:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-002 \
  --videos Test/video_3.mp4
```

Sonra üç video:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-002
```

## 4. Hızlı Smoke Seçenekleri

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-001 \
  --videos Test/video_3.mp4 \
  --frame-stride 5 \
  --video-scale 0.35
```

`frame_stride=5` yalnız kod/ROI smoke testi içindir. Overlay devamlılığı ve model
seçimi `frame_stride=1` sonucu üzerinden değerlendirilir.

## 5. `POSE-EXP-003` RTMPose-L Body7 384x288 ONNX

ONNXRuntime'ı kur:

```bash
UV_CACHE_DIR=.uv-cache uv pip install \
  --python .venv-yolo/bin/python \
  "onnxruntime>=1.18,<2"
```

Resmi OpenMMLab model paketini indir ve runner'ın beklediği ada taşı:

```bash
mkdir -p models/checkpoints/cabin/rtmpose_l_body7_384x288
curl -L \
  "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/rtmpose-l_simcc-body7_pt-body7_420e-384x288-3f5a1437_20230504.zip" \
  -o models/checkpoints/cabin/rtmpose_l_body7_384x288.zip
unzip -o models/checkpoints/cabin/rtmpose_l_body7_384x288.zip \
  -d models/checkpoints/cabin/rtmpose_l_body7_384x288
find models/checkpoints/cabin/rtmpose_l_body7_384x288 \
  -name "end2end.onnx" \
  -exec cp {} models/checkpoints/cabin/rtmpose-l_simcc-body7_384x288.onnx \;
```

Önce yalnız `video_3` full-rate:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-003 \
  --videos Test/video_3.mp4
```

`video_3` tam overlay manuel incelemede anlamlıysa üç video:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-003
```

## 6. Çıktılar

YOLO:

* `models/benchmarks/artifacts/POSE-EXP-001-yolo11n_pose_coco17-summary.json`
* `testing/reports/pose_exp_001_pose_summary.md`
* `runs/cabin_pose/pose_exp_001/`

MediaPipe:

* `models/benchmarks/artifacts/POSE-EXP-002-mediapipe_pose_landmarker_full-summary.json`
* `testing/reports/pose_exp_002_pose_summary.md`
* `runs/cabin_pose/pose_exp_002/`

RTMPose:

* `models/benchmarks/artifacts/POSE-EXP-003-rtmpose_l_body7_384x288_onnx-summary.json`
* `testing/reports/pose_exp_003_pose_summary.md`
* `runs/cabin_pose/pose_exp_003/`

## 7. Manuel Review

`testing/templates/manual_driver_pose_review.csv` doldurulur. Model seçimi yalnız:

1. iki full-rate JSON özeti,
2. üçer overlay videosu,
3. manuel review

birlikte değerlendirildikten sonra yapılır.

## 8. `POSE-EXP-004` RTMW-L WholeBody

Resmi OpenMMLab ONNX paketini indir:

```bash
mkdir -p models/checkpoints/cabin/rtmw_l_cocktail14_384x288
curl -L \
  "https://download.openmmlab.com/mmpose/v1/projects/rtmw/onnx_sdk/rtmw-dw-x-l_simcc-cocktail14_270e-384x288_20231122.zip" \
  -o models/checkpoints/cabin/rtmw_l_cocktail14_384x288.zip
unzip -o models/checkpoints/cabin/rtmw_l_cocktail14_384x288.zip \
  -d models/checkpoints/cabin/rtmw_l_cocktail14_384x288
find models/checkpoints/cabin/rtmw_l_cocktail14_384x288 \
  -name "end2end.onnx" \
  -exec cp {} models/checkpoints/cabin/rtmw-l_simcc-cocktail14_384x288.onnx \;
```

Telefon kolunun açık görüldüğü `video_1` ilk ayırt edici smoke testidir:

```bash
python scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-004 \
  --videos Test/video_1.mp4
```

Overlay'de body skeleton mor, whole-body el landmark'ları cyan/turuncu çizilir.
`Hand` ve `Hand Near Face` oranları ayrıca raporlanır.

## 9. `POSE-EXP-005/006` ViTPose-B

Model önbelleği hazır değilse bir kez indir:

```bash
HF_HOME=.hf-cache python -c "from transformers import AutoProcessor, VitPoseForPoseEstimation; m='usyd-community/vitpose-base-simple'; AutoProcessor.from_pretrained(m); VitPoseForPoseEstimation.from_pretrained(m); print('ViTPose-B ready')"
```

`POSE-EXP-005` ham modeldir. `POSE-EXP-006`, aynı çıktıya 200 ms kısa kayıp taşıma,
yüz-relative smoothing ve ani sıçrama reddi uygular.

Üç-video full-rate stabilize benchmark:

```bash
HF_HOME=.hf-cache MPLCONFIGDIR=.mplconfig python \
  scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-006
```

Çıktılar:

* `models/benchmarks/artifacts/POSE-EXP-006-vitpose_b_temporal_stabilized_v1-summary.json`
* `testing/reports/pose_exp_006_pose_summary.md`
* `runs/cabin_pose/pose_exp_006/annotated/`

Bu koşu phone/seatbelt/smoking sınıflandırması değildir. Final seçim için
`POSE-EXP-005` ve `POSE-EXP-006` overlay'leri yan yana manuel incelenir.

## 10. Seçilen Final Torso Baseline

`POSE-EXP-009`, ViTPose-B'yi yalnız omuz/torso ve seatbelt ROI anchor kapsamında
çalıştırır. Dirsek/bilek overlay ve action kararları kapalıdır.

```bash
HF_HOME=.hf-cache MPLCONFIGDIR=.mplconfig python \
  scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-009
```

Final videolar `runs/cabin_pose/pose_exp_009/annotated/` altına yazılır.
