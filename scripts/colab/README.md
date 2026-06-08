# Colab Helper Scripts

Bu klasör Google Colab deneylerini destekleyen küçük helper scriptleri içerir.

## `download_bdd100k.py`

BDD100K ham verisini Google Drive altındaki dataset klasörüne indirmek için opsiyonel yardımcıdır.

Varsayılan hedef:

```text
/content/drive/MyDrive/anomali-road-safety-ai/datasets/bdd100k
```

Desteklenen modlar:

```bash
# Kaggle mirror/dataset kullanımı, credentials Colab secrets/env üzerinden.
python scripts/colab/download_bdd100k.py \
  --method kaggle \
  --kaggle-dataset OWNER/DATASET_SLUG \
  --extract

# Direct resmi URL veya kullanıcı tarafından sağlanan arşiv URL'leri.
python scripts/colab/download_bdd100k.py \
  --method direct \
  --url "https://example.com/bdd100k_images.zip" \
  --url "https://example.com/bdd100k_labels.zip" \
  --extract

# Google Drive ID/URL kullanımı.
python scripts/colab/download_bdd100k.py \
  --method gdown \
  --gdrive "GOOGLE_DRIVE_FILE_ID_OR_URL" \
  --extract
```

Credential, API key, direct URL ve download token bilgileri Git'e yazılmamalıdır. Colab secrets, environment variable veya notebook runtime input ile verilmelidir.
