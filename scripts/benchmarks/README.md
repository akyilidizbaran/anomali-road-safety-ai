# Benchmark Scripts

Bu klasör lokal benchmark koşularını tekrar üretmek için kullanılan scriptleri tutar.

## `run_tracking_baseline.py`

Vehicle tracking baseline deneylerini çalıştırır.

Varsayılan koşu:

```bash
.venv-yolo/bin/python scripts/benchmarks/run_tracking_baseline.py \
  --experiments TRK-EXP-001 TRK-EXP-002
```

Varsayılanlar:

* Model: `yolo11n.pt`
* Videolar: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
* Sınıflar: `car`, `motorcycle`, `bus`, `truck`
* `TRK-EXP-001`: ByteTrack
* `TRK-EXP-002`: BoT-SORT ReID kapalı

Büyük annotated video çıktıları `runs/tracking/` altında kalır ve Git'e eklenmez. Küçük JSON özetleri `models/benchmarks/artifacts/` altında tutulur.
