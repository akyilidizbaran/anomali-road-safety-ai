# SMOKING-EXP-000 Segment Review Pack

Tarih: 2026-06-23

## Amaç

Sigara/smoking çalışmasının ilk uygulama adımıdır. Model eğitmez ve risk üretmez.
Mevcut driver arm/pose evidence'i kullanarak ağız-el çevresi aday segmentlerini
manuel review için klip ve contact sheet formatına çevirir.

## Komut

```bash
.venv-yolo/bin/python scripts/benchmarks/prepare_smoking_segment_review.py
```

## Girdi

* Arm/pose summary:
  `models/benchmarks/artifacts/phone_call_baseline_v2/ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json`
* Videolar:
  `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`

## Çıktılar

* Review CSV:
  `runs/smoking_review/segment_review_v1/manual_smoking_segments_review.csv`
* Klipler:
  `runs/smoking_review/segment_review_v1/clips/`
* Contact sheet görselleri:
  `runs/smoking_review/segment_review_v1/contact_sheets/`
* Trace artifact:
  `models/benchmarks/artifacts/smoking/SMOKING-EXP-000-segment_review_pack.json`

## Sonuç

| Video | Segment | Aday frame | Not |
|---|---:|---:|---|
| `video_1.mp4` | 2 | 181 | mouth/hand review gerekli |
| `video_2.mp4` | 2 | 202 | phone-call hard-negative olabilir |
| `video_3.mp4` | 2 | 113 | mouth/hand review gerekli |

Toplam:

* `segment_count=6`
* review pack boyutu yaklaşık `45 MB`

## Yorum

Ağız-el yakınlığı kaba ve yüksek recall'lı bir sinyaldir; sigara var demek değildir.
Bu pack'in amacı pozitif/hard-negative/neutral segmentleri insan review'una
taşımaktır.

İlk review'da özellikle şunlar işaretlenmeli:

* `smoking`
* `neutral`
* `face_touch_hard_negative`
* `drink_eat_hard_negative`
* `phone_call_hard_negative`
* `unknown`

Final baseline veya risk kararı değildir.
