# PHONE-CALL-EXP-002 Summary

Telefon nesnesi ve zamansal el-kulak davranis kanitini ayri tutar.
Telefon kutusunun yoklugu davranis adayini veto etmez.

| Video | Object | Call status | Pose | Confidence | Hand-ear rate | Longest | Side |
|---|---:|---|---|---:|---:|---:|---|
| video_1.mp4 | False | candidate | usable_borderline | 0.898 | 0.8556 | 1.08s | right |
| video_2.mp4 | True | handheld_call_likely | decision_usable | 1.0 | 0.9474 | 3.6s | right |
| video_3.mp4 | False | candidate | usable_borderline | 0.7654 | 0.4552 | 0.2s | left |

Risk kapali tutulmustur. Yuz kasima, gozluk/sac duzeltme, yanaga
dayanma ve benzeri hard-negative review tamamlanmadan phone_risk uretilmez.
