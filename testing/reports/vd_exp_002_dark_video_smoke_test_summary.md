# VD-EXP-002 Dark Video Smoke Test Summary

## Kapsam

Bu rapor, fine-tuned `vehicle_detector_general` checkpoint'i ile lokal dark video
smoke test sonucunu kaydetmek icindir. Bu test final model dogrulugu iddiasi
degildir; FTR raporunda `manual qualitative review` ve pipeline kullanilabilirligi
kaniti olarak kullanilmalidir.

## Kosu Bilgisi

* Weights: `models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt`
* Device: `mps`
* Image size: `640`
* Confidence threshold: `0.25`
* Classes: `[0, 1, 2, 3]`
* Annotated output root: `runs/vehicle_detection/VD-EXP-002-dark-smoke`

## Video Sonuclari

| Video | Frames | Detected Frames | Detections | Classes | Mean Conf | Mean ms | p95 ms | FPS | Annotated |
|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| Test/video_1.mp4 | 423 | 423 | 598 | car:598 | 0.779 | 17.263 | 24.224 | 28.945 | `runs/vehicle_detection/VD-EXP-002-dark-smoke/video_1/video_1.mp4` |
| Test/video_2.mp4 | 457 | 457 | 645 | car:645 | 0.735 | 16.276 | 21.998 | 30.625 | `runs/vehicle_detection/VD-EXP-002-dark-smoke/video_2/video_2.mp4` |
| Test/video_3.mp4 | 383 | 383 | 617 | car:611, motorcycle:6 | 0.732 | 16.983 | 25.073 | 28.446 | `runs/vehicle_detection/VD-EXP-002-dark-smoke/video_3/video_3.mp4` |

## Rapor Notu

* Bu smoke test 3 lokal dark video uzerinde gorsel kontrol icin uretilir.
* Annotated videolar `runs/` altindadir ve Git'e eklenmez.
* Manuel review tamamlanmadan accuracy, recall veya hukuki kanit iddiasi kurulmaz.
