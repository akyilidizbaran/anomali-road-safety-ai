# Smoking Benchmark Plan

Tarih: 2026-06-23

## Amaç

Sürücü sigara içme davranışını mevcut cabin/driver pipeline'ına güvenli şekilde
eklemek.

İlk faz final risk üretmez. Amaç:

* cigarette object candidate üretmek,
* hand-mouth temporal evidence ölçmek,
* hard-negative ayrıştırma kapasitesini test etmek,
* baseline kabul kapısını tanımlamak.

## Deney Listesi

| Experiment | Yöntem | Durum | Kabul hedefi |
|---|---|---|---|
| `SMOKING-EXP-001` | YOLO26s/YOLO26s-P2 cigarette object in mouth/hand ROI | planned | object smoke/challenger |
| `SMOKING-EXP-002` | object + hand-mouth temporal fusion | planned | behavior candidate |
| `SMOKING-EXP-003` | external smoker/cigarette model challenger | planned | domain transfer ölçümü |
| `SMOKING-EXP-004` | temporal head from reviewed segments | planned | data yeterliyse trainable |

## Metrikler

Object branch:

* frame-level detection rate,
* candidate segment hit rate,
* false-positive rate on hard negatives,
* mean/P95 latency,
* ROI coverage.

Behavior branch:

* event recall,
* event specificity,
* hard-negative specificity,
* longest sustained hand-mouth sequence,
* mouth-zone dwell rate,
* pose reliability status.

## Kabul Kapısı

Baseline ancak şu koşullarda accepted olabilir:

* `positive_smoking_sessions >= 3`
* `negative_sessions >= 5`
* `hard_negative_sessions >= 3`
* `occluded_or_tiny_cigarette_positive_sessions >= 1`
* event recall `>= 0.80`
* event specificity `>= 0.90`
* hard-negative specificity `>= 0.90`

Bu kapı geçilmezse:

* `smoking_status` metadata olarak yazılabilir,
* `smoking_confidence` yazılabilir,
* ama risk skoru yükseltilmez.

## Review CSV Taslağı

Kolonlar:

* `segment_id`
* `video`
* `session_id`
* `start_sec`
* `end_sec`
* `split`
* `final_label`
* `cigarette_visibility`
* `negative_subtype`
* `driver_visible`
* `notes`

Label değerleri:

* `smoking`
* `neutral`
* `face_touch_hard_negative`
* `drink_eat_hard_negative`
* `phone_call_hard_negative`
* `not_evaluable`
* `unknown`

`not_evaluable` eğitim ve baseline metriği dışında tutulur.

## İlk Review Sonucu

`SMOKING-EXP-000` visual review sonucunda mevcut üç videoda net sigara pozitif
bulunmadı:

* `smoking=0`
* `phone_call_hard_negative=1`
* `unknown=2`
* `not_evaluable=3`

Bu nedenle mevcut veriyle sigara detector/temporal-head eğitimi başlatılmamalıdır.
`video_2` sigara için hard-negative olarak saklanabilir.

## İlk Komut Hedefleri

Henüz script yok. Telefon tarafı pattern'i takip edilecek:

```bash
.venv-yolo/bin/python scripts/benchmarks/prepare_smoking_segment_review.py

.venv-yolo/bin/python scripts/benchmarks/run_smoking_baseline.py \
  --model <candidate.pt> \
  --roi-mode mouth_hand \
  --confidence 0.05 \
  --imgsz 960

.venv-yolo/bin/python scripts/benchmarks/train_smoking_temporal_head.py \
  --segment-labels runs/smoking_review/segment_review_v1/manual_smoking_segments_review.csv
```

## İlk Veri İhtiyacı

Mevcut üç videoda pozitif sigara yoksa model araştırması tek başına yetmez.
Ekipten en az şu veri istenmeli:

* 3 farklı sigara pozitif video/session,
* 5 sigara yok video/session,
* 3 hard-negative video/session,
* en az 1 düşük görünürlük/kısmi sigara pozitif.
