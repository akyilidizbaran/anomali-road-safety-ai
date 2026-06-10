# Next Phase - Track Output to Target and Event Pipeline

Tarih: 2026-06-10

Son uygulama güncellemesi: 2026-06-11

## Durum

ByteTrack, mevcut dark test videolarında manuel gözlemle iyi çalışıyor. Otomatik benchmarkta da BoT-SORT ReID-off'a göre daha düşük pipeline latency ve daha yüksek FPS verdi.

Bu nedenle sıradaki iş yeni tracker aramak değildir. Sıradaki iş, ByteTrack çıktısını sistemin karar ve evidence hattına bağlamaktır.

## 2026-06-11 Uygulama Durumu

İlk track-to-event implementation tamamlandı.

Eklenen script:

* `scripts/benchmarks/build_track_event_skeleton.py`

Güncellenen tracking benchmark script'i:

* `scripts/benchmarks/run_tracking_baseline.py`
* Track summary artık `center_history_sample`, `bbox_history_sample` ve `history_sample_strategy` alanlarını üretir.

Üretilen artifactler:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-track-postprocess.json`
* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`
* `testing/reports/trk_exp_001_track_to_event_summary.md`

Bu implementation gerçek risk kararı üretmez. Amacı ByteTrack sonucunu `track_stability`, `target_selection_score`, `selected_target_track_id` ve `target_vehicle_selected` event skeleton'ına dönüştürmektir.

## Önerilen Sonraki Faz

Faz adı:

**Track Post-Processing + Target Vehicle Selection + First Event/Evidence Skeleton**

## Neden Bu Faz?

Plate OCR, speed estimation, QoD ve risk decision modüllerinin tamamı güvenilir `track_id` ve hedef araç seçimine bağlıdır.

ByteTrack iyi çalışıyorsa, doğrudan plaka veya hız modeline geçmek yerine önce şu ara katmanlar tamamlanmalıdır:

1. Track çıktısı normalize edilmeli.
2. Track state store kurulmalı.
3. Class voting / confidence smoothing uygulanmalı.
4. `track_stability` metriği üretilmeli.
5. Hedef araç seçimi yapılmalı.
6. İlk event/evidence JSON skeleton'ı oluşturulmalı.

Bu katman kurulmadan plate OCR veya speed çıktısı yanlış araca bağlanabilir.

## Yapılacaklar

### 1. Tracking Output Normalizer

Durum: İlk implementation tamamlandı.

Ultralytics tracking sonucu, proje contract'ına çevrilir.

Girdi:

* `result.boxes.id`
* `result.boxes.xyxy`
* `result.boxes.xywh`
* `result.boxes.cls`
* `result.boxes.conf`
* `frame_id`
* `timestamp_utc`

Çıktı:

* `TrackingOutput`
* `track_id`
* `bbox`
* `center_xy`
* `class_name`
* `raw_confidence`
* `tracker_version`

### 2. Track State Store

Durum: İlk implementation tamamlandı.

Her track için kısa süreli state tutulur.

Tutulacak alanlar:

* track start frame,
* last seen frame,
* seen frame count,
* missed frame count,
* bbox history,
* center history,
* class votes,
* confidence history,
* best frame candidate,
* best crop candidate.

### 3. Class Voting ve Confidence Smoothing

Durum: İlk implementation tamamlandı.

Amaç:

* 2-3 frame `car -> motorcycle` gibi flicker davranışını bastırmak.
* Tek frame class değişimini final karar olarak kabul etmemek.

Başlangıç kuralı:

* Son 15-30 frame ağırlıklı class voting.
* Confidence ile ağırlıklandırılmış oy.
* Track yaşı 5 frame altındaysa `stable_class = unstable`.
* Ani class değişimi en az 3-5 ardışık frame desteklenmedikçe kabul edilmez.

### 4. Track Stability Score

Durum: İlk implementation tamamlandı.

`track_stability`, uzman model çağırma ve event güveni için kullanılacak ana sinyaldir.

Önerilen bileşenler:

* track age,
* missed frame oranı,
* bbox jitter,
* confidence smoothing,
* class stability,
* ID switch suspicion.

İlk değer aralığı:

* `0.0 - 1.0`

Örnek yorum:

* `>= 0.75`: plate/speed/evidence için uygun
* `0.50 - 0.75`: düşük güvenli aday
* `< 0.50`: uzman model çağırma ertelenir veya düşük güvenle işaretlenir

### 5. Target Vehicle Selection

Durum: İlk implementation tamamlandı.

Normal modda tüm araçlar izlenir; ağır uzmanlar yalnız hedef/riskli track için çağrılır.

Başlangıç skor bileşenleri:

* track stability,
* bbox büyüklüğü,
* frame merkezine yakınlık,
* confidence,
* track age,
* plaka görünürlüğü ihtimali,
* motion anomaly başlangıç sinyali.

Çıktı:

* `target_track_id`
* `target_score`
* `selection_reasons`
* `target_bbox`
* `target_roi`

### 6. First Event / Evidence Skeleton

Durum: İlk implementation tamamlandı.

Bu fazda gerçek risk modeli şart değildir. İlk amaç, track tabanlı event/evidence contract'ın çalışmasıdır.

İlk event tipi:

* `tracking_candidate_event`
* `target_vehicle_selected`
* `motion_candidate`

Evidence alanları:

* event ID,
* frame window,
* track ID,
* stable class,
* bbox history sample,
* center history sample,
* best frame,
* best crop,
* tracker version,
* track stability,
* decision reason.

## Çıkış Kriterleri

Bu faz tamamlanmış sayılırsa:

* [x] ByteTrack output'u `TrackingOutput` contract'ına çevriliyor olmalı.
* [x] Track state store çalışıyor olmalı.
* [x] Class flicker `stable_class` ile bastırılıyor olmalı.
* [x] `track_stability` hesaplanıyor olmalı.
* [x] En az bir `target_track_id` seçiliyor olmalı.
* [x] İlk event/evidence JSON örneği üretilebiliyor olmalı.

## Sonraki Faz

Bu fazdan sonra önerilen sıra:

1. Speed baseline: track center displacement + relative speed.
2. Plate detection/OCR: target ROI üstünde plate detector + OCR temporal voting.
3. Condition profile: düşük frekanslı scene/weather/visibility routing.
4. QoD policy: target/evidence quality üzerinden candidate/request/active kararı.

## Ertelenenler

* BoT-SORT ReID-on: yalnız ID switch problemi kanıtlanırsa.
* OC-SORT: yalnız ByteTrack/BoT-SORT yetersiz kalırsa.
* Fine-tune: track-to-event omurgası çalışmadan açılmamalı.
