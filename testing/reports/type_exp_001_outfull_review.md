# TYPE-EXP-001 Outfull Run Review

Date: 2026-06-22

Notebook reviewed:

```text
notebooks/Outputs Saved/TYPE_EXP_001_FTR_Vehicle_Type_Classifier_Colab_outfull.ipynb
```

## Executive Decision

The run completed technically, but it should **not** be promoted as the final FTR vehicle type
classifier yet.

Reasons:

1. `kamyon` has `0` mapped examples, so the model cannot learn or evaluate that FTR class.
2. Target ROI smoke inference was skipped because no target ROI crop directory was found in the
   Colab runtime.
3. The Stanford mapping had label-noise risk: broad substring matching allowed `van` to match
   `Vantage`, causing coupe/convertible examples to be mapped as `panelvan`.
4. Test macro-F1 is moderate, not final-quality: `0.6120`.

## Run Health

The notebook ran end-to-end:

- Runtime: Colab L4 GPU
- Smoke mode: `False`
- Epoch target: `18`
- Dataset source: Stanford Cars Kaggle archive
- Manual FTR folder: empty / skipped
- Best backbone: `efficientnet_b0`
- Best checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/vehicle_type/TYPE-EXP-001-efficientnet_b0-best.pth
```

## Dataset Mapping

The Stanford annotation parser worked after the previous fixes.

| Item | Count |
|---|---:|
| Stanford local images | 16185 |
| Stanford mapped records | 5687 |
| Stanford skipped records | 2457 |
| Manual records | 0 |

Mapped FTR class counts:

| FTR type | Count |
|---|---:|
| `sedan` | 2148 |
| `suv` | 1477 |
| `hatchback` | 674 |
| `pickup` | 761 |
| `minibus` | 289 |
| `panelvan` | 338 |
| `kamyon` | 0 |

The missing `kamyon` class is a blocker for full FTR promotion.

## Split

Group split was correctly done by `source_class`, which reduces leakage compared with random
image-level splitting.

| Split | Count |
|---|---:|
| train | 3956 |
| validation | 850 |
| test | 881 |

However, `kamyon` remains `0` in all splits.

## Training Summary

Two backbones were compared:

| Backbone | Best val macro-F1 | Best epoch |
|---|---:|---:|
| `efficientnet_b0` | 0.5414 | 8 |
| `mobilenet_v3_large` | 0.4592 | 7 |

`efficientnet_b0` was correctly selected as the best backbone.

## Test Performance

Overall test metrics:

| Metric | Value |
|---|---:|
| Test accuracy | 0.6595 |
| Test macro-F1 | 0.6120 |

Per-class test F1:

| FTR type | F1 | Support | Comment |
|---|---:|---:|---|
| `pickup` | 0.9786 | 164 | Strong |
| `sedan` | 0.6723 | 259 | Usable but not final |
| `suv` | 0.6465 | 126 | Usable but not final |
| `panelvan` | 0.4800 | 40 | Weak and label-noise sensitive |
| `hatchback` | 0.4713 | 207 | Weak |
| `minibus` | 0.4234 | 85 | Weak |
| `kamyon` | 0.0000 | 0 | Not trained/evaluated |

This is enough to prove the pipeline works, but not enough to lock the final vehicle type model.

## Label Mapping Issue Found

The outfull run revealed a serious mapping issue in the source notebook:

```text
Aston Martin V8 Vantage Convertible 2012 -> panelvan
Aston Martin V8 Vantage Coupe 2012 -> panelvan
```

Root cause:

```python
if needle in norm
```

This allowed the rule token `van` to match the substring `van` inside `vantage`.

The active notebook has been patched after this review:

- single-token rules now require token-boundary matching,
- multi-token rules are matched as underscore-delimited phrases,
- `Ford E-Series Wagon Van 2012` is preserved through an explicit override,
- coupe/convertible examples such as `Vantage` are skipped instead of mislabeled.

Expected corrected examples:

| Source class | Corrected mapping |
|---|---|
| `Aston Martin V8 Vantage Convertible 2012` | skipped: `unsupported_body_style:convertible` |
| `Aston Martin V8 Vantage Coupe 2012` | skipped: `unsupported_body_style:coupe` |
| `Ford E-Series Wagon Van 2012` | `panelvan` via override |
| `GMC Savana Van 2012` | `panelvan` |
| `Freightliner Box Truck` | `kamyon` |

## Target ROI Smoke Test

Cell 13 output:

```text
No existing target ROI crop directory found. Smoke inference skipped.
```

This means the checkpoint has not yet been validated on our actual target vehicle crops from
`Test/video_1-3.mp4`.

Runtime promotion requires this smoke/manual review step.

## Required Next Run

Rerun the active notebook after the mapper patch:

1. Cell 4: config
2. Cell 5: data download/extract
3. Cell 6: mapping helpers
4. Cell 7: metadata build
5. Cell 8: split
6. Training/evaluation cells

Expected changes:

- Fewer noisy `panelvan` records.
- Possibly lower but cleaner mapped count.
- `kamyon` may still remain missing unless a truck source is added.

## Final Recommendation

Do not lock `TYPE-EXP-001` yet.

Proceed as follows:

1. Rerun the patched notebook to remove label noise.
2. Add manual or external data for `kamyon`.
3. Add target ROI crop smoke inference path in Colab or run local smoke inference after checkpoint download.
4. Promote only if class-level metrics and manual target ROI outputs are acceptable.
