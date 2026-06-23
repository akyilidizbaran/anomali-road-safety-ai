# Decision - Driver Detection Baseline v1

Tarih: 2026-06-23

## Karar

İlk driver detection baseline olarak `DRIVER-EXP-001 =
yunet_view_policy_driver_presence_v1` kullanılacak.

Bu deney yeni bir model eğitmez. Daha önce seçilmiş `CABIN-EXP-004`
OpenCV YuNet 2026may cabin/face baseline'ının temporal summary çıktısını
driver-presence contract'ına dönüştürür.

## Gerekçe

* `CABIN-EXP-004`, mevcut üç demo videoda en iyi face/occupant sürekliliğini verdi.
* Driver action modellerinden önce sürücünün görülebilirliği ve rol ataması ayrı
  ölçülmelidir.
* YuNet + view-profile policy, action classifier'a göre daha açıklanabilir bir
  driver-presence sinyali üretir.
* Bu modül risk veya ihlal kararı üretmediği için yanlış action iddiası kurmaz.

## Kapsam

Kapsam içi:

* cabin ROI görünürlük durumu,
* yüz/occupant temporal sinyali,
* sürücü adayı var/yok,
* yolcu sayısı için destekleyici tahmin,
* evidence JSON'a driver-presence metadata yazımı.

Kapsam dışı:

* `telefonla_konusma`,
* `su_icme`,
* `sigara_icme`,
* `esneme`,
* `emniyet_kemeri_ihlali`,
* `etrafa_bakinma`,
* hukuki risk veya ihlal kararı.

## Kabul Kriteri

Bu baseline yalnız şu durumda action specialist zincirini açabilir:

* `driver_detection.status == "detected"`
* `driver_detection.driver_present == true`
* `driver_detection.confidence` makul seviyede olmalı
* `driver_detection.cabin_visibility` `limited` veya `good` olmalı

Bu koşullar sağlanmazsa sonraki driver-action modelleri `not_evaluable` dönmelidir.

## Çıktılar

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-driver-detection.json`
* `models/benchmarks/artifacts/driver_detection/DRIVER-EXP-001-yunet_view_policy_driver_presence_v1/driver_exp_001_driver_detection_summary.json`
* `testing/reports/driver_exp_001_driver_detection_summary.md`
* `models/benchmarks/cabin/driver_detection_baseline_comparison.csv`

## Sonraki Adım

`DRIVER-EXP-001` tamamlandıktan sonra `DACT-EXP-020B` driver action classifier
notebook'u hazırlanacaktır.
