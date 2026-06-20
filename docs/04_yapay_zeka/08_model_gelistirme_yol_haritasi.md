# Model Geliştirme Yol Haritası

## Mevcut Karar

Model geliştirme sıfırdan tüm modülleri aynı anda hedeflemeyecek. İlk odak **araç tespiti** olacak. Araç tespiti tamamlandıktan sonra diğer modüller faz sırasıyla eklenecek.

Eğitimin ana yükü sıfırdan model eğitmek olmayacak. İnternet üzerinde erişilebilir public/pretrained modeller araştırılacak; uygun modeller Colab üzerinde fine-tune, veri işleme, post-processing ve event JSON entegrasyonu ile proje amacına uyarlanacak.

Runtime akışında ortam/hava/ışık/görüş bağlamı erken üretilir; ancak model geliştirme yükü açısından ilk ana araştırma ve deney başlığı araç tespitidir. Bu ayrım raporda açık tutulmalıdır.

2026-06-20 FTR güncellemesi: Resmi teslim dokümanı otomatik değerlendirme için
`results.json` formatını zorunlu kıldığı için geliştirme sırası artık bu contract'a göre
önceliklendirilir. Geniş event/evidence mimarisi korunur, fakat FTR scoring için ana hedef
`arac_bilgisi` ve `tespitler` üretmektir.

2026-06-15 güncel durum:

* `VD-EXP-002-GENERAL-YOLO11N`, mevcut MVP için aktif/best vehicle detector olarak sabitlendi.
* Runtime/demo evidence/final-acceptance confidence gate: `TBD after threshold sweep`.
* Current manual-review candidate false-positive pruning gate: `0.60`.
* Manuel review: `Test/video_1-3.mp4` içinde ana araç her frame'de yakalanıyor, bbox stabil, `0.60` aday gate sonrası gözlenen false positive kalmıyor. Bu değer final threshold değildir.
* `VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N` başarısız/regresyon kabul edildi; motorcycle özel fine-tune ertelendi.
* Zaman kısıtı nedeniyle ağır vehicle detection tune yerine diğer AI modüllerinin baseline/tune aşamalarına geçilecek.

## FTR'ye Göre Güncel Geliştirme Sırası

1. FTR `results.json` adapter ve validator.
2. Docker submission skeleton: `Dockerfile`, `main.py`, `/app/data/input/video.mp4`, `/app/data/output/results.json`.
3. Araç tespiti, tracking ve tek ana araç seçimi.
4. Araç tipi sınıflandırma ve FTR label mapping:
   * `sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan`, `kamyon`.
5. Plaka tespiti + CCT-XS OCR + Türkiye plaka regex normalization.
6. Araç rengi tahmini:
   * `beyaz`, `siyah`, `gri`, `kirmizi`, `mavi`, `sari`, `yesil`, `turuncu`, `kahverengi`.
7. Sürücü eylemi tespitleri:
   * `arkaya_bakma`, `esneme`, `sigara_icme`, `su_icme`, `telefonla_konusma`, `slalom`, `etrafa_bakinma`, `emniyet_kemeri_ihlali`.
8. Nesne tespitleri:
   * `teknocan`, `bilgisayar`.
9. Yolcu konum tespitleri:
   * `arka_koltuk_1`, `arka_koltuk_2`, `on_koltuk`.
10. T4 runtime, image size ve 10 dakika limit validasyonu.
11. Rich evidence/QoD/dashboard/LLM katmanları.

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

## Güncel Aktif Sıra - 2026-06-20

Araç tespiti, tracking, plate detector ve CCT-XS OCR omurgası FTR için kullanılabilir
aday kabul edildiği için sıradaki çalışma sırası aşağıdaki gibi güncellendi:

1. **FTR output adapter + validator**
   * Internal event/evidence çıktısını resmi `results.json` formatına dönüştürür.
   * Key/label/ASCII/regex/confidence validasyonu yapar.
2. **Docker submission skeleton**
   * Root `Dockerfile`, `main.py`, `src/predict.py`, `src/utils.py`.
   * Runtime path'leri `/app/data/input/video.mp4` ve `/app/data/output/results.json`.
3. **Vehicle info completion**
   * Mevcut detector/tracker + plate/OCR korunur.
   * Araç tipi FTR label setine map edilir.
   * Araç rengi modeli veya güçlü heuristic eklenir.
4. **Cabin / Driver-Object-Passenger baseline**
   * FTR'nin asıl eksik kısmı budur.
   * `sofor_eylemi`, `nesneler`, `yolcular` için pretrained/fine-tune seçenekleri araştırılır.
   * 2026-06-20 itibarıyla `CABIN-EXP-012-runtime-foundation` ile araç/cabin ROI,
     visibility gate ve torso ROI üretimi çalışır hale getirildi.
   * Bu deney ihlal kararı üretmez; phone/smoking/seatbelt/yolcu specialist modelleri için
     giriş contract'ını hazırlar.
   * Bir sonraki aktif cabin işi `PHONE-EXP-003/004` phone specialist baseline/fine-tune
     çalışmasıdır.
5. **Speed / Motion Signal**
   * FTR'de doğrudan hız alanı yoktur.
   * Yalnız `slalom` ve rapor/evidence desteği için kullanılabilir.
   * Mevcut 005A grafikleri gürültülü olduğundan final hız iddiası kurulmayacaktır.

Bu sırada araç tespiti tekrar açılacaksa yalnız şu koşullarda açılmalıdır:

* Threshold sweep sonrası seçilen confidence gate altında ana araç / evidence kabul davranışı bozulursa.
* Car bbox stabilitesi evidence crop için yetersiz kalırsa.
* Yeni test videolarında sistematik false positive tekrar ortaya çıkarsa.
* Yeni veri seti veya hedef senaryo car/general detection başarısını belirgin düşürürse.

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

FTR'de sonraki modüle geçiş için yalnız model doğruluğu yeterli değildir. Her modül şu
şartları karşılamalıdır:

* Resmi FTR label setine map edilebilmeli.
* `results.json` adapter tarafından yazılabilmeli.
* Confidence skoru 0.0-1.0 aralığında olmalı.
* Docker runtime içinde 10 dakika limitini zorlamamalı.
* Hatalı/düşük güvenli durumda schema-valid fallback üretebilmeli.
