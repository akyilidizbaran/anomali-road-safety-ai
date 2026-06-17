# Decision - Vehicle Detector v1

Tarih: 2026-06-08
Son güncelleme: 2026-06-15

## Karar Durumu

Status: **Active runtime baseline locked for current MVP**

Bu dosya ilk ölçülebilir baseline kararını ve 2026-06-15 itibarıyla aktif MVP
runtime detector seçimini kaydeder. Bu karar nihai akademik/ürün modeli iddiası
değildir; mevcut demo ve FTR kanıt üretimi için sabitlenen çalışma modelidir.

## Seçilen İlk Baseline

İlk deney modeli: **YOLO11n**

## Aktif MVP Detector Kararı - 2026-06-15

Aktif checkpoint:

```text
models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

Aktif model etiketi:

```text
vehicle_detector_general_yolo11n_bdd100k_v1
```

Runtime evidence / final-acceptance confidence gate:

```text
TBD after threshold sweep
```

Current manual-review candidate gate:

```text
0.60
```

Manual review sonucu:

* `Test/video_1.mp4`, `Test/video_2.mp4` ve `Test/video_3.mp4` içinde ana araç her frame'de yakalanıyor.
* BBox ana araç için stabil.
* Daha düşük threshold değerlerinde false positive gözleniyor.
* `confidence >= 0.60` ile gözlenen false positive problemi demo/manual review kapsamında ortadan kalkıyor.
* `0.60` final threshold değildir; yalnız mevcut 3 video manual review kapsamında gözlenen aday downstream evidence/target acceptance gate değeridir.
* Frame-level candidate detection ve tracking continuity gerekirse daha düşük aday eşiğiyle çalışabilir; final event/evidence threshold değeri threshold sweep + manuel review sonrası seçilecektir.
* Bu sonuç frame-level ground truth accuracy değildir; `manual qualitative review` olarak raporlanmalıdır.

Model lock kararı:

* `VD-EXP-002-GENERAL-YOLO11N`, mevcut MVP için active/best detector olarak sabitlenir.
* `VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N`, başarısız/regresyon üreten deneme olarak kaydedildi ve runtime'a terfi ettirilmedi.
* Motorcycle özel fine-tune şimdilik ertelendi; kısa vadeli odak `car` / genel araç varlığı, tracking, plate/OCR, speed/risk/evidence modüllerine kaydırıldı.

## Gerekçe

YOLO11n:

* hızlı Colab iterasyonu sağlar,
* küçük model boyutuyla MacBook runtime benchmark için uygundur,
* Ultralytics train/val/predict/export akışıyla hızlı prototipleme sağlar,
* ilk amaç olan output contract + tracking/evidence pipeline uyumluluğunu hızlı test etmeye uygundur.

## Final Karar İçin Yarışacak Modeller

* YOLO11n
* YOLO11s
* YOLOv10n
* YOLOv10s
* YOLOv8n
* RT-DETR-L
* NanoDet-Plus-m veya YOLOv6Lite-M, yalnız on-device fallback ihtiyacı güçlenirse

## Karar Verme Yöntemi

Final seçim public benchmark skoruna göre yapılmayacak.

Final seçim şu birleşimle yapılacak:

1. Public reference score.
2. Bizim Colab validation/test sonuçlarımız.
3. MacBook runtime p95 latency ve FPS.
4. Output contract uyumu.
5. Tracking başlatma ve target selection katkısı.
6. Evidence crop kullanılabilirliği.
7. Export ve lisans riski.

## Lisans Notu

Ultralytics tabanlı modeller AGPL-3.0 / Enterprise lisans riskleri nedeniyle ürünleşme aşamasında yeniden değerlendirilecektir. Yarışma prototipi için kullanılacak model ve ağırlıkların lisans durumu ayrıca doğrulanmadan final raporda kesin ticari uygunluk iddiası kurulmaz.

## Yeniden Karar Koşulları

YOLO11n aşağıdaki durumlardan biri gerçekleşirse baseline olmaktan çıkar:

* BDD100K/UA-DETRAC validation sonuçları belirgin düşük kalır.
* MacBook p95 latency hedefi aşılır.
* Output contract dönüşümü kırılgan çıkar.
* Tracking ve evidence crop kalitesi yetersiz olur.
* Lisans değerlendirmesi kullanım amacına uygun bulunmaz.
* Threshold sweep sonrası seçilen değer altında ana araç detection sürekliliği bozulursa veya false positive tekrar sistematik hale gelirse.

## Sonraki Aksiyonlar

* `final_confidence_threshold` quantitative threshold sweep + manual review sonrası seçilecek.
* `candidate_evidence_confidence_threshold=0.60` yalnız mevcut dark-video manual review gözlemi olarak korunacak.
* Heavy vehicle detection fine-tune durdurulacak; zaman kısıtı nedeniyle sıradaki modüller için baseline/tune akışına geçilecek.
* Sıradaki AI kapsamları: tracking stability, plate detection/OCR, relative speed, risk/evidence fusion, cabin/driver-object kapsamı.
* `architecture/contracts/model_output_contract.md` VehicleDetectionOutput örneği threshold seçim durumuyla hizalanacak.
