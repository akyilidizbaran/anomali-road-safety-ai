# MVP, Final Architecture ve Future Scope

## Neden Üç Seviyeli Kapsam Gerekli?

Projenin mimari kapsamı geniştir; ancak ilk çalışan MVP daha dar ve gerçekçi olmalıdır. Bu ayrım yapılmazsa repo ve rapor, henüz uygulanmamış modüller için fazla iddialı görünebilir.

## A) Core MVP

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

## B) Final Architecture Scope

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
   * MVP'de relative speed / motion anomaly fallback.
   * Final scope'ta calibrated homography-based km/h denemesi.
   * Relative speed / motion anomaly fallback if calibration does not exist.

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

## C) Future / Research Scope

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
