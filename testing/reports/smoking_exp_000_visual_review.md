# SMOKING-EXP-000 Visual Review

Tarih: 2026-06-23

## Sonuç

Mevcut `Test/video_1-3.mp4` review setinde net sigara pozitif bulunmadı.

| Label | Segment |
|---|---:|
| `smoking` | 0 |
| `phone_call_hard_negative` | 1 |
| `unknown` | 2 |
| `not_evaluable` | 3 |

## Segment Kararları

| Segment | Karar | Gerekçe |
|---|---|---|
| `video_1_mouth_hand_candidate_01` | `unknown` | Sigara seçilemiyor; driver/mouth region çok küçük ve belirsiz. Negatif sayılmadı. |
| `video_1_mouth_hand_candidate_02` | `not_evaluable` | Araç/sürücü kadrajdan çıkmış; pose ROI stale. |
| `video_2_mouth_hand_candidate_01` | `phone_call_hard_negative` | Bilinen telefonla konuşma segmenti; sigara görünmüyor. |
| `video_2_mouth_hand_candidate_02` | `not_evaluable` | Araç/sürücü kadrajdan çıkmış. |
| `video_3_mouth_hand_candidate_01` | `unknown` | Sigara seçilemiyor; uzak/düşük ışık. Negatif sayılmadı. |
| `video_3_mouth_hand_candidate_02` | `not_evaluable` | Araç/sürücü kadrajdan çıkmış. |

## Karar

Bu review sonucuyla sigara modeli eğitimi veya final baseline değerlendirmesi
başlatılamaz.

Blocker:

* `positive_smoking_sessions=0<3`
* `negative_sessions=0<5`
* `hard_negative_sessions=1<3`
* trainable smoking pozitif segment yok

## Sıradaki Teknik Adım

1. Ekipten pozitif sigara içme videosu/session istenmeli.
2. Mevcut `video_2` sigara için `phone_call_hard_negative` olarak saklanmalı.
3. Hazır cigarette detector challenger denenirse yalnız false-positive smoke testi
   olarak raporlanmalı; pozitif recall metriği üretilemez.
