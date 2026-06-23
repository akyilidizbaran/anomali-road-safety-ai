# DACT-EXP-020B Full Run Review

Tarih: 2026-06-24

## Karar

`DACT-EXP-020B`, State Farm subject-disjoint benchmark üzerinde ilk driver-action
classifier baseline olarak kilitlenebilir.

Bu karar şu sınırlamayla geçerlidir:

* Model tek başına final runtime `sofor_eylemi` kararı değildir.
* `DRIVER-EXP-001` driver presence / role-assignment gate sonrası çalışmalıdır.
* Runtime event üretimi için temporal persistence/confidence gate uygulanmalıdır.
* `arkaya_bakma_candidate`, final `arkaya_bakma` değildir; head/torso yönü ile
  desteklenmelidir.
* `sigara_icme`, `esneme`, `emniyet_kemeri_ihlali` ve `etrafa_bakinma` ayrı
  specialist fazları olarak kalır.

## Girdi ve Veri Sağlığı

Notebook:

```text
DACT_EXP_020B_Driver_Action_Classifier_Colab_outfull.ipynb
```

Run mode:

```text
RUN_MODE = full
```

Veri:

```text
State Farm Distracted Driver Detection
```

Sağlık kontrolleri:

| Kontrol | Sonuç |
|---|---:|
| Raw records | 22,424 |
| Usable records | 22,424 |
| Missing images | 0 |
| Subjects | 26 |
| Train subjects | 18 |
| Val subjects | 4 |
| Test subjects | 4 |
| Subject leakage check | Passed |

Split dağılımı:

| Split | safe | telefon | phone_non_call | su | arkaya_candidate | passenger | hard_negative |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 1,787 | 3,219 | 3,224 | 1,627 | 1,407 | 1,477 | 2,961 |
| val | 369 | 701 | 699 | 335 | 301 | 339 | 631 |
| test | 333 | 723 | 690 | 363 | 294 | 313 | 631 |

## Backbone Karşılaştırması

| Backbone | Best val macro-F1 | Best epoch | Karar |
|---|---:|---:|---|
| MobileNetV3-Large | 0.8462 | 10 | Challenger |
| EfficientNet-B0 | 0.9227 | 11 | Seçilen baseline |

Aktif checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/cabin_driver/DACT-EXP-020B/DACT-EXP-020B-efficientnet_b0-best.pth
```

Label map:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/cabin_driver/DACT-EXP-020B/DACT-EXP-020B-label-map.json
```

## Test Metrikleri

| Metrik | Değer |
|---|---:|
| Accuracy | 0.9017 |
| Macro-F1 | 0.8658 |
| Weighted-F1 | 0.8962 |
| Test support | 3,347 |

Per-class test metrikleri:

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `safe_or_no_event` | 0.6903 | 0.9369 | 0.7949 | 333 |
| `telefonla_konusma` | 0.9743 | 0.9972 | 0.9856 | 723 |
| `phone_use_non_call` | 0.9438 | 0.9986 | 0.9704 | 690 |
| `su_icme` | 0.9545 | 0.9256 | 0.9399 | 363 |
| `arkaya_bakma_candidate` | 1.0000 | 0.7619 | 0.8649 | 294 |
| `passenger_interaction_candidate` | 0.8735 | 0.4633 | 0.6054 | 313 |
| `other_distraction_hard_negative` | 0.8653 | 0.9366 | 0.8995 | 631 |

## Quick Run'a Göre Değişim

| Alan | Quick | Full | Yorum |
|---|---:|---:|---|
| Test accuracy | 0.5924 | 0.9017 | Büyük iyileşme |
| Test macro-F1 | 0.5921 | 0.8658 | Büyük iyileşme |
| `telefonla_konusma` F1 | 0.6014 | 0.9856 | Kilitlenebilir |
| `su_icme` F1 | 0.7385 | 0.9399 | Kilitlenebilir |
| `arkaya_bakma_candidate` F1 | 0.7353 | 0.8649 | Candidate olarak kullanılabilir |
| `safe_or_no_event` F1 | 0.4074 | 0.7949 | Belirgin toparlandı |
| `passenger_interaction_candidate` F1 | 0.2751 | 0.6054 | Hala final etiket değildir |
| `other_distraction_hard_negative` F1 | 0.5120 | 0.8995 | Belirgin toparlandı |

## Raporlanabilir Yorum

Bu run, State Farm tabanlı sürücü eylemi sınıflandırma modülünün özellikle
`telefonla_konusma` ve `su_icme` için güçlü bir başlangıç baseline'ı ürettiğini
gösterir. `phone_use_non_call` sınıfının ayrı tutulması, texting/phone-use ile
gerçek `telefonla_konusma` iddiasını karıştırmamak açısından doğru bir tasarım
kararıdır.

`arkaya_bakma_candidate`, `c7 reaching behind` sınıfından geldiği için yalnız
aday sinyaldir. Final `arkaya_bakma` için head/torso orientation veya temporal
driver-pose gate gereklidir.

## Teknik Notlar

Full run sırasında `torch.utils.data.DataLoader` cleanup kaynaklı
`can only test a child process` uyarıları görüldü. Bunlar notebook'u düşürmedi,
checkpoint/metrik üretimini bozmadı ve fatal error olarak değerlendirilmedi.
Aktif notebook'ta sonraki run'lar için `NUM_WORKERS=0` yapıldı.

## Çıktılar

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/cabin_driver/DACT-EXP-020B/dact-exp-020b_summary_full.json
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/cabin_driver/DACT-EXP-020B/dact-exp-020b_backbone_summary_full.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/cabin_driver/DACT-EXP-020B/dact-exp-020b_classification_report_full.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/cabin_driver/DACT-EXP-020B/dact-exp-020b_confusion_matrix_full.csv
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/cabin_driver/DACT-EXP-020B/dact-exp-020b_test_predictions_full.csv
/content/drive/MyDrive/anomali-road-safety-ai/testing/reports/dact_exp_020b_driver_action_classifier.md
```

Repo içi kanıt notebook:

```text
notebooks/Outputs Saved/DACT_EXP_020B_Driver_Action_Classifier_Colab_outfull.ipynb
```

## Sonraki Adım

`DACT-EXP-020C` açılmalıdır:

1. `DRIVER-EXP-001` ile driver-visible target event seç.
2. Driver/cabin crop penceresi çıkar.
3. `DACT-EXP-020B-efficientnet_b0-best.pth` ile frame-level action score üret.
4. Track/event seviyesinde temporal voting uygula.
5. `telefonla_konusma` ve `su_icme` için confidence/persistence gate belirle.
6. `driver_action` alanını event/evidence JSON'a ekle.

Bu adımdan sonra modelin 3 demo video üzerinde ne ürettiği görsel ve JSON
olarak incelenebilir.
