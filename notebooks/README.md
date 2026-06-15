# Colab Notebooks

Bu klasör, Anomali Road Safety AI model deneylerini Google Colab üzerinde tekrar üretilebilir şekilde çalıştırmak için notebook skeleton'larını içerir.

## Aktif Notebooklar

* `VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`: BDD100K indirme, Drive yerleşimi, YOLO dönüşümü, pretrained baseline validation, fine-tune, challenger model testleri, condition breakdown ve baseline-delta karşılaştırmasını tek notebook içinde yürütür.
* `COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab.ipynb`: BDD100K `weather/timeofday/scene` metadata'sından condition label üretir, MobileNetV3-Small ve ResNet18 condition classifier backbone'larını aynı ağır comparison run içinde eğitir, en iyi backbone'u validation macro-F1 ile seçer ve dark video condition smoke test'i destekler.

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
2. Ortam değişkenleri:
   * `KAGGLE_USERNAME`
   * `KAGGLE_KEY`
3. Runtime prompt:
   * username normal input,
   * API key `getpass` ile gizli input.

Bu sayede notebook tek dosyada otomatik indirme yapabilir; key repoya yazılmaz.

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
