# PHONE-EXP-003 Phone Summary

Tarih: 2026-06-18T10:35:40Z

`YuNet cabin/driver ROI -> yolo26s_p2_phone_windshield_seed_smoke -> temporal candidate metadata`

Bu deney telefon nesnesi arar; tek başına ihlal veya `phone_risk` üretmez.

| Video | Profil | Evaluable | Positive | Detection Rate | Near Face Rate | Status | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---|---:|---:|
| video_1.mp4 | side_driver_window | 233 | 6 | 0.0258 | 1.0 | not_detected | 112.198 | 139.535 |
| video_2.mp4 | side_driver_window | 245 | 109 | 0.4449 | 0.9725 | detected | 115.112 | 133.087 |
| video_3.mp4 | front_lhd | 156 | 3 | 0.0192 | 0.3333 | not_detected | 120.307 | 130.888 |

Manuel review: `testing/templates/manual_phone_review.csv`
