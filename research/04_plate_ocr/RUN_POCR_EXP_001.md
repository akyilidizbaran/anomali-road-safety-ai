# POCR-EXP-001 — Plaka Tespit Smoke Test: MacBook Çalıştırma Talimatı

Tarih: 2026-06-11

Bu adım **sadece plaka tespiti** yapar (OCR yok). İki plaka modelini hedef aracın tespit
edildiği her karede çalıştırıp karşılaştırır. Çıktıları sen manuel inceleyip hangi modelin
daha iyi olduğuna karar vereceksin.

> Not: Bu script model **indiremeyen** ortamda (ör. sandbox) çalışmaz; ağırlıklar/HF erişimi
> için MacBook'ta, internet açıkken çalıştır.

## 1) Ortamı hazırla

```bash
cd "/Users/elifsena/Downloads/5G Teknofest"
source .venv-yolo/bin/activate
# YOLOS (HuggingFace) için transformers gerekir:
pip install "transformers>=4.40" pillow
```

`torch`, `ultralytics`, `opencv` zaten `.venv-yolo` içinde mevcut.

## 2) Plaka modeli ağırlıklarını edin

İki model var:

**A) Ultralytics YOLO plaka modeli (`yolo`)** — yerel bir `.pt` ağırlığı gerekir.
Bir tane indir ve şu yola koy: `models/checkpoints/plate/license_plate_detector.pt`

```bash
mkdir -p models/checkpoints/plate
# Örnek kaynak (HuggingFace Hub'dan; lisansı model kartından DOĞRULA):
pip install huggingface_hub
python - <<'PY'
from huggingface_hub import hf_hub_download
import shutil, os
# morsetechlab/yolov11-license-plate-detection (Ultralytics/AGPL notu var; smoke-test için)
# Mevcut dosyalar: license-plate-finetune-v1{n,s,m,l,x}.pt  (n=nano en hızlı)
p = hf_hub_download(repo_id="morsetechlab/yolov11-license-plate-detection",
                    filename="license-plate-finetune-v1n.pt")
os.makedirs("models/checkpoints/plate", exist_ok=True)
shutil.copy(p, "models/checkpoints/plate/license_plate_detector.pt")
print("kaydedildi:", "models/checkpoints/plate/license_plate_detector.pt")
PY
```

> Daha yüksek isabet için nano yerine `license-plate-finetune-v1s.pt` veya `...-v1m.pt`
> kullanabilirsin (karanlık videoda daha iyi olabilir). Farklı ağırlık koyarsan
> `--plate-yolo-weights <yol>` ile geç.

**B) YOLOS (`yolos`)** — ağırlık indirmeye gerek yok; ilk çalıştırmada
`nickmuchi/yolos-small-finetuned-license-plate-detection` otomatik HF'den iner.

## 3) Çalıştır

Script artık **orijinal video üzerine** hedef araç + plaka kutularını çizip her kaynak
video için tam **annotated video** üretir (tıpkı vehicle detection / tracking çıktıları gibi).

Hızlı ve akıcı tam çözünürlüklü inceleme videosu için **tek model (YOLO, MPS'te hızlı):**

```bash
python scripts/benchmarks/run_plate_detection_smoke.py --models yolo
```

İki modeli karşılaştırmak için (YOLO yeşil + YOLOS mavi, aynı video üzerinde):

```bash
python scripts/benchmarks/run_plate_detection_smoke.py --models yolo yolos
```

> **YOLOS yavaştır (CPU):** İki modeli birden seçersen tespit her hedef karede çalışır ve
> YOLOS CPU'da kare başına ~1-2 sn sürer; tam video ~20-30 dk alabilir (donmaz, her 25 karede
> ilerleme basar). Seçenekler: önce `--models yolo` ile hızlı tam videoyu üret; YOLOS'u ayrı
> ve atlamalı dene: `--models yolos --frame-stride 5`.

Faydalı bayraklar:

- `--frame-stride 5` — tespiti her 5. karede çalıştır (video tüm kareleri oynatır, kutular her 5 karede güncellenir; çok daha hızlı).
- `--video-scale 0.5` — annotated videoyu yarı çözünürlükte yaz (4K dosyayı küçültür, daha hızlı).
- `--padding-ratio 0.10` — araç kutusu etrafındaki pay (plaka kenarda kalıyorsa artır).
- `--plate-conf 0.25` — plaka tespiti güven eşiği.
- `--device mps` — Apple GPU'yu zorla (varsayılan auto).
- `--videos Test/video_3.mp4` — tek video.

> Not: İki modeli ayrı ayrı çalıştırırsan özet JSON üzerine yazılır; karşılaştırma için ikisini
> aynı komutta (`--models yolo yolos`) çalıştır.

## 4) Çıktılar

- **Özet (Git'e girer, küçük):** `models/benchmarks/artifacts/POCR-EXP-001-plate-detection-summary.json`
- **Rapor (Git'e girer):** `testing/reports/pocr_exp_001_plate_detection_summary.md`
- **İnceleme materyali (Git'e GİRMEZ, ignore'lu):**
  - Annotated video (orijinal kare + kutular): `runs/plate_ocr/POCR-EXP-001-plate-detection/annotated/<video>_plate_detection.mp4`
  - Plaka kırpıntıları (OCR aşaması için): `runs/plate_ocr/POCR-EXP-001-plate-detection/plates/<model>/<video>/`

## 5) Manuel inceleme (senin adımın)

Annotated videoları izleyip her model için değerlendir (beyaz kutu = hedef araç, yeşil = YOLO, mavi = YOLOS):

- Plaka doğru yerde mi kutulanıyor? (özellikle video_1/2'de plaka çoğu karede görünmüyor — bu beklenen)
- Yan profilde/yanlış yerde false positive var mı?
- Hangi model daha çok karede ve daha yüksek güvenle plaka yakalıyor?

Notlarını `testing/templates/manual_plate_ocr_review.csv` şablonuna göre kaydet. Kararını
söyle; seçilen model `POCR-EXP-002` (PaddleOCR) ve `POCR-EXP-003` (EasyOCR) OCR aşamalarına
girdi olacak.
