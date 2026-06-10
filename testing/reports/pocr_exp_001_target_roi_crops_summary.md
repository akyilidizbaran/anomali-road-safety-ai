# POCR-EXP-001 Target ROI Crop Extraction Smoke Test

Tarih: 2026-06-11

## Amaç

Bu çalışma Plate Detection + OCR değildir. Amaç, ByteTrack ile seçilmiş `target_vehicle_selected` event skeleton'larından raw video üzerindeki hedef araç ROI crop'larını üretmek ve sonraki plate detector/OCR modülüne sağlam giriş verisi hazırlamaktır.

## Girdi

* Event skeleton: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* Video dizini: `Test`
* Padding ratio: `0.08`

## Çıktı

* Crop dizini: `runs/plate_ocr/POCR-EXP-001-target-roi-crops`
* Summary JSON: `models/benchmarks/artifacts/POCR-EXP-001-target-roi-crops-summary.json`
* Manual review şablonu: `testing/templates/manual_plate_ocr_review.csv`

## Sonuç

* Event sayısı: `3`
* Üretilen crop sayısı: `3`
* Üretilen sample crop sayısı: `39`
* Üretilen target ROI clip sayısı: `3`
* Başarısız crop sayısı: `0`

## Crop Listesi

| Event ID | Video | Track | Best Frame | Status | Best Crop | Samples | Clip Frames | Clip URI |
|---|---|---|---:|---|---:|---:|---:|---|
| EVT-TRK-EXP-001-video_1-TRK-001 | video_1.mp4 | TRK-001 | 276 | created | 1819x1417 | 13 | 344 | `runs/plate_ocr/POCR-EXP-001-target-roi-crops/clips/EVT-TRK-EXP-001-video_1-TRK-001_TRK-001_target_roi_clip.mp4` |
| EVT-TRK-EXP-001-video_2-TRK-001 | video_2.mp4 | TRK-001 | 281 | created | 1953x1342 | 13 | 344 | `runs/plate_ocr/POCR-EXP-001-target-roi-crops/clips/EVT-TRK-EXP-001-video_2-TRK-001_TRK-001_target_roi_clip.mp4` |
| EVT-TRK-EXP-001-video_3-TRK-002 | video_3.mp4 | TRK-002 | 214 | created | 2432x1609 | 13 | 287 | `runs/plate_ocr/POCR-EXP-001-target-roi-crops/clips/EVT-TRK-EXP-001-video_3-TRK-002_TRK-002_target_roi_clip.mp4` |

## Notlar

* Crop görselleri `runs/` altında kaldığı için Git'e eklenmez.
* Target ROI clip videoları `runs/` altında kaldığı için Git'e eklenmez.
* Bu aşama final plaka okuma doğruluğu iddiası kurmaz.
* Plate visibility ve OCR başarısı bu script tarafından değerlendirilmez; bunlar manual review ve sonraki plate detector/OCR koşularında işaretlenecektir.
* Sonraki adım `POCR-EXP-001` plate detector smoke test'idir.
