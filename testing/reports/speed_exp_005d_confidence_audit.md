# SPEED-EXP-005D Confidence Audit

Bu rapor, hız katmanlarındaki confidence skorlarının ne anlama geldiğini ayırmak için oluşturuldu.
Mevcut üç demo videoda ground-truth hız bulunmadığı için hiçbir confidence değeri mutlak km/s doğruluğu olarak yorumlanmamalıdır.

## Kısa Sonuç

* `SPEED-EXP-004A`: Track/bbox göreli hareket sinyalidir; km/s üretmez. Confidence, track kararlılığı ve bbox geçmiş kalitesidir.
* `SPEED-EXP-002`: Plaka ölçeği destek sinyalidir. Mevcut aspect-ratio sapmaları nedeniyle düşük confidence ile tutulur.
* `SPEED-EXP-005A`: Bbox geometry otomatik yaklaşık km/s adayıdır. Confidence, uzun/stabil track ve filtrelenmiş segment kalitesidir.
* `SPEED-EXP-005D`: 004A + 002 + 005A sinyallerini birleştirir. Fusion confidence, adayların birbirini destekleme düzeyidir; ground-truth accuracy değildir.

## Üretilen Grafikler

* `/Users/baran/Desktop/5G Teknofest/runs/speed/SPEED-EXP-005D-candidate-fusion/plots/speed_candidate_comparison.png`
* `/Users/baran/Desktop/5G Teknofest/runs/speed/SPEED-EXP-005D-candidate-fusion/plots/confidence_comparison.png`
* `/Users/baran/Desktop/5G Teknofest/runs/speed/SPEED-EXP-005D-candidate-fusion/plots/fusion_confidence_breakdown.png`
* `/Users/baran/Desktop/5G Teknofest/runs/speed/SPEED-EXP-005D-candidate-fusion/plots/speed_candidate_timeseries_grid.png`

## Katman Sonuçları

| Video | 004A relative | 004A conf | 002 plate km/h | 002 conf | 005A bbox km/h | 005A conf | 005D final km/h | 005D conf | Yorum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| video_1.mp4 | normal | 0.8717 | 3.7806 | 0.28 | 2.640442 | 0.72 | 2.640442 | 0.7072 | High support for approximate candidate; not ground-truth km/h. |
| video_2.mp4 | normal | 0.5877 | 3.8768 | 0.28 | 2.334246 | 0.72 | 2.334246 | 0.651 | Bbox signal is internally stable, but final support is limited. |
| video_3.mp4 | fast | 0.6298 | 12.8163 | 0.28 | 15.064621 | 0.72 | 15.064621 | 0.72 | High support for approximate candidate; not ground-truth km/h. |

## Confidence Formülleri

### 004A Relative Track/BBox

```text
confidence = 0.35
           + 0.45 * track_stability
           + 0.10 * min(history_count / 30, 1)
           + 0.05 if median_bbox_height >= 80
           - 0.12 * min(bbox_jitter_score / 1.25, 1)
           - 0.25 if id_switch_suspected
cap: 0.95
```

Bu skor track kalitesidir; km/s doğruluğu değildir.

### 005A BBox Geometry

```text
confidence = 0.20
           + 0.22 * min(observation_count / 240, 1)
           + 0.18 * min(median_bbox_height / 300, 1)
           + 0.15 if moving_average_speed exists
           + 0.12 * (1 - speed_cv / 1.2)
           - invalid/outlier penalties
cap: 0.72
```

Bu skor otomatik monocular aday sinyalinin iç stabilitesidir. Ölçülü referans veya ground truth yoksa nihai hız doğruluğu anlamına gelmez.

### 005D Candidate Fusion

```text
fusion_confidence = 0.20
                  + 0.38 * bbox_confidence
                  + 0.12 * plate_confidence
                  + 0.10 * relative_confidence
                  + 0.13 * agreement_support
                  + 0.07 if relative_label supports candidate
cap: 0.72
```

Bu skor aday hızların birbirini destekleme skorudur. En doğru yorum: `support/evidence confidence`.

## Kapanış Kararı

Hız modülü mevcut FTR fazı için `support evidence only` olarak yeterlidir. 005D grafikleri, üç videoda göreli sinyal + bbox geometry + plaka ölçeği arasında tutarlı bir destek olduğunu gösterir. Ancak bu, gerçek hız ground-truth'u olmadığı için mutlak hız modelinin tamamlandığı anlamına gelmez. Hız konusu FTR geliştirmesini bloklamamalı; future scope'ta kontrollü ground-truth video veya kalibrasyonlu sahne ile doğrulanmalıdır.
