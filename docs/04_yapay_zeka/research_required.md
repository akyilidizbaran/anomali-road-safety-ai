# Research Required

Bu dosya kaynak veya literatür doğrulaması yapılmadan final model kararı verilemeyecek başlıkları listeler.

## Model Ailesi Seçimi

Araç tespiti için YOLO/RT-DETR veya alternatif modeller araştırılmalıdır.

İlk çalışma düzeni: Colab üzerinde araştırma/fine-tune, MacBook üzerinde runtime benchmark.

İlk ölçülebilir baseline: YOLO11n. Final karar benchmark sonrası verilecektir.

Gerekli çıktı:

* Aday model listesi.
* Lisans durumu.
* Pretrained weight erişimi.
* Colab uyumu.
* MacBook runtime uyumu.
* ONNX/TFLite export durumu.
* Benchmark planı.
* 720p source frame -> model input resize politikası.
* Lisans ve ürünleşme riski notu.

## Tracking

ByteTrack, BoT-SORT veya alternatif tracking yöntemleri incelenmelidir.

Gerekli çıktı:

* Araç detection ile uyum.
* Track stability metriği.
* Edge latency etkisi.

## Plate Detection / OCR

Türk plaka formatı ve public OCR modelleri araştırılmalıdır.

Başlangıç yaklaşımı kural tabanlı format validation, il kodu kontrolü, OCR post-processing ve temporal voting birleşimidir. Bu yaklaşım literatür/açık kaynak çalışma araştırmasıyla doğrulanmalıdır.

Gerekli çıktı:

* Plate detector adayları.
* OCR adayları.
* Türk plaka format validation kuralları.
* Düşük ışık/blur fallback stratejisi.

## Speed Estimation

Tek kamera hız kestirimi için homography/kalibrasyon gereksinimleri araştırılmalıdır.

Kalibrasyon denemesi final scope'tadır. MVP için göreli hız / motion anomaly fallback metriği tanımlanmalıdır.

Gerekli çıktı:

* Kalibrasyon yöntemleri.
* Referans mesafe seçenekleri.
* Göreli hız fallback metrikleri.

## Lane / Road Marking

Lane/road marking modelleri ve düşük görüş fallback stratejileri araştırılmalıdır.

Bu modül plate/OCR ve evidence hattından sonra ele alınacaktır.

## Scene / Weather / Visibility

Sahne/hava/görüş sınıflandırması için hafif modeller ve veri setleri araştırılmalıdır.

## Cabin Risk

Dış kamera ile cabin risk güvenilirliği araştırılmalıdır. Bu başlık MVP kararı için engelleyici değildir; future/research scope olarak kalabilir.

## Dataset and License

Her veri seti için:

* Kaynak URL.
* Lisans.
* Citation.
* Kişisel veri riski.
* Redistribution sınırı.

`docs/05_veri_seti/04_dataset_license_checklist.md` doldurulmadan final veri kararı verilmemelidir.
