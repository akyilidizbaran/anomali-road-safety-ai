# Driver Upper-Body / Pose Deep Research

Tarih: 2026-06-12

## Problem

Kamera araç dışındadır ve driver çoğu karede küçük, kısmi ve cam arkasındadır.
Klasik full-body pose problemi değildir. Mevcut cabin ROI yüz için tasarlandığından
omuz ve gövdeyi kesebilir; pose modelini doğrudan bu crop üzerinde çalıştırmak
seatbelt/phone modülleri için hatalı anchor üretir.

Bu nedenle YuNet'in view-profile ile atanmış driver yüzü başlangıç anchor'ı yapılır.
Yüz kutusu araç koordinatına taşınır, hedef araç bbox sınırları içinde aşağı doğru
genişleyen ayrı bir upper-body ROI çıkarılır. Pose instance'ı driver yüz geometrisiyle
eşleştirilmeden torso veya kol kararı üretilmez.

## Resmi Kaynak Bulguları

Ultralytics pose çıktısı instance bbox ile keypoint koordinatlarını birlikte verir.
COCO pretrained pose ailesi 17 insan keypoint'i içerir; omuz, dirsek, bilek ve kalça
anchor'ları bu faz için yeterlidir. Projede Ultralytics ve MPS/CPU çalışma ortamı
zaten kullanıldığı için entegrasyon riski düşüktür.

MediaPipe Pose Landmarker:

* image, video ve live-stream modlarını destekler,
* video modunda tracking kullanır,
* `num_poses` ile birden fazla pose yapılandırabilir,
* image ve world koordinatlarında 33 landmark üretir,
* lite, full ve heavy model bundle seçenekleri sunar.

MediaPipe daha yoğun el/ayak anchor'ları sağlasa da resmi açıklamadaki fitness/full
body odağı nedeniyle küçük ve kısmi dış-kamera driver görüntülerindeki başarı
benchmark ile kanıtlanmalıdır.

## Aday Kararı

### `POSE-EXP-001` - YOLO11n-pose

Ana adaydır:

* çok kişili instance bbox ve keypoint aynı sonuçta gelir,
* driver yüzü ile pose association izlenebilir yapılabilir,
* mevcut Ultralytics runtime ve cihaz seçimini kullanır,
* COCO-17 omuz-dirsek-bilek-kalça sözleşmesi sonraki seatbelt/phone fazına yeterlidir.

YOLO26 güncel dokümantasyondaki yeni aile olsa da repo vehicle hattı YOLO11 üzerinde
kuruludur. Bu fazda model ailesi değişkenini artırmamak ve mevcut runtime ile doğrudan
karşılaştırma yapmak için `yolo11n-pose.pt` dondurulmuştur.

### `POSE-EXP-002` - MediaPipe Pose Landmarker Full

Challenger'dır:

* 33 landmark ve video tracking avantajı vardır,
* mevcut `mediapipe` bağımlılığıyla çalışır,
* dense kol/el anchor'ları phone fazında yararlı olabilir.

Full model, lite'a göre ilk kalite challenger'ıdır. Heavy model ancak Full anlamlı
kalite artışı gösterip latency sınırı sorun olursa açılacaktır.

### `POSE-EXP-003` - RTMPose-L Body7 384x288 ONNX

YOLO11n-pose, MediaPipe Full ve deterministic torso tam-video manuel incelemede
reddedildikten sonra ilk yeni challenger olarak açılmıştır:

* top-down modeldir; YuNet yüzünden üretilen tek-driver ROI doğrudan modele verilir,
* Body7 checkpoint'i COCO, AI Challenger, CrowdPose, MPII, sub-JHMDB, Halpe ve
  PoseTrack18 birleşimiyle eğitilmiştir,
* aynı resmi tabloda OCHuman eklenmiş Body8 değerlendirmesinde `PCK@0.1=95.56`,
  `AUC=74.38` raporlanmıştır,
* `384x288` giriş, küçük sürücü görüntüsünde `256x192` adaydan daha fazla uzamsal
  çözünürlük sağlar,
* resmi ONNXRuntime örneği sayesinde MMPose/MMCV mevcut benchmark ortamına
  kurulmadan çalıştırılabilir.

OCHuman burada eğitim verisi değil değerlendirme kapsamıdır. Bu sonuç araç camı
arkasındaki sürücü başarısını kanıtlamaz; yalnız kısmi/örtülü insan görünümüne karşı
önceki iki generic adaydan daha gerekçeli bir challenger seçilmesini sağlar.

### İkinci Kademe Adaylar

* `POSE-EXP-004`: RTMW-L Cocktail14 WholeBody 384x288. UBody ve InterHand dahil
  14 veri kümesi, 133 keypoint ve ONNXRuntime yolu nedeniyle action-grade kol/el
  takibi için sıradaki challenger.
* `POSE-EXP-005`: ViTPose-B. COCO val AP `75.8`, OCHuman test AP `88.0`;
  yüksek kapasiteli top-down challenger. Resmi repo eski PyTorch/MMCV sürümlerine
  bağlı olduğundan RTMW sonucundan sonra ayrı ortamda ele alınacak.
* `POSE-EXP-006`: RTMO-L Body7. Tek-aşamalı ve dedektörsüzdür; çok kişili
  görüntülerde avantajlıdır. Bizim tek-driver, yüz-anchor'lı ROI problemimizde
  top-down RTMPose'tan önce çalıştırılması gerekçeli değildir.

## Güvenli Karar Politikası

Bir kare yalnız şu koşullarda `driver_analysis_ready=true` olur:

1. Cabin visibility `good` veya `limited`.
2. YuNet driver yüz rolü atanmış.
3. Pose instance driver yüzüyle geometrik olarak eşleşmiş.
4. Sol ve sağ omuz confidence eşiğini geçmiş.
5. Torso ROI minimum boyutları sağlamış.

Kalçalar görünmüyorsa sonuç reddedilmez; omuz genişliğine dayalı kontrollü torso
alt sınırı üretilir ve durum `torso_shoulders_extrapolated` olarak kaydedilir.

Model seçimi için bu kare-bazlı şartlar tek başına yeterli değildir. Her videoda
tam overlay manuel incelemesi, en uzun kopma süresi ve normalize omuz jitter metriği
de geçmelidir.

## Sonraki Modüller

Seatbelt specialist torso ROI üzerinde diyagonal kemer sinyali arayacaktır. Phone
specialist driver torso ROI ile omuz-dirsek-bilek keypoint'lerini birlikte kullanacak,
telefon nesnesini yalnız driver kol/baş yakınlığıyla ilişkilendirecektir. Yüz kutusunun
altında kör arama yapılmayacaktır.
