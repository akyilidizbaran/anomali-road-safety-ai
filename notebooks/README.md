# Colab Notebooks

Bu klasör, Anomali Road Safety AI model deneylerini Google Colab üzerinde tekrar üretilebilir şekilde çalıştırmak için notebook skeleton'larını içerir.

## Aktif Notebooklar

* `VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`: BDD100K indirme, Drive yerleşimi, YOLO dönüşümü, pretrained baseline validation, fine-tune, challenger model testleri, condition breakdown ve baseline-delta karşılaştırmasını tek notebook içinde yürütür.
* `VD_EXP_006_MOTORCYCLE_FOCUS_YOLO11n_Colab.ipynb`: `VD-EXP-002` general checkpoint'inden devam ederek BDD100K üzerinde motorcycle-focused sampling ile genel motorcycle/car ayrımını iyileştirmeyi hedefler. `Test/video_1-3.mp4` yalnız smoke/failure-case kontrolüdür; eğitim hedefi bu üç videoya overfit etmek değildir. Notebook tek başına çalışabilmesi için başta gömülü `VD-EXP-002 Local Dataset Bootstrap` hücreleri içerir; bu bölüm Drive arşiv/cache kaynaklarından local `/content/anomali-road-safety-ai-work/datasets/bdd100k_vehicle_yolo/profiles/general/data.yaml` üretir ve eğitim başlatmaz. Checkpoint için hem `VD-EXP-002/train/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt` hem alternatif Drive path'leri denenir. Drive'daki boş `bdd100k_vehicle_yolo/images/all` ve `labels/all` klasörleri kaynak olarak kullanılmaz. Local metadata yoksa profile listeleri + YOLO label dosyalarından `bdd100k_vehicle_metadata_rebuilt_from_profile_lists.csv` üretir; bu fallback'te `condition_profile=unknown` olur ve `night_low_light` slice boşsa evaluation adımı skip edilir.
* `COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab.ipynb`: BDD100K `weather/timeofday/scene` metadata'sından condition label üretir, MobileNetV3-Small ve ResNet18 condition classifier backbone'larını aynı ağır comparison run içinde eğitir, en iyi backbone'u validation macro-F1 ile seçer ve dark video condition smoke test'i destekler.
* `POCR_EXP_005_YOLO11N_Plate_Detector_Colab.ipynb`: Turkish Number Plates + Roboflow LPR veri setlerini Roboflow API veya manual zip fallback ile indirir, class-normalized/dedup edilmiş tek sınıf `license_plate` YOLO dataset'i üretir, YOLO11n plate detector fine-tune eder, mevcut `license_plate_detector.pt` baseline ile karşılaştırır ve UFPR-ALPR izinli zip varsa external benchmark çalıştırır. Ağır işlem local `/content/anomali-road-safety-ai-work/` altında yapılır; kalıcı checkpoint/metric/report çıktıları Drive'a yazılır.
* `VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab.ipynb`: BoxCars116k üzerinden araç crop'ları için vehicle attribute / dimension prior classifier kurar. İlk amaç marka-modeli kesin kanıt yapmak değil, `Speed Fusion Layer` için `body_type`, yaklaşık `wheelbase` ön bilgisi ve güven skoru üretmektir. Varsayılan smoke mode küçük subset ile çalışır; ağır run için `SMOKE_MODE=False`, daha fazla epoch ve ek backbone açılır.
* `SPEED_EXP_006_VS13_Known_Speed_Calibration_Colab.ipynb`: VS13 bilinen hızlı araç videolarını doğrudan resmi linklerden Colab/Drive cache'e indirir, küçük subset çıkarır, video dosya adındaki hız suffix'inden ground-truth km/s okur, YOLO + ByteTrack ile ana araç track'i üretir, bbox-geometry hız adayını hesaplar ve train/val/test split üzerinde global scale/FOV/vehicle-height/moving-average parametre optimizasyonu yapar. Bu notebook yeni neural speed modeli eğitmez; hız adayının bilinen km/s videolarda ne kadar kalibre edilebildiğini ölçer.
* `SPEED_EXP_006B_VS13_Wide_Subset_Speed_Calibration_Colab.ipynb`: `SPEED-EXP-006` sanity check sonrası genişletilmiş hız kalibrasyon notebook'udur. VS13 içindeki 13 araç paketini destekler, varsayılan olarak her araçtan dengeli 12 video seçer, leave-one-vehicle-out cross-validation uygular ve `global_alpha`, `linear_raw`, `huber_raw` ile hafif tabular regressor kalibrasyonlarını karşılaştırır. FTR `results.json` hız alanı istemediği için bu notebook FTR ana teslimini bloklamaz; sonuç iyi çıkarsa yalnız `dataset-calibrated approximate speed candidate`, aksi halde `relative/support evidence` kararı üretir.
* `CABIN_EXP_020A_Cabin_Driver_View_Baseline_Colab.ipynb`: `CABIN-EXP-012` heuristik ROI denemesi reddedildikten sonra model-first cabin/driver görünürlük gate baseline'ını kurar. State Farm Distracted Driver görüntülerini pozitif `driver_cabin_visible`, mevcut BDD100K veya manuel `not_cabin_view` klasörünü negatif sınıf olarak kullanır; MobileNetV3-Large ve EfficientNet-B0 binary classifier karşılaştırması, leakage-safe split, confusion matrix, checkpoint export ve lokal video smoke inference üretir.

## Output-Saved Notebooklar

Colab çıktısı alınmış notebooklar `notebooks/Outputs Saved/` altında tutulur. Bu dosyalar geçmiş koşunun kanıtıdır; aktif geliştirme için kökteki outputsuz notebook kullanılmalıdır.

Git'te takip edilen output-saved koşular:

* `Outputs Saved/COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab_outputsaved.ipynb`

## Kural

Notebooklar ham veri, model ağırlığı veya run çıktısı üretse bile bu artefactler Git'e eklenmez. Colab/Drive tarafında tutulur.

Git'e yalnız şunlar eklenir:

* deney planı,
* mapping/config,
* küçük benchmark CSV/JSON özetleri,
* model card ve deney notları.

## Drive Yapısı Önerisi

```text
/content/drive/MyDrive/anomali-road-safety-ai/
  datasets/
    bdd100k/
      images/
      labels/
    bdd100k_vehicle_yolo/
      images/
      labels/
      splits/
      metadata/
      data.yaml
  runs/
  exports/
```

BDD100K ham veri dosyaları repoya eklenmemelidir.

## Notebook İçinden İndirme

BDD100K indirme otomasyonu notebook içine gömülüdür. Config hücresinde şu modlardan biri seçilir:

* `manual`
* `kaggle`
* `direct`
* `gdown`

`scripts/colab/download_bdd100k.py` aynı indirme mantığını notebook dışında çalıştırmak için opsiyonel helper olarak kalır.

## Kaggle Credential Kullanımı

Kaggle API key notebook veya Git dosyasına düz metin olarak yazılmaz.

Notebook şu sırayla credential okur:

1. Colab Secrets:
   * `KAGGLE_USERNAME`
   * `KAGGLE_KEY`
   * alternatif küçük harfli adlar: `kaggle_username`, `kaggle_key`
2. Ortam değişkenleri:
   * `KAGGLE_USERNAME`
   * `KAGGLE_KEY`
   * alternatif küçük harfli adlar: `kaggle_username`, `kaggle_key`
3. Runtime prompt:
   * username normal input,
   * API key `getpass` ile gizli input.

Bu sayede notebook tek dosyada otomatik indirme yapabilir; key repoya yazılmaz.

### State Farm Kaggle Troubleshooting

`CABIN_EXP_020A_Cabin_Driver_View_Baseline_Colab.ipynb` State Farm verisini resmi Kaggle
competition endpoint'i ile indirir:

```text
kaggle competitions download -c state-farm-distracted-driver-detection
```

Credential dosyası oluştuğu halde bu komut exit code `1` ile düşerse en sık nedenler:

* `401 Unauthorized`: Kaggle API token geçersizdir, iptal edilmiştir veya username/token aynı hesaba ait değildir.
* Kaggle hesabında yarışma kuralları/data terms kabul edilmemiştir.
* Colab Secrets içindeki API key, kuralları kabul eden Kaggle hesabına ait değildir.
* API token iptal edilmiş, yanlış kopyalanmış veya başında/sonunda boşluk vardır.
* Eski competition endpoint'i ilgili hesaba geçici olarak kapalıdır.

Kontrol adımları:

1. Aynı Kaggle hesabıyla `https://www.kaggle.com/competitions/state-farm-distracted-driver-detection/data`
   sayfasına gir ve Join/Accept Rules adımı görünüyorsa tamamla.
2. Kaggle Account > Settings > API > Create New Token ile yeni token üret.
3. Colab Secrets içine `KAGGLE_USERNAME` / `KAGGLE_KEY` veya küçük harfli
   `kaggle_username` / `kaggle_key` olarak ekle.
4. Notebook Cell 1-3'ü yeniden çalıştır. Güncel notebook Kaggle stdout/stderr çıktısını
   görünür basar.
5. Güncel notebook resmi competition endpoint'i başarısız olursa public Kaggle mirror
   `rightway11/state-farm-distracted-driver-detection` kaynağını fallback olarak dener.
   Bu fallback de `401` verirse sorun veri kaynağı değil Kaggle token/hesap doğrulamasıdır.
6. API hâlâ engellenirse `state-farm-distracted-driver-detection.zip`, `imgs.zip` veya
   extracted `imgs/train/c0..c9` yapısını Drive'da
   `/content/drive/MyDrive/anomali-road-safety-ai/datasets/cabin_exp_020a/state_farm/`
   altına manuel yerleştir.
7. Büyük zip dosyası connector/upload limiti nedeniyle parçalara bölünmüşse parçalar
   `state_farm/chunks/state-farm-distracted-driver-detection.zip.part-*` altında durabilir.
   Güncel notebook Cell 3 bu parçaları otomatik birleştirip zip'i yeniden oluşturur.

## Tek Notebook Akışı

`VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb` şu çıktıları üretir:

* BDD100K raw veri doğrulama veya indirme.
* BDD100K JSON -> YOLO label dönüşümü.
* `data.yaml`.
* Condition metadata CSV.
* Pretrained baseline validation.
* Fine-tuned validation.
* Baseline vs fine-tuned delta tablosu.
* Condition breakdown validation.
* Optional ONNX export.

`COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab.ipynb` şu çıktıları üretir:

* BDD100K image attribute metadata doğrulama veya üretim.
* `condition_metadata.csv`.
* `train/val/test` split CSV'leri.
* MobileNetV3-Small condition classifier checkpoint'i.
* Opsiyonel ResNet18 challenger karşılaştırması.
* Macro-F1, per-class precision/recall/F1 ve confusion matrix.
* Opsiyonel dark video condition smoke test ve router fallback özeti.

`POCR_EXP_005_YOLO11N_Plate_Detector_Colab.ipynb` şu çıktıları üretir:

* Roboflow raw dataset cache.
* Plate detection YOLO metadata CSV.
* YOLO11n `best.pt` ve `last.pt`.
* Opsiyonel ONNX export.
* Existing local plate baseline vs fine-tuned model val/test metrikleri.
* UFPR-ALPR external benchmark sonucu veya `missing/skipped` durumu.

`VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab.ipynb` şu çıktıları üretir:

* BoxCars116k `dataset.pkl` / `classification_splits.pkl` / `atlas.pkl` preflight kontrolü.
* `body` split varsa body-type classifier, yoksa fine-grained/make split fallback.
* MobileNetV3-Large checkpoint ve opsiyonel EfficientNet-B0 challenger.
* Label map, dimension-prior table, metrics JSON ve Markdown summary.
* Optional existing vehicle crop smoke inference.

`SPEED_EXP_006_VS13_Known_Speed_Calibration_Colab.ipynb` şu çıktıları üretir:

* VS13 `RenaultCaptur`, `KiaSportage`, `VWPassat` zip cache dosyaları.
* `vs13_subset_manifest.csv`.
* `vs13_base_speed_candidates.csv`.
* `vs13_calibration_grid_metrics.csv`.
* `vs13_best_calibrated_predictions.csv`.
* `speed_exp_006_vs13_known_speed_calibration_summary.json`.
* GT-vs-pred, absolute error ve confidence-vs-error grafikleri.

`SPEED_EXP_006B_VS13_Wide_Subset_Speed_Calibration_Colab.ipynb` şu çıktıları üretir:

* VS13 seçili araç paketleri için geniş subset manifest'i.
* `vs13b_first_stage_loo_metrics.csv`.
* `vs13b_first_stage_loo_predictions.csv`.
* `vs13b_second_stage_feature_model_metrics.csv`.
* `vs13b_second_stage_feature_model_predictions.csv`.
* `vs13b_combined_calibration_metrics.csv`.
* `vs13b_best_loo_predictions.csv`.
* `speed_exp_006b_vs13_wide_subset_calibration_summary.json`.
* Leave-one-vehicle-out GT-vs-pred, absolute error ve confidence-vs-error grafikleri.

`CABIN_EXP_020A_Cabin_Driver_View_Baseline_Colab.ipynb` şu çıktıları üretir:

* State Farm Kaggle competition cache ve extracted train klasörü.
* `cabin_exp_020a_metadata.csv`.
* `cabin_exp_020a_splits.csv`.
* MobileNetV3-Large / EfficientNet-B0 leaderboard.
* `cabin_exp_020a_test_classification_report.csv`.
* `cabin_exp_020a_confusion_matrix.png`.
* `cabin_exp_020a_summary.json`.
* `CABIN-EXP-020A-<backbone>-best.pth`.
* Opsiyonel lokal demo video smoke CSV ve preview görselleri.
