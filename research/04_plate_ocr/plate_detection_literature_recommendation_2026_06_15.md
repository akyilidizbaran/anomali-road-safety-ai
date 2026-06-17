# Plate Detection Literature Recommendation - 2026-06-15

## Kapsam

Bu not yalnız **plate detection** aşaması içindir. OCR, Türk plaka karakter post-processing ve temporal voting sonraki aşamada ele alınacaktır.

Bu aşamadaki hedef, ByteTrack ile seçilmiş `target_track_id` / target vehicle ROI üzerinde plaka bounding box'ı üreten, açıklanabilir ve evidence package'a bağlanabilir bir plate detector baseline seçmektir.

## OCR'a Geçmeden Önce Kapanması Gerekenler

1. **Vehicle detector modeli sabit, threshold seçimi açık olmalı.**
   * Aktif detector: `VD-EXP-002-GENERAL-YOLO11N`.
   * Final confidence threshold henüz seçilmedi; `0.60` yalnız mevcut manual review kapsamındaki false-positive pruning aday gate değeridir.
   * Plate detection crop üretimi için candidate detection/tracking tarafında daha düşük eşik gerekebilir; OCR'a geçmeden önce bu ayrım korunmalıdır.

2. **Plate detector tam frame yerine target vehicle ROI üzerinde çalışmalı.**
   * ALPR literatüründe önce vehicle/ROI ile arama alanını daraltmak false positive ve runtime maliyetini düşürür.
   * Bizim sistemde zaten ByteTrack target seçtiği için plate detection'ın giriş birimi `target_vehicle_roi_window` olmalıdır.

3. **Tek best frame yeterli değildir.**
   * Plaka görünürlüğü vehicle detection confidence ile aynı şey değildir.
   * Her target track için `best_frame` yanında en az 10-30 frame'lik ROI sample window tutulmalıdır.
   * Plate detector için manual review `per-frame` değil `per-track usable plate crop` olarak yapılmalıdır.

4. **Plate detection manual review şablonu OCR'dan bağımsız doldurulmalı.**
   * `plate_visible_manual`
   * `plate_detected_model`
   * `plate_bbox_correct_manual`
   * `plate_crop_usable_for_ocr`
   * `failure_reason`
   * `needs_qod_manual`

5. **Gizlilik ve artifact politikası net kalmalı.**
   * Plate crop ve overlay çıktıları `runs/` altında kalmalı, Git'e eklenmemelidir.
   * Raporlarda gerçek plaka metni kullanılmamalı; OCR sonraki aşamada masked/hashed gösterimle ele alınmalıdır.

## Literatürden Çıkan Teknik Dersler

* İki aşamalı ALPR yaklaşımı proje için daha uygun: önce plate detection, sonra OCR. Böylece plate bbox, crop kalitesi, OCR confidence ve failure reason ayrı ayrı evidence package'a yazılabilir.
* YOLO tabanlı plate detection, gerçek zamanlı ALPR literatüründe güçlü bir başlangıç çizgisidir. Laroca vd. YOLO tabanlı ALPR çalışmalarında önce vehicle/plate detection, sonra temporal redundancy/recognition hattını kullanır; UFPR-ALPR çalışması hareketli kamera ve gerçek trafik koşullarını özellikle vurgular.
* Dataset metrikleri doğrudan final iddia olarak kullanılmamalıdır. Özellikle Roboflow Universe üstündeki bazı model kartları yüksek mAP/precision/recall verse de split contamination uyarısı bulunabilir; bu nedenle kendi train/val/test split ve manuel review şarttır.

## Veri Seti Kararı

### Birincil Fine-Tune Verisi

**Turkish Number Plates - Roboflow Universe**

* Link: <https://universe.roboflow.com/plakatanima-vnt3k/turkish-number-plates>
* Lisans: CC BY 4.0 olarak listeleniyor.
* Hacim: 2,246 image, tek sınıf `license_plate`.
* Neden birinci sırada:
  * Türkiye plaka formatına en yakın açık kaynak plate detection verisi.
  * Direkt plate bbox göreviyle uyumlu.
  * Modelin Türkiye plaka geometrisi, plaka oranı ve lokal görüntü örneklerine alışması için en mantıklı başlangıç.
* Risk:
  * Hacim orta/küçük.
  * Roboflow hosted dataset olduğu için split kalitesi ve görüntü tekrarları ayrıca kontrol edilmeli.
  * Reported Roboflow metriği final kanıt olarak kullanılmamalı.

### İkinci Eğitim Kaynağı / Veri Artırma Omurgası

**License Plate Recognition Dataset - Roboflow Universe**

* Link: <https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e>
* Lisans: CC BY 4.0 olarak listeleniyor.
* Hacim: 10,125 image, tek sınıf `License_Plate`.
* Neden kullanılmalı:
  * Turkish dataset'e göre daha fazla plate bbox örneği sağlar.
  * YOLO formatına kolay export edilebilir.
  * İlk YOLO11n plate detector fine-tune için hacim sağlar.
* Risk:
  * HF `morsetechlab/yolov11-license-plate-detection` model card'ı aynı upstream dataset için train/test contamination uyarısı veriyor.
  * Bu yüzden bu dataset kullanılacaksa kendi hash/perceptual-hash duplicate temizliği ve sıfırdan split şarttır.

### Benchmark / Generalization Kaynağı

**UFPR-ALPR**

* Link: <https://github.com/raysonlaroca/ufpr-alpr-dataset>
* Hacim: 4,500 fully annotated image, 150 vehicle/video sequence, gerçek trafik.
* Neden değerli:
  * Hareketli kamera, farklı araç tipleri, farklı lighting/background koşulları içerir.
  * Plate detection + OCR + temporal voting mantığını test etmek için iyi akademik referanstır.
  * FTR raporunda “gerçek trafik koşullarına yakın dış benchmark” olarak anlatılabilir.
* Neden birincil training değil:
  * Brezilya plaka formatı Türkiye plakasından farklı.
  * Hacim Turkish + Roboflow birleşimi kadar büyük değil.

### Opsiyonel Pretraining / Zor Koşul Kaynağı

**CCPD**

* Link: <https://github.com/detectrecog/CCPD>
* Hacim: 300k+ image olarak belirtiliyor; blur, rotation, tilt, challenge gibi alt kümeler mevcut.
* Neden opsiyonel:
  * Büyük hacim ve zor koşul varyasyonları plate localization kabiliyetini artırabilir.
  * Low-light/blur/tilt augmentation fikri için referans olabilir.
* Neden dikkatli:
  * Çin plaka formatı Türkiye plakasından farklı.
  * Lisans/kullanım koşulu proje raporu ve yarışma sunumu öncesi ayrıca doğrulanmalıdır.
  * İlk MVP için veri pipeline'ını gereksiz büyütebilir.

## Model Kararı

### İlk Fine-Tune Modeli

**YOLO11n plate detector**

Başlangıç checkpoint:

```text
yolo11n.pt
```

Önerilen deney adı:

```text
POCR-EXP-005-YOLO11N-PLATE-DETECTOR
```

Neden:

* Vehicle detection tarafında zaten YOLO11n + Ultralytics pipeline kullanıyoruz; Colab, export, inference ve rapor formatı aynı kalır.
* Target vehicle ROI içinde tek sınıf `license_plate` detection için küçük model yeterli olabilir.
* MacBook local runtime için YOLO11n, YOLO11s/m gibi daha ağır varyantlara göre daha mantıklı latency başlangıcıdır.
* Plate bbox çıktısı evidence package ile doğrudan uyumludur.

Lisans notu:

* Ultralytics YOLO11 AGPL-3.0 / Enterprise lisans çizgisindedir. Yarışma/prototip ve private repo kapsamında kullanılabilirlik ayrı, ürünleşme/ticari dağıtım ayrı değerlendirilmelidir.

### İlk Smoke-Test Pretrained Adayı

**morsetechlab/yolov11-license-plate-detection**

* Link: <https://huggingface.co/morsetechlab/yolov11-license-plate-detection>
* Kullanım amacı:
  * Sıfır fine-tune öncesi “target ROI içinde plate bbox çıkıyor mu?” smoke test.
* Sınırlama:
  * Model card upstream Roboflow dataset contamination uyarısı içeriyor.
  * Bu modelin metrikleri final benchmark olarak kullanılmamalıdır.

### Bağımsız İkinci Baseline

**nickmuchi/yolos-small-finetuned-license-plate-detection**

* Link: <https://huggingface.co/nickmuchi/yolos-small-finetuned-license-plate-detection>
* Kullanım amacı:
  * Ultralytics dışı, Transformers tabanlı detector sanity check.
* Sınırlama:
  * YOLOS/ViT tabanlı yapı MacBook runtime ve video pipeline için YOLO11n kadar pratik olmayabilir.
  * İlk üretim hattı değil, karşılaştırma baseline'ı olarak tutulmalıdır.

## Önerilen Deney Sırası

1. `POCR-EXP-001/002` çıktılarındaki target ROI window üretimini doğrula.
2. Pretrained smoke:
   * `morsetechlab/yolov11-license-plate-detection`
   * `nickmuchi/yolos-small-finetuned-license-plate-detection`
3. Turkish Number Plates + Roboflow LPR birleşik dataset hazırlığı:
   * class normalize: `license_plate`
   * duplicate / near-duplicate temizliği
   * source-grouped train/val/test split
   * YOLO format export
4. YOLO11n fine-tune:
   * `imgsz=640`
   * tek sınıf plate detector
   * low-light/blur/glare augmentation
5. Değerlendirme:
   * mAP@0.5
   * precision/recall
   * plate detection recall on target ROI
   * false positive per target ROI
   * usable crop rate
   * p95 latency
6. OCR'a geçiş kriteri:
   * Target track başına en az bir usable plate crop üretilebilmeli.
   * Plate bbox manual review “çoğunlukla doğru” olmalı.
   * Düşük güven/plate-not-visible/failure reason alanları doğru yazılmalı.

## Nihai Öneri

İlk gerçek plate detection fine-tune için:

```text
Model: YOLO11n single-class plate detector
Training data: Turkish Number Plates (primary) + Roboflow License Plate Recognition 10,125 (support)
Benchmark/generalization: UFPR-ALPR
Optional later: CCPD for pretraining/adverse condition robustness
```

OCR'a doğrudan geçmeden önce hedefimiz “plaka yazısını okumak” değil, **target vehicle ROI içinde güvenilir plate bbox ve usable plate crop üretmek** olmalıdır.

## Kaynaklar

* UFPR-ALPR dataset: <https://github.com/raysonlaroca/ufpr-alpr-dataset>
* Laroca et al., Robust Real-Time ALPR Based on YOLO: <https://arxiv.org/abs/1802.09567>
* Laroca et al., Layout-Independent ALPR Based on YOLO: <https://arxiv.org/abs/1909.01754>
* CCPD dataset: <https://github.com/detectrecog/CCPD>
* Turkish Number Plates Roboflow dataset: <https://universe.roboflow.com/plakatanima-vnt3k/turkish-number-plates>
* Roboflow License Plate Recognition dataset/model: <https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e>
* YOLO11 docs/license note: <https://docs.ultralytics.com/models/yolo11/>
* Ultralytics license page: <https://www.ultralytics.com/license>
* morsetechlab YOLOv11 plate detector: <https://huggingface.co/morsetechlab/yolov11-license-plate-detection>
* nickmuchi YOLOS plate detector: <https://huggingface.co/nickmuchi/yolos-small-finetuned-license-plate-detection>
