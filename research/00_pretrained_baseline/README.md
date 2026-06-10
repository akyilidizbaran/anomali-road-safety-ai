# System-Wide Pretrained Baseline Plan

Tarih: 2026-06-10

## Amaç

Bu dosya, `pretrained baseline` ifadesinin proje genelindeki anlamını netleştirir.

Bu aşamada hedef yalnız araç tespit modeli seçmek değildir. Hedef, araç tespiti, takip, hız yaklaşımı, plaka tespiti/OCR, yol/şerit/tabela, ortam koşulu ve cabin risk gibi tüm AI modüllerinin önce dış kaynaklı pretrained model veya doğrulanabilir algoritmik baseline ile uçtan uca çalışır hale gelmesidir.

Fine-tune bu aşamada yapılmaz. Her modül önce hazır model / hazır ağırlık / açık kaynak çalışma / algoritmik baseline ile denenir. Tüm baseline omurga çalışınca faz faz fine-tune'a dönülür.

## Temel Karar

Pretrained baseline şu anlama gelir:

* Her AI modülü için sıfırdan eğitim yapılmadan ilk çalışan inference hattı kurulur.
* Dış veri setleri, açık kaynak pretrained ağırlıklar ve resmi model dokümanları kullanılır.
* Çıktılar ortak event/evidence contract yapısına çevrilir.
* Hangi modülün gerçekten ayrı model çağrısı gerektirdiği ayrılır.
* Tracking, hız, QoD ve evidence gibi bazı adımların model değil algoritma/policy katmanı olduğu açık tutulur.

## Runtime Model Call Sırası

### 0. Frame Input ve Quality Metrics

Çağrı tipi: **Model değil, görüntü işleme / metadata katmanı**

Çalışma zamanı:

* Her frame veya düşük maliyetle sürekli.

Üretilen sinyaller:

* blur score,
* brightness,
* contrast,
* compression artifact,
* frame drop / jitter,
* source resolution,
* timestamp integrity.

Neden ayrı pretrained model değil?

Bu aşama alarm üretmez. Diğer modellerin güven skorunu ve QoD adaylığını yorumlamak için bağlam üretir. İlk baseline OpenCV / NumPy tabanlı metriklerle kurulmalıdır.

### 1. Condition Profile / Scene-Weather-Visibility

Çağrı tipi: **Ayrı düşük frekanslı model çağrısı**

Başlangıç baseline:

* CLIP / zero-shot image classification ile `day`, `night`, `low_light`, `rain`, `fog`, `clear`, `wet_road` gibi etiketleri kaba sınıflandırma.
* Alternatif olarak ImageNet/ResNet/EfficientNet tabanlı classifier + prompt/label mapping.
* Fine-tune aşamasında BDD100K `weather`, `timeofday`, `scene` attribute'ları kullanılabilir.

Çalışma zamanı:

* 1-2 Hz yeterli.
* Detection hattını bloklamaz.
* Frame-level değil, kısa pencere/scene-level karar üretir.

Routing etkisi:

* Hangi vehicle detector profile'ının çağrılacağına sinyal verir.
* QoD adaylığına katkı verir.
* OCR/hız/lane güven skorlarını yorumlar.

Not:

Condition profile doğrudan aracı bulmaz. Ana görevi detector ve uzman model routing için bağlam üretmektir.

### 2. Vehicle / Road Object Detection

Çağrı tipi: **Ana kök model çağrısı**

Başlangıç baseline:

* YOLO11n / YOLO11s pretrained COCO.
* YOLOv10n pretrained düşük latency challenger.
* YOLOv8n pretrained stabil fallback.

İzlenecek sınıflar:

* `car`,
* `motorcycle`,
* `bus`,
* `truck`,
* gerekirse `person`, `bicycle`.

Çalışma zamanı:

* Normal modda yüksek frekans.
* Tüm araçları hafif şekilde bulur.

Neden kök model?

Tracking, hız, plaka ROI, lane ilişkisi, external road user proximity ve risk scoring bu çıktıya bağlıdır.

Baseline sonrası fine-tune:

* BDD100K / UA-DETRAC / seçilecek açık kaynak road-domain datasetleriyle condition-aware general vehicle detector.
* Sonra yalnız faydası kanıtlanan `night_low_light`, `rain`, `fog_low_visibility` specialist dalları.

### 3. Vehicle Tracking

Çağrı tipi: **Ayrı model değil, detector üstü tracking algoritması**

Başlangıç baseline:

* ByteTrack.
* BoT-SORT.

Çalışma zamanı:

* Detection sonrası her frame veya detector frekansında.

Üretilen çıktı:

* `track_id`,
* track age,
* trajectory,
* class voting,
* confidence smoothing,
* missing frame tolerance.

Neden model değil?

Tracking, frame bazlı bbox'ları zaman içinde aynı fiziksel araca bağlar. Başlangıçta ayrı eğitim gerektirmez. ReID gerekiyorsa BoT-SORT tarafında ek model/embedding sonradan değerlendirilebilir.

Önemli:

Mevcut `car -> motorcycle` gibi 2-3 frame class flicker hataları ilk önce track-level voting ile çözülmelidir, fine-tune ile değil.

### 4. External Road User / Roadside Object Signal

Çağrı tipi: **Başlangıçta ayrı model değil, ana detector sınıfları**

Başlangıç baseline:

* Vehicle detector içindeki `person`, `bicycle`, `motorcycle` sınıfları.

Çalışma zamanı:

* Normal modda düşük maliyetli sinyal.

Ayrı model ne zaman gerekir?

* Yaya/bisikletli false negative yüksek çıkarsa,
* küçük obje performansı yetersizse,
* risk senaryolarında external road user proximity ana kriter haline gelirse.

O zaman ayrı pedestrian/cyclist detector veya road-user specialist açılır.

### 5. Target Vehicle Selection

Çağrı tipi: **Model değil, scoring / policy katmanı**

Girdi:

* bbox büyüklüğü,
* merkeze yakınlık,
* track stability,
* detection confidence,
* plaka görünürlüğü ihtimali,
* condition profile,
* external road user yakınlığı,
* preliminary motion anomaly.

Çıktı:

* `target_track_id`,
* `target_roi`,
* `risk_candidate_score`.

Neden model değil?

İlk baseline açıklanabilir olmalı. Bu katman rule-based score ile başlamalı; ileride supervised risk classifier'a dönüştürülebilir.

### 6. Speed Estimation Expert

Çağrı tipi: **Başlangıçta ayrı pretrained model değil, tracking + geometri algoritması**

Başlangıç baseline:

* Track displacement over time.
* Pixel speed.
* Relative speed class: `slow`, `normal`, `fast`, `suspicious`.
* Kalibrasyon varsa homography / pixel-to-meter dönüşümü.

Çalışma zamanı:

* Track yaşı yeterliyse çalışır.
* Kritik modda hedef araç için daha sık hesaplanır.

Neden ayrı model değil?

Tek kameradan hız tahmini genelde detector + tracker + kamera/yol kalibrasyonu ile yapılır. Pretrained bir "speed model" çağırmak yerine önce iz tabanlı hesaplama kurulmalıdır.

Fallback:

* Kalibrasyon yoksa mutlak km/s iddiası verilmez.
* Relative speed ve motion anomaly kullanılır.

### 7. Plate Detection Expert

Çağrı tipi: **Ayrı uzman detector model çağrısı**

Başlangıç baseline:

* License plate detector pretrained / public weights.
* İlk aşamada hedef araç ROI üzerinde çalışır, tüm frame'de sürekli çalışmaz.
* Türk plakasına özgü fine-tune sonraya bırakılır.

Çalışma zamanı:

* Track stable olduğunda.
* Plaka görünürlüğü yeterli olduğunda.
* Kritik olayda evidence değeri varsa.
* QoD aktif olduğunda daha yüksek kaliteli frame üzerinde tekrar denenebilir.

Çıktı:

* plate bbox,
* plate crop,
* plate visibility score,
* detection confidence.

Neden ayrı model?

COCO vehicle detector plaka kutusu üretmez. Plaka küçük ve yüksek çözünürlük isteyen ayrı bir nesnedir.

### 8. Plate OCR Expert

Çağrı tipi: **Ayrı OCR model çağrısı**

Başlangıç baseline:

* PaddleOCR PP-OCRv5.
* Alternatif: EasyOCR.
* Türk plaka regex + il kodu kontrolü + temporal voting.

Çalışma zamanı:

* Yalnız plate crop üzerinde.
* Tek frame sonucuna güvenilmez; track boyunca birkaç crop birleştirilir.

Çıktı:

* raw OCR text,
* normalized plate candidate,
* OCR confidence,
* regex validity,
* temporal vote score.

Neden ayrı model?

Plate detection yalnız plaka bölgesini bulur. Karakter okuma farklı bir OCR problemidir.

### 9. Traffic Sign / Road Sign Detection

Çağrı tipi: **Kapsam açılırsa ayrı uzman detector/classifier**

Not:

Kullanıcının "plaka tabelası" ifadesi license plate anlamına geliyorsa bu modül MVP için zorunlu değildir. Eğer yol tabelası / trafik levhası da isteniyorsa ayrı modül olarak açılmalıdır.

Başlangıç baseline:

* Traffic sign detector: YOLO tabanlı pretrained veya public TT100K / Mapillary kaynaklı modeller.
* Sign recognition: crop classifier.

Çalışma zamanı:

* Düşük frekans.
* Scene ROI / yol kenarı ROI.
* Kritik event evidence değerine katkı veriyorsa.

Neden ayrı model?

Traffic sign nesneleri küçük, sınıf sayısı fazla ve araç/plaka probleminden farklıdır. Vehicle detector ile aynı çıktıya zorlanmamalıdır.

### 10. Lane / Road Marking / Drivable Area

Çağrı tipi: **Ayrı segmentation / lane model çağrısı**

Başlangıç baseline:

* YOLOP tarzı multi-task driving perception.
* Alternatif lane detection / drivable area segmentation modelleri.

Çalışma zamanı:

* MVP'de plate/evidence sonrası.
* Düşük frekans veya kritik modda hedef araç çevresinde.

Çıktı:

* lane mask / lane lines,
* drivable area,
* target-lane relation,
* lane departure / lane violation signal.

Neden ayrı model?

Şerit ve sürülebilir alan pixel-level veya çizgi-level algı gerektirir; bbox detector çıktısıyla güvenilir kurulmaz.

### 11. Cabin / Driver-Passenger / In-Vehicle Risk

Çağrı tipi: **Final genişletme için ayrı uzman model çağrısı**

Başlangıç baseline:

* Önce cabin visibility gate.
* Görünürlük varsa face/person/pose detection.
* MediaPipe face / pose veya YOLO person/seatbelt/phone specialist adayları.
* Driver distraction datasetleri yalnız araştırma/fine-tune adayı olarak tutulur.

Çalışma zamanı:

* Sürekli çalışmaz.
* Sadece hedef araç ROI ve yeterli windshield/cabin görünürlüğü varsa.
* Kontrollü sürücü videosu ile final demo genişletmesi olarak ele alınır.

Çıktı:

* driver visible,
* passenger visible,
* occupant count estimate,
* phone/seatbelt/smoking gibi risk sinyalleri sadece görünürlük yeterliyse.

Kritik sınır:

Demo kamera açısı dışarı/yol yönünde olduğundan cabin risk güvenilirliği zayıf olabilir. Baseline "analiz güvenilir değil" fallback'ini desteklemelidir.

### 12. Risk Decision / Event Fusion

Çağrı tipi: **Başlangıçta model değil, event fusion policy**

Girdi:

* detection confidence,
* track stability,
* condition profile,
* speed signal,
* plate confidence,
* lane relation,
* external road user proximity,
* QoD status,
* evidence quality.

Çıktı:

* event type,
* risk level,
* confidence,
* decision reason,
* experts called,
* evidence package fields.

Neden model değil?

İlk baseline açıklanabilir olmalı. Event fusion rule-based başlar; veri birikirse supervised risk scorer sonra açılır.

### 13. QoD Orchestration

Çağrı tipi: **Model değil, network/evidence policy**

Çalışma koşulu:

* Riskli/hedef araç var.
* Karar güveni veya evidence kalitesi artacak.
* Network/QoD availability uygun.

Çıktı:

* `qod_status`: not_required, candidate, requested, active, unavailable.
* `qod_reason`.
* video quality escalation request.

Neden model değil?

QoD bir inference modeli değil; ağ kaynağı ve evidence değerini birlikte değerlendiren orchestration katmanıdır.

### 14. LLM Explanation Layer

Çağrı tipi: **Opsiyonel text generation / explanation adapter**

Çalışma zamanı:

* Event JSON üretildikten sonra.
* Canlı karar zincirinde zorunlu değil.

Girdi:

* structured event JSON.

Çıktı:

* Türkçe karar açıklaması,
* rapor/evidence açıklama metni.

Kritik sınır:

LLM karar vermez. Sadece model ve policy çıktısını insan tarafından okunabilir hale getirir.

Fallback:

* API yoksa template-based açıklama.
* Local LLM varsa aynı adapter contract'ı.

## Ayrı Model Çağrısı Gerektiren Modüller

| Sıra | Modül | Ayrı model mi? | Başlangıç baseline | Runtime sıklığı | Fine-tune zamanı |
|---|---|---:|---|---|---|
| 1 | Condition profile | Evet | CLIP / image classifier | 1-2 Hz | BDD100K condition split sonrası |
| 2 | Vehicle detection | Evet | YOLO11n/s, YOLOv10n, YOLOv8n | yüksek | Pretrained kıyas + tracking sonrası |
| 3 | Tracking | Hayır | ByteTrack / BoT-SORT | detector sonrası | gerekirse ReID sonra |
| 4 | External road user | Başta hayır | vehicle detector person/bicycle/motorcycle | normal mod | recall düşükse |
| 5 | Speed estimation | Hayır | tracking + homography/relative speed | track stable | kalibrasyon final scope |
| 6 | Plate detection | Evet | public LP detector | hedef ROI / kritik | Türk plaka verisiyle sonra |
| 7 | Plate OCR | Evet | PaddleOCR / EasyOCR | plate crop | Türk plaka OCR sonra |
| 8 | Traffic sign | Evet, kapsam açılırsa | TT100K/Mapillary tabanlı detector | düşük frekans | Türkiye levha verisi gerekirse |
| 9 | Lane/drivable area | Evet | YOLOP / lane segmentation | düşük/kritik | plate/evidence sonrası |
| 10 | Cabin risk | Evet, final | MediaPipe face/pose + specialist aday | yalnız görünürse | kontrollü sürücü videosu sonrası |
| 11 | Risk fusion | Hayır | rule-based policy | event window | veri birikirse |
| 12 | QoD orchestration | Hayır | policy | event window | model değil |
| 13 | LLM explanation | Opsiyonel | API/local/template | event sonrası | model geliştirme değil |

## Önerilen Aşama Sırası

### Faz A - Detection + Tracking Omurgası

1. Vehicle detection pretrained kıyası.
2. ByteTrack / BoT-SORT entegrasyonu.
3. Track-level class voting.
4. Target vehicle selection.
5. İlk event/evidence JSON.

Bu faz bitmeden plaka, hız ve cabin modellerine geçmek doğru değildir; çünkü hepsi `track_id` ve `target_roi` sürekliliğine bağlıdır.

### Faz B - Plate Baseline

1. Plate detector pretrained/public weights.
2. PaddleOCR / EasyOCR baseline.
3. Türk plaka regex + il kodu validasyonu.
4. Temporal voting.
5. Evidence package içinde plate candidate.

### Faz C - Speed Baseline

1. Track trajectory çıkar.
2. Pixel displacement / frame time ölç.
3. Relative speed class üret.
4. Eğer demo alanında referans ölçüm kurulursa homography ile yaklaşık km/s dene.

### Faz D - Condition Routing

1. Condition profile modelini düşük frekanslı çalıştır.
2. `dark`, `rain`, `fog_low_visibility`, `night_low_light` routing kararını event JSON'a yaz.
3. Detector profile selection için sadece sinyal üret.
4. Fine-tune sonrası specialist detector çağrılarına dön.

### Faz E - Lane / Road / Sign

1. YOLOP veya lane/drivable area baseline.
2. Target-lane relation.
3. Eğer trafik levhası kapsamda kalacaksa TT100K/Mapillary tabanlı sign detector.

### Faz F - Cabin Risk

1. Cabin visibility gate.
2. Face/person/pose baseline.
3. Kontrollü video ile final genişletme.
4. Görünürlük yoksa "analysis_not_reliable".

## Kaynak Notları

* Ultralytics YOLO11 dokümanı, YOLO11'in object detection, segmentation, classification, pose ve OBB görevlerini desteklediğini ve COCO pretrained detect modellerinin kullanılabildiğini gösterir: https://docs.ultralytics.com/models/yolo11/
* Ultralytics tracking dokümanı, Detect/Segment/Pose modelleriyle BoT-SORT ve ByteTrack kullanılabildiğini gösterir: https://docs.ultralytics.com/modes/track/
* YOLOv10 dokümanı, NMS-free real-time object detection yaklaşımını düşük latency challenger olarak değerlendirmek için kullanılabilir: https://docs.ultralytics.com/models/yolov10/
* Ultralytics lisans sayfası, YOLO modellerinde AGPL/Enterprise ayrımının proje lisans kararlarında dikkate alınması gerektiğini gösterir: https://www.ultralytics.com/license
* PaddleOCR PP-OCRv5, çok dilli OCR ve scene text recognition için güçlü bir OCR baseline adayıdır: https://github.com/PaddlePaddle/PaddleOCR
* PaddleOCR Apache-2.0 lisansı OCR tarafında daha permissive bir başlangıç sağlar: https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/LICENSE
* EasyOCR Apache-2.0 lisansı alternatif OCR baseline olarak değerlendirilebilir: https://raw.githubusercontent.com/JaidedAI/EasyOCR/master/LICENSE
* BDD100K, object bbox, weather/time/scene, lane marking ve drivable area gibi çok görevli driving perception etiketleriyle condition-aware fine-tune ve lane/drivable area için ana kaynak adaydır: https://bair.berkeley.edu/blog/2018/05/30/bdd/
* YOLOP, object detection, drivable area segmentation ve lane detection görevlerini birlikte yapan pretrained driving perception baseline adayıdır: https://pytorch.org/hub/hustvl_yolop/
* TT100K, trafik levhası detection/classification için büyük ölçekli benchmark dataset olarak değerlendirilebilir: https://docs.ultralytics.com/datasets/detect/tt100k/
* Mapillary Traffic Sign Dataset, dünya çapında traffic sign bbox/class annotation sağlayan ayrı bir trafik levhası kaynağıdır: https://www.mapillary.com/dataset/trafficsign
* UFPR-ALPR, license plate detection/recognition için gerçek senaryo anotasyonları içeren akademik araştırma veri seti adayıdır: https://web.inf.ufpr.br/vri/databases/ufpr-alpr/
* CCPD, büyük ölçekli license plate detection/recognition benchmark kaynağıdır: https://github.com/detectrecog/ccpd
* MediaPipe Face/Pose modelleri cabin visibility uygunsa driver/passenger sinyali için baseline adaydır: https://developers.google.com/edge/mediapipe/solutions/vision/face_detector ve https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker

## Açık Netleştirme

Şu soru ileride netleşmeli:

* "Plaka tabelası" ile yalnız araç plakası mı kastediliyor, yoksa trafik levhaları da kapsamda mı?

Bu netleşene kadar araç plakası zorunlu baseline, trafik levhası ise ayrı opsiyonel uzman modül olarak tutulur.
