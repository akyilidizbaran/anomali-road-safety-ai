# MVP, Final Architecture ve Future Scope

## Neden Üç Seviyeli Kapsam Gerekli?

Projenin mimari kapsamı geniştir; ancak ilk çalışan MVP daha dar ve gerçekçi olmalıdır. Bu ayrım yapılmazsa repo ve rapor, henüz uygulanmamış modüller için fazla iddialı görünebilir.

## A) FTR Core Submission

FTR Core Submission, resmi değerlendirme sisteminin doğrudan çalıştıracağı Docker tabanlı
çıkarım paketidir.

Must include:

1. **Docker runtime**
   * Root `Dockerfile`.
   * `nvidia/cuda:12.1.0-base-ubuntu22.04` base image.
   * T4 GPU uyumlu inference.

2. **Path contract**
   * Input: `/app/data/input/video.mp4`.
   * Output: `/app/data/output/results.json`.
   * Model directory: `/app/models/`.

3. **FTR JSON output**
   * `video_id`.
   * `arac_bilgisi`.
   * `tespitler`.
   * ASCII-safe exact labels.

4. **Vehicle information**
   * `tip`.
   * `plaka`.
   * `renk`.
   * `confidence_score`.

5. **Timed detections**
   * `sofor_eylemi`.
   * `nesneler`.
   * `yolcular`.

6. **Validation**
   * JSON schema/contract validation.
   * Runtime smoke test.
   * 10 dakika ve 8 GB image limit kontrolü.

## B) Internal Core MVP

Core MVP, ilk çalışan uçtan uca AI hattıdır.

Must include:

1. **Live frame input contract**
   * Frame ID.
   * Timestamp.
   * Source metadata.
   * Resolution/FPS metadata.
   * 720p source frame and model-input resize metadata.

2. **Vehicle detection**
   * Araç bbox.
   * Araç sınıfı.
   * Confidence.
   * Model version.

3. **Vehicle tracking**
   * Track ID.
   * Track stability.
   * Track history.

4. **Target vehicle selection**
   * Hedef araç seçimi.
   * Selection score.
   * Selection reasons.

5. **Lightweight scene/frame quality context**
   * Işık/görüş/blur gibi düşük maliyetli bağlam sinyali.
   * Model confidence ve evidence quality yorumuna destek.
   * Full scene/weather model benchmarkı final scope'ta kalabilir.

6. **Plate detection/OCR**
   * Target vehicle ROI.
   * Plate bbox.
   * OCR text.
   * OCR confidence.
   * Unknown/low confidence states.
   * Türk plaka formatı için ilk yaklaşım: regex, il kodu kontrolü, OCR post-processing ve temporal voting.

7. **Event JSON**
   * `architecture/contracts/event.schema.json`.
   * Partial output support.
   * Model version tracking.

8. **Evidence screenshot and metadata**
   * Original frame reference.
   * Overlay screenshot reference.
   * Target crop reference.
   * Plate crop if available.
   * Risk reasons and confidence scores.

## C) Final Architecture Scope

Final architecture scope, rapor ve final demo için kademeli eklenecek modülleri içerir.

May include:

1. **Scene/weather/visibility**
   * Hava, ışık, görüş.
   * Model confidence yorumunu ve QoD kararını etkiler.

2. **Lane/road marking**
   * Şerit görünürlüğü.
   * Hedef araç lane boundary ilişkisi.
   * Lane risk.

3. **Speed estimation**
   * FTR JSON'da doğrudan hız alanı yoktur.
   * `slalom` veya risk/evidence destek sinyali olarak kullanılabilir.
   * Kalibrasyonsuz bbox geometry grafikleri gürültülü olduğu için final km/s iddiası kurulmaz.
   * Kalibrasyon veya güvenilir depth/fusion olmadan relative/motion anomaly fallback korunur.

4. **Risk scoring**
   * Rule-based başlangıç.
   * Model confidence, track stability, scene context, lane/speed/plate signals.

5. **QoD decision**
   * Riskli araçta candidate/request akışı.
   * Aktiflik yalnız karar güveni veya evidence kalitesi artacaksa.
   * Gerçek API/adapter entegrasyonu hedeflenir; API erişimi yoksa mock/status-policy fallback kullanılır.

6. **Expanded evidence package**
   * Expert outputs.
   * Latency/FPS info.
   * QoD status.
   * Routing decision.

7. **Optional LLM explanation**
   * Structured output açıklaması.
   * Karar verici değil.
   * API/local/template fallback.

## D) Future / Research Scope

Future scope, daha fazla veri, deney ve entegrasyon gerektiren araştırma alanlarıdır.

May include:

1. **Robust cabin risk from external camera**
   * Dış kamera açısından görünürlük sınırlıdır.
   * Yalnız görünürlük yeterliyse çalışır.

2. **Multi-target traffic mode**
   * Birden fazla hedef için uzman model çağrısı.
   * Daha yüksek latency ve kaynak yönetimi gerekir.

3. **Advanced learned risk model**
   * Rule-based routing yerine öğrenilebilir risk fusion.
   * Event-level etiketli veri gerekir.

4. **Large-scale domain adaptation**
   * Farklı yol, ışık, kamera ve hava koşullarına adaptasyon.
   * Lisanslı ve güvenilir veri setleri gerekir.

5. **Real 5G QoD optimization experiments**
   * Gerçek QoD API ve ağ metrikleriyle test.
   * Bitrate/FPS/resolution/priority etkisinin ölçülmesi gerekir.

## Scope Guardrails

* MVP çıktısı final architecture gibi anlatılmamalıdır.
* Mimari kapsam geniş tutulabilir; uygulama kapsamı açık etiketlenmelidir.
* Future/research modülleri için benchmark veya field-performance iddiası kurulmaz.
* Cabin, speed ve QoD özellikle koşullu modüllerdir.

## Repo Etiketleme Kuralı

Her yeni AI dokümanı veya contract şu kapsamlardan biriyle etiketlenmelidir:

* `MVP`
* `Final Architecture`
* `Future / Research`
* `Cross-cutting Contract`
