# Deterministic Driver Torso Baseline Çalıştırma Kılavuzu

Tarih: 2026-06-12

Bu deney pose modeli çalıştırmaz. YuNet summary içindeki driver yüzünden deterministik
torso/seatbelt candidate crop üretir.

## Test

```bash
cd "/Users/elifgungen/Downloads/5G Teknofest"
source .venv-yolo/bin/activate
python -m pytest testing/test_driver_torso_utils.py -q
```

## Önce `video_3` Smoke

```bash
python scripts/benchmarks/run_driver_torso_baseline.py \
  --videos Test/video_3.mp4
```

Çıktı:

* `runs/driver_torso/torso_exp_001/annotated/video_3_*.mp4`
* `runs/driver_torso/torso_exp_001/rois/video_3/`
* `models/benchmarks/artifacts/TORSO-EXP-001-*-summary.json`
* `testing/reports/torso_exp_001_summary.md`

## Üç Video

`video_3` kutusu göğüs/kemer bölgesini doğru kapsıyorsa:

```bash
python scripts/benchmarks/run_driver_torso_baseline.py
```

## Manuel Review

`testing/templates/manual_driver_torso_review.csv` kullanılır.

Özellikle:

* yeşil kutu göğüs ve seatbelt hattını kapsıyor mu,
* yolcu veya araç dış yüzeyi kutunun çoğunu kaplıyor mu,
* uzak kareler yanlış biçimde `usable` sayılıyor mu,
* kutu araç hareketinde sürücünün gerisinde kalıyor mu

kontrol edilmelidir.

## Ayar Bayrakları

```bash
python scripts/benchmarks/run_driver_torso_baseline.py \
  --videos Test/video_3.mp4 \
  --smoothing-alpha 0.65 \
  --min-face-dimension 40 \
  --min-torso-width 56 \
  --min-torso-height 72 \
  --min-retained-ratio 0.62
```

Profil geometrileri:

* `architecture/contracts/driver_torso_profiles.example.json`
