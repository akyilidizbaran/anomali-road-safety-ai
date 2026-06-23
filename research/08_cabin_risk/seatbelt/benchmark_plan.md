# Seatbelt Benchmark Planı

## Deneyler

### SEATBELT-EXP-001

* Girdi: `POSE-EXP-009` torso ROI.
* Yöntem: OpenCV diyagonal çizgi evidence heuristic.
* Amaç: pipeline, temporal aggregation, latency ve event enrichment doğrulaması.
* Karar: seçilmedi; false-positive üreten referans.

### SEATBELT-EXP-002

* Girdi: YuNet + cabin-motion tabanlı driver-context ROI.
* Challenger: `RISEF/yolov11s-seatbelt` YOLO11s binary classifier.
* Kollar: raw ve lokal condition-routed enhancement.
* Amaç: mevcut üç videoda pretrained transfer ve düşük ışık smoke testi.
* Karar sınırı: binary candidate sonuçlar event/risk'e yazılmaz.

### SEATBELT-EXP-003

* Girdi: kontrollü, etiketli driver-context crop veri seti.
* İlk local challenger: hafif image classifier.
* Sınıflar: `belted`, `unbelted`, `incorrect`, `not_evaluable`.
* Detector challenger yalnız kemer lokalizasyon etiketi yeterliyse açılır.

## Veri Matrisi

Her sınıf için şu koşullar kapsanmalıdır:

* `front_lhd` ve `side_driver_window`;
* gündüz, düşük ışık, parlama ve yansıma;
* açık/koyu kıyafet ve farklı kemer renkleri;
* direksiyon, kapı çizgisi, kıyafet katı ve cam yansıması hard-negative;
* sürücü kısmi görünür ve görünmez `not_evaluable` örnekleri.

Train/validation/test ayrımı kare bazında değil, video/çekim oturumu bazında
yapılır. Aynı videonun komşu kareleri farklı split'lere konulmaz.

## Metrikler

* sınıf bazlı precision, recall ve F1;
* confusion matrix;
* false-positive oranı ve hard-negative hata dökümü;
* temporal persistence ve en uzun karar kaybı;
* mean/P95 latency;
* view-profile bazlı sonuçlar.
* raw ile condition-routed kol arasındaki recall/false-positive farkı;
* driver identity switch ve temporal ROI hold hata sayısı.

## Kabul Kapısı

Model ancak etiketli test setinde manuel review ile birlikte kabul edilir.
`unbelted` ve `incorrect` kararları, sınıf bazlı ölçüm yapılmadan event'e
yazılmaz. `poor/not_evaluable` kareler risk kararı üretmez.
