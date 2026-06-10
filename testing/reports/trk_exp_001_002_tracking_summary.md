# TRK-EXP-001 / TRK-EXP-002 Tracking Summary

Tarih: 2026-06-10

## Amaç

Vehicle detection sonrası ilk tracking baseline koşularını çalıştırmak ve ByteTrack ile BoT-SORT ReID-off davranışını aynı test videoları üzerinde karşılaştırmak.

## Koşu Parametreleri

| Alan | Değer |
|---|---|
| Detector | `yolo11n.pt` |
| Detector durumu | Interim pretrained detector |
| Tracker 1 | ByteTrack / `bytetrack.yaml` |
| Tracker 2 | BoT-SORT / `botsort.yaml`, `with_reid: False` |
| Video seti | `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4` |
| Condition profile | `dark` |
| Input size | `640` |
| Confidence threshold | `0.25` |
| Vehicle classes | `car`, `motorcycle`, `bus`, `truck` |
| Device | `mps` |

## Otomatik Sonuç Özeti

| Deney | Tracker | Frame | Track gözlemi | Unique track | Ortalama pipeline ms | P95 pipeline ms | Wall FPS | Ortalama track yaşı | Raw class switch | Suppressed class switch |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `TRK-EXP-001` | ByteTrack | 1263 | 1371 | 15 | 17.665 | 25.284 | 31.742 | 111.014 | 15 | 29 |
| `TRK-EXP-002` | BoT-SORT ReID-off | 1263 | 1373 | 15 | 28.470 | 34.986 | 23.771 | 111.042 | 14 | 38 |

Not: Pipeline latency, Ultralytics `model.track()` çağrısının detector + tracker birleşik süresidir. Saf tracker update latency değildir.

## İlk Yorum

ByteTrack bu koşuda daha hızlıdır:

* Daha düşük ortalama pipeline latency.
* Daha düşük p95 pipeline latency.
* Daha yüksek wall FPS.

BoT-SORT ReID-off bu koşuda raw class switch sayısını 1 adet azaltmıştır; ancak daha yüksek latency üretmiştir. Bu fark tek başına BoT-SORT'a geçmek için yeterli değildir. ID switch, fragmentation, speed trail ve evidence usability manuel review ile doğrulanmalıdır.

## Üretilen Artifactler

JSON özetleri:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-summary.json`
* `models/benchmarks/artifacts/TRK-EXP-002-yolo11n-botsort-summary.json`

Lokal annotated videolar:

* `runs/tracking/TRK-EXP-001-yolo11n-bytetrack/video_1_tracked.mp4`
* `runs/tracking/TRK-EXP-001-yolo11n-bytetrack/video_2_tracked.mp4`
* `runs/tracking/TRK-EXP-001-yolo11n-bytetrack/video_3_tracked.mp4`
* `runs/tracking/TRK-EXP-002-yolo11n-botsort/video_1_tracked.mp4`
* `runs/tracking/TRK-EXP-002-yolo11n-botsort/video_2_tracked.mp4`
* `runs/tracking/TRK-EXP-002-yolo11n-botsort/video_3_tracked.mp4`

Annotated videolar büyük artifact olduğu için Git'e eklenmez.

## Manuel Review Gerekenler

Şu alanlar otomatik olarak kesin değerlendirilemez:

* ID switch count.
* Fragmentation count.
* Lost/recovered correctness.
* Speed trail usability.
* Plate temporal voting usability.
* Evidence track usability.

Manuel inceleme için şablon:

* `testing/templates/manual_tracking_review.csv`

## Geçici Karar

Manuel review tamamlanana kadar **ByteTrack aktif baseline olarak korunur**.

Gerekçe:

* Aynı unique track sayısına ulaşmıştır.
* BoT-SORT'a göre daha düşük latency ve daha yüksek FPS vermiştir.
* BoT-SORT'un class switch avantajı bu otomatik koşuda çok küçüktür.

BoT-SORT ReID-off ikinci alternatif olarak kalır. ReID açık mod (`TRK-EXP-003`) yalnız manuel review sonucunda ID switch / occlusion problemi kanıtlanırsa çalıştırılmalıdır.
