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

2026-06-11 güncellemesiyle track summary içinde compact history alanları da üretilir:

* `center_history_sample`
* `bbox_history_sample`
* `history_sample_strategy`

Bu alanlar speed baseline, plate temporal voting, target selection ve evidence skeleton için kullanılır.

## `build_track_event_skeleton.py`

ByteTrack benchmark summary dosyasını okuyup track-level post-process ve ilk event/evidence skeleton çıktısını üretir.

Varsayılan koşu:

```bash
python3 scripts/benchmarks/build_track_event_skeleton.py
```

Üretilen çıktılar:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-track-postprocess.json`
* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* `testing/reports/trk_exp_001_track_to_event_summary.md`

Bu script gerçek risk alarmı üretmez. `target_vehicle_selected` seviyesinde ara event skeleton'ı oluşturur ve sonraki speed, plate OCR, QoD ve evidence modülleri için aynı `track_id` üzerinden bağlanacak kayıtları hazırlar.

## `extract_plate_ocr_target_rois.py`

Plate Detection + OCR MVP için ilk giriş verisini üretir. `target_vehicle_selected` event skeleton dosyasını okuyup raw test videolarındaki `best_frame` karesinden hedef araç ROI crop'larını çıkarır.

Varsayılan koşu:

```bash
.venv-yolo/bin/python scripts/benchmarks/extract_plate_ocr_target_rois.py
```

Varsayılan input:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`

Üretilen çıktılar:

* Crop görselleri: `runs/plate_ocr/POCR-EXP-001-target-roi-crops/`
* Summary JSON: `models/benchmarks/artifacts/POCR-EXP-001-target-roi-crops-summary.json`
* Rapor: `testing/reports/pocr_exp_001_target_roi_crops_summary.md`

Bu aşama plate detection veya OCR değildir. Yalnız plate detector/OCR için target vehicle ROI girişlerini hazırlar. Crop görselleri büyük/gizlilik duyarlı artifact sayıldığı için Git'e eklenmez.
