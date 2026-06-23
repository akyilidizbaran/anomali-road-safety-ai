# SEATBELT-EXP-002 Condition-Aware Classifier Challenger

Tarih: 2026-06-14T15:14:11Z

Bu deney seçilmiş baseline değildir. Raw ve lokal condition-routed driver-context ROI çıktıları karşılaştırılır. Candidate kararlar event riskine yazılmaz.

| Video | Direct ROI | Held ROI | Severe Low Light | Candidate | Mean ms | P95 ms |
|---|---:|---:|---:|---|---:|---:|
| video_2.mp4 | 267 | 52 | 319 | belted_candidate | 6.25 | 6.945 |

Model kartı gece/tinted glass/glare verisinin az ve eğitim verisinin dengesiz olduğunu belirtir. Sonuçlar manuel review ve kontrollü veri olmadan kabul edilmeyecektir.
