# VD-EXP-002 Dark Video Smoke Test Runbook

## Amaç

Fine-tuned `VD-EXP-002-GENERAL-YOLO11N` checkpoint'i ile lokal `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4` üzerinde araç tespiti smoke test'i çalıştırmak.

Bu test final accuracy değildir. Amaç:

* Fine-tuned general detector'ın lokal videolarda çalıştığını görmek.
* Annotated video üretip manuel kontrol yapmak.
* FTR raporuna "manual qualitative review / pipeline usability" kanıtı eklemek.

## Ön Koşullar

Checkpoint Drive'dan lokal repoya kopyalanmalı:

```text
Drive:
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/VD-EXP-002/train/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt

Local:
models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

Drive file:

```text
https://drive.google.com/file/d/1bRBN58HyQYufsfKxVp87AEwAAZYAPnkr/view
```

Lokal Python ortamında Ultralytics kurulu olmalı:

```bash
source .venv-yolo/bin/activate
python -m pip install ultralytics opencv-python
```

## Koşu

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_vehicle_detection_video_smoke.py \
  --weights models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

Hızlı ön kontrol için:

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_vehicle_detection_video_smoke.py \
  --weights models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt \
  --max-frames 300
```

## Çıktılar

| Çıktı | Path | Git Durumu |
|---|---|---|
| Summary JSON | `models/benchmarks/artifacts/VD-EXP-002-general-yolo11n-dark-smoke-summary.json` | Commitlenebilir küçük artifact |
| Markdown rapor | `testing/reports/vd_exp_002_dark_video_smoke_test_summary.md` | Commitlenebilir |
| Annotated videolar | `runs/vehicle_detection/VD-EXP-002-dark-smoke/` | Git'e eklenmez |

## Manual Review Notları

Annotated videolar izlenirken şu alanlar not edilmeli:

| Alan | Açıklama |
|---|---|
| missed detection | Araç varken kutu yok |
| false positive | Araç değilken araç kutusu |
| wrong class | Araç otomobil yerine motor/truck gibi kısa süre yanlış sınıf |
| bbox adequacy | Kutu aracı yeterli kapsıyor mu |
| low-light failure | Hata düşük ışık/parlama/blur kaynaklı mı |
| condition note | Video frame'i gece/düşük ışık/rain/fog vb. mi |

Bu sonuçlar `testing/templates/manual_video_benchmark_review.csv` formatına işlenebilir.

## Rapor Dili

Kullanılabilir ifade:

> Fine-tuned general YOLO11n detector, üç karanlık demo videosunda smoke test protokolüyle çalıştırılmış ve annotated video çıktıları manuel qualitative review için üretilmiştir.

Kaçınılması gereken ifade:

> Model karanlık ortamda kesin doğrulukla araç tespiti yapmaktadır.

## Sorun Giderme

* `FileNotFoundError: Fine-tuned weights not found`: Checkpoint lokal path'e kopyalanmamış.
* `ModuleNotFoundError: ultralytics`: `.venv-yolo` aktif değil veya paket kurulu değil.
* Annotated video yoksa `--no-save-annotated` kullanılmadığından emin olun.
* Büyük video çıktıları `runs/` altında kalmalı; Git'e eklenmemeli.
