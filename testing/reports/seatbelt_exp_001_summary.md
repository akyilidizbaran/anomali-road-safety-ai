# SEATBELT-EXP-001 Baseline Summary

Tarih: 2026-06-14T14:31:33Z

## Karar Sınırı

Bu heuristic yalnız tekrarlanan diyagonal kemer kanıtından `belted` adayı üretir. Çizgi yokluğu `unbelted` değildir; `incorrect` sınıfı kontrollü etiketli model olmadan kapalıdır.

| Video | Profil | Evaluable | Evidence-only | Belt Evidence Rate | Temporal Status | Mean ms | P95 ms |
|---|---|---:|---:|---:|---|---:|---:|
| video_1.mp4 | side_driver_window | 174 | 38 | 0.0402 | unknown | 2.056 | 4.716 |
| video_2.mp4 | side_driver_window | 209 | 43 | 0.0096 | unknown | 1.906 | 3.338 |
| video_3.mp4 | front_lhd | 121 | 88 | 0.0 | unknown | 1.182 | 3.615 |

## Çıktılar

* Manual review: `testing/templates/manual_seatbelt_review.csv`
* Büyük crop/overlay çıktıları: `runs/seatbelt/`
