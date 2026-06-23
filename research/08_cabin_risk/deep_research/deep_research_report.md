# Cabin / Driver Baseline Deep Research

Tarih: 2026-06-12

## Problem Tanımı

Proje kamerası araç dışında ve yol yönündedir. Bu nedenle cabin analizi klasik
dashboard-camera sürücü davranışı probleminden farklıdır. Cam yansıması, açı, araç
hareketi, gece, iç mekân karanlığı ve sürücünün çok küçük görünmesi nedeniyle doğrudan
telefon/kemer sınıflandırmasına geçmek yüksek yanlış pozitif riski taşır.

İlk teknik problem risk sınıflandırması değil, şu iki sorunun güvenilir cevaplanmasıdır:

1. Hedef araç içindeki cabin bölgesi analiz edilebilir mi?
2. Analiz edilebiliyorsa yüz/occupant ve açık kamera geometrisinde driver candidate
   temporal olarak görülebiliyor mu?

## Model Kararı

İlk baseline için MediaPipe Face Detector seçilmiştir. Resmi Python task API:

* image, video ve live-stream çalışma modlarını destekler,
* yüz bbox, confidence ve altı facial keypoint üretir,
* video/live-stream modunda tracking kullanarak her karede detector çağırma maliyetini
  azaltabilir,
* Python 3.9 ve üzerini destekler.

İki BlazeFace modeli karşılaştırılacaktır:

* **Full-range:** Dışarıdan/back-camera benzeri geniş görüntü için ana baseline.
* **Short-range:** Yakın yüzlerde olası kalite avantajını görmek için challenger.

Her iki model de hafif 128x128 float16 BlazeFace ailesindedir. Final seçim public model
iddiasına göre değil, mevcut üç 4K test videosundaki visibility, temporal face recall,
driver assignment usability ve latency sonuçlarına göre yapılacaktır.

## Visibility Gate

Face detector yalnız hedef araç içindeki cabin candidate ROI üzerinde çalışır. Öncesinde
OpenCV tabanlı şu metrikler hesaplanır:

* brightness,
* contrast,
* Laplacian sharpness,
* dark pixel ratio,
* glare ratio,
* minimum ROI dimension.

Çıktı `good`, `limited`, `poor` veya `not_visible` olur. `poor/not_visible` karelerde
yüz sonucu risk veya driver kararına dönüştürülmez.

## Driver Rolü

Yüz tespiti tek başına hangi kişinin sürücü olduğunu söylemez. Bu nedenle rol ataması
yalnız izlenebilir view-profile politikasıyla yapılır:

* `side_driver_window`: en büyük front-seat yüz driver candidate.
* `front_lhd`: görüntünün sağ yarısındaki en büyük front-seat yüz driver candidate.
* `unknown`: yalnız occupant count; driver kararı `null`.

Tek kare sonucu yeterli değildir. Driver candidate kararı en az üç kare ve görünür
karelerin en az yüzde 30'unda destek gerektirir.

## Bu Fazın Sınırı

Telefon, emniyet kemeri ve sigara sınıfları bu baseline'a dahil değildir. Bu görevler
kontrollü pozitif/negatif videolar ve ayrı specialist benchmark gerektirir. Occupant
varlığı risk skorunu yükseltmez; yalnız evidence metadata olarak kaydedilir.

## Sonuç

İlk uygulanabilir Cabin/Driver hattı:

`target track -> cabin ROI -> visibility gate -> face/occupant -> view-profile driver policy -> temporal decision -> event enrichment`

Bu sıra, görünür olmayan cabin görüntülerinde iddialı ve denetlenemez risk kararı
üretilmesini engeller.

## BlazeFace Sonrası Model Escalation

Full-rate `CABIN-EXP-001` sonucunda sürücü yüzü bazı karelerde yakalansa da temporal
devamlılık ve arka yolcu recall'u kabul eşiğini geçmemiştir. Bu nedenle aşağıdaki
adaylar araştırılmıştır:

1. **OpenCV YuNet 2026may:** İlk yeni challenger. Resmi OpenCV Zoo modeli MIT
   lisanslıdır, çoklu yüz üretir ve yaklaşık `10x10` ile `300x300` piksel arasındaki
   yüzleri hedeflediğini belirtir. OpenCV DNN ile mevcut ortamda ek runtime gerektirmez.
2. **SCRFD-2.5G_KPS / SCRFD-10G_KPS:** İkinci kademe güçlü challenger. Resmi SCRFD
   sonuçlarında WIDER FACE hard AP sırasıyla `77.13` ve `82.80` olarak raporlanır.
   Dinamik ONNX inference desteği vardır. Ancak pretrained checkpoint kullanım koşulu
   teknik entegrasyondan önce ayrıca doğrulanmalıdır.
3. **RetinaFace MobileNet/ResNet:** Fallback araştırma adayı. MIT kod tabanı ve
   WIDER FACE hard odaklı sonuçları vardır; eski PyTorch bağımlılıkları nedeniyle
   ilk uygulama adayı yapılmamıştır.

Yeni deney sırası:

`CABIN-EXP-004 YuNet -> manuel/full-rate review -> gerekirse SCRFD`

Kaynaklar:

* OpenCV YuNet: https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
* SCRFD resmi repo: https://github.com/deepinsight/insightface/tree/master/detection/scrfd
* SCRFD makalesi: https://arxiv.org/abs/2105.04714
* RetinaFace PyTorch: https://github.com/biubug6/Pytorch_Retinaface
