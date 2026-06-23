# Phone Baseline Çalıştırma

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_phone_baseline.py
python scripts/benchmarks/enrich_event_skeleton_with_phone.py
```

Yalnız `video_3`:

```bash
python scripts/benchmarks/run_phone_baseline.py \
  --videos Test/video_3.mp4
```

Çıktılar:

* `models/benchmarks/artifacts/PHONE-EXP-001-yolo11n_coco_cell_phone_driver_roi_v1-summary.json`
* `testing/reports/phone_exp_001_summary.md`
* `runs/phone/phone_exp_001/`
* `testing/templates/manual_phone_review.csv`

Telefon pozitif frame/crop etiket hazırlığı:

```bash
python scripts/benchmarks/prepare_phone_finetune_samples.py \
  --video video_2.mp4 \
  --frames 30-230 \
  --stride 10
```

Seed manuel bbox CSV'sinden YOLO dataset üretimi:

```bash
python scripts/benchmarks/prepare_phone_specialist_yolo_dataset.py
```

Çıktı:

* `runs/phone/specialist_datasets/phone_windshield_seed_v1/data.yaml`
* `runs/phone/specialist_datasets/phone_windshield_seed_v1/dataset_summary.json`
* `runs/phone/specialist_datasets/phone_windshield_seed_v1/previews/`

Uzun sürecek fine-tune komutu kullanıcı terminalinde çalıştırılmalı:

```bash
yolo detect train \
  model=yolo11n.pt \
  data=runs/phone/specialist_datasets/phone_windshield_seed_v1/data.yaml \
  epochs=80 \
  imgsz=640 \
  batch=8 \
  project=runs/phone/training \
  name=phone_windshield_seed_yolo11n
```

Eğitim bittikten sonra challenger overlay/summary:

```bash
python scripts/benchmarks/run_phone_baseline.py \
  --experiment-id PHONE-EXP-002 \
  --model-key yolo11n_phone_windshield_seed_v1 \
  --model runs/phone/training/phone_windshield_seed_yolo11n/weights/best.pt \
  --class-name phone \
  --run-name phone_exp_002 \
  --report-name phone_exp_002_summary.md \
  --videos Test/video_2.mp4 \
  --confidence 0.10 \
  --imgsz 960
```

Bu komut yalnız challenger üretir. Tek videodan üretilmiş pozitif seed dataset ile
başarı alınırsa bile model baseline seçilmiş sayılmaz; negatif/yansıma/yolcu telefonu
ve ayrı pozitif videolarla tekrar ölçüm gerekir.

## Yeni Small-Object Deney Sirasi

`PHONE-EXP-002` YOLO11n komutu artik yalniz kontrol/smoke deneyidir. Yeni ana
challenger, veri kapisi tamamlandiktan sonra YOLO26s-P2 olacaktir:

```bash
source .venv-yolo/bin/activate
python - <<'PY'
from ultralytics import YOLO

model = YOLO("yolo26s-p2.yaml")
model.load("yolo26s.pt")
model.train(
    data="runs/phone/specialist_datasets/phone_windshield_v2/data.yaml",
    epochs=120,
    imgsz=960,
    batch=4,
    hsv_v=0.5,
    mosaic=0.5,
    close_mosaic=15,
    project="runs/phone/training",
    name="phone_exp_003_yolo26s_p2",
)
PY
```

Standard-head kontrol:

```bash
yolo detect train \
  model=yolo26s.pt \
  data=runs/phone/specialist_datasets/phone_windshield_v2/data.yaml \
  epochs=120 imgsz=960 batch=4 hsv_v=0.5 mosaic=0.5 close_mosaic=15 \
  project=runs/phone/training name=phone_exp_004_yolo26s
```

Bu komutlar mevcut 21-crop seed setiyle baseline egitimi icin calistirilmamalidir.
Once session-level train/val ayrimi ve negatif/hard-negative veri eklenmelidir.

## Mevcut 21-Crop Veriyle Manuel Smoke Karsilastirmasi

Bu kosu model secmez. Amac iki mimarinin mevcut telefon crop'larini ogrenip
ogrenemedigini ve uc videodaki overlay davranisini manuel gormektir.

Iki modeli ayni ayarlarla egit:

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/train_phone_specialist_challengers.py \
  --allow-positive-only-smoke
```

Script `auto` cihaz secimi kullanir. Terminalde MPS gorunmuyorsa kontrol:

```bash
python -c "import torch; print(torch.backends.mps.is_available())"
```

P2 modelini uc videoda face-near ROI ile calistir:

```bash
python scripts/benchmarks/run_phone_baseline.py \
  --experiment-id PHONE-EXP-003 \
  --model-key yolo26s_p2_phone_windshield_seed_smoke \
  --model runs/phone/training/phone_exp_003_yolo26s_p2_seed_smoke/weights/best.pt \
  --class-name phone \
  --roi-mode face_near \
  --run-name phone_exp_003_seed_smoke \
  --report-name phone_exp_003_seed_smoke_summary.md \
  --confidence 0.05 \
  --imgsz 960
```

Standard YOLO26s kontrolunu ayni protokolde calistir:

```bash
python scripts/benchmarks/run_phone_baseline.py \
  --experiment-id PHONE-EXP-004 \
  --model-key yolo26s_phone_windshield_seed_smoke \
  --model runs/phone/training/phone_exp_004_yolo26s_seed_smoke/weights/best.pt \
  --class-name phone \
  --roi-mode face_near \
  --run-name phone_exp_004_seed_smoke \
  --report-name phone_exp_004_seed_smoke_summary.md \
  --confidence 0.05 \
  --imgsz 960
```

Manuel incelenecek videolar:

* `runs/phone/phone_exp_003_seed_smoke/annotated/`
* `runs/phone/phone_exp_004_seed_smoke/annotated/`

`video_2` train kaynagiyla ayni oldugu icin recall sonucu genelleme kaniti degildir.
`video_1/3` false-positive davranisi ve kutu kararliligi icin incelenmelidir.
