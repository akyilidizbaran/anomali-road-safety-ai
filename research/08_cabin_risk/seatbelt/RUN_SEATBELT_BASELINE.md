# Seatbelt Baseline Çalıştırma

```bash
source .venv-yolo/bin/activate

python -m pytest \
  testing/test_seatbelt_utils.py \
  testing/test_seatbelt_event_enrichment.py -q

python scripts/benchmarks/run_seatbelt_baseline.py
python scripts/benchmarks/enrich_event_skeleton_with_seatbelt.py
```

Condition-aware ROI smoke testi, model indirmeden:

```bash
python scripts/benchmarks/run_seatbelt_classifier_challenger.py \
  --extract-only \
  --videos Test/video_2.mp4 \
  --frame-stride 10
```

Pretrained classifier challenger:

```bash
python scripts/benchmarks/run_seatbelt_classifier_challenger.py \
  --videos Test/video_2.mp4
```

İlk model koşusu Hugging Face'ten yaklaşık 11 MB `best.pt` indirir. Model kartı
AGPL-3.0 lisanslıdır ve gece/tinted-glass verisinin az olduğunu belirtir.

Tek video smoke testi:

```bash
python scripts/benchmarks/run_seatbelt_baseline.py \
  --videos Test/video_3.mp4
```

Varsayılan enrichment yalnız candidate metadata ekler ve
`seatbelt_status=unknown` bırakır. `--accept-decisions`, ancak etiketli benchmark
ve manuel review sonrasında kullanılmalıdır.

Çıktılar:

* `models/benchmarks/artifacts/SEATBELT-EXP-001-opencv_diagonal_belt_evidence_v1-summary.json`
* `testing/reports/seatbelt_exp_001_summary.md`
* `testing/templates/manual_seatbelt_review.csv`
* `runs/seatbelt/seatbelt_exp_001/`
* `models/benchmarks/artifacts/SEATBELT-EXP-002-*-summary.json`
* `runs/seatbelt/seatbelt_exp_002/`
