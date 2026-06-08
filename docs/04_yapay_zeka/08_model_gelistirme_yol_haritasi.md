# Model Geliştirme Yol Haritası

## Mevcut Karar

Model geliştirme sıfırdan tüm modülleri aynı anda hedeflemeyecek. İlk odak **araç tespiti** olacak. Araç tespiti tamamlandıktan sonra diğer modüller faz sırasıyla eklenecek.

Eğitimin ana yükü sıfırdan model eğitmek olmayacak. İnternet üzerinde erişilebilir public/pretrained modeller araştırılacak; uygun modeller Colab üzerinde fine-tune, veri işleme, post-processing ve event JSON entegrasyonu ile proje amacına uyarlanacak.

Runtime akışında ortam/hava/ışık/görüş bağlamı erken üretilir; ancak model geliştirme yükü açısından ilk ana araştırma ve deney başlığı araç tespitidir. Bu ayrım raporda açık tutulmalıdır.

## Geliştirme Sırası

1. Araç tespiti.
2. Araç takibi ve hedef araç seçimi.
3. Plaka tespiti ve OCR.
4. Evidence sistemi.
5. Hafif sahne/hava/görüş koşulu bağlamı.
6. Genel yol ve araç dışı kullanıcı/yaya durumu.
7. Context-gated model routing ve uzman model seçimi.
8. Şerit/road marking analizi.
9. Hız kestirimi.
10. Sürücü/yolcu ve cabin risk analizi.

## Eğitim Ortamı

Ana deney ve eğitim ortamı **Google Colab** olacak.

Colab kullanımının gerekçeleri:

* GPU erişimi kolaydır.
* Model denemeleri hızlı başlatılabilir.
* Notebook tabanlı deney kayıtları rapora aktarılabilir.
* Farklı model aileleri aynı ortamda karşılaştırılabilir.

Demo/inference çalışma ortamı ise Colab değil, MacBook üzerinde çalışan local edge runtime olacaktır. Colab model araştırması ve fine-tune içindir; canlı demo pipeline'ı MacBook backend üzerinden çalışmalıdır.

## Input ve Resize Kararı

Canlı demo input'u 720p frame seviyesinde planlanır. Modeller bu frame'i doğrudan 720p olarak çalıştırmak zorunda değildir; preprocessing aşaması seçilen modelin beklediği input boyutuna resize eder. Benchmark kayıtlarında hem kaynak çözünürlük hem model input boyutu yazılmalıdır.

## Model Ailesi Seçimi

Başlangıç modeli araştırma sonrası seçilecek. Araştırmada şu adaylar kıyaslanmalıdır:

* YOLOv8 nano/small.
* YOLOv10 nano/small.
* YOLOv11 nano/small.
* RT-DETR gibi alternatifler.

Seçim yalnız doğruluğa göre yapılmamalıdır. Edge gerçek zamanlılık hedefi nedeniyle şu kriterler birlikte değerlendirilmelidir:

* mAP / precision / recall.
* FPS.
* Inference latency.
* Model boyutu.
* Colab eğitim süresi.
* ONNX/TFLite export kolaylığı.
* Mobil-edge pipeline uyumu.

## Sonraki Modüller

Araç tespitinden sonra tasarlanan modüller sırasıyla:

1. **Araç takibi ve hedef araç seçimi:** Detection outputları track ID’ye dönüştürülür, tek hedef araç seçilir.
2. **Plaka tespiti ve OCR:** Hedef araç ROI’den plate bbox ve OCR sonucu üretilir.
3. **Evidence package sistemi:** Model çıktıları, görsel kesit ve metadata olay kaydına dönüşür.
4. **Sahne/hava/görüş analizi:** Işık, hava ve görüş koşulu sınıflandırılır.
5. **Genel yol ve araç dışı kullanıcı/yaya durumu:** Yol bağlamı, yaya/bisikletli/motosikletli ve riskli araca yakınlık sinyali üretilir.
6. **Context-gated model routing:** Ortam, görünürlük, yol bağlamı, track stability ve risk ön skoru hangi uzman modelin çağrılacağını belirler.
7. **Şerit / road marking analizi:** Hedef aracın şerit içindeki konumu ve ihlal şüphesi çıkarılır.
8. **Hız kestirimi:** MVP'de göreli hareket/risk sinyali; final scope'ta kalibrasyon denemesiyle km/s yaklaşımı.
9. **Sürücü/yolcu ve cabin risk:** Kontrollü video ve görünürlük yeterliyse final genişletme olarak çalışır.
10. **Risk skoru ve kritik mod orkestrasyonu:** Modül çıktıları tek risk skoruna ve uzman çağırma politikasına bağlanır.
11. **5G/QoD adapter:** Riskli araçta QoD aday/request akışı başlatılır; aktif olursa gerçek video kalite artırımı seçici şekilde bağlanır.
12. **LLM açıklama katmanı:** Event JSON, API/local LLM/template fallback ile insan okunur açıklamaya çevrilir.

## İlk Model İçin Kabul Kriteri

Araç tespit modeli şu çıktıları üretmelidir:

* Araç bbox.
* Araç sınıfı.
* Confidence skoru.
* Frame ID ile eşleşen model output.
* Mobil overlay’e dönüştürülebilecek JSON formatı.

## İzole Test Ortamı

Test verisinin gerçekleştirildiği ortam izole olacak. Bu, özellikle maskeleme yapılmayacağı için önemlidir.

İzole test yaklaşımı:

* Test verisi eğitim verisinden ayrılmalı.
* Video-level split korunmalı.
* Test görüntüleri dışarıya kontrolsüz paylaşılmamalı.
* Rapor için kullanılacak görseller ayrıca seçilmeli.
* Plaka/yüz içeren görsellerin saklama ve erişim sınırı belirlenmeli.

## Sonraki Modüle Geçiş Kriteri

Araç tespiti için dengeli metrik paketi kabul edilebilir seviyeye geldiğinde tracking modülüne geçilir. Tek bir metrik iyi diye modül tamamlanmış sayılmamalıdır; hız, doğruluk ve sistem uyumu birlikte değerlendirilmelidir.
