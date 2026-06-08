# Runtime AI Pipeline Mimarisi

## Purpose of the Runtime AI Pipeline

Runtime AI pipeline, mobil kameradan gelen canlı frame verisini uçtan uca işleyerek yol güvenliği açısından anlamlı, açıklanabilir ve denetlenebilir olay kayıtlarına dönüştüren yapay zeka çalışma hattıdır.

Bu pipeline tek bir monolitik model olarak tasarlanmaz. Ana omurga araç tespiti, takip ve hedef araç seçimi üzerine kurulur. Ağır uzman modeller yalnız gerektiğinde, riskli/hedef araç veya olay penceresi üzerinde çalışır.

Sistem şu sınırla anlatılmalıdır:

* Sistem karar destek ve erken uyarı mimarisidir.
* Otomatik ceza veya hukuki yaptırım sistemi değildir.
* Model çıktıları risk skoru, güven skoru, karar gerekçesi ve evidence package üretmek için kullanılır.
* Uygulama iddiası ile mimari/final kapsam iddiası ayrı tutulur.

## Live Frame Input and Metadata

Canlı frame mobil uygulamadan edge/backend inference katmanına gönderilir. MVP için ilk teknik sözleşme frame input contract olmalıdır.

Zorunlu metadata:

* `session_id`: doğrulanmış kullanıcı/cihaz oturumu.
* `frame_id`: benzersiz frame kimliği.
* `timestamp_utc`: UTC zaman damgası.
* `device_id`: mobil cihaz kimliği.
* `camera_mode`: `live`, `controlled_video`, `offline_replay`.
* `resolution`: ör. `1280x720`; demo hedefi 720p source frame.
* `fps`: kamera veya stream FPS bilgisi.
* `orientation`: portrait/landscape veya rotation.

Opsiyonel metadata:

* `gps_context`: demo politikası izin veriyorsa konum bağlamı.
* `network_type`: 5G/Wi-Fi/local.
* `qod_available`: QoD servisinin kullanılabilirliği.
* `calibration_profile_id`: hız kestirimi için kamera/yol kalibrasyonu.

## Frame Preprocessing

Frame preprocessing, modellerin ortak input formatını hazırlar.

Adımlar:

1. Frame decode.
2. Resolution normalize.
3. Color conversion.
4. Timestamp/frame ID binding.
5. Optional stabilization metadata.
6. Model input resize.
7. Quality analysis için temel görüntü metrikleri.

Preprocessing çıktısı her frame için izlenebilir olmalıdır. Bir model output'u daha sonra event JSON'a girdiğinde hangi frame'den üretildiği açık kalmalıdır.

İlk demo varsayımı: Android cihaz 720p seviyesinde canlı frame/stream üretir; MacBook üzerinde çalışan local edge/backend bu input'u seçilen modelin beklediği input boyutuna resize eder. Colab eğitim/fine-tune ortamıdır, canlı demo runtime ortamı değildir.

## Frame Quality Analysis

Frame quality analysis, model güvenini ve QoD adaylığını etkileyen görüntü kalitesi sinyallerini üretir.

Örnek sinyaller:

* Blur score.
* Brightness/low-light score.
* Contrast.
* Compression artifact signal.
* Occlusion estimate.
* Frame drop veya timestamp jitter.

Bu modül tek başına alarm üretmez. Karar routing, model confidence yorumu ve evidence quality selector için bağlam üretir.

## Scene / Weather / Visibility Analysis

Scene/weather/visibility analysis, ortam koşullarını sınıflandırır.

Çıktılar:

* `weather`: clear, rain, fog, snow, unknown.
* `lighting`: day, dusk, night, low_light, glare, unknown.
* `visibility`: good, limited, poor, unknown.
* `road_surface`: dry, wet, unknown.
* `confidence`: sınıflandırma güveni.

Bu modül düşük frekansta çalışabilir. Örneğin 1-2 Hz, çoğu demo için yeterlidir. Detection ve tracking hattını bloklamamalıdır.

## Vehicle Detection

Vehicle detection runtime pipeline’ın kök modelidir.

Neden kök model?

* Tracking, hedef araç seçimi ve ROI üretimi detection çıktısına bağlıdır.
* Plaka, hız, lane ilişkilendirme ve risk analizi hedef araç üzerinden yapılır.
* MVP’nin ilk model geliştirme odağı araç tespitidir.

Çıktılar:

* Vehicle bbox.
* Class name: car, bus, truck, motorcycle vb.
* Confidence.
* Frame ID.
* Model version.

MVP’de araç tespiti tüm araçları hafif şekilde bulmalıdır. Ağır uzman analizler tüm araçlar için çalıştırılmaz.

## Vehicle Tracking

Vehicle tracking, frame'ler arası araç sürekliliğini kurar.

Amaç:

* Track ID üretmek.
* Hedef araç sürekliliğini korumak.
* Ani yanal hareket, hız şüphesi ve kaybolma riskini izlemek.
* Uzman modellerin aynı araca ait çıktıları birleştirmesini sağlamak.

Tracking, detection sonrası yüksek frekanslı çalışmalıdır. ByteTrack/BoT-SORT benzeri yaklaşımlar araştırma adayıdır; nihai seçim benchmark sonrası yapılmalıdır.

## Target Vehicle Selection

Target vehicle selection, normal modda izlenen araçlar arasından detaylı analiz için öncelikli aracı seçer.

Sinyaller:

* Bbox büyüklüğü.
* Kamera merkezine yakınlık.
* Detection confidence.
* Track stability.
* Plaka görünürlüğü.
* Lane/road position.
* Preliminary risk score.
* External road user yakınlığı.

MVP ve ana demo single-target mode ile tasarlanır. Multi-target mode final/future genişletme olarak korunur.

## Target ROI Generation

Target ROI generation, uzman modellerin tüm frame yerine hedef bölge üzerinde çalışmasını sağlar.

ROI tipleri:

* Target vehicle crop.
* Plate candidate crop.
* Lane/road region around target.
* Speed tracking window.
* Windshield/cabin candidate region.
* External road user proximity region.

ROI tabanlı çalışma latency ve kaynak kullanımını düşürür.

## Normal Mode

Normal mode sürekli çalışan hafif analiz hattıdır.

Normal mode çalışmaları:

* Frame preprocessing.
* Frame quality analysis.
* Scene/visibility context.
* Vehicle detection.
* Multi-vehicle lightweight tracking.
* Target vehicle selection.
* External road user lightweight signal.
* Preliminary risk score.
* Live overlay response.

Normal mode’da OCR, speed, lane, cabin gibi ağır uzmanlar her frame’de çalışmaz.

## Critical Mode

Critical mode, riskli araç veya anlamlı yol güvenliği olayı sinyali oluştuğunda devreye girer.

Tetikleyici örnekleri:

* Risk score threshold aşımı.
* Ani yanal hareket.
* Track stability yüksek ve plaka görünürlüğü yeterli.
* Hız şüphesi.
* Lane/road marking yakınlığı.
* Düşük görüş + model belirsizliği.
* Yaya/bisikletli/motosikletli yakınlığı.

Critical mode’da yalnız ilgili uzman modeller çağrılır ve event fusion yapılır.

## Expert Model Routing

Expert routing, hangi uzman modelin ne zaman çalışacağını belirleyen context-gated policy katmanıdır.

Routing girdileri:

* Scene/visibility context.
* Frame quality metrics.
* Detection confidence.
* Track stability.
* Target vehicle ROI quality.
* Plate visibility.
* Lane visibility.
* Track history length.
* Calibration availability.
* External user proximity.
* Current risk score.
* QoD availability.

Routing çıktıları:

* `experts_to_call`.
* `routing_reasons`.
* `qod_status`.
* `target_roi`.
* `fallback_mode`.

Policy örneği `architecture/contracts/expert_routing_policy.example.json` altında tutulur.

## Plate Detection and OCR Expert

Plate expert, hedef araç ROI içinde plaka bölgesini bulur ve OCR sonucunu üretir.

Çalışma koşulları:

* Target vehicle stable olmalı.
* Plate visibility yeterli veya kritik olay için gerekli olmalı.
* Görüntü kalitesi çok düşükse QoD candidate olabilir.

Çıktılar:

* Plate bbox.
* Plate detected status.
* OCR text.
* Format validity.
* OCR confidence.
* Failure reason: blur, low_light, not_visible, not_run.

MVP içinde plate detection/OCR önceliklidir.

## Lane / Road Marking Expert

Lane expert, hedef aracın şerit/road marking ilişkisini değerlendirir.

Çalışma koşulları:

* Lane/road marking görünürlüğü yeterli.
* Hedef araç lane boundary’ye yakın.
* Ani yanal hareket veya şerit ihlali şüphesi var.

Çıktılar:

* Lane status.
* Lane boundary proximity.
* Lane risk level.
* Confidence.
* Failure reason: marking_not_visible, low_visibility, not_run.

## Speed Estimation Expert

Speed estimation iki modlu tasarlanmalıdır.

MVP aşamasında bu uzman mutlak km/s üretmek zorunda değildir. Kalibrasyon denemesi final scope'ta tutulur; MVP'de relative speed veya motion anomaly çıktısı kullanılabilir.

### Mode A: Calibrated Homography-Based km/h

Bu mod yalnız kamera/yol kalibrasyonu veya güvenilir referans mesafe varsa kullanılmalıdır.

Girdiler:

* Track history.
* Calibration profile.
* Frame timestamps.
* Reference plane/scale.

Çıktılar:

* Estimated km/h.
* Confidence.
* Calibration profile ID.
* Estimation window.

### Mode B: Uncalibrated Relative Speed / Motion Anomaly Fallback

Kalibrasyon yoksa sistem mutlak km/s iddiası kurmamalıdır. Bunun yerine göreli hız veya motion anomaly sinyali üretmelidir.

Çıktılar:

* Relative motion score.
* Motion anomaly label.
* Direction/trajectory change.
* Confidence.

## Driver / Passenger / Cabin Risk Expert

Cabin risk dış kameradan her zaman güvenilir değildir. Bu uzman yalnız görünürlük yeterliyse çalışmalıdır.

Çalışma koşulları:

* Windshield/cabin visibility sufficient.
* Hedef araç crop içinde cabin bölgesi görülebilir.
* Kontrollü video veya final genişletme senaryosu uygundur.

Çıktılar:

* Visibility: good, limited, poor, not_visible.
* Driver detected.
* Passenger count if reliable.
* Phone risk / seatbelt status only if confidence sufficient.
* Unknown state when not reliable.

Cabin risk MVP zorunlu çıktısı değildir; final/future genişletme olarak korunur.

## External Road User / Pedestrian Expert

External road user expert, araç dışı kullanıcıları ve riskli araca yakınlıklarını değerlendirir.

Sınıflar:

* Pedestrian.
* Bicycle.
* Motorcycle.
* Roadside human.
* Traffic officer/demo person, kontrollü senaryoda.

Çıktılar:

* User type.
* Bbox.
* Confidence.
* Relative position.
* Risk relation to target vehicle.

Bu modül normal modda hafif sinyal, kritik modda hedef araç yakınlığı bağlamı olarak çalışabilir.

## Risk Score Calculation

Risk score başlangıçta rule-based olabilir.

Sinyaller:

* Target vehicle track stability.
* Detection confidence.
* Scene/visibility risk.
* Plate/OCR status.
* Lane proximity.
* Speed anomaly.
* External road user proximity.
* Cabin risk if visible.
* Model uncertainty.
* Evidence quality.

Risk seviyeleri:

| Score | Level |
|---:|---|
| 0.00-0.30 | low |
| 0.30-0.60 | medium |
| 0.60-0.80 | high |
| 0.80-1.00 | critical |

## QoD Candidate Decision

QoD her riskte otomatik aktif olmaz.

QoD candidate olabilecek durumlar:

* Risk yüksek ama görüntü/evidence kalitesi düşük.
* Plaka/OCR kritik ama bulanık.
* Düşük ışık/görüş model güvenini azaltıyor.
* Hedef araç kısa süre içinde kaybolabilir.
* Network/video quality karar güvenini etkiliyor.

QoD status değerleri:

* `not_available`
* `mock_ready`
* `not_needed`
* `candidate`
* `requested`
* `active`
* `failed`

## Event Fusion

Event fusion, farklı model çıktılarının tek olay objesinde birleştirilmesidir.

Fusion girdileri:

* Frame metadata.
* Target vehicle.
* Scene/visibility.
* Expert outputs.
* Risk score.
* Routing decision.
* QoD status.
* Model versions.

Fusion çıktısı:

* Event JSON.
* Evidence references.
* User-level explanation input.

## Event JSON Generation

Event JSON, teknik kanıtın ana sözleşmesidir.

Ana kaynak:

* `architecture/contracts/event.schema.json`

Event JSON partial expert output desteklemelidir. Normal modda bazı uzmanlar çalışmadıysa ilgili alanlar `not_run`, `not_available`, `unknown` veya boş obje olarak temsil edilebilir.

## Evidence Package Generation

Evidence package, kritik veya anlamlı olayın denetlenebilir kayıt paketidir.

İçerik:

* Original frame reference.
* Overlay screenshot reference.
* Target vehicle crop.
* Plate crop if available.
* Event JSON.
* Called expert models.
* Model versions.
* Confidence scores.
* Risk reasons.
* QoD status.
* Latency/FPS metadata.

Gerçek evidence görselleri Git reposuna commit edilmez.

## Optional LLM Explanation Layer

LLM karar verici değildir.

LLM yalnız structured event JSON ve model output alanlarından kullanıcı dostu açıklama üretir. LLM yeni risk kararı veremez, model çıktısını değiştiremez ve hukuki hüküm kuramaz.

Fallback:

* LLM API yoksa local LLM kullanılabilir.
* Local LLM yoksa template açıklama kullanılabilir.

## Model Frequency Plan

Detaylı frekans planı:

* `docs/04_yapay_zeka/11_model_frekans_latency_budget.md`

Kısa özet:

* Camera preview 30 FPS hedefleyebilir.
* Vehicle detection 15-30 FPS aralığında hedeflenir.
* Tracking yüksek frekansta çalışır.
* Scene/weather 1-2 Hz olabilir.
* OCR event-based veya 5-10 frame penceresiyle çalışır.
* Heavy expert modeller her frame’de çalışmaz.

## Latency / FPS Budget

30 FPS ifadesi yalnız kamera preview hedefi olarak kullanılmalıdır. Bu, tüm uzman modellerin 30 FPS çalışacağı anlamına gelmez.

Runtime mimari gerçek zamanlı davranışı şu şekilde korur:

* Normal mode hafif tutulur.
* Tracking yüksek frekanslıdır.
* Heavy experts ROI ve event-based çalışır.
* QoD yalnız seçici aday durumunda devreye alınır.
* Evidence generation event-based çalışır.

## MVP Scope vs Final Architecture Scope vs Future Scope

Detaylı scope ayrımı:

* `docs/04_yapay_zeka/12_mvp_final_future_scope.md`

Kısa ayrım:

* Core MVP: frame contract, detection, tracking, target selection, plate/OCR, event JSON, evidence metadata.
* Final architecture: scene/weather, lane, speed, risk scoring, QoD, expanded evidence, optional LLM.
* Future/research: robust cabin risk, multi-target traffic mode, learned risk model, real 5G QoD experiments.

## Technical Risks and Fallbacks

Detaylı risk register:

* `docs/04_yapay_zeka/13_ai_module_risk_register.md`

Ana fallbacks:

* Speed: calibrated km/h yoksa relative speed / motion anomaly.
* Cabin: visibility yetersizse not_visible/unknown.
* OCR: low light/blur durumunda QoD candidate veya not_reliable.
* Lane: poor visibility durumunda düşük confidence ve fallback risk reason.
* Dataset: public dataset lisansı doğrulanmadan model kararı finalleştirilmez.
* LLM: API/local yoksa template explanation.
