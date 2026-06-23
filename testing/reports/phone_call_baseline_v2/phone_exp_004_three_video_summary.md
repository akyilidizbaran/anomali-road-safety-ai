# PHONE-EXP-004 Phone Summary

Tarih: 2026-06-18T10:37:38Z

`YuNet cabin/driver ROI -> yolo26s_phone_windshield_seed_smoke -> temporal candidate metadata`

Bu deney telefon nesnesi arar; tek başına ihlal veya `phone_risk` üretmez.

| Video | Profil | Evaluable | Positive | Detection Rate | Near Face Rate | Status | Mean ms | P95 ms |
|---|---|---:|---:|---:|---:|---|---:|---:|
| video_1.mp4 | side_driver_window | 233 | 8 | 0.0343 | 0.5 | not_detected | 79.802 | 96.345 |
| video_2.mp4 | side_driver_window | 245 | 200 | 0.8163 | 0.975 | detected | 81.397 | 92.554 |
| video_3.mp4 | front_lhd | 156 | 8 | 0.0513 | 0.0 | not_detected | 86.731 | 94.102 |

Manuel review: `testing/templates/manual_phone_review.csv`
