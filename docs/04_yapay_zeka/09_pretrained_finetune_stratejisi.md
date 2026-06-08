# Public/Pretrained Model ve Fine-Tune Stratejisi

## Ana Karar

Bu projede eğitimin ana yükü sıfırdan model eğitmek olmayacak. Temel yaklaşım, internet üzerinde erişilebilir public/pretrained modelleri araştırmak, uygun olanları seçmek ve proje ihtiyaçlarına göre veri işleme, fine-tune, post-processing ve entegrasyon ile uyarlamaktır.

## Neden Bu Yaklaşım?

Proje çok görevli bir sistemdir. Araç tespiti, takip, plaka/OCR, şerit, hız, sahne/görüş ve cabin risk görevlerini sıfırdan model eğitimiyle çözmek süre, veri ve donanım açısından gerçekçi değildir.

Public/pretrained model yaklaşımı şu avantajları sağlar:

* Daha hızlı başlangıç.
* Literatür ve açık kaynak sonuçlarıyla karşılaştırılabilirlik.
* Colab üzerinde daha yönetilebilir fine-tune.
* Model geliştirme yükünü veri işleme ve hedefe uyarlamaya odaklama.
* Rapor için daha savunulabilir baseline ve iyileştirme akışı.

## Kapsam

Yapılacak işler:

* Public/pretrained model araştırması.
* Veri seti seçimi ve veri ön işleme.
* Fine-tune veya transfer learning.
* Model outputlarını proje event JSON formatına uyarlama.
* Threshold, confidence, NMS, temporal voting gibi post-processing.
* Colab deneyleri.
* Doğruluk, hız, latency, model boyutu ve export metriklerinin ölçülmesi.

Yapılmayacak veya ana hedef olmayan işler:

* Büyük modeli sıfırdan eğitmek.
* Devasa veri seti üretmek.
* Her modül için özgün mimari tasarlamak.
* Yerel veri toplamayı ana veri kaynağı yapmak.

## Colab Çalışma Standardı

Her Colab deneyi şu bilgileri kaydetmelidir:

* Deney ID.
* Model adı ve kaynak linki.
* Veri seti adı ve kaynak linki.
* Veri split bilgisi.
* Fine-tune parametreleri.
* Eğitim süresi.
* Validation metrikleri.
* Test metrikleri.
* Model export durumu.
* Notlar ve hata kayıtları.

## Colab ve MacBook Ayrımı

Colab, eğitim/fine-tune ve araştırma ortamıdır. Canlı demo çıkarımı MacBook üzerinde çalışan local edge/backend runtime ile yapılacaktır.

Bu nedenle deney kayıtları iki ayrı performans bilgisini karıştırmamalıdır:

* **Colab sonuçları:** eğitim süresi, validation/test metrikleri, model seçimi ve fine-tune davranışı.
* **MacBook runtime sonuçları:** canlı inference latency, pipeline FPS, CPU/GPU/RAM kullanımı, stream ve evidence üretim süresi.

Model final adayına yaklaşırken aynı export edilmiş model MacBook üzerinde de benchmark edilmelidir.

## İlk Odak: Araç Tespiti

Araç tespiti sistemi şu nedenle ilk modüldür:

* Diğer modüllerin çoğu araç bbox çıktısına bağlıdır.
* Tracking için detection gerekir.
* Plaka/OCR için vehicle ROI gerekir.
* Hız için track edilen araç noktası gerekir.
* Evidence için anlaşılır görsel kanıtın ilk katmanı bbox’tır.

## Araştırma Sonrası Model Seçimi

Başlangıç model ailesi araştırma sonrası seçilecek. Adaylar:

* YOLOv8 nano/small.
* YOLOv10 nano/small.
* YOLOv11 nano/small.
* RT-DETR edge uygun varyantlar.
* Araç tespiti için özel traffic/road pretrained modeller.

Seçim kriterleri:

* mAP.
* Precision/recall dengesi.
* Inference latency.
* FPS.
* Model boyutu.
* Colab fine-tune kolaylığı.
* ONNX/TFLite export kolaylığı.
* Mobil-edge pipeline uyumu.

## Veri İşleme Rolü

Model geliştirmede ana katkı veri işleme ve hedefe uyarlama olacaktır:

* Veri seti format dönüşümü.
* Sınıf eşleme.
* Frame/video-level split.
* Class imbalance yönetimi.
* Augmentation.
* ROI çıkarımı.
* Confidence threshold ayarı.
* Post-processing.
* Event JSON uyumluluğu.

## Test Ortamı

Test verisinin gerçekleştirildiği ortam izole olacak. Maskeleme yapılmayacağı için:

* Test verileri kontrollü erişimde tutulmalı.
* Repoya test görüntüsü eklenmemeli; private repo olsa bile ham/evidence görselleri Git dışında kalmalı.
* Rapor için kullanılacak görseller ayrıca seçilmeli.
* Veri seti lisansları doğrulanmalı.
