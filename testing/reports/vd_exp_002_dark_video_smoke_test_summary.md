# VD-EXP-002 Dark Video Smoke Test Summary

## Kapsam

Bu rapor, secilen fine-tuned vehicle detector checkpoint'i ile lokal dark video
smoke test sonucunu kaydetmek icindir. Bu test final model dogrulugu iddiasi
degildir; FTR raporunda `manual qualitative review` ve pipeline kullanilabilirligi
kaniti olarak kullanilmalidir.

## Kosu Bilgisi

* Weights: `models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt`
* Device: `mps`
* Image size: `640`
* Confidence threshold: `0.6` (diagnostic/candidate gate run; final threshold TBD)
* Classes: `[0, 1, 2, 3]`
* Annotated output root: `runs/vehicle_detection/VD-EXP-002-dark-smoke`
* Condition profile enabled: `True`
* Detector routing policy: `condition profile is advisory; specialist detector profiles are not promoted until condition-specific benchmarks beat the general detector`
* Unpromoted condition profiles: `['fog_low_visibility']`
* Manual review enabled: `True`
* Manual review source: `testing/manual_reviews/vd_exp_002_dark_video_manual_review.json`

## Video Sonuclari

| Video | Condition | Cond Conf | Detector Profile | Evidence Class Policy | Frames | Detected Frames | Detections | Classes | Mean Conf | Mean ms | p95 ms | FPS | Annotated |
|---|---|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| Test/video_1.mp4 | `night_low_light` | 0.769 | `general` | `raw_detector_class` | 423 | 388 | 476 | car:476 | 0.853 | 21.157 | 30.468 | 26.171 | `runs/vehicle_detection/VD-EXP-002-dark-smoke/video_1/video_1.mp4` |
| Test/video_2.mp4 | `night_low_light` | 0.743 | `general` | `raw_detector_class` | 457 | 365 | 468 | car:468 | 0.831 | 19.458 | 25.152 | 27.793 | `runs/vehicle_detection/VD-EXP-002-dark-smoke/video_2/video_2.mp4` |
| Test/video_3.mp4 | `night_low_light` | 0.723 | `general` | `raw_detector_class` | 383 | 373 | 486 | car:486 | 0.8 | 20.297 | 27.974 | 25.956 | `runs/vehicle_detection/VD-EXP-002-dark-smoke/video_3/video_3.mp4` |

## Rapor Notu

* Bu smoke test 3 lokal dark video uzerinde gorsel kontrol icin uretilir.
* Annotated videolar `runs/` altindadir ve Git'e eklenmez.
* Manuel review tamamlanmadan accuracy, recall veya hukuki kanit iddiasi kurulmaz.
* 2026-06-15 manuel review kararina gore ana arac `Test/video_1-3.mp4` boyunca her frame'de yakalanmaktadir.
* Ana arac bbox davranisi stabil kabul edilmistir.
* Düsuk threshold degerlerinde false positive gozlenmistir; `0.60` bu manual review kapsaminda false-positive pruning icin aday downstream evidence/final-acceptance gate degeridir.
* Final confidence threshold bu smoke test ile sabitlenmez; threshold sweep + manuel review sonrasi secilecektir.
* `VD-EXP-002-GENERAL-YOLO11N`, mevcut MVP icin active/best detector olarak sabitlenmistir.
* Condition classifier bu fazda detector secimini otomatik degistirmez; specialist modeller general modele gore daha iyi oldugu kanitlanmadan `general` fallback korunur.
* `night_low_light` profilinin `general` fallback'e dusmesi condition classifier'in kotu cikmasi anlamina gelmez. Bu, night/rain/fog specialist detector'larin henuz general detector'a gore ustunlugunun kanitlanmamis olmasindan kaynaklanan bilincli runtime politikasidir.
* `fog_low_visibility` bu fazda promoted/supported routing kapsami disinda tutulur.
* Manual review ile bir failure case gorulse bile bu smoke pipeline raw detector class etiketini event/evidence tarafina oldugu gibi tasir.
* Motorcycle/car karisikligi bu 3 videoya ozel runtime override ile ele alinmaz; `VD-EXP-006` denemesi basarisiz/regresyon kabul edildigi icin motorcycle ozel fine-tune simdilik ertelenmistir.

## Motorcycle / Car Class Confusion Notu

Kullanici manuel gozlemine gore `video_3` icinde normalde 1 araba + 1 motosiklet vardir.
Ana arac her frame'de dogru tespit edilmektedir. Arka plandaki cok karanlik motosiklet ise gorunur oldugu karelerde sistematik bicimde `car` olarak siniflandirilmaktadir.
Bu gozlem event/evidence tarafinda per-video override olarak kullanilmaz; detector `car` diyorsa event/evidence sinifi `car` olarak tasinir.
Bu konu condition classifier ile cozulmez. Motorcycle-focused `VD-EXP-006` denemesi beklenen sonucu vermedigi icin bu baslik simdilik ertelenir; mevcut MVP raporunda ana arac / car detection ve evidence pipeline guvenceye alinir.

Runtime politikasi:

* Raw detector class count korunur ve event/evidence tarafina oldugu gibi tasinir.
* Etkilenen sample, model gelistirme failure case'i olarak kaydedilir.
* Runtime/demo downstream evidence/final-acceptance gate degeri henuz final degildir; `0.60` yalniz mevcut manual review adayidir.
* Zaman kisiti nedeniyle agir vehicle/motorcycle tune yerine diger AI modullerinin baseline/tune asamasina gecilir.

Detay aksiyon dosyasi:

* `testing/reports/vd_exp_002_motorcycle_class_confusion_action.md`
