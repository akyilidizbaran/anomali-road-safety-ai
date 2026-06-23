# Cabin / Driver Benchmark Plan

Tarih: 2026-06-12

## Deneyler

| Experiment | Model | Veri | Amaç | Durum |
|---|---|---|---|---|
| `CABIN-EXP-001` | BlazeFace full-range | `Test/video_1-3.mp4` | Ana visibility + driver baseline | script_ready |
| `CABIN-EXP-002` | BlazeFace short-range | aynı videolar | Yakın yüz challenger | script_ready |
| `CABIN-EXP-003` | Seçilen model | enriched event JSON | Temporal sonucu event/evidence hattına bağlama | script_ready |

## Sabit Protokol

* Input event: plate/OCR enriched tracking skeleton.
* Vehicle detector/tracker: `yolo11n.pt` + ByteTrack.
* Target matching: event best-frame bbox ile IoU; fallback en uzun track.
* Final model-selection runs use frame stride `1`.
* Frame stride `5` or `10` is only for quick smoke tests and must not be used
  to judge overlay continuity.
* Face confidence: 0.50.
* View profiles:
  * `video_1.mp4`: `side_driver_window`
  * `video_2.mp4`: `side_driver_window`
  * `video_3.mp4`: `front_lhd`
* Büyük görsel/video artifactleri: `runs/cabin/`.
* Küçük JSON/Markdown sonuçları: Git içinde.

## Otomatik Metrikler

* processed frame count,
* visible frame rate,
* visibility class ve mean score,
* face detection frame rate,
* stable occupant count,
* driver candidate frame/rate,
* mean/p95 face latency,
* best cabin frame ve ROI.

## Manuel Metrikler

* cabin ROI doğruluğu,
* visibility gate doğruluğu,
* face count doğruluğu,
* driver assignment doğruluğu,
* best-frame usability,
* false driver decision.

## Başarı Kriterleri

* Üç videoda visibility sonucu üretilmeli.
* `video_3` için occupant ve driver candidate yakalanmalı.
* `video_1/2` yan/düşük ışık görünümü güvenli biçimde `limited/poor` olarak
  reddedilebilmeli veya desteklenmeli.
* `poor/not_visible` kare tek başına driver kararı üretmemeli.
* YuNet `poor` karelerde overlay/evidence devamlılığı için çalışabilir; bu
  tespitler temporal driver/risk kararına dahil edilmez.
* Phone `null`, seatbelt `unknown` kalmalı.
* Event enrichment mevcut plate alanını ve risk skorunu değiştirmemeli.

## Model Seçimi

Full-range varsayılan seçilir. Short-range'e ancak manuel review'da driver/occupant
tespitini artırırken yanlış pozitif ve p95 latency kabul edilebilir kalırsa geçilir.
