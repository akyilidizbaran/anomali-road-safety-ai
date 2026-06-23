# Phone-Call Behavior Evaluation

* Baseline accepted: `False`
* Coverage gate: `False`
* Quality gate: `False`
* TP/FP/TN/FN: `{'tp': 1, 'fp': 0, 'tn': 0, 'fn': 1}`
* Precision: `1.0`
* Recall: `0.5`
* Specificity (overall): `None`
* Specificity (hard-negative): `None`
* F1: `0.6667`

## Coverage (distinct sessions)
* Positive: `2` (occluded: `2`)
* Negative: `0` (hard: `0`)
* Hard-negative subtypes: `{}`
* Pending review: `['video_3.mp4']`

## Blockers
* Coverage: `['positive_sessions=2<3', 'negative_sessions=0<5', 'hard_negative_sessions=0<2']`
* Quality: `['recall=0.5<0.8', 'specificity=None<0.9', 'hard_negative_specificity=None<0.9']`

Aday model, minimum pozitif/negatif/hard-negative/occluded-positive session
kapsami ve hem genel hem hard-negative kalite esikleri ayni anda gecilmeden
baseline olarak sabitlenmez.
