# AI Module Risk Register

## Amaç

Bu dosya yapay zeka modülleriyle ilgili teknik riskleri ve azaltma stratejilerini listeler. Amaç rapor, demo ve implementation sırasında aşırı iddia veya kırılgan mimari üretmemektir.

## Risk Tablosu

| Risk | Etki | Azaltma |
|---|---|---|
| Too many tasks for MVP | İlk çalışan sistem gecikir ve kapsam bulanıklaşır | MVP’yi frame contract, detection, tracking, target selection, plate/OCR, event JSON ve evidence ile sınırla |
| 30 FPS overclaim risk | Tüm modellerin 30 FPS çalıştığı sanılır | 30 FPS’i camera preview hedefi olarak yaz; ağır uzman modellerin event-based çalıştığını belirt |
| Speed estimation calibration risk | Mutlak km/h iddiası güvenilir olmayabilir | Homography/calibration varsa km/h; yoksa relative speed / motion anomaly fallback |
| Cabin visibility risk | Dış kameradan sürücü/yolcu her zaman görünmez | Cabin expert yalnız visibility good/limited ise çalışır; aksi halde not_visible/unknown |
| OCR under low light / blur | Plaka yanlış veya düşük güvenle okunabilir | OCR confidence, plate visibility, temporal voting ve QoD candidate politikası kullan |
| Lane detection under poor visibility | Şerit riski yanlış yorumlanabilir | Lane visibility field, low-confidence state ve fallback risk reason kullan |
| Dataset domain gap | Public veri seti demo ortamına uymayabilir | Dataset inventory, domain comparison ve Colab benchmark yap |
| Public dataset license issues | Rapor ve model kullanımı lisans riski taşır | Dataset license checklist zorunlu olsun |
| False positives / false negatives | Sistem güvenilirliği düşer | Event-level test, precision/recall/F1 ve threshold tuning yap |
| Evidence privacy/security | Plaka/yüz/cabin veya raw video sızıntısı olabilir | Evidence medyasını Git dışında tut; private storage ve checklist kullan |
| Model export/quantization accuracy drop | Edge performansı artarken doğruluk düşebilir | ONNX/TFLite export sonrası ayrı benchmark yap |
| QoD overuse | Ağ kaynağı gereksiz tüketilir | QoD yalnız candidate/request policy ile ve evidence/decision quality gerekçesiyle aktif olur |
| LLM hallucination | Açıklama model çıktısından kopabilir | LLM yalnız structured event JSON’dan açıklama üretir; template fallback korunur |
| Multi-target complexity | Latency ve routing karmaşıklığı artar | MVP single-target; multi-target future/research scope |

## Risk Detayları

### Too Many Tasks for MVP

Proje mimarisi araç, plaka, hız, lane, scene, cabin, external user, QoD ve LLM gibi çok sayıda modül içerir. Bunların tamamını ilk MVP’ye koymak gerçekçi değildir.

Mitigation:

* Core MVP kapsamı ayrı tutulur.
* Final architecture ve future scope etiketleri kullanılır.
* `docs/04_yapay_zeka/12_mvp_final_future_scope.md` referans alınır.

### 30 FPS Overclaim Risk

Camera preview 30 FPS olabilir; ancak OCR, speed, lane, cabin gibi uzman modeller her frame’de çalışmaz.

Mitigation:

* Frekans planı ayrı yazılır.
* Rapor dili dikkatli kurulur.
* Latency benchmark olmadan final performans iddiası yazılmaz.

### Speed Estimation Calibration Risk

Tek kamera ile mutlak hız için ölçek ve kalibrasyon gerekir.

Mitigation:

* `homography_kmh` modu yalnız kalibrasyon varsa kullanılır.
* Kalibrasyon yoksa `relative_motion` fallback kullanılır.
* Event JSON’da speed mode açıkça yazılır.

### Cabin Visibility Risk

Yol kenarı dış kamera açısından araç içi görünürlük çoğu zaman sınırlıdır.

Mitigation:

* Cabin expert future/extended scope olarak tutulur.
* Visibility gate zorunludur.
* `not_visible` ve `unknown` state’leri desteklenir.

### OCR Under Low Light / Blur

Plaka OCR düşük ışık, blur veya düşük çözünürlükte kırılgandır.

Mitigation:

* Plate visibility ve OCR confidence ayrı tutulur.
* QoD candidate reason olarak blur/low_light yazılır.
* Evidence package içinde plate crop ve confidence saklanır.

### Lane Detection Under Poor Visibility

Şerit çizgisi görünmüyorsa lane expert yanlış alarm üretebilir.

Mitigation:

* Lane visibility alanı zorunlu context olarak kullanılır.
* Low visibility durumunda lane sonucu düşük güvenle raporlanır.
* Lane expert event-based çalışır.

### Dataset Domain Gap

Public veri setleri Türkiye yol koşulu, kamera açısı veya demo ortamını tam temsil etmeyebilir.

Mitigation:

* Dataset inventory hazırlanır.
* Model adayları aynı benchmark şablonuyla karşılaştırılır.
* Gerekirse fine-tune/adaptation yapılır.

### Model Export / Quantization Drop

Edge deployment için export/quantization gerekir; bu doğruluğu düşürebilir.

Mitigation:

* Export öncesi ve sonrası metrikler ayrı tutulur.
* Model size, latency ve accuracy trade-off birlikte değerlendirilir.

## Rapor Notu

Bu riskler projenin zayıflığı olarak değil, mühendislik kontrol planı olarak anlatılmalıdır. Final raporda her risk için hangi fallback veya test yaklaşımının kullanıldığı gösterilmelidir.
