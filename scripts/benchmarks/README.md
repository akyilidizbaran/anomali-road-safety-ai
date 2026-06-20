# Benchmark Scripts

Bu klasör lokal benchmark koşularını tekrar üretmek için kullanılan scriptleri tutar.

## `run_tracking_baseline.py`

Vehicle tracking baseline deneylerini çalıştırır.

Varsayılan koşu:

```bash
.venv-yolo/bin/python scripts/benchmarks/run_tracking_baseline.py \
  --experiments TRK-EXP-001 TRK-EXP-002
```

Varsayılanlar:

* Model: `yolo11n.pt`
* Videolar: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
* Sınıflar: `car`, `motorcycle`, `bus`, `truck`
* `TRK-EXP-001`: ByteTrack
* `TRK-EXP-002`: BoT-SORT ReID kapalı

Büyük annotated video çıktıları `runs/tracking/` altında kalır ve Git'e eklenmez. Küçük JSON özetleri `models/benchmarks/artifacts/` altında tutulur.

2026-06-11 güncellemesiyle track summary içinde compact history alanları da üretilir:

* `center_history_sample`
* `bbox_history_sample`
* `history_sample_strategy`

Bu alanlar speed baseline, plate temporal voting, target selection ve evidence skeleton için kullanılır.

## `build_track_event_skeleton.py`

ByteTrack benchmark summary dosyasını okuyup track-level post-process ve ilk event/evidence skeleton çıktısını üretir.

Varsayılan koşu:

```bash
python3 scripts/benchmarks/build_track_event_skeleton.py
```

Üretilen çıktılar:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-track-postprocess.json`
* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* `testing/reports/trk_exp_001_track_to_event_summary.md`

Bu script gerçek risk alarmı üretmez. `target_vehicle_selected` seviyesinde ara event skeleton'ı oluşturur ve sonraki speed, plate OCR, QoD ve evidence modülleri için aynı `track_id` üzerinden bağlanacak kayıtları hazırlar.

## `run_relative_track_speed_baseline.py`

`SPEED-EXP-004A` relative track/bbox speed baseline script'idir. CCT-XS ile zenginleştirilmiş
event skeleton'ı okuyup ByteTrack target history üzerinden kalibrasyonsuz göreli hız sinyali
üretir. Bu script **km/s üretmez**; `relative_speed_score`, `relative_speed_label`,
`fusion_confidence`, `warning_flags` ve `fallback_reason` alanlarını oluşturur.

Varsayılan koşu:

```bash
python3 scripts/benchmarks/run_relative_track_speed_baseline.py
```

Varsayılan input:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-fastplate.json`

Üretilen çıktılar:

* Summary JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-004A-relative-track-bbox/speed_exp_004a_relative_track_speed_summary.json`
* Summary CSV: `models/benchmarks/artifacts/speed/SPEED-EXP-004A-relative-track-bbox/speed_exp_004a_relative_track_speed_summary.csv`
* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004a.json`
* Rapor: `testing/reports/speed_exp_004a_relative_track_bbox_baseline.md`

`fallback_reason=no_reliable_metric_calibration` hata değildir; homografi veya ölçülü referans
olmadığı için bu çıktının mutlak hız yerine relative motion evidence olarak yorumlanması
gerektiğini belirtir.

## `run_speed_004b_plate_vattr_sanity.py`

`SPEED-EXP-004B` plate-scale + VATTR sanity-check script'idir. `SPEED-EXP-004A`
relative speed block'unu, `SPEED-EXP-002` plate-scale adayını ve `VATTR-EXP-001`
vehicle body/dimension-prior classifier çıktısını aynı event/evidence contract'ında
birleştirir.

Varsayılan koşu:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_speed_004b_plate_vattr_sanity.py
```

Gerekli lokal checkpoint:

* `models/checkpoints/vehicle_attribute/VATTR-EXP-001-efficientnet_b0-best.pth`

Bu `.pth` dosyası Git'e eklenmez. Drive kaynağı:

* `VATTR-EXP-001-efficientnet_b0-best.pth`
* Drive file ID: `1tQVq24gKbbhODVqBYG7fG9g-0GYZgHt9`

Küçük label/prior JSON dosyaları:

* `models/checkpoints/vehicle_attribute/VATTR-EXP-001-label-map.json`
* `models/checkpoints/vehicle_attribute/VATTR-EXP-001-dimension-prior-table.json`

Üretilen çıktılar:

* Summary JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-004B-plate-vattr-sanity/speed_exp_004b_plate_vattr_sanity_summary.json`
* Summary CSV: `models/benchmarks/artifacts/speed/SPEED-EXP-004B-plate-vattr-sanity/speed_exp_004b_plate_vattr_sanity_summary.csv`
* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004b.json`
* Rapor: `testing/reports/speed_exp_004b_plate_vattr_sanity.md`

Bu script de kesin km/s üretmez. VATTR çıktısı doğrudan hız değil, body/dimension prior
ve sanity-check sinyali olarak kullanılmalıdır.

## `prepare_speed_004c_homography_calibration.py`

`SPEED-EXP-004C` semi-manual homography absolute-candidate hazırlık script'idir.
Bu adım eğitim veya GPU gerektirmez; local MacBook üzerinde OpenCV ile demo videolardan
kalibrasyon kareleri çıkarır ve manuel doldurulacak homografi profil şablonunu üretir.

Varsayılan koşu:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/prepare_speed_004c_homography_calibration.py --overwrite-profile
```

Varsayılan input:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004b.json`
* `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`

Üretilen çıktılar:

* Kalibrasyon kareleri: `runs/speed/SPEED-EXP-004C-homography/calibration_frames/`
* Profil şablonu: `configs/speed_calibration/CALIB-DEMO-001.template.json`
* Summary JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-004C-homography/speed_exp_004c_homography_calibration_prep_summary.json`
* Rapor: `testing/reports/speed_exp_004c_homography_calibration_preparation.md`

Bu script **mutlak km/s üretmez**. En az dört ölçülü yol düzlemi referans noktası
`image_points_px` ve `world_points_m` olarak girilmeden sonraki 004C homografi doğrulama
adımına geçilmemelidir.

## `run_speed_005a_bbox_geometry_candidate.py`

`SPEED-EXP-005A` bbox geometry automatic speed candidate script'idir. Manuel yol
referans noktası gerektirmez; hedef track için full per-frame bbox timeline çıkarır,
varsayılan araç fiziksel boyutu ve FOV prior ile yaklaşık km/s adayı üretir. Piklerden
etkilenmemek için ana `estimated_kmh` değeri moving average serisinin ortalaması olarak
raporlanır; grafiklerde raw segment, rolling median ve moving average çizgileri birlikte
gösterilir.

Varsayılan koşu:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_speed_005a_bbox_geometry_candidate.py
```

Varsayılan input:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004b.json`
* `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
* Plate karşılaştırması: `models/benchmarks/artifacts/speed/SPEED-EXP-002-plate-bbox-xyz/speed_exp_002_plate_bbox_xyz_summary.json`

Üretilen çıktılar:

* Summary JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-005A-bbox-geometry-auto/speed_exp_005a_bbox_geometry_summary.json`
* Timeseries CSV: `models/benchmarks/artifacts/speed/SPEED-EXP-005A-bbox-geometry-auto/speed_exp_005a_bbox_geometry_timeseries.csv`
* Grafikler: `runs/speed/SPEED-EXP-005A-bbox-geometry-auto/plots/`
* Rapor: `testing/reports/speed_exp_005a_bbox_geometry_auto_candidate.md`

Bu script de hukuki/final hız ölçümü değildir. `estimated_kmh` alanı yalnız
`speed_mode=approximate_candidate` olarak yorumlanmalıdır. Bbox jump/outlier segmentleri
otomatik filtrelenir; düşük güvenli sonuçlarda `warning_flags` ve `failure_flags` okunmalıdır.
Moving average penceresi varsayılan olarak `--moving-average-window 25` frame'dir ve
CLI üzerinden değiştirilebilir. Araç kadrajdan çıkarken oluşan terminal hız pikleri için
`--post-peak-shrink-ratio 0.85` gate'i kullanılır.

## `run_plate_detection_smoke.py`

`POCR-EXP-001` plaka tespit smoke test'i. `run_tracking_baseline.py` ile aynı mantıkta çalışır:
`yolo11n` + ByteTrack ile hedef track bulunur, hedef aracın tespit edildiği karelerde plaka
TESPİTİ yapılır ve — tracking çıktısı gibi — **orijinal video üzerine kutular çizilmiş tam
annotated video** üretilir. OCR (metin okuma) bu aşamada yoktur.

Varsayılan koşu (önce venv aktive et — `.venv-yolo/bin/python` doğrudan çağrısı bazı kurulumlarda çalışmaz):

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_plate_detection_smoke.py            # iki model (YOLOS yavaş)
python scripts/benchmarks/run_plate_detection_smoke.py --models yolo   # hızlı, tek model
```

Varsayılanlar:

* Araç detector: `yolo11n.pt` / tracker: ByteTrack
* Videolar: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
* Hedef track: event skeleton'daki `best_frame` bbox'ı ile IoU eşleşmesi
* Plaka modelleri: `yolo` (Ultralytics, `models/checkpoints/plate/license_plate_detector.pt`) + `yolos` (HF `nickmuchi/yolos-small-...`)
* Çizim: beyaz kutu = hedef araç, yeşil = YOLO, mavi = YOLOS

Faydalı bayraklar: `--models yolo` (tek model, hızlı), `--frame-stride 5` (hız), `--video-scale 0.5` (küçük dosya).

Üretilen çıktılar:

* Annotated videolar: `runs/plate_ocr/POCR-EXP-001-plate-detection/annotated/<video>_plate_detection.mp4`
* Plaka kırpıntıları (OCR için): `runs/plate_ocr/POCR-EXP-001-plate-detection/plates/<model>/<video>/`
* Summary JSON: `models/benchmarks/artifacts/POCR-EXP-001-plate-detection-summary.json`
* Rapor: `testing/reports/pocr_exp_001_plate_detection_summary.md`

Büyük annotated video çıktıları ve plaka kırpıntıları `runs/` altında kalır ve Git'e eklenmez
(plaka metni/görseli kişisel veridir). Çalıştırma detayları: `research/04_plate_ocr/RUN_POCR_EXP_001.md`.

> Eski `extract_plate_ocr_target_rois.py` (tek best-frame crop yaklaşımı) `archive/plate_ocr_v1/` altına alınmıştır.

## `run_plate_ocr_baseline.py`

`POCR-EXP-002/003/004` OCR baseline script'i. `POCR-EXP-001` summary JSON'unu okuyup
secilen detector'un plate crop'lari ustunde OCR engine'lerini calistirir. OCR sonucu:

* raw text
* Turk plaka normalize sonucu
* format valid / il kodu valid flag'leri
* temporal voting sonucu

olarak raporlanir.

Varsayilan kosu:

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/run_plate_ocr_baseline.py --engines paddle
python scripts/benchmarks/run_plate_ocr_baseline.py --engines easyocr
python scripts/benchmarks/run_plate_ocr_baseline.py --engines paddle easyocr
```

Faydali bayraklar:

* `--detector-key yolo|yolos`
* `--frame-stride 5`
* `--limit-per-video 50`
* `--variants original gray clahe`
* `--upscale 2.0`
* `--keep-per-crop`

Uretilen ciktilar:

* Summary JSON: `models/benchmarks/artifacts/POCR-EXP-002-paddleocr-summary.json`
* Summary JSON: `models/benchmarks/artifacts/POCR-EXP-003-easyocr-summary.json`
* Summary JSON: `models/benchmarks/artifacts/POCR-EXP-004-tesseract-summary.json`
* Rapor: `testing/reports/pocr_exp_002_004_plate_ocr_summary_<engine>.md`
* Manuel review seed: `runs/plate_ocr/POCR-EXP-002-004-ocr/manual_review_<engine>.csv`

Detayli calistirma notlari: `research/04_plate_ocr/RUN_POCR_EXP_002.md`.

## `enrich_event_skeleton_with_plate_ocr.py`

`build_track_event_skeleton.py` ile uretilmis tracking skeleton eventlerini, secilen OCR
baseline sonucuyla zenginlestirir. Varsayilan kaynak `POCR-EXP-002-paddleocr-summary.json`
olup ciktida `plate`, `models`, `routing_decision`, `evidence` ve `explanation` alanlari
guncellenir.

Varsayilan kosu:

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/enrich_event_skeleton_with_plate_ocr.py
```

Uretilen ciktilar:

* Enriched event JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle.json`
* Rapor: `testing/reports/trk_exp_001_plate_ocr_event_enrichment_summary.md`

Bu adimdan sonra plate/OCR benchmark'i ayrik bir deney olmaktan cikmis olur; secilen final
track-level plaka karari event/evidence hattina baglanmis olur.

## `run_vehicle_detection_video_smoke.py`

`VD-EXP-002` fine-tuned general YOLO11n checkpoint'i ile lokal `Test/video_1-3.mp4`
smoke test'i çalıştırır. Güncel sürüm condition classifier/router çıktısını da aynı
JSON/Markdown rapora bağlar.

Varsayılan koşu:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_vehicle_detection_video_smoke.py
```

Varsayılanlar:

* Vehicle detector: `models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt`
* Condition classifier: `models/checkpoints/condition_profile/COND-EXP-001-mobilenet_v3_small-best.pt`
* Condition örnekleme: her 15 frame
* Routing policy: condition profile yalnız advisory sinyaldir; specialist detector'lar general detector'a göre üstünlüğü kanıtlanmadan otomatik promote edilmez.
* Bu fazda `fog_low_visibility` promoted/supported routing kapsamı dışında tutulur.
* Manual review: `testing/manual_reviews/vd_exp_002_dark_video_manual_review.json`
* Manual review ile doğrulanan sınıf karışıklığı varsa raw detector sınıfı yine event/evidence tarafına taşınır; review notu yalnız model geliştirme failure-case'i olarak `class_quality` içinde tutulur.

Üretilen çıktılar:

* Summary JSON: `models/benchmarks/artifacts/VD-EXP-002-general-yolo11n-dark-smoke-summary.json`
* Rapor: `testing/reports/vd_exp_002_dark_video_smoke_test_summary.md`
* Annotated videolar: `runs/vehicle_detection/VD-EXP-002-dark-smoke/`

Condition classifier'ı kapatmak için:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_vehicle_detection_video_smoke.py --no-condition-profile
```

Manual review merge katmanını kapatmak için:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_vehicle_detection_video_smoke.py --no-manual-review
```

Not: Manual review katmanı raw model çıktısını değiştirmez ve sınıf etiketini override etmez. Detector `car` diyorsa event/evidence tarafına `car` gider; failure-case bilgisi yalnız genel model iyileştirme planına kaynak olur.
