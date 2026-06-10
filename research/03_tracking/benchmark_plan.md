# Vehicle Tracking Benchmark Plan

Tarih: 2026-06-10

## Amaç

Vehicle detection sonrası araçları kararlı `track_id` ile takip etmek ve tracking çıktısını speed, plate OCR, QoD ve evidence modüllerine güvenilir girdi haline getirmek.

## Aktif Karar

* İlk baseline: `ByteTrack`
* İkinci alternatif: `BoT-SORT` ReID kapalı
* ReID: yalnız ID switch veya occlusion problemi kanıtlanırsa denenir
* Fine-tune: yok

## Deneyler

| Experiment | Tracker | Detector | Source | Status | Amaç |
|---|---|---|---|---|---|
| `TRK-EXP-001` | ByteTrack | selected pretrained detector | `Test/video_1-3.mp4` | Planned | İlk tracking baseline |
| `TRK-EXP-002` | BoT-SORT ReID off | selected pretrained detector | `Test/video_1-3.mp4` | Planned | ByteTrack alternatif kıyası |
| `TRK-EXP-003` | BoT-SORT ReID on | selected pretrained detector | `Test/video_1-3.mp4` | Optional | ID switch problemi varsa |
| `TRK-EXP-004` | OC-SORT | selected pretrained detector | `Test/video_1-3.mp4` | Optional | Üçüncü aday |
| `TRK-EXP-005` | Kalman + IoU | selected pretrained detector | `Test/video_1-3.mp4` | Optional | Debug fallback |

## Sabit Protokol

* Source resolution: mevcut test videosu, gerekirse 720p resize.
* Detector: vehicle detection fazında seçilen pretrained baseline.
* Tracker input: bbox, class, confidence, frame ID, timestamp.
* Tracker output: track ID, bbox history, stable class, track stability, speed trail, best frame candidate.
* Video artifacts: Git dışında `runs/` altında.
* Küçük sonuç dosyaları: CSV/JSON/Markdown olarak Git'e eklenebilir.

## Makine Metrikleri

* processed frame count
* active track count
* new track count
* lost track count
* recovered track count
* mean tracker latency ms
* p95 tracker latency ms
* pipeline FPS
* average track age
* average missing frame count
* class switch raw count
* class switch suppressed count

## Manuel Metrikler

* selected visible target count
* correct continuous track count
* ID switch count
* fragmentation count
* lost and recovered correctly
* class stability score
* speed trail usable
* plate temporal voting usable
* evidence track usable
* reviewer notes

## Karar Kriterleri

İlk baseline tracker seçiminde öncelik:

1. Track ID sürekliliği.
2. ID switch azlığı.
3. Kısa detection kayıplarında toparlama.
4. Class flicker'ı track-level smoothing ile yönetebilme.
5. Speed trail kullanılabilirliği.
6. Plate/evidence crop seçimine katkı.
7. p95 latency ve pipeline FPS.
8. Lisans riski.

## Başarı Eşiği

Ground truth olmadığı için ilk eşikler manual review tabanlıdır:

* seçilen hedef araçların çoğunda ID sürekliliği korunmalı,
* kısa false negative sonrası track tamamen parçalanmamalı,
* 2-3 frame class flicker `stable_class` çıktısını bozmamalı,
* speed trail görsel olarak tutarlı olmalı,
* evidence için best frame/crop seçilebilir olmalı.

## Sonraki Adım

`TRK-EXP-001` ve `TRK-EXP-002` tamamlandıktan sonra:

* tracker baseline seçilecek,
* `TrackingOutput` contract alanları kesinleştirilecek,
* target vehicle selection modülüne geçilecek,
* speed baseline ve plate OCR temporal voting için track history kullanılacak.
