# Cabin / Driver Benchmarks

Bu klasör Cabin/Driver baseline karşılaştırmasının küçük, Git'te takip edilebilir
sonuçlarını tutar.

Ana tablo:

* `cabin_baseline_comparison.csv`
* `driver_detection_baseline_comparison.csv`
* `driver_pose_baseline_comparison.csv`
* `driver_torso_baseline_comparison.csv`
* `seatbelt_baseline_comparison.csv`

Deneyler:

* `CABIN-EXP-001`: MediaPipe BlazeFace full-range.
* `CABIN-EXP-002`: MediaPipe BlazeFace short-range.
* `CABIN-EXP-003`: Seçilen baseline event/evidence enrichment.
* `DRIVER-EXP-001`: Seçilen YuNet cabin/face summary üstünden driver presence
  ve role-assignment event enrichment.

Cabin crop, yüz görüntüsü ve overlay videoları kişisel veri riski nedeniyle yalnız
ignore edilen `runs/cabin/` altında tutulur.

## Seatbelt

`SEATBELT-EXP-001`, `POSE-EXP-009` torso ROI üzerinde OpenCV diyagonal çizgi
evidence referansıdır. Üç videoda çalışmış olsa da manuel incelemede yansıma ve
araç çizgileri false-positive üretebildiği için seçilmemiştir. Tüm event
kararlarında `seatbelt_status=unknown` korunur. Sonraki aday kontrollü etiketli
veri üzerinde öğrenilebilir classifier/detector olacaktır.
