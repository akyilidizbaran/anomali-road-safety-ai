# COND-EXP-001 Fine-Tuned Condition Classifier Review

## Amaç

Bu rapor, `notebooks/COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab_finetuned_out.ipynb` çıktısını ve Drive'dan alınan seçili checkpoint ile yapılan local smoke test sonucunu değerlendirir.

Bu deney araç tespiti modeli değildir. Görevi canlı frame için `condition_profile` üretmek ve ileride condition-aware detector routing kararına bağlam sinyali sağlamaktır.

## İncelenen Kaynaklar

| Kaynak | Durum |
|---|---|
| Colab çıktı notebook'u | `notebooks/COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab_finetuned_out.ipynb` |
| Drive run root | `/content/drive/MyDrive/anomali-road-safety-ai/runs/condition_profile/COND-EXP-001/` |
| Seçili Drive checkpoint | `/content/drive/MyDrive/anomali-road-safety-ai/runs/condition_profile/COND-EXP-001/train/COND-EXP-001-mobilenet_v3_small/best.pt` |
| Lokal checkpoint | `models/checkpoints/condition_profile/COND-EXP-001-mobilenet_v3_small-best.pt` |
| Lokal smoke summary | `models/benchmarks/artifacts/COND-EXP-001-local-dark-video-smoke-summary.json` |
| Lokal smoke raporu | `testing/reports/cond_exp_001_local_dark_video_smoke_test.md` |

Notebook çıktılarında Python error hücresi görülmedi.

## Eğitim Gerçekten Yapıldı mı?

Evet. Notebook yalnız eski checkpoint'i raporlamadı; iki backbone için Colab GPU üzerinde gerçek fine-tune koşusu yaptı.

Kanıtlar:

* `RUN_MOBILENETV3_SMALL=True` ve `RUN_RESNET18=True` aktifti.
* `device: cuda` ile eğitim çalıştı.
* MobileNetV3-Small ve ResNet18 için ayrı `best.pt`, `history.csv` ve `summary.json` çıktıları üretildi.
* Her iki modelde de en iyi checkpoint validation macro-F1'a göre kaydedildi.
* Backbone karşılaştırması `best_val_macro_f1` ile yapıldı; test seti model seçimi için kullanılmadı.

Bu seçim protokolü doğru: test seti yalnız final raporlama için ayrılmalı, model seçimi validation metriğiyle yapılmalıdır.

## Veri Hazırlama ve Sınıf Kapsamı

Notebook önceki koşudaki duplicate riskini temizledi:

```text
Found existing condition metadata: (160000, 8)
Dropped duplicate condition metadata rows: 80000
Persisted deduplicated condition metadata: (80000, 8)
```

Deduplicate sonrası condition dağılımı:

| Condition profile | Örnek sayısı |
|---|---:|
| `night_low_light` | 29388 |
| `day_clear` | 27747 |
| `adverse_other` | 11488 |
| `rain` | 5821 |
| `low_light_transition` | 5411 |
| `fog_low_visibility` | 143 |
| `unknown` | 2 |

Split dağılımı:

| Split | Satır |
|---|---:|
| train | 25636 |
| val | 1859 |
| test | 1880 |

Sınıf bazlı test support değerleri:

| Sınıf | Test support | Değerlendirme |
|---|---:|---|
| `day_clear` | 412 | Yeterli ilk baseline |
| `night_low_light` | 351 | Yeterli ilk baseline |
| `low_light_transition` | 364 | Yeterli ilk baseline |
| `rain` | 363 | Yeterli ilk baseline |
| `adverse_other` | 385 | Yeterli ama heterojen sınıf |
| `fog_low_visibility` | 5 | Yetersiz |

`unknown` sınıfı label sözleşmesinde kalabilir, ancak bu koşuda yalnız 2 örnek olduğu için etkin şekilde eğitilmiş bir sınıf değildir. Runtime'da fallback etiketi gibi ele alınmalıdır.

## Backbone Karşılaştırması

| Backbone | Best epoch | Best val macro-F1 | Test accuracy | Test macro-F1 | Test weighted-F1 | Karar |
|---|---:|---:|---:|---:|---:|---|
| MobileNetV3-Small | 3 | 0.6823 | 0.7644 | 0.6388 | 0.7625 | Seçildi |
| ResNet18 | 3 | 0.6668 | 0.7559 | 0.6600 | 0.7544 | Challenger |

MobileNetV3-Small validation macro-F1'daki üstünlüğü ve daha hafif runtime profili nedeniyle seçildi. ResNet18 test macro-F1 değeri biraz daha yüksek görünse de test setiyle model seçimi yapılmamalıdır; bu yüzden seçili modelin MobileNetV3-Small kalması doğrudur.

## Sınıf Bazlı Sonuçlar

MobileNetV3-Small:

| Sınıf | Precision | Recall | F1 | Support | Yorum |
|---|---:|---:|---:|---:|---|
| `day_clear` | 0.7383 | 0.7257 | 0.7319 | 412 | Kullanılabilir |
| `night_low_light` | 0.8198 | 0.9459 | 0.8783 | 351 | Güçlü |
| `low_light_transition` | 0.6566 | 0.7775 | 0.7119 | 364 | Kullanılabilir |
| `rain` | 0.8662 | 0.7135 | 0.7825 | 363 | Kullanılabilir |
| `fog_low_visibility` | 0.0000 | 0.0000 | 0.0000 | 5 | Başarısız / veri yetersiz |
| `adverse_other` | 0.7765 | 0.6857 | 0.7283 | 385 | Kullanılabilir ama heterojen |

ResNet18:

| Sınıf | Precision | Recall | F1 | Support | Yorum |
|---|---:|---:|---:|---:|---|
| `day_clear` | 0.7823 | 0.6019 | 0.6804 | 412 | Kullanılabilir |
| `night_low_light` | 0.8431 | 0.9031 | 0.8721 | 351 | Güçlü |
| `low_light_transition` | 0.6555 | 0.7527 | 0.7008 | 364 | Kullanılabilir |
| `rain` | 0.8114 | 0.7466 | 0.7776 | 363 | Kullanılabilir |
| `fog_low_visibility` | 0.1429 | 0.2000 | 0.1667 | 5 | Yetersiz |
| `adverse_other` | 0.7243 | 0.8052 | 0.7626 | 385 | Kullanılabilir |

## Local Dark Video Smoke Test

Colab koşusunda Drive altında `Test/` klasörü bulunmadığı için dark-video smoke test boş kalmıştı. Seçili Drive checkpoint lokal makineye alındı ve `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4` üzerinde tekrar çalıştırıldı.

Komut:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_condition_profile_video_smoke.py
```

Sonuç:

| Video | Örneklenen frame | Baskın profil | Baskın confidence | Ortalama confidence | Router kararı |
|---|---:|---|---:|---:|---|
| `video_1.mp4` | 28 | `night_low_light` | 0.769 | 0.769 | General fallback |
| `video_2.mp4` | 30 | `night_low_light` | 0.743 | 0.729 | General fallback |
| `video_3.mp4` | 25 | `night_low_light` | 0.723 | 0.708 | General fallback |

Bu sonuç, mevcut 3 dark video için beklenen davranışla uyumludur. Ancak bu ölçüm ground-truth accuracy değildir; yalnız qualitative smoke test ve pipeline usability kanıtıdır.

Manuel görsel kontrol için Git'e eklenmeyen contact sheet çıktıları üretildi:

```text
runs/condition_profile/COND-EXP-001-local-dark-video-smoke/previews/video_1_condition_contact_sheet.jpg
runs/condition_profile/COND-EXP-001-local-dark-video-smoke/previews/video_2_condition_contact_sheet.jpg
runs/condition_profile/COND-EXP-001-local-dark-video-smoke/previews/video_3_condition_contact_sheet.jpg
```

## İstediğimiz Condition Profilleri Gözlemlendi mi?

Kısmen evet.

Gözlemlenebilir ve raporlanabilir profiller:

* `night_low_light`: Güçlü performans ve local dark video uyumu var.
* `rain`: İlk baseline için yeterli sınıf performansı var.
* `day_clear`: İlk baseline için yeterli sınıf performansı var.
* `low_light_transition`: Kullanılabilir ama `night_low_light` ve `day_clear` ile geçiş hataları beklenebilir.
* `adverse_other`: Heterojen bir sınıf olduğu için karar sinyali olarak dikkatli kullanılmalı.

Gözlemlenmiş ama yeterli olmayan profil:

* `fog_low_visibility`: Bu koşuda model güvenilir değildir. Test support yalnız 5 ve MobileNetV3-Small F1 değeri 0.0'dır.

Eğitilmemiş/fallback profil:

* `unknown`: Sözleşmede bulunur, fakat bu koşuda öğrenilmiş sınıf olarak yorumlanmamalıdır.

## Tekrar Run Gerekli mi?

Genel condition router baseline için tekrar full run gerekli değil. Bu koşu, MobileNetV3-Small tabanlı ilk condition classifier'ın çalıştığını ve local dark videolarda beklenen profili ürettiğini kanıtlamak için yeterlidir.

Tekrar run gerektiren durumlar:

1. `fog_low_visibility` için raporda güçlü iddia kurulacaksa ACDC/DAWN/Foggy tabanlı ek veriyle yeni koşu gerekir.
2. ONNX/TorchScript deployment çıktısı istenecekse export açık yeni bir kısa run veya checkpoint export hücresi çalıştırılmalıdır.
3. Drive tabanlı dark-video smoke test'in Colab raporunda dolu görünmesi isteniyorsa Drive'a `Test/video_1-3.mp4` konup smoke hücresi tekrar çalıştırılmalıdır.
4. Threshold calibration veya temporal smoothing iddiası kurulacaksa ayrı validation/smoke koşusu gerekir.

Tekrar run gerektirmeyen durum:

* MobileNetV3-Small ile `night_low_light`, `rain`, `day_clear`, `low_light_transition`, `adverse_other` için ilk router baseline'ı raporlamak.

## FTR / Rapor Şablonu Açısından Durum

Bu run, FTR içinde "Kondisyon Profili ve Saptanması" başlığına şu bilgileri sağlamak için yeterlidir:

* Kullanılan veri kaynağı: BDD100K image attributes.
* Etiket üretim mantığı: `weather`, `timeofday`, `scene` alanlarından condition profile mapping.
* Model: ImageNet-pretrained MobileNetV3-Small, ResNet18 challenger.
* Eğitim ortamı: Colab GPU.
* Değerlendirme: accuracy, macro-F1, weighted-F1, per-class precision/recall/F1.
* Runtime rolü: detector seçimi için karar verici değil, routing sinyali üreten lightweight classifier.
* Demo smoke: 3 dark video üzerinde `night_low_light` baskınlığı.

Şu iddialar için yeterli değildir:

* Sisli ortamları güvenilir sınıflandırır.
* Her koşulu yüksek doğrulukla ayırır.
* Kondisyon router doğrudan specialist detector'ı otomatik terfi ettirir.
* Bu classifier tek başına risk kararı verir.

## Nihai Karar

`COND-EXP-001` tamamlanmış bir ilk condition classifier/router baseline olarak kabul edilebilir.

Aktif checkpoint:

```text
models/checkpoints/condition_profile/COND-EXP-001-mobilenet_v3_small-best.pt
```

Drive kaynak checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/condition_profile/COND-EXP-001/train/COND-EXP-001-mobilenet_v3_small/best.pt
```

Bu model şu anda specialist detector'ı otomatik aktif etmeyecek; `condition_profile`, `condition_confidence` ve temporal stability sinyali üretip general detector fallback ile çalışacaktır. Specialist detector terfisi yalnız ilgili specialist modelin general modele göre condition-specific benchmark üstünlüğü kanıtlandıktan sonra açılmalıdır.

## Sonraki Aksiyon

1. Condition classifier çıktısını vehicle detection smoke script'ine bağla.
2. 3 test videosunda frame/window bazlı `condition_profile` + vehicle detection sonuçlarını aynı JSON raporunda üret.
3. Router kararını şimdilik `general fallback` tut.
4. Fog için güçlü iddia gerekiyorsa ACDC/DAWN/Foggy veri araştırma ve yeni koşu aç.
5. FTR metninde `fog_low_visibility` sınırlılığı ve `unknown` fallback karakteri açıkça yaz.
