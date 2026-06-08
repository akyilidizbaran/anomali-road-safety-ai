# Colab Notebooks

Bu klasör, Anomali Road Safety AI model deneylerini Google Colab üzerinde tekrar üretilebilir şekilde çalıştırmak için notebook skeleton'larını içerir.

## Aktif Notebooklar

* `VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`: BDD100K üzerinden 4 sınıflı condition-aware general vehicle detector fine-tune hattı.

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
