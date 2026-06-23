# DACT-EXP-020B Driver Action Classifier Runbook

## Amaç

`DACT-EXP-020B`, `DRIVER-EXP-001` driver presence / role-assignment gate
sonrasında çalışacak ilk sürücü eylemi sınıflandırma deneyidir. Bu fazda amaç
tek seferde tüm FTR sürücü eylemlerini kapatmak değildir. İlk savunulabilir
baseline şu sınıfları ayırır:

* `telefonla_konusma`
* `su_icme`
* `arkaya_bakma_candidate`
* `phone_use_non_call`
* `passenger_interaction_candidate`
* `other_distraction_hard_negative`
* `safe_or_no_event`

`sigara_icme`, `esneme`, `emniyet_kemeri_ihlali` ve `etrafa_bakinma` bu deneyle
kapatılmaz; ayrı uzman veri/model fazları olarak planlanır.

## Notebook

```text
notebooks/DACT_EXP_020B_Driver_Action_Classifier_Colab.ipynb
```

Varsayılan çalışma:

```python
RUN_MODE = 'quick'
```

Bu mod yavaş başlangıç içindir; yalnız MobileNetV3-Large, kısa epoch ve sınıf
başına sınırlı örnek kullanır. İlk Colab sanity run başarılı olursa ağır koşu:

```python
RUN_MODE = 'full'
```

`full` mod MobileNetV3-Large ve EfficientNet-B0 karşılaştırmasını açar ve sınıf
başına quick cap uygulamaz.

## Veri Kaynağı

Birincil veri:

```text
State Farm Distracted Driver Detection
```

Notebook önce mevcut Drive cache'i arar:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/cabin_exp_020a/state_farm/state-farm-distracted-driver-detection.zip
```

Zip yoksa sırasıyla şunları dener:

1. `chunks/state-farm-distracted-driver-detection.zip.part-*` parçalarını
   birleştirme.
2. Kaggle competition endpoint'i.
3. Tanımlı Kaggle dataset fallback slug'ları.

Image extraction Drive'a yapılmaz. Çok sayıda küçük dosya kaynaklı Drive I/O
hatalarını önlemek için eğitim görüntüleri local Colab runtime altına çıkarılır:

```text
/content/anomali-road-safety-ai-work/datasets/driver_action_exp_020b/state_farm/
```

Ek olarak, `OSError: [Errno 107] Transport endpoint is not connected` gibi
Drive FUSE kopmalarını azaltmak için notebook, 4.3 GB State Farm zip'ini
extraction öncesinde local runtime archive cache'e kopyalar:

```text
/content/anomali-road-safety-ai-work/archives/driver_action_exp_020b/state-farm-distracted-driver-detection.zip
```

Bu kopya tamamlandıktan sonra binlerce küçük image okuması Drive üzerinden değil
local disk üzerinden yapılır. Kopyalama sırasında aynı hata alınırsa Colab
runtime yeniden başlatılıp Drive `force_remount=True` ile tekrar bağlanmalıdır.

## State Farm Sınıf Eşlemesi

| State Farm | İç Etiket | FTR Kararı |
|---|---|---|
| `c0 safe driving` | `safe_or_no_event` | event üretmez |
| `c1 texting - right` | `phone_use_non_call` | telefon var ama `telefonla_konusma` değil |
| `c2 talking on the phone - right` | `telefonla_konusma` | FTR adayı |
| `c3 texting - left` | `phone_use_non_call` | telefon var ama `telefonla_konusma` değil |
| `c4 talking on the phone - left` | `telefonla_konusma` | FTR adayı |
| `c5 operating the radio` | `other_distraction_hard_negative` | hard negative |
| `c6 drinking` | `su_icme` | FTR adayı |
| `c7 reaching behind` | `arkaya_bakma_candidate` | weak candidate |
| `c8 hair and makeup` | `other_distraction_hard_negative` | hard negative |
| `c9 talking to passenger` | `passenger_interaction_candidate` | FTR dışı candidate |

`arkaya_bakma_candidate`, yalnız bu classifier çıktısıyla final `arkaya_bakma`
sayılmaz. Runtime'da head/torso yönü veya temporal gate ile desteklenmelidir.

## Çıktılar

Notebook aşağıdaki kalıcı çıktıları Drive'a yazar:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/cabin_driver/DACT-EXP-020B/
/content/drive/MyDrive/anomali-road-safety-ai/models/benchmarks/artifacts/cabin_driver/DACT-EXP-020B/
/content/drive/MyDrive/anomali-road-safety-ai/testing/reports/dact_exp_020b_driver_action_classifier.md
```

Beklenen temel artefactler:

* En iyi checkpoint: `DACT-EXP-020B-<backbone>-best.pth`
* Label map: `DACT-EXP-020B-label-map.json`
* Split metadata: `dact_exp_020b_metadata_<run_mode>.csv`
* Classification report CSV
* Confusion matrix CSV/PNG
* Sample predictions PNG
* Summary JSON

## Başarı Kriteri

İlk quick run için başarı kriteri yalnız pipeline sağlığıdır:

* State Farm zip/cache bulunur veya indirilebilir.
* Subject/driver group leakage kontrolü geçer.
* Train/val/test split boş kalmaz.
* Test classification report ve confusion matrix üretilir.
* `telefonla_konusma` ve `su_icme` sınıflarında gözle görülür recall oluşur.

Full run sonrası rapora yazılabilir baseline için:

* `telefonla_konusma` ve `su_icme` per-class F1 değerleri ayrıca raporlanır.
* `phone_use_non_call` ile `telefonla_konusma` karışımı confusion matrix'te
  incelenir.
* `arkaya_bakma_candidate` weak-label olduğu açıkça belirtilir.
* Bu model tek-frame classifier olduğu için runtime'da temporal voting/gate
  gerektirdiği not edilir.

## Sonraki Adım

Notebook çıktısı alındıktan sonra output-saved `.ipynb` repo içine konur ve şu
kontroller yapılır:

1. Per-class metrikler okunur.
2. Confusion matrix telefon/texting ayrımında incelenir.
3. En iyi checkpoint Drive path'i rapora ve `PROJECT_MEMORY.md` dosyasına yazılır.
4. Gerekirse `DACT-EXP-020C` temporal voting + driver crop smoke inference fazı
   açılır.
