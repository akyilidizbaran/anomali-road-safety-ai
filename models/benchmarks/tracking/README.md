# Tracking Benchmarks

Bu klasör vehicle tracking deney sonuçlarını küçük, Git'te takip edilebilir CSV/Markdown/JSON dosyalarıyla kaydetmek için ayrılmıştır.

Büyük video çıktıları, annotated video dosyaları, model ağırlıkları ve run artifactleri Git'e eklenmez; lokal `runs/` veya ignore edilen artifact klasörlerinde tutulur.

Ana tablo:

* `tracking_baseline_comparison.csv`

İlk planlanan deneyler:

* `TRK-EXP-001`: ByteTrack
* `TRK-EXP-002`: BoT-SORT ReID kapalı
* `TRK-EXP-003`: BoT-SORT ReID açık, yalnız gerekirse
* `TRK-EXP-004`: OC-SORT, opsiyonel
* `TRK-EXP-005`: Kalman + IoU debug fallback
