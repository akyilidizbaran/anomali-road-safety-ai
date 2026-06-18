# SPEED-EXP-004A Relative Track/BBox Speed Baseline

## Özet

Bu rapor, ByteTrack target vehicle history çıktılarından kalibrasyonsuz göreli hız sinyali üretir.

Sonuç: Bu aşama **km/s üretmez**. Çıktı, `relative` / `unavailable` speed mode, göreli hız skoru, bbox scale dinamiği, güven skoru ve fallback gerekçesi üretir.

## Deney Bilgisi

* Experiment: `SPEED-EXP-004A`
* Input event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-fastplate.json`
* Summary JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-004A-relative-track-bbox/speed_exp_004a_relative_track_speed_summary.json`
* Summary CSV: `models/benchmarks/artifacts/speed/SPEED-EXP-004A-relative-track-bbox/speed_exp_004a_relative_track_speed_summary.csv`
* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004a.json`
* Minimum track stability: `0.7`
* Minimum history points: `8`
* Minimum bbox height: `60.0`

## Üretilen Sinyaller

* `bottom_center_x/y`
* `pixel_velocity_px_s`
* `bbox_height`
* `bbox_area`
* `bbox_height_delta_norm`
* `bbox_area_delta_log`
* `scale_normalized_speed`
* `bbox_motion_jitter_score`

## Mod ve Label Dağılımı

```json
{
  "speed_mode": {
    "relative": 3
  },
  "relative_speed_label": {
    "normal": 2,
    "fast": 1
  }
}
```

## Event Sonuçları

| Video | Event | Track | Mode | Label | Score | px/s median | Confidence | Fallback |
|---|---|---:|---|---|---:|---:|---:|---|
| video_1.mp4 | EVT-TRK-EXP-001-video_1-TRK-001 | TRK-001 | relative | normal | 0.244016 | 307.39154 | 0.8717 | no_reliable_metric_calibration |
| video_2.mp4 | EVT-TRK-EXP-001-video_2-TRK-001 | TRK-001 | relative | normal | 0.22973 | 261.361693 | 0.5877 | no_reliable_metric_calibration |
| video_3.mp4 | EVT-TRK-EXP-001-video_3-TRK-002 | TRK-002 | relative | fast | 0.62354 | 414.122766 | 0.6298 | no_reliable_metric_calibration |

## Yorum

Bu deney, sonraki `SPEED-EXP-004B` plate-scale + VATTR sanity-check aşamasına giriş olacak relative motion contract'ını üretir.

`fallback_reason = no_reliable_metric_calibration` değeri hata değildir. Bu, sabit kamera homografisi veya güvenilir metrik referans olmadığı için çıktının mutlak km/s olarak yorumlanmaması gerektiğini belirtir.

## Sınırlamalar

* Bu sonuç hukuki hız ölçümü değildir.
* `center_history_sample` ve `bbox_history_sample` içinde gerçek frame id saklanmadığı için frame index'leri `target_vehicle.frame_window` aralığına eşit dağıtılarak türetilmiştir.
* Bbox kırpılması, perspektif ve detector jitter skor büyüklüğünü etkileyebilir.
* `relative_speed_label` eşikleri ilk heuristic değerlerdir; manuel review sonrası ayarlanmalıdır.

## Sonraki Adım

1. Üç demo video için bu sonuçlar manuel gözle kontrol edilmeli.
2. `VATTR-EXP-001-efficientnet_b0-best.pth` target crop smoke test ile doğrulanmalı.
3. `SPEED-EXP-004B` içinde plate-scale ve VATTR signal, bu relative speed block üstüne sanity-check olarak bağlanmalı.
