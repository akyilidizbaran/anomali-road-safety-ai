# TYPE-EXP-001 Stanford Annotation Parser Fix

Date: 2026-06-22

## Problem

`TYPE-EXP-001` Cell 5 produced:

```text
Stanford records: 0 skipped: 16185
Manual records: 0 skipped: 0
RuntimeError: No FTR type-labelled images were inferred.
```

The dataset downloaded and extracted correctly:

```text
Stanford local image count: 16185
```

The failure was caused by the initial notebook assuming a class-folder dataset layout. The Kaggle Stanford Cars archive used in this run stores images under broad folders such as `cars_train` and `cars_test`; the true class labels are in Stanford annotation metadata files.

Because the immediate parent folder was `cars_test`, every image was interpreted as source class `cars_test`, which has no valid FTR type mapping.

## Fix

The active notebook was patched so Cell 4/5 now:

1. Reads Stanford `.mat` metadata with `scipy.io.loadmat`.
2. Loads `cars_meta.mat` / `class_names`.
3. Reads annotation files such as `cars_train_annos.mat`, `cars_test_annos*.mat`, or similarly named annotation `.mat` files.
4. Resolves `class_id -> Stanford class name`.
5. Resolves annotation `fname -> actual image path`.
6. Applies the existing conservative FTR type mapping to the Stanford class name.
7. Falls back to class-folder parsing only if annotation parsing yields no records.

## Expected Next Run Behavior

After rerunning Cells 4 and 5, the notebook should no longer show `source_class=cars_test` for every image. Instead, `source_class` should look like Stanford class names, for example:

```text
Honda Accord Sedan 2012
Dodge Durango SUV 2012
Ford F-150 Regular Cab 2012
```

The first quality gate is Cell 5 class counts:

```text
Mapped images: > 0
sedan/suv/hatchback/pickup/minibus/panelvan/kamyon counts printed
```

If any FTR class is still low or missing, add images under:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/type_exp_001/manual/<ftr_label>/
```

## Notes

This fix does not loosen the FTR mapping rules. Ambiguous classes such as `coupe`, `convertible`, `roadster`, or `wagon` are still skipped rather than forced into an incorrect FTR label.

## Follow-up Fix: NumPy Array Truth-Value

After the first parser patch, Cell 5 produced a second error:

```text
ValueError: The truth value of an array with more than one element is ambiguous.
```

The root cause was a Python fallback pattern inside the `.mat` parser:

```python
mat.get("class_names") or mat.get("classNames")
```

`scipy.io.loadmat` can return NumPy arrays for these keys. NumPy arrays cannot be used directly in boolean `or` expressions when they contain more than one element.

The notebook now uses explicit `is None` checks for:

- `class_names` / `classNames`
- `annotations` / `annos` / `records`

This keeps fallback behavior but avoids NumPy truth-value ambiguity.

## Required Colab Action

Pull/reopen the updated notebook, then rerun:

1. Cell 4: mapping + Stanford annotation parser helpers
2. Cell 5: dataset metadata build

If the Colab runtime was not restarted, the previously extracted Stanford files can be reused. Dataset download should not be repeated unless the local runtime was cleared.
