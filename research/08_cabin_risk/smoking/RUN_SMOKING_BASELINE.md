# RUN Smoking Baseline / Challenger

Tarih: 2026-06-23

Bu dosya kısmen uygulanmıştır. İlk review pack scripti hazır:

* `scripts/benchmarks/prepare_smoking_segment_review.py`

## 1. İlk Manuel Kontrol

Önce mevcut test videolarında sigara pozitif var mı kontrol edilir:

```bash
ls Test/*.mp4
```

Eğer pozitif sigara görünmüyorsa mevcut videolar sadece negative/hard-negative
olarak kullanılabilir.

## 2. Review Pack

Telefon tarafındaki yaklaşımın sigara versiyonu:

```bash
.venv-yolo/bin/python scripts/benchmarks/prepare_smoking_segment_review.py
```

Üretilecek beklenen dosyalar:

* `runs/smoking_review/segment_review_v1/manual_smoking_segments_review.csv`
* `runs/smoking_review/segment_review_v1/clips/`
* `runs/smoking_review/segment_review_v1/contact_sheets/`
* `models/benchmarks/artifacts/smoking/SMOKING-EXP-000-segment_review_pack.json`

23 Haziran 2026 koşusunda 3 video için toplam 6 mouth/hand review segmenti
üretildi.

## 3. Object Challenger

Hazır veya fine-tune edilmiş cigarette detector:

```bash
.venv-yolo/bin/python scripts/benchmarks/run_smoking_baseline.py \
  --model <model.pt> \
  --model-key <model_key> \
  --class-name cigarette \
  --roi-mode mouth_hand \
  --confidence 0.05 \
  --imgsz 960
```

İlk smoke/challenger sonuçları:

* `models/benchmarks/cabin/smoking_baseline_comparison.csv`
* `models/benchmarks/artifacts/SMOKING-EXP-001-<model_key>-summary.json`
* `testing/reports/smoking_exp_001_summary.md`
* `runs/smoking/smoking_exp_001/annotated/`

## 4. Temporal Behavior

Reviewed segment label dosyası dolduktan sonra:

```bash
.venv-yolo/bin/python scripts/benchmarks/train_smoking_temporal_head.py \
  --segment-labels runs/smoking_review/segment_review_v1/manual_smoking_segments_review.csv
```

Script en az iki sınıf ve yeterli session coverage yoksa eğitim üretse bile
`baseline_eligible=false` yazmalıdır.

## 5. Risk Contract

Kabul seti geçilene kadar:

* `smoking_status` yazılabilir,
* `smoking_confidence` yazılabilir,
* `smoking_risk` veya ana event risk artışı kapalı kalır.
