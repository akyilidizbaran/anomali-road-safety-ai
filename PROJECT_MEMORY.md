# PROJECT_MEMORY

## 0) TL;DR (En güncel durum)

* Şu an ne yapıyoruz? Arkadaşlar plate/OCR hattını ilerletirken ana çalışma tekrar Vehicle Detection fine-tune hazırlığına döndü. İlk resmi model omurgası `YOLO11n + BDD100K + Colab/Drive` olarak FTR formatına göre planlanıyor.
* Son değişiklik neydi? `deep-research-report.md`, `research/02_vehicle_detection/deep_research/condition_experts_deep_research_report.md` konumuna taşındı; `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb` general + opsiyonel night/rain/fog specialist fine-tune ve karşılaştırma notebook'u olarak yeniden yazıldı.
* Bir sonraki net adım ne? Notebook, label/image overlap sıfır çıkarsa Archive.org `bdd100k_images.zip` paketini Drive'a indirip çıkaracak, image index cache'lerini yenileyecek ve YOLO dönüşümü eşleşen BDD100K image setiyle yeniden deneyecek. Sonra VD-EXP-002 conversion/fine-tune akışı Colab'da çalıştırılacak.

## 1) Proje Amacı ve Kapsam

* Amaç: Kullanıcı adı/şifre ve Number Verification doğrulaması sonrası telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka çıkarım hattında analiz ederek araç, plaka, hız, şerit, sürücü/yolcu, yol-hava-ışık koşulu ve araç dışı kullanıcı/yaya durumunu değerlendiren; riskli olayları mobil arayüzde gösteren ve kritik olayları denetlenebilir evidence paketlerine dönüştüren karar destek sistemi geliştirmek.
* Kapsam içi: Mobil login, Number Verification request/response, mobil kamera, edge/backend çıkarım, ortam/sahne analizi, araç tespiti, tracking, tek hedef araç, genel yol durumu, araç dışı kullanıcı/yaya durumu, plaka/OCR, hız yaklaşımı, şerit/road marking, cabin risk koşullu analizi, normal/kritik mod, riskli araçta QoD aday/request/aktif akışı, event JSON, evidence package, test metrikleri, KVKK/etik.
* Kapsam dışı: Otomatik ceza kesme, hukuki kusur kararı verme, her koşulda kesin km/s iddiası, QoD’nin her riskte otomatik açılması, izinsiz kişisel veri saklama.

## 2) Non-negotiables / Kırmızı Çizgiler

* Sistem karar destek sistemi olarak anlatılmalı; ceza veya hukuki hüküm sistemi olarak anlatılmamalı.
* QoD seçici kullanılmalı; yalnız karar güveni veya kanıt kalitesi artacaksa aday/aktif olmalı.
* Hız için kalibrasyon yoksa mutlak km/s yerine göreli hız/risk skoru anlatılmalı.
* Cabin risk yalnız görünürlük yeterliyse çalışmalı; görünürlük yetersizse “analiz güvenilir değil” çıktısı verilmeli.
* Evidence package içinde event ID, timestamp, track ID, bbox, confidence, model version, QoD status ve karar gerekçesi bulunmalı.
* LLM karar verici değil, structured event JSON’u açıklayan katman olarak konumlandırılmalı.
* Demo gerçek yol kenarında, sabit kamera ve canlı kamera akışıyla tasarlanmalı.
* Maskeleme yapılmayacağı için veri lisansı, izin, minimum saklama ve erişim kontrolü ayrıca sıkı ele alınmalı.
* Model geliştirme araç tespitiyle başlamalı; diğer modüller sırayla eklenmeli.
* Başarı tek metrikle değil, doğruluk + hız + latency + model boyutu + sistem/evidence katkısı dengesine göre değerlendirilmeli.
* Eğitimin ana yükü sıfırdan model eğitmek değildir; public/pretrained modeller araştırılıp Colab üzerinde fine-tune, veri işleme, post-processing ve output uyarlaması yapılacaktır.
* Canlı demo/inference ortamı MacBook local edge runtime olacak; Colab canlı demo ortamı değil, eğitim/fine-tune ortamıdır.
* Canlı kaynak frame hedefi 720p olacak; seçilen modelin input boyutuna preprocessing aşamasında resize edilecektir.
* Hız kalibrasyon denemesi final scope'ta tutulacak; MVP'de göreli hız / motion anomaly sinyali yeterli kabul edilebilir.
* Şerit/road marking modülü plate/OCR ve evidence hattından sonra ele alınmalıdır.
* Araç tespiti için ilk ölçülebilir baseline YOLO11n'dir; final model kararı Colab fine-tune + MacBook runtime benchmark + lisans/export/evidence/tracking katkısı sonrası verilecektir.
* Fine-tune şimdilik aktif iş değildir; TODO/backlog'da tutulacak ve önce pretrained baseline + tracking/smoothing pipeline'ı olgunlaştırılacaktır.
* Pretrained baseline artık sistem geneli anlam taşır: her AI modülü önce dış kaynaklı pretrained model veya algoritmik baseline ile çalışır hale getirilecek, fine-tune yalnız bu omurga tamamlandıktan sonra faz bazlı açılacaktır.
* Pretrained baseline kıyasları aynı test verisi, aynı input size, aynı confidence threshold, aynı class filter ve aynı kayıt formatıyla yapılmalıdır.
* Vehicle tracking için ilk baseline ByteTrack'tir; ikinci alternatif BoT-SORT ReID kapalıdır. ReID yalnız ID switch/occlusion problemi kanıtlanırsa açılacaktır.
* 2026-06-10 otomatik tracking koşusunda ByteTrack, BoT-SORT ReID-off'a göre daha düşük birleşik detector+tracker pipeline latency ve daha yüksek FPS verdi; manuel review tamamlanana kadar ByteTrack aktif baseline olarak korunur.
* Kullanıcı manuel kontrolde ByteTrack'in gayet iyi çalıştığını belirtti; bu nedenle sıradaki faz yeni tracker denemesi değil, ByteTrack çıktısını target/evidence hattına bağlamaktır.
* Tracking tek başına alarm üretmez; speed, plate OCR, risk fusion, QoD ve evidence için `track_id`, `stable_class`, `track_stability`, `bbox_history`, `center_history`, `best_frame_id` ve `best_crop_ref` üretir.
* Track-to-event skeleton gerçek risk/ihlal kararı değildir; yalnız hedef araç seçimi ve sonraki speed/plate/QoD/evidence modülleri için ara contract üretir.
* Hız estimation kullanıcı kararıyla sona bırakıldı; track-to-event sonrası aktif faz plate detection + OCR'dır.
* Plate/OCR ilk MVP iki aşamalı kurulacak: target vehicle ROI içinde plate detection, plate crop üzerinde OCR, Türk plaka regex/il kodu post-processing, track-level temporal voting ve evidence JSON update.
* Plate/OCR ilk baseline'da fine-tune yapılmayacak; önce pretrained/public detector + PaddleOCR/EasyOCR karşılaştırması ile pipeline usability kanıtlanacak.
* `runs/plate_ocr/POCR-EXP-001-target-roi-crops/` altındaki crop görselleri ve ROI clip videoları Git'e eklenmeyecek; yalnız küçük JSON summary ve rapor takip edilecek.
* Plate/OCR için tek `best_frame` yeterli değildir; vehicle detector confidence ile plate visibility aynı şey değildir. Manual review ve plate detector smoke test için track penceresinden sample crop ve ROI clip üretilmelidir.
* Condition-specific detector routing kullanılacak: `general`, `dark`, `rain`, `fog_low_visibility`, `night_low_light`. Her frame için model eğitilmez; sahne/koşul profili seçilir ve önceden eğitilmiş/fine-tune edilmiş detector çağrılır.
* Mevcut 3 dark video training set değildir; yalnız manuel benchmark/smoke-test materyalidir ve benchmark sonrası silinebilir.
* Condition expert training sırası Strateji 1 olacak: önce `vehicle_detector_general`, sonra yalnız benchmark ile faydası kanıtlanan `night_low_light`, `rain`, `fog_low_visibility` uzmanları. `dark`, `tunnel_or_parking_dark`, `glare`, `low_contrast` başlangıçta ayrı detector değil condition label/routing sinyali olarak izlenecek.
* `vehicle_detector_general` yalnız gündüz/normal koşul modeli değildir; ilk fine-tune aşamasında night/rain/fog örnekleri condition metadata ile general training/validation breakdown içinde korunacaktır.

## 3) Mimari Özet

* Bileşenler: Login/Auth client, Number Verification adapter, Android mobil istemci, video aktarım katmanı, edge/backend inference server, normal mode pipeline, critical mode expert selector, QoD/5G adapter, event fusion, evidence store, explanation layer.
* Veri akışı: Kullanıcı adı/şifre girilir -> Number Verification API kullanıcı/cihaz/oturum eşleşmesini doğrular -> CameraX 720p frame/stream üretir -> MacBook local edge/backend alır -> frame preprocessing/quality analysis ve model input resize -> normal mod ortam/sahne analizi -> araç detection root model -> tüm araçlar için hafif tracking -> target/risky vehicle selection -> target ROI generation -> context-gated expert routing -> riskli araçta QoD aday/request akışı -> kritik mod gerekiyorsa seçili uzman modeller -> event fusion -> event JSON -> evidence package -> mobil overlay/evidence ekranı.
* Önemli dizinler/modüller: `docs/` rapor ve teknik açıklamalar; `research/` derin araştırma başlıkları; `reports/` resmi rapor çalışma alanı; `architecture/` diyagram ve contract; `project/` karar/risk/gereksinim; `mobile/`, `backend/`, `data/`, `models/`, `testing/`, `governance/` geliştirme alanları.
* Condition experts araştırma alanı: `research/03_condition_experts/` deep research raporunu, kapsam denetimini, dataset kaynak/lisans checklist'ini ve yol haritasını tutar.

## 4) Konvansiyonlar ve Standartlar

* Kod stili / lint / format: Henüz kod projesi kurulmadı; bu aşama dokümantasyon ve planlama aşamasıdır.
* Branch/commit yaklaşımı: Private GitHub repo `akyilidizbaran/anomali-road-safety-ai` üzerinde `main` branch kullanılıyor. Araştırma/dokümantasyon değişiklikleri ayrı commitlerle yapılmalı; büyük mimari kararlar `project/decisions/` altında tarihli Markdown dosyalarıyla, riskler `project/risks/` altında takip edilmeli.
* İsimlendirme/klasör düzeni: Resmi raporlar `PDR_OTR` ve `PCR_FTR` adlarıyla tutulur; PDR=ÖTR, PCR=FTR karşılığı olarak not edilmiştir.

## 5) Kurulum & Çalıştırma

* Gereksinimler: Bu aşamada yalnız Markdown dosyalarını okuyacak/edit edecek bir editör yeterlidir.
* Komutlar: Yok.
* Ortam değişkenleri (sadece İSİMLER): Yok.
* Lokal geliştirme notları: Kod geliştirme başladığında mobil/backend için ayrı kurulum dosyaları eklenmelidir.
* GitHub repo: `https://github.com/akyilidizbaran/anomali-road-safety-ai` (`PRIVATE`)

## 6) Decision Log (append-only)

* 2026-06-06 — Karar: Web tabanlı React/Vite demo prototip seçildi. | Gerekçe: Hızlı görsel demo. | Etki: Bu karar 2026-06-07’de kullanıcı tarafından kapsam dışı bırakıldı. | Alternatifler: Android/Kotlin gerçek prototip.
* 2026-06-06 — Karar: Gerçek backend yerine mock JSON event verisi kullanıldı. | Gerekçe: Demo amaçlı hızlı UI akışı. | Etki: Bu karar 2026-06-07’de yeni resmi rapor/dokümantasyon kapsamı için geçerli ana yön olmaktan çıkarıldı. | Alternatifler: Gerçek API contract.
* 2026-06-06 — Karar: QoD durumu seçici karar olarak temsil edildi. | Gerekçe: Proje anlatımında QoD’nin her olayda otomatik açılmaması kritik. | Etki: Bu karar yeni kapsamda da korunur. | Alternatifler: Tek statik QoD aktif göstergesi.
* 2026-06-07 — Karar: Proje sıfırdan resmi rapor ve `.txt` kapsamına göre dokümantasyon-first yapıda kuruldu. | Gerekçe: Kullanıcı önceki demo gösterimlerinin istenen kapsamda olmadığını belirtti. | Etki: `docs/`, `research/`, `reports/`, `architecture/`, `project/` ve geliştirme hazırlık klasörleri oluşturuldu. | Alternatifler: Eski demo üzerinde devam etmek.
* 2026-06-07 — Karar: PDR ifadesi resmi ÖTR şablonuyla, PCR ifadesi resmi FTR şablonuyla eşleştirildi. | Gerekçe: Kök dizindeki resmi dosyalar Ön Tasarım Raporu ve Final Tasarım Raporu olarak adlandırılmış. | Etki: Klasörler `PDR_OTR` ve `PCR_FTR` olarak kuruldu. | Alternatifler: Yalnız PDR/PCR adlarını kullanmak.
* 2026-06-07 — Karar: Demo gerçek yol kenarında, sabit kamera ve canlı kamera üzerinden tasarlanacak. | Gerekçe: Kullanıcı demo koşullarını netleştirdi. | Etki: Demo ve hız kestirimi dokümanları güncellendi. | Alternatifler: Kontrollü alan veya offline video.
* 2026-06-07 — Karar: Hızda hedef mutlak km/s, fallback göreli hız/risk sınıflandırması olacak. | Gerekçe: Tek kamera gerçek hız için ölçek/kalibrasyon ister; başarısız durumda iddialı olmayan fallback gerekir. | Etki: Homografi/yarı otomatik kalibrasyon ve literatür tabanlı değerlendirme yönü benimsendi. | Alternatifler: Sadece göreli hız.
* 2026-06-07 — Karar: Cabin risk kontrollü video ile final genişletme olarak tasarlanacak. | Gerekçe: Görev zor ve görünürlük koşullu. | Etki: MVP odağı araç/takip/plaka/hız/şerit/evidence hattında kalır. | Alternatifler: MVP’ye dahil etmek.
* 2026-06-07 — Karar: LLM açıklama katmanı API, local LLM veya template fallback ile çalışabilecek. | Gerekçe: Bağlantı ve model erişimi değişebilir. | Etki: LLM karar verici değil, açıklayıcı adapter olarak tasarlanır. | Alternatifler: LLM kullanmamak.
* 2026-06-07 — Karar: QoD sağlandığında gerçek video kalitesi artırılacak. | Gerekçe: QoD’nin proje değerini gerçek kalite artışıyla göstermek. | Etki: QoD kalite parametreleri araştırılmalı. | Alternatifler: Yalnız mock statü.
* 2026-06-07 — Karar: Yerel veri mümkünse toplanmayacak ve maskeleme yapılmayacak. | Gerekçe: Kullanıcı tercihi. | Etki: Açık veri seti lisansları, kişisel veri riski ve saklama politikası kritik hale geldi. | Alternatifler: Kontrollü yerel veri ve maskeleme.
* 2026-06-07 — Karar: Model geliştirme araç tespitiyle başlayacak, sonra modüller sırayla eklenecek. | Gerekçe: Projenin temel AI girdisi araç bbox ve sınıf çıktısıdır. | Etki: İlk araştırma ve Colab deney planı araç tespiti odağında hazırlanacak. | Alternatifler: Plaka/OCR veya tracking ile başlamak.
* 2026-06-07 — Karar: Eğitim ve deney ortamı Google Colab olacak. | Gerekçe: GPU erişimi ve notebook tabanlı deney kaydı kolaylığı. | Etki: Model deney planları Colab uyumlu hazırlanacak. | Alternatifler: Yerel MacBook, bulut GPU, Kaggle.
* 2026-06-07 — Karar: Başlangıç model ailesi araştırma sonrası seçilecek. | Gerekçe: YOLO/RT-DETR gibi adaylar doğruluk, latency, model boyutu ve export kolaylığına göre kıyaslanmalı. | Etki: Önce karşılaştırma tablosu hazırlanacak. | Alternatifler: Doğrudan tek YOLO sürümü seçmek.
* 2026-06-07 — Karar: Başarı dengeli metrik paketiyle ölçülecek. | Gerekçe: Canlı mobil-edge sistemde yalnız accuracy yeterli değil. | Etki: mAP/precision/recall/F1 yanında FPS, latency, model size, export ve evidence katkısı izlenecek. | Alternatifler: Tek metrik odaklı seçim.
* 2026-06-07 — Karar: Test ortamı izole olacak. | Gerekçe: Maskeleme yapılmayacağı için veri erişim ve paylaşım riski azaltılmalı. | Etki: Test verisi eğitimden ayrılacak, kontrollü saklanacak ve dışa paylaşım sınırlandırılacak. | Alternatifler: Açık/karma test ortamı.
* 2026-06-07 — Karar: Model geliştirme public/pretrained model araştırması + fine-tune/adaptation şeklinde yürütülecek. | Gerekçe: Proje çok görevli; sıfırdan model eğitmek veri/donanım/süre açısından ana hedef değil. | Etki: Colab deneyleri, veri işleme, post-processing, model seçimi ve dengeli benchmark öncelik kazanır. | Alternatifler: Sıfırdan model eğitimi.
* 2026-06-07 — Karar: Repo public olarak oluşturulacak. | Gerekçe: Kullanıcı public repo istedi ve gerekirse sonradan private alacağını belirtti. | Etki: Büyük veri, checkpoint, secrets ve kişisel veri içeren materyaller `.gitignore` ile dışarıda tutulmalı. | Alternatifler: Private repo.
* 2026-06-07 — Karar: Public GitHub repo `akyilidizbaran/anomali-road-safety-ai` olarak oluşturuldu. | Gerekçe: Kullanıcı gerekli düzenlemeleri GitHub üzerinden yapmak istedi. | Etki: İlk dokümantasyon commit’i `main` branch’e pushlandı. | Alternatifler: Repo oluşturmadan lokal kalmak.
* 2026-06-07 — Karar: Ana erişim akışı kullanıcı adı/şifre sonrası Number Verification API doğrulaması olacak. | Gerekçe: Kullanıcı ana isteği bu şekilde netleştirdi ve `leD24n5kb...pdf` içeriği Number Verification kapısını destekliyor. | Etki: Mobil login ve auth contract dokümanları bu akışa göre yazıldı. | Alternatifler: Doğrudan mock verified state ile sisteme giriş.
* 2026-06-07 — Karar: Normal modda ilk erken bağlam sinyali ortam/sahne analizi olacak. | Gerekçe: Hava, ışık, görüş ve yol koşulu detection, OCR, hız ve QoD kararlarını etkiler. | Etki: Sistem mimarisi ve normal/kritik mod dokümanları ortam analizi önceliğiyle güncellendi. | Alternatifler: Önce detection, sonra sahne analizi.
* 2026-06-07 — Karar: Riskli araç tespitinde QoD tetikleme aday/request akışı başlatılacak, ancak her riskte otomatik aktif olmayacak. | Gerekçe: PDF kapsamındaki QoD yaklaşımı seçici kullanım gerektiriyor; kullanıcı riskli araçta QoD tetikleneceğini belirtti. | Etki: QoD dokümanı “trigger/candidate/request/active” ayrımıyla hizalandı. | Alternatifler: Her riskte sürekli QoD aktif etmek.
* 2026-06-07 — Karar: Genel yol durumu ve araç dışı kullanıcı/yaya durumu ayrı bağlam modülü olarak eklendi. | Gerekçe: Kullanıcı genel yol ve araç dışı kullanıcı durumunun sistem içinde belirtilmesini istedi. | Etki: Model yol haritası, event JSON ve mimari dokümanları yeni modülü kapsıyor. | Alternatifler: Bu bilgileri yalnız sahne analizi altında yan alan olarak tutmak.
* 2026-06-07 — Karar: Repo durumu açıkça planning/documentation/research scaffolding olarak işaretlenecek. | Gerekçe: Public repoya bakan kişi çalışan sistem ile dokümantasyon/contract aşamasını ayırt edebilmeli. | Etki: `STATUS.md`, `ROADMAP.md` ve root README Current Status bölümü eklendi. | Alternatifler: README’de yalnız proje vizyonu bırakmak.
* 2026-06-07 — Karar: Event JSON, mobile overlay response, backend API ve QoD enum contractları `architecture/contracts/` altında tek kaynak olarak tutulacak. | Gerekçe: Docs, backend, mobile ve evidence tarafında schema farklılaşmasını önlemek. | Etki: Contract dosyaları eklendi; docs API/event dosyaları bu kaynaklara referans verecek şekilde güncellendi. | Alternatifler: Contractları yalnız docs altında örnek JSON olarak tutmak.
* 2026-06-07 — Karar: Benchmark/experiment klasörlerinde küçük CSV/JSON/Markdown sonuçlar takip edilecek, ağır artifactler ignore edilecek. | Gerekçe: Final rapor metrik kanıtları Git’te kalmalı; model ağırlıkları ve büyük run çıktıları public repoya girmemeli. | Etki: `.gitignore`, model benchmark ve experiment şablonları güncellendi. | Alternatifler: Tüm benchmark/experiment çıktısını ignore etmek.
* 2026-06-07 — Karar: Resmi `.docx`/`.pdf` şablonları şimdilik kök dizinde kalacak. | Gerekçe: Kullanıcı bu dosyaları kök dizindeki adlarıyla referanslıyor; taşıma şu aşamada yol karışıklığı yaratabilir. | Etki: `reports/_official_templates/README.md` ileride taşıma notu olarak eklendi. | Alternatifler: Dosyaları hemen `reports/_official_templates/` altına taşımak.
* 2026-06-08 — Karar: Context-gated model routing kullanılacak. | Gerekçe: Hava/ışık/görüş/yol bağlamı model güveni, QoD adaylığı ve uzman model seçimini etkilemeli; normal mod tüm araçları hafif takip ederken ağır uzman modeller yalnız riskli/hedef araçta çalışmalı. | Etki: `docs/04_yapay_zeka/11_context_gated_model_routing.md`, AI omurgası, risk orkestrasyonu, mimari flow ve contract schema dosyaları güncellendi. | Alternatifler: Ortam analizini detection öncesi bloklayıcı aşama yapmak veya tüm araçlarda sürekli uzman model çalıştırmak.
* 2026-06-08 — Karar: GitHub repo private görünürlüğe alındı. | Gerekçe: Kullanıcı repoyu private almak istedi; kişisel veri, API key, model ve evidence riskleri nedeniyle sınırlı erişim daha uygun. | Etki: Repo görünürlüğü `PRIVATE`; güvenlik kuralı yine secret/veri/model/evidence dosyalarının Git’e eklenmemesi olarak korunur. | Alternatifler: Public repo olarak devam etmek.
* 2026-06-08 — Karar: Runtime AI architecture report-ready ve implementation-ready contract setiyle tanımlanacak. | Gerekçe: Mimari kapsam geniş ama MVP dar tutulmalı; frame inputtan event/evidence çıktısına kadar model pipeline net olmalı. | Etki: `docs/04_yapay_zeka/10_runtime_ai_pipeline_mimarisi.md`, `architecture/contracts/model_output_contract.md`, `architecture/contracts/expert_routing_policy.example.json`, güncellenmiş `event.schema.json`, frequency/scope/evidence/risk dokümanları eklendi. | Alternatifler: Modül dokümanlarını dağınık bırakmak.
* 2026-06-08 — Karar: Eğitim/fine-tune Colab GPU, canlı inference MacBook local edge/backend üzerinde yürütülecek. | Gerekçe: Colab araştırma için, MacBook saha demosunda edge runtime için daha gerçekçi. | Etki: README, roadmap, backend, AI pipeline, research ve memory dosyaları güncellendi. | Alternatifler: Android on-device inference veya cloud-only inference.
* 2026-06-08 — Karar: Canlı input 720p source frame/stream olarak planlanacak ve model input boyutuna resize edilecek. | Gerekçe: Kamera kaynağı ile model benchmark inputu ayrıştırılmalı. | Etki: Runtime pipeline, demo ve vehicle detection araştırması güncellendi. | Alternatifler: Tek sabit model inputunu source resolution gibi anlatmak.
* 2026-06-08 — Karar: Demo kamera açısı göğüs yüksekliğine yakın, dışarı/yol yönüne bakan sabit kamera olarak tanımlandı. | Gerekçe: Kullanıcı demo kamera kurulumunu netleştirdi. | Etki: Demo senaryosu ve açık sorular güncellendi. | Alternatifler: Araç içi dashcam veya yüksek direk kamerası.
* 2026-06-08 — Karar: Testler internet üzerindeki açık veri setleri, makale/proje ekleri ve açık kaynak benchmark materyalleriyle yürütülecek; lisanslar kaynaklarından doğrulanacak. | Gerekçe: Yerel veri mümkünse toplanmayacak ve maskeleme yapılmayacak. | Etki: Veri stratejisi, data policy ve açık sorular güncellendi. | Alternatifler: Yerel veri toplama.
* 2026-06-08 — Karar: Türk plaka OCR post-processing için başlangıç yaklaşımı regex + il kodu kontrolü + temporal voting olacak. | Gerekçe: Kullanıcı bu kararı internet/literatür çalışmalarına göre bırakmak istedi; ilk uygulanabilir ve açıklanabilir yaklaşım kural tabanlı doğrulamadır. | Etki: Plate OCR research ve research_required güncellendi. | Alternatifler: Format kontrolsüz OCR veya tamamen learned correction.
* 2026-06-08 — Karar: Hız kalibrasyon denemesi final scope'ta tutulacak; MVP'de göreli hız / motion anomaly sinyali yeterli olacak. | Gerekçe: Mutlak km/s için kamera/yol kalibrasyonu gerekir ve ilk MVP'yi riske atar. | Etki: Hız dokümanları, test stratejisi, scope ve research dosyaları güncellendi. | Alternatifler: Kalibrasyonu MVP şartı yapmak.
* 2026-06-08 — Karar: Şerit/road marking modülü plate/OCR ve evidence hattından sonra ele alınacak. | Gerekçe: Önce detection->tracking->plate->evidence uçtan uca akışı kurulmalı. | Etki: Lane docs ve roadmap dili güncellendi. | Alternatifler: Lane modelini plaka/evidence öncesinde geliştirmek.
* 2026-06-08 — Karar: QoD için hedef gerçek API/adapter entegrasyonu olacak, mock/status-policy fallback korunacak. | Gerekçe: Gerçek API erişimi gecikebilir; pipeline adapter bağımlılığına kırılgan olmamalı. | Etki: QoD dokümanı ve QoD API delay riski güncellendi. | Alternatifler: Yalnız mock QoD göstergesi veya API gelene kadar beklemek.
* 2026-06-08 — Karar: Araç tespiti için ilk ölçülebilir baseline YOLO11n olacak. | Gerekçe: Hızlı Colab iterasyonu, küçük model boyutu, güçlü train/val/predict/export akışı ve MacBook runtime benchmark için pratik başlangıç. | Etki: `research/02_vehicle_detection/`, `models/benchmarks/vehicle_detection_comparison.csv`, `models/experiments/vehicle_detection_experiment_template.md`, `architecture/contracts/model_output_contract.md`, `architecture/contracts/event.schema.json`, `architecture/contracts/mobile_overlay_response.schema.json`, `docs/04_yapay_zeka/01_arac_tespiti_takip.md` güncellendi. | Alternatifler: YOLO11s, YOLOv10n/s, YOLOv8n, RT-DETR-L.
* 2026-06-08 — Karar: Araç tespiti condition-specific detector routing destekleyecek. | Gerekçe: Karanlık, yağmur, sis ve düşük görüş koşulları detection hata profilini değiştirir; ancak 3 dark video specialist model eğitimi için yeterli değildir. | Etki: `Test/`, `.gitignore`, `research/02_vehicle_detection/condition_specific_detector_routing.md`, benchmark/fine-tune planları, manual review şablonu ve contract routing alanları güncellendi. | Alternatifler: Tek general detector veya 3 video ile hemen dark model eğitmek.
* 2026-06-08 — Karar: Condition expert geliştirme için Strateji 1 seçildi. | Gerekçe: Deep research, doğrudan her koşul için ayrı detector eğitmenin veri parçalanması, yanlış routing ve bakım riskini büyüttüğünü; önce general road-domain detector, sonra kanıtlanmış specialist dalları yaklaşımının daha savunulabilir olduğunu gösterdi. | Etki: `research/03_condition_experts/`, `research/02_vehicle_detection/condition_specific_detector_routing.md`, condition expert benchmark/experiment şablonları eklendi. | Alternatifler: Doğrudan her condition için specialist eğitmek veya tek all-weather detector + preprocessing ile kalmak.
* 2026-06-08 — Karar: İlk fine-tune condition-aware general vehicle detector olacak. | Gerekçe: VD-EXP-001 manual review genel araç yakalamanın iyi olduğunu, hataların daha çok kısa süreli class flicker ve bazı false negative'ler olduğunu gösterdi; bu aşamada condition classifier veya ayrı specialist detector beklemek gereksiz gecikme yaratır. | Etki: `research/02_vehicle_detection/finetune_plan.md`, `research/03_condition_experts/action_roadmap.md`, benchmark notları ve manual review summary güncellendi. | Alternatifler: Önce condition profile modeli eğitmek veya doğrudan night_low_light specialist açmak.
* 2026-06-08 — Karar: BDD100K Colab fine-tune hattı VD-EXP-002 olarak kurulacak. | Gerekçe: BDD100K road object labels ve weather/timeofday/scene metadata'sı condition-aware general detector için en uygun ilk public veri kaynağıdır. | Etki: `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`, BDD100K dataset card/mapping ve benchmark planı eklendi. | Alternatifler: UA-DETRAC ile başlamak veya önce condition classifier eğitmek.
* 2026-06-08 — Karar: BDD100K için opsiyonel otomatik Colab indirme desteklenecek. | Gerekçe: Repo public paylaşılmayacak ve lisanslı/private kullanım planlanıyor; yine de ham veri Git'e eklenmemeli, credential/URL/token bilgilerinin repo dışında kalması gerekir. | Etki: `scripts/colab/download_bdd100k.py`, `scripts/colab/README.md`, notebook ve dataset card güncellendi. | Alternatifler: Sadece manuel Drive upload ile ilerlemek.
* 2026-06-08 — Karar: VD-EXP-002 tek notebook uçtan uca pipeline olacak. | Gerekçe: Kullanıcı BDD100K indirme, Drive yerleşimi, fine-tune model eğitimi, test ve baseline farklarının tek Colab notebook içinde yürütülmesini istedi. | Etki: `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`, experiment planı, fine-tune planı ve action roadmap güncellendi. | Alternatifler: Ayrı download notebook/script ve ayrı training notebook tutmak.
* 2026-06-08 — Karar: Kaggle API key notebook/repo içine düz metin olarak yazılmayacak. | Gerekçe: Kullanıcı key paylaşmış olsa bile secret'lar Git geçmişine veya notebook hücresine gömülmemeli; Colab Secrets/env/prompt aynı pratikliği sağlar. | Etki: Notebook'a güvenli Kaggle credential setup hücresi eklendi. | Alternatifler: Key'i notebook config hücresine yazmak.
* 2026-06-10 — Karar: Fine-tune kapsamı TODO/backlog'a alındı; aktif model fazı pretrained zero-fine-tune baseline benchmark olacak. | Gerekçe: YOLO11n pretrained smoke test kullanılabilir sonuç verdi; eğitim maliyetine geçmeden model aileleri, latency, bbox stabilitesi, output contract ve evidence/tracking uygunluğu ölçülmeli. | Etki: `project/decisions/2026-06-10-defer-finetune-pretrained-baselines.md`, `research/02_vehicle_detection/pretrained_baseline_plan.md`, benchmark/fine-tune planları ve comparison CSV güncellendi. | Alternatifler: Hemen BDD100K fine-tune'a başlamak veya önce condition profile modeli eğitmek.
* 2026-06-10 — Karar: Pretrained baseline kapsamı sistem geneline genişletildi. | Gerekçe: Kullanıcı araç yakalama, hız, plaka, OCR, sürücü/yolcu/cabin gibi tüm modüllerin önce dış kaynaklı pretrained/algorithmic baseline ile kurulmasını ve fine-tune'un tüm baseline omurga tamamlandıktan sonra aşama bazlı yapılmasını istedi. | Etki: `research/00_pretrained_baseline/README.md` eklendi; ayrı model çağrısı gerektiren ve gerektirmeyen modüller ayrıldı. | Alternatifler: Sadece vehicle detector kıyası yapmak.
* 2026-06-10 — Karar: Vehicle tracking ilk baseline ByteTrack, ikinci alternatif BoT-SORT ReID kapalı olacak. | Gerekçe: Mevcut ihtiyaç düşük latency ile detection çıktılarını kararlı `track_id` değerlerine bağlamak, kısa false negative/class flicker davranışını track-level smoothing ile yönetmek ve speed/plate/evidence hattına track history sağlamaktır. | Etki: `research/03_tracking/deep_research/deep_research_report.md`, `research/03_tracking/benchmark_plan.md`, `research/03_tracking/decision_tracking_baseline_v1.md`, tracking benchmark CSV, manual review template, `TrackingOutput` contract güncellendi. | Alternatifler: DeepSORT/StrongSORT ReID tabanlı tracker'lar, OC-SORT, Norfair, Kalman+IoU.
* 2026-06-10 — Karar: Manuel review tamamlanana kadar ByteTrack aktif tracking baseline olarak korunacak. | Gerekçe: `TRK-EXP-001` ve `TRK-EXP-002` otomatik koşularında her iki tracker 15 unique track üretti; ByteTrack 17.665 ms mean / 25.284 ms p95 pipeline latency ve 31.742 FPS ile BoT-SORT ReID-off'tan daha hızlı çalıştı. | Etki: Tracking benchmark CSV ve summary raporu güncellendi; manuel ID switch/fragmentation incelemesi sıradaki iş olarak kaldı. | Alternatifler: BoT-SORT ReID-off'u latency pahasına seçmek veya ReID açık denemeye geçmek.
* 2026-06-10 — Karar: ByteTrack iyi çalıştığı için sonraki faz Track Post-Processing + Target Vehicle Selection + First Event/Evidence Skeleton olacak. | Gerekçe: Speed, plate OCR, QoD ve risk decision modülleri güvenilir `track_id`, `stable_class`, `track_stability` ve `target_track_id` olmadan yanlış araca bağlanabilir. | Etki: `research/03_tracking/next_phase_track_to_event_plan.md` eklendi; tracking summary güncellendi. | Alternatifler: Hemen speed veya plate OCR modülüne geçmek.
* 2026-06-11 — Karar: İlk track-to-event implementation heuristic post-processing olarak kurulacak. | Gerekçe: Ground-truth tracking/risk etiketi olmadan ölçülebilir ve tekrar üretilebilir ara contract gerekir; bu aşamada gerçek risk alarmı değil `target_vehicle_selected` skeleton yeterlidir. | Etki: `scripts/benchmarks/build_track_event_skeleton.py`, track post-process JSON, event skeleton JSON ve track-to-event raporu eklendi. | Alternatifler: Doğrudan speed/plate OCR model çağrılarına geçmek.
* 2026-06-11 — Karar: Hız estimation sona bırakılıp sıradaki aktif AI fazı Plate Detection + OCR olacak. | Gerekçe: Hız tek kamera kalibrasyon/perspektif nedeniyle daha kırılgan; plate/OCR ByteTrack target skeleton üstüne daha doğrudan bağlanır. | Etki: `research/04_plate_ocr/` altında deep research, decision, benchmark planı ve lisans checklist'i eklendi. | Alternatifler: Relative speed baseline'a hemen geçmek.
* 2026-06-11 — Karar: Plate/OCR ilk MVP iki aşamalı pipeline olacak. | Gerekçe: Evidence package, hata ayrıştırma, QoD sinyali, Türk plaka post-processing ve temporal voting açısından plate detection ile OCR'ın ayrı tutulması daha denetlenebilir. | Etki: İlk detector target ROI içinde çalışacak; ilk OCR baseline PaddleOCR, ikinci EasyOCR, debug fallback Tesseract olacak. | Alternatifler: End-to-end ALPR veya OCR-only ROI denemesi.
* 2026-06-11 — Karar: Plate/OCR'a sıfırdan başlanacak; v1 iş ürünleri arşivlenecek. | Gerekçe: Kullanıcı plaka tarafına baştan başlamak istedi; eski crop extraction tek best-frame + interpolasyonlu sample bbox kullanıyordu ve video_1/2 best-frame'lerinde plaka görünmüyordu. | Etki: `archive/plate_ocr_v1/` (script+summary+rapor) ve `runs/_archive/plate_ocr_v1_...` (ham görseller, ignore'lu) oluşturuldu; `extract_plate_ocr_target_rois.py` arşive taşındı. | Alternatifler: Eski crop'lar üzerinde devam etmek.
* 2026-06-11 — Karar: Plaka tespit smoke test'i (POCR-EXP-001) iki modeli karşılaştıracak ve hedef aracın TESPİT EDİLDİĞİ HER karede çalışacak; OCR bu aşamada yok. | Gerekçe: Kullanıcı iki modeli (Ultralytics YOLO plate + HF YOLOS) karşılaştırıp manuel seçmek istedi; best-frame plaka görünürlüğünü temsil etmiyor, bu yüzden tüm detected frame'ler taranmalı. | Etki: `scripts/benchmarks/run_plate_detection_smoke.py` ve `research/04_plate_ocr/RUN_POCR_EXP_001.md` eklendi; hedef track ID'ye değil best_frame IoU eşleşmesine göre seçilir. | Alternatifler: Tek detector ile başlamak, yalnız best/sample crop'larda çalışmak, tespit+OCR'ı zincirlemek.
* 2026-06-11 (eski/superseded) — Karar: Plate/OCR MVP ilk uygulama adımı target vehicle ROI crop extraction + sample frame extraction + target ROI clip üretimi olacak. | Gerekçe: Plate detector/OCR koşmadan önce ByteTrack target eventlerinin raw videoda doğru araç crop'una bağlandığı doğrulanmalı; tek best-frame crop plaka görünürlüğünü temsil etmeyebilir. | Etki: `scripts/benchmarks/extract_plate_ocr_target_rois.py`, `POCR-EXP-001-target-roi-crops-summary.json` ve crop extraction raporu eklendi/güncellendi. | Alternatifler: Doğrudan plate detector çalıştırmak veya yalnız tek best-frame crop üretmek.
* 2026-06-12 — Karar: Vehicle detection fine-tune hazırlığı FTR formatına göre yeniden aktif hale getirildi. | Gerekçe: Kullanıcı araç tespitinden başlayarak veri seti/model kapsamını final rapor beklentileriyle tam hazırlamak istiyor. | Etki: `research/02_vehicle_detection/ftr_vehicle_detection_finetune_plan.md` eklendi; `finetune_plan.md` aktif planlama durumuna çekildi. | Alternatifler: Plate/OCR bitene kadar fine-tune'u bekletmek.
* 2026-06-12 — Karar: İlk resmi fine-tune omurgası `YOLO11n + BDD100K + Colab/Drive` olacak. | Gerekçe: BDD100K yol-domain bbox ve condition metadata sağlıyor; YOLO11n MacBook local edge hedefi için hafif ve Colab'da pratik. | Etki: `.pt` zorunlu çıktı, ONNX opsiyonel deployment kanıtı; ACDC/DAWN/ExDark/Foggy Cityscapes ilk merge değil specialist/evaluation adayı. | Alternatifler: Birden fazla adverse dataset'i baştan merge etmek veya YOLO11s ile başlamak.
* 2026-06-12 — Karar: Vehicle detection Colab notebook'u general + opsiyonel specialist karşılaştırma hattı olarak tek dosyada tutulacak. | Gerekçe: FTR için aynı split/protokol altında baseline, fine-tune, condition breakdown ve specialist-vs-general tablolarının tek yerden üretilebilir olması gerekiyor. | Etki: `VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb` yeniden yazıldı; `SMOKE_LIMIT_IMAGES`, `RUN_SPECIALISTS`, `RUN_NIGHT_SPECIALIST`, `RUN_RAIN_SPECIALIST`, `RUN_FOG_SPECIALIST`, `RUN_EXPORT_ONNX` flagleri eklendi. | Alternatifler: Her condition için ayrı notebook tutmak.
* 2026-06-12 — Karar: BDD100K notebook indirme modu Kaggle'a sabitlendi ve pratik mirror olarak `solesensei/solesensei_bdd100k` seçildi. | Gerekçe: Kullanıcı manuel indirmek istemiyor; bu mirror BDD100K aramasında yüksek download/vote sinyali taşıyor ve etiketli yol görüntüsü kapsamına daha yakın görünüyor. | Etki: Notebook `DOWNLOAD_METHOD='kaggle'` ve `KAGGLE_DATASET_SLUG='solesensei/solesensei_bdd100k'` olarak güncellendi; dataset card ve inventory mirror notu aldı. | Alternatifler: Hazır YOLO mirror kullanmak, resmi portalı manuel indirmek, Drive mirror kurmak.
* 2026-06-12 — Karar: BDD100K Colab path discovery sabit path listesi yerine recursive repair/discovery kullanacak. | Gerekçe: Kaggle mirror indirildikten sonra label JSON dosyaları beklenen resmi path'lerde bulunmadı; mirror klasör yapısı değişken olabilir. | Etki: Notebook nested archive extraction, tree preview, recursive label JSON discovery ve recursive image dir discovery yapan hücreyle güncellendi. | Alternatifler: Kullanıcıdan dosyaları manuel taşımayı istemek.
* 2026-06-13 — Karar: Notebook varsayılanı mevcut Drive verisini kullanacak ve Drive'da veri varsa Kaggle indirmesini tekrar başlatmayacak. | Gerekçe: Kullanıcı Drive'da `datasets/bdd100k` ve `bdd100k_vehicle_yolo` klasörlerinin bulunduğunu gösterdi; önceki config her çalıştırmada Kaggle download'a girmeye çalışıyordu. | Etki: `USE_EXISTING_DRIVE_DATA=True`, `DOWNLOAD_METHOD='manual'` yapıldı; Kaggle slug fallback olarak kaldı. | Alternatifler: Her çalıştırmada Kaggle download yapmak.
* 2026-06-13 — Karar: BDD100K path discovery hücresi Google Drive I/O için optimize edildi. | Gerekçe: Kullanıcı L4 runtime'da 35 dakika bekledi; bu aşama GPU değil Drive I/O, zip extraction ve 100K dosya tarama darboğazıdır. | Etki: Notebook artık image klasörü varsa büyük archive extraction'ı atlar, full sorted `rglob` preview yapmaz, JSON label aramasını hızlı common-path + targeted recursive aramaya indirir. | Alternatifler: Colab hücresinin uzun taramayı bitirmesini beklemek.
* 2026-06-13 — Karar: Drive'da BDD100K image verisi var ama `Detection 2020 Labels` görünmüyor; yeniden image indirmek yerine label-only ekleme yapılacak. | Gerekçe: Google Drive aramalarında `det_train.json`, `det_val.json`, `bdd100k_labels_images_train.json`, `bdd100k_labels_images_val.json` ve `Detection 2020 Labels` bulunmadı. | Etki: Notebook `DETECTION_LABELS_ARCHIVE_PATH` ile yalnız label arşivini otomatik açacak şekilde güncellendi. | Alternatifler: Hazır YOLO mirror'a geçmek veya tüm dataset'i yeniden indirmek.
* 2026-06-13 — Karar: Resmi BDD100K `Detection 2020 Labels` ana yol; hazır YOLO Kaggle dataset yalnız fallback olacak. | Gerekçe: Hazır YOLO dataset detector eğitebilir ama `weather/timeofday/scene` condition metadata'sını kaybettirebilir; FTR condition breakdown için resmi BDD label JSON daha doğru. | Etki: Notebook'a `USE_YOLO_READY_FALLBACK` ve `YOLO_READY_FALLBACK_KAGGLE_SLUG='a7madmostafa/bdd100k-yolo'` notları eklendi, default kapalı tutuldu. | Alternatifler: Doğrudan YOLO-ready dataset ile başlamak.
* 2026-06-13 — Karar: `Detection 2020 Labels` için ETH public mirror direct URL notebook'a eklendi. | Gerekçe: Kullanıcı resmi portal yolunu tamamlayamadı; ETH indexinde `bdd100k_det_20_labels_trainval.zip` public görünüyor ve yalnız 53 MB label arşivi gerekiyor. | Etki: Notebook `DETECTION_LABELS_DOWNLOAD_URL` üzerinden sadece label arşivini Drive'a indirip açacak; image verisini tekrar indirmeyecek. | Alternatifler: Kullanıcının label zip'i manuel Drive'a yüklemesi veya YOLO-ready Kaggle fallback.
* 2026-06-13 — Karar: VD-EXP-002 Colab notebook full specialist training moduna alındı. | Gerekçe: Kullanıcı tüm specialist modelleri eğitmek istedi ve Drive path'i mount edilmeden boş klasör görme hatası verdi. | Etki: Notebook başına `drive.mount('/content/drive')` + dependency install hücresi eklendi; `SMOKE_LIMIT_IMAGES=None`, `RUN_SPECIALISTS=True`, `RUN_NIGHT_SPECIALIST=True`, `RUN_RAIN_SPECIALIST=True`, `RUN_FOG_SPECIALIST=True` yapıldı. | Alternatifler: Önce küçük smoke test veya yalnız general model eğitimi.
* 2026-06-13 — Karar: BDD100K label indirme notebook'ta çoklu fallback'e çevrildi. | Gerekçe: Colab `dl.cv.ethz.ch` için DNS `gaierror` verdi ve daha önce denenen BDD S3 URL'si public erişimde 404 döndü. | Etki: `DETECTION_LABELS_DOWNLOAD_URLS` artık önce ETH Detection 2020 Labels, sonra erişilebilir Internet Archive `bdd100k_labels.zip` fallback'ini dener; indirme `urllib -> curl -> wget` sırasıyla tekrarlanır. | Alternatifler: Label zip'i manuel Drive'a yüklemek veya YOLO-ready Kaggle fallback'e geçmek.
* 2026-06-13 — Karar: VD-EXP-002 notebook per-image BDD100K label formatını destekleyecek. | Gerekçe: Internet Archive fallback `labels/100k/train/*.json` dizin formatını çıkardı; Kaggle image mirror içinde `val` image klasörü bulunmadı. | Etki: Notebook aggregate `det_train.json` yanında per-image label dizinlerini okuyabilir; `val` image yoksa resmi val conversion atlanır ve mevcut train görüntüleri hash ile train/val/test split'e ayrılır. | Alternatifler: Val image arşivini ayrıca indirmek veya dataset'i baştan resmi paketle kurmak.
* 2026-06-13 — Karar: Akademik bildiri figürleri script tabanlı üretilecek. | Gerekçe: Önceki görseller renkli, kalabalık ve küçük yazılıydı; bildiri için siyah-beyaz, sade ve yeniden üretilebilir çıktı gerekiyor. | Etki: `scripts/figures/generate_academic_bw_figures.py` eklendi; PNG/PDF/SVG çıktıları `outputs/academic_figures_bw/` altında üretilir. | Alternatifler: Elle çizim veya renkli dashboard tarzı görseller.
* 2026-06-13 — Karar: VD-EXP-002 notebook Drive cache/reuse/resume davranışıyla çalışacak. | Gerekçe: Per-image BDD100K label okuma Colab/Drive üzerinde saatler sürebiliyor ve tekrar çalıştırmada sıfırdan yapılmamalı. | Etki: `train_label_entries_cache.json` label cache'i kullanılır; `bdd100k_vehicle_metadata.csv` varsa YOLO conversion atlanır; `best.pt` varsa eğitim atlanır, `last.pt` varsa eğitim resume edilir. | Alternatifler: Her runtime restart sonrası tüm dönüşüm/eğitimi sıfırdan başlatmak.
* 2026-06-14 — Karar: VD-EXP-002 YOLO conversion aşaması partial checkpoint ile resume edilecek. | Gerekçe: Label cache tam oluşsa bile conversion hücresi kesilirse `bdd100k_vehicle_metadata.csv` eksik/bozuk kalıp `split` kolonu hatası verebilir. | Etki: Conversion sırasında `train_conversion_rows_partial.csv` gibi partial metadata dosyaları yazılır; yeniden çalıştırmada mevcut satırlar atlanır ve eksik kalan image'lar tamamlanır. | Alternatifler: Conversion'ı her kesintiden sonra baştan döndürmek.
* 2026-06-14 — Karar: VD-EXP-002 notebook label/image overlap preflight yapacak. | Gerekçe: Drive'daki mevcut image mirror ile Archive.org/BDD label seti eşleşmedi; conversion 23.193 label için 0 image buldu ve boş metadata CSV üretti. | Etki: Notebook artık image index cache üretir ve conversion öncesi örnek label adlarının image klasöründe karşılığı var mı kontrol eder; eşleşme yoksa saatlerce conversion döndürmeden durur. | Alternatifler: Eşleşmeyen image setiyle conversion'ı boşa çalıştırmak.
* 2026-06-14 — Karar: VD-EXP-002 notebook, overlap sıfırsa Archive.org `bdd100k_images.zip` paketini otomatik Drive'a indirip çıkaracak. | Gerekçe: Mevcut Kaggle/Drive image mirror'ı Archive.org/BDD label adlarıyla eşleşmedi; kullanıcı image paketini notebook içinden doğrudan indirmek istiyor. | Etki: `AUTO_DOWNLOAD_MATCHING_BDD_IMAGES=True`; eşleşme yoksa `datasets/bdd100k/bdd100k_images.zip` indirilir, çıkarılır, stale `train_image_index.csv` / `val_image_index.csv` silinir ve overlap tekrar denenir. | Alternatifler: Kullanıcının image zip'i manuel yüklemesi veya YOLO-ready condition metadata'sız fallback'e geçmek.
* 2026-06-14 — Karar: VD-EXP-002 image lookup uzantı toleranslı olacak. | Gerekçe: Archive.org label cache'i bazı entry adlarını uzantısız stem (`0000f77c-...`) olarak veriyor; image index ise `.jpg` dosya adlarıyla oluşuyor. | Etki: Notebook image index'i hem stem hem `.jpg/.jpeg/.png` anahtarlarıyla eşler; conversion çıktısı gerçek image dosya adıyla yazılır ve `source_label_name` ayrıca saklanır. | Alternatifler: Label cache'i manuel silip yeniden üretmek veya tüm image dosyalarını yeniden adlandırmak.
* 2026-06-14 — Karar: VD-EXP-002 image index cache'i current root doğrulaması yapacak. | Gerekçe: Drive'da eski 11.124 satırlı `train_image_index.csv`, official 70.000 train image extract edildikten sonra da cache olarak yüklenip conversion'ı eski mirror path'leriyle başlatıyordu. | Etki: Notebook cached image index'i yalnız `TRAIN_IMAGE_DIR` / `VAL_IMAGE_DIR` altındaki path'lere aitse kullanır; farklı root'a ait cache stale sayılır ve yeniden build edilir. | Alternatifler: Kullanıcının cache dosyasını manuel silmesi.
* 2026-06-14 — Karar: VD-EXP-002 conversion 0 satır üretirse boş metadata yazmayacak. | Gerekçe: Eski runtime 11.124 satırlı stale image index ile çalışıp 0 usable row üretti; sonraki distribution cell `metadata_df` kolonları olmadığı için patladı. | Etki: Notebook artık 0-row conversion durumunda stale metadata/partial artifactleri siler ve net RuntimeError ile durur; sonraki hücreye bozuk `(0, 0)` metadata taşımaz. | Alternatifler: Sonraki distribution cell'de hatayı yakalamak.
* 2026-06-14 — Karar: VD-EXP-002 içinde `Colab/Drive Cache Repair` hücresi bulunacak. | Gerekçe: Kullanıcı manuel temizleme cell'ini ayrı kopyalamak yerine notebook'u toplu çalıştırmak istiyor. | Etki: Conversion öncesinde bozuk/boş `bdd100k_vehicle_metadata.csv`, eski `train_image_index.csv` / `val_image_index.csv` ve partial conversion dosyaları otomatik temizlenir; `train_label_entries_cache.json` korunur. | Alternatifler: Her hata sonrası Drive dosyalarını manuel silmek.
* 2026-06-14 — Karar: VD-EXP-002 official BDD100K train/val image archive kontrolü yapacak. | Gerekçe: Drive'daki Archive.org `bdd100k_images.zip` extract'i `images/100k/test` gösterdi; detection training için beklenen yapı 70K train + 10K val + 20K test. Eski nested mirror 11.124 train image içeriyor ve usable detection row üretmedi. | Etki: Notebook conversion öncesi train/val image split sayısını kontrol eder; eksikse `https://dl.cv.ethz.ch/bdd100k/data/100k_images_train.zip` ve `100k_images_val.zip` arşivlerini indirip çıkarır. `find_image_dir` artık en çok image içeren candidate'ı seçer. | Alternatifler: Eksik train/val ile küçük mirror üzerinde devam etmek veya kullanıcıdan manuel resmi train/val zip yüklemesini istemek.
* 2026-06-14 — Karar: VD-EXP-002 download URL sanitize ve combined archive inspect yapacak. | Gerekçe: Colab çıktısında URL'ler Markdown link formatı gibi görünebiliyor ve Drive'da mevcut `bdd100k_images.zip` train/val içerebilir veya yalnız test içerebilir. | Etki: Download helper `[https://...](https://...)` formatını düz URL'ye çevirir; official train/val indirmeden önce mevcut `bdd100k_images.zip` split sayıları incelenir ve train/val yeterliyse marker kaldırılıp tekrar extract edilir. | Alternatifler: Her durumda network download denemek veya manuel Drive yüklemesi istemek.

## 7) Milestones / Dönüm Noktaları (append-only)

* 2026-06-06 — Milestone: İlk web demo prototipi oluşturuldu. | Sonuç: Kullanıcı 2026-06-07’de bu kapsamı istemediğini belirtti; yeni yapı sıfırdan kuruldu.
* 2026-06-07 — Milestone: Resmi rapor başlıkları çıkarıldı. | Sonuç: ÖTR/PDR ve FTR/PCR `.docx` şablon başlıkları Markdown dosyalarına ayrıldı.
* 2026-06-07 — Milestone: Kapsamlı proje klasör yapısı kuruldu. | Sonuç: Rapor, mimari, araştırma, veri, model, mobil, backend, test ve governance alanları oluşturuldu.
* 2026-06-07 — Milestone: PDF ana akışı repo dokümantasyonuna işlendi. | Sonuç: Number Verification, ortam analizi, riskli araçta QoD ve yol/araç dışı kullanıcı durumu README, mimari, AI ve event şemasına eklendi.
* 2026-06-07 — Milestone: Repo hygiene ve contract scaffold eklendi. | Sonuç: Status/roadmap/security, contract schema, section map, data/model/test/governance şablonları ve project requirements/risks/decisions dosyaları oluşturuldu.
* 2026-06-08 — Milestone: Context-gated routing policy eklendi. | Sonuç: Ortam bağlamına göre QoD/uzman model çağırma politikası ve normal/kritik mod kaynak ayrımı netleştirildi.
* 2026-06-08 — Milestone: Repo private yapıldı. | Sonuç: GitHub visibility `PRIVATE` olarak doğrulandı.
* 2026-06-08 — Milestone: Runtime AI architecture contract paketi eklendi. | Sonuç: Frame inputtan final event/evidence çıktısına kadar pipeline, output contractları, routing policy, latency planı, scope ayrımı ve evidence UI logic dokümante edildi.
* 2026-06-08 — Milestone: Model araştırma ve demo runtime kararları netleştirildi. | Sonuç: Colab/MacBook ayrımı, 720p input, kamera açısı, açık veri/lisans yaklaşımı, hız final scope, lane sonrası faz ve QoD gerçek adapter hedefi dokümante edildi.
* 2026-06-08 — Milestone: Araç tespiti research paketi aksiyon dosyalarına bölündü. | Sonuç: Deep research raporu taşındı, kaynak listesi eklendi, model/dataset/benchmark/fine-tune/decision dosyaları oluşturuldu ve VehicleDetectionOutput contractı genişletildi.
* 2026-06-08 — Milestone: Dark manual test set ve condition-specific detector routing eklendi. | Sonuç: 3 dark video `Test/` altına taşındı, video dosyaları Git dışında bırakıldı, manual review CSV şablonu ve condition profile routing planı oluşturuldu.
* 2026-06-08 — Milestone: VD-EXP-001 YOLO11n pretrained dark detection koşusu çalıştırıldı. | Sonuç: `Test/video_1-3.mp4` üzerinde 1263 frame işlendi; detection outputs/labels local `runs/` altında, özet JSON `models/benchmarks/artifacts/VD-EXP-001-yolo11n-dark-summary.json` altında üretildi; manual accuracy pending.
* 2026-06-08 — Milestone: Condition experts deep research aksiyonlaştırıldı. | Sonuç: Rapor ilgili araştırma klasörüne taşındı; soru kapsam denetimi, dataset kaynak/lisans checklist'i, aksiyon yol haritası ve condition expert benchmark/experiment şablonları oluşturuldu.
* 2026-06-08 — Milestone: VD-EXP-001 qualitative manual review kaydedildi. | Sonuç: Genel araç detection davranışı kullanılabilir bulundu; false negative'ler ve kısa class flicker not edildi; sayısal manual accuracy counts pending.
* 2026-06-08 — Milestone: VD-EXP-002 BDD100K Colab skeleton eklendi. | Sonuç: BDD100K -> YOLO dönüşümü, condition metadata koruma, YOLO11n fine-tune, overall validation, condition breakdown validation ve export adımlarını içeren notebook oluşturuldu.
* 2026-06-08 — Milestone: BDD100K opsiyonel downloader helper eklendi. | Sonuç: Kaggle/direct/gdown modlarıyla Drive altına veri indirebilen helper script oluşturuldu; credential ve URL bilgileri repo dışında tutulacak.
* 2026-06-08 — Milestone: VD-EXP-002 notebook tek dosya pipeline'a çevrildi. | Sonuç: Notebook artık BDD100K indirme/yerleşim, conversion, pretrained baseline, fine-tune, optional challenger, baseline-delta ve condition breakdown adımlarını aynı dosyada yürütür.
* 2026-06-08 — Milestone: VD-EXP-002 Kaggle credential setup eklendi. | Sonuç: Notebook Colab Secrets, env veya gizli runtime prompt üzerinden Kaggle credential okuyabilir; API key repoya yazılmaz.
* 2026-06-10 — Milestone: Fine-tune backlog'a alındı ve pretrained baseline fazı açıldı. | Sonuç: Pretrained YOLO11s, YOLOv10n, YOLOv8n ve opsiyonel RT-DETR deneyleri comparison CSV ve plan dosyalarına eklendi.
* 2026-06-10 — Milestone: Sistem geneli pretrained baseline çağrı matrisi eklendi. | Sonuç: Condition, vehicle, tracking, speed, plate, OCR, traffic sign, lane/drivable area, cabin, risk fusion, QoD ve LLM explanation aşamaları ayrı model/policy/algorithm olarak sınıflandırıldı.
* 2026-06-10 — Milestone: Vehicle tracking deep research tamamlandı. | Sonuç: ByteTrack ilk baseline, BoT-SORT ReID-off ikinci alternatif seçildi; DeepSORT/StrongSORT ertelendi; benchmark planı, karar dosyası, CSV ve manual review şablonu eklendi.
* 2026-06-10 — Milestone: İlk tracking benchmark koşuları tamamlandı. | Sonuç: `TRK-EXP-001` ByteTrack ve `TRK-EXP-002` BoT-SORT ReID-off, 1263 frame üzerinde çalıştı; JSON özetleri ve lokal annotated videolar üretildi.
* 2026-06-10 — Milestone: ByteTrack manuel geri bildirimi kaydedildi. | Sonuç: Kullanıcı ByteTrack'in gayet iyi çalıştığını belirtti; aktif yön target/evidence hattına bağlama olarak netleşti.
* 2026-06-11 — Milestone: İlk track-to-event skeleton tamamlandı. | Sonuç: ByteTrack summary history sample ile yeniden üretildi; 3 video için hedef track seçildi ve `target_vehicle_selected` event skeletonları oluşturuldu.
* 2026-06-11 — Milestone: Plate/OCR deep research tamamlandı. | Sonuç: İki aşamalı target ROI plate detector + PaddleOCR/EasyOCR OCR + Türk plaka post-processing + temporal voting MVP kararı kaydedildi.
* 2026-06-11 — Milestone: POCR-EXP-001 target ROI crop/sample/clip extraction tamamlandı (v1). | Sonuç: 3 best ROI crop, 39 sample ROI crop ve 3 clip üretildi; sonradan `archive/plate_ocr_v1/` ve `runs/_archive/` altına taşındı.
* 2026-06-11 — Milestone: Plaka tarafına sıfırdan başlandı; v1 arşivlendi ve yeni plaka tespit smoke-test script'i yazıldı. | Sonuç: `run_plate_detection_smoke.py` (2 model, detected-frame bazlı, OCR yok) + `RUN_POCR_EXP_001.md` talimatı eklendi. Çalıştırma kullanıcının MacBook'unda yapılacak (sandbox'ta internet/torch yok).
* 2026-06-12 — Milestone: FTR uyumlu vehicle detection fine-tune planı oluşturuldu. | Sonuç: YOLO11n + BDD100K + Colab/Drive ana omurga seçildi; adverse condition datasetleri specialist/evaluation fazına ayrıldı.
* 2026-06-12 — Milestone: Vehicle detection deep research ve notebook birleştirildi. | Sonuç: Condition expert deep research raporu araç tespiti deep research klasörüne taşındı; notebook general/specialist fine-tune ve karşılaştırma akışını destekleyecek şekilde yeniden yazıldı.
* 2026-06-13 — Milestone: VD-EXP-002 Colab notebook ilk hücre syntax hatası düzeltildi. | Sonuç: Yanlışlıkla `code` hücresi olarak kalan kopya Config açıklaması kaldırıldı; tüm Python hücreleri `ast.parse` ve notebook JSON validasyonundan geçti.
* 2026-06-13 — Milestone: VD-EXP-002 Colab notebook Drive mount + all-specialists config ile güncellendi. | Sonuç: Notebook artık `/content/drive` path'leri oluşturulmadan önce Drive'ı mount eder; general, night, rain ve fog specialist deneyleri aktif gelir.
* 2026-06-13 — Milestone: VD-EXP-002 label download fallback düzeltildi. | Sonuç: Google Drive incelemesinde `det_train.json` bulunmadı; notebook label-only indirmede ETH hata verirse Internet Archive fallback ile eski BDD100K image label JSON'larını kullanabilecek.
* 2026-06-13 — Milestone: VD-EXP-002 per-image label + missing val image düzeltmesi yapıldı. | Sonuç: `TRAIN_LABEL_DIR -> labels/100k/train` formatı desteklendi; `VAL_IMAGE_DIR` yoksa hata yerine uyarı verilecek ve hash split kullanılacak.
* 2026-06-13 — Milestone: 4 siyah-beyaz akademik figür üretildi. | Sonuç: Şekil 1 sistem mimarisi, Şekil 2 algoritmik pipeline, Şekil 3 event/evidence JSON akışı ve Şekil 5 gerçek demo frame overlay çıktıları PNG/PDF/SVG olarak üretildi; PNG'ler 3000x1800 ve 300 DPI.
* 2026-06-13 — Milestone: VD-EXP-002 cache/reuse patch'i eklendi. | Sonuç: Notebook artık label cache, metadata cache, checkpoint skip ve interrupted training resume destekliyor.
* 2026-06-14 — Milestone: VD-EXP-002 metadata validation + partial conversion resume eklendi. | Sonuç: Eksik `split` kolonlu metadata CSV artık geçerli sayılmayacak; conversion partial checkpoint üzerinden devam edebilecek.
* 2026-06-14 — Milestone: BDD100K image/label mismatch teşhis edildi. | Sonuç: `bdd100k_vehicle_metadata.csv` boş; `skipped_no_image=23193` çıktı. Mevcut Drive image setindeki örnek dosyalar label adlarıyla eşleşmiyor; eşleşen BDD100K 100K Images paketi veya label seti gerekiyor.
* 2026-06-14 — Milestone: VD-EXP-002 Archive.org image auto-repair patch'i eklendi. | Sonuç: Notebook artık zero-overlap durumunda Archive.org `bdd100k_images.zip` arşivini Drive'a indirip çıkarabilir, image index cache'lerini sıfırlayıp dönüşümü yeniden deneyebilir.
* 2026-06-14 — Milestone: VD-EXP-002 uzantısız label adı eşleştirme hatası düzeltildi. | Sonuç: `0000f77c-6257be58` gibi label adları `0000f77c-6257be58.jpg` image dosyalarıyla eşleşebilir hale getirildi.
* 2026-06-14 — Milestone: VD-EXP-002 stale image index cache hatası düzeltildi. | Sonuç: 11.124 satırlı eski mirror index'i, official `bdd100k/bdd100k/images/100k/train` root'una ait olmadığı için otomatik yok sayılacak ve 70.000 satırlı yeni index üretilecek.
* 2026-06-14 — Milestone: VD-EXP-002 zero-row metadata guard eklendi. | Sonuç: Boş `bdd100k_vehicle_metadata.csv` sonraki cell'lere taşınmayacak; conversion hücresi 0 satırda kendisi temizleyip duracak.
* 2026-06-14 — Milestone: VD-EXP-002 `Colab/Drive Cache Repair` hücresi eklendi. | Sonuç: Notebook `Run All` ile çalıştırıldığında conversion başlamadan önce stale cache temizliği otomatik yapılır.
* 2026-06-14 — Milestone: VD-EXP-002 official train/val image auto-download patch'i eklendi. | Sonuç: Notebook artık 11.124 image'lık eski mirror yerine yaklaşık 70.000 train ve 10.000 val image bekler; eksikse resmi image arşivlerini indirmeyi dener.
* 2026-06-14 — Milestone: VD-EXP-002 URL sanitize + combined archive inspect patch'i eklendi. | Sonuç: Colab Markdown URL formatı ve mevcut `bdd100k_images.zip` yeniden extract ihtimali otomatik ele alınır.

## 8) Yapılanlar

* [x] Yeni `.txt` kapsamı okundu.
* [x] Resmi ÖTR/PDR ve FTR/PCR `.docx` başlıkları çıkarıldı.
* [x] `docs/01_resmi_raporlar/PDR_OTR` altında tüm PDR/ÖTR başlık dosyaları oluşturuldu.
* [x] `docs/01_resmi_raporlar/PCR_FTR` altında tüm PCR/FTR başlık dosyaları oluşturuldu.
* [x] Proje kapsamı, sistem mimarisi, AI, veri seti, mobil, backend, 5G/QoD, evidence, test, etik ve rapor yazımı dokümanları oluşturuldu.
* [x] 14 araştırma başlığı `research/` altında ayrı klasörlere ayrıldı.
* [x] Açık sorular merkezi dosyada toplandı.
* [x] `leD24n5kb...pdf` içindeki ana akış mevcut repo kapsamıyla karşılaştırıldı.
* [x] Login/Number Verification, ortam analizi, riskli araçta QoD ve araç dışı kullanıcı/yol durumu dokümanlaştırıldı.
* [x] Ana auth-normal mode-QoD akışı `architecture/flows/auth_normal_qod_flow.md` dosyasına Mermaid diyagramı olarak eklendi.
* [x] GPT feedback içinden geçerli repo hijyeni, security, contract, section map ve şablon önerileri işlendi.
* [x] Repo güvenliği için `.gitignore` sıkılaştırıldı; benchmark/experiment küçük kanıt dosyaları takip edilebilir hale getirildi.
* [x] Context-gated model routing dokümanı ve contract alanları eklendi.
* [x] GitHub repo private görünürlüğe alındı.
* [x] Runtime AI pipeline, model output contract, expert routing policy, event schema, latency/frequency, scope, evidence UI logic ve AI risk register eklendi.
* [x] Model araştırma ve demo runtime varsayımları dokümante edildi.
* [x] Araç tespiti deep research raporu taşındı ve aksiyon dosyalarına bölündü.
* [x] YOLO11n ilk ölçülebilir vehicle detector baseline olarak kaydedildi.
* [x] VehicleDetectionOutput contractı bbox/evidence/tracking uyumlu olacak şekilde genişletildi.
* [x] 3 dark/low-light manuel test videosu `Test/` altına taşındı ve Git dışında bırakıldı.
* [x] Condition-specific detector routing planı oluşturuldu.
* [x] Manual video benchmark review şablonu eklendi.
* [x] VD-EXP-001 YOLO11n pretrained zero-fine-tune dark detection koşusu çalıştırıldı.
* [x] Condition experts deep research raporu taşındı ve kapsam/aksiyon dosyalarına bölündü.
* [x] Condition expert stratejisi Strateji 1 olarak netleştirildi.
* [x] VD-EXP-001 qualitative manual review summary kaydedildi.
* [x] İlk fine-tune yönü condition-aware general vehicle detector olarak netleştirildi.
* [x] BDD100K dataset card, class/condition mapping ve VD-EXP-002 Colab notebook skeleton eklendi.
* [x] BDD100K için opsiyonel Colab downloader helper eklendi.
* [x] VD-EXP-002 notebook tek dosyada download + placement + training + test + baseline-delta pipeline'a çevrildi.
* [x] Kaggle credential setup notebook içine güvenli şekilde eklendi.
* [x] Fine-tune kapsamı TODO/backlog olarak kaydedildi.
* [x] Pretrained zero-fine-tune vehicle detector baseline fazı planlandı.
* [x] Sistem geneli pretrained baseline model çağrı matrisi oluşturuldu.
* [x] Vehicle tracking deep research raporu yazıldı.
* [x] ByteTrack / BoT-SORT tracking baseline kararı kaydedildi.
* [x] Tracking benchmark planı ve manuel review şablonu oluşturuldu.
* [x] `TRK-EXP-001` ByteTrack tracking koşusu çalıştırıldı.
* [x] `TRK-EXP-002` BoT-SORT ReID-off tracking koşusu çalıştırıldı.
* [x] Tracking otomatik sonuç özet raporu oluşturuldu.
* [x] ByteTrack manuel geri bildirimi kaydedildi.
* [x] Track-to-target/event next-phase planı oluşturuldu.
* [x] `TrackingOutput` post-process script'i eklendi.
* [x] Track state summary içine `center_history_sample` ve `bbox_history_sample` eklendi.
* [x] `track_stability` ve `target_selection_score` heuristic hesaplaması eklendi.
* [x] Her dark test videosu için bir `target_track_id` seçildi.
* [x] İlk `target_vehicle_selected` event/evidence skeleton JSON çıktıları üretildi.
* [x] Plate/OCR deep research raporu yazıldı.
* [x] Plate/OCR baseline kararı kaydedildi.
* [x] Plate/OCR benchmark planı oluşturuldu.
* [x] Plate/OCR dataset/lisans checklist'i oluşturuldu.
* [x] Plate/OCR manual review CSV şablonu eklendi.
* [x] Target ROI crop extraction script'i yazıldı.
* [x] `POCR-EXP-001` target ROI crop extraction smoke test çalıştırıldı.
* [x] 3 target event için 3 ROI crop üretildi.
* [x] 3 target event için 39 sample ROI crop ve 3 target ROI clip üretildi.
* [x] FTR uyumlu vehicle detection fine-tune planı oluşturuldu.
* [x] Condition expert deep research raporunu vehicle detection deep research klasörüne taşı.
* [x] BDD100K YOLO11n Colab notebook'unu general + opsiyonel night/rain/fog specialist comparison hattı olarak yeniden yaz.
* [x] BDD100K Kaggle mirror path discovery hatası için recursive repair cell eklendi.

## 9) Yapılacaklar (Next)

* [x] `docs/15_acik_sorular/00_acik_sorular.md` içindeki ilk soru seti kullanıcıyla netleştirildi.
* [ ] `reports/PDR_OTR` altında resmi Ön Tasarım Raporu taslağını yaz.
* [ ] Rapor için ilk sistem diyagramını `architecture/diagrams` altında gerçek içerikle üret.
* [x] Event JSON contractını `architecture/contracts` altında ayrı dosyaya taşı.
* [ ] Veri seti kaynaklarını lisanslarıyla doğrula.
* [ ] `docs/04_yapay_zeka/research_required.md` içindeki araştırma gereksinimlerini kaynak/link/lisans bilgileriyle doldur.
* [x] Model geliştirme ilk odağı belirlendi.
* [x] Araç tespiti için Colab deney planı oluştur.
* [x] Araç tespiti için MacBook runtime benchmark planı oluştur.
* [x] YOLO/RT-DETR adayları için araştırma karşılaştırma tablosu oluştur.
* [x] VD-EXP-001 YOLO11n pretrained zero-fine-tune baseline deneyini çalıştır.
* [x] `Test/video_1-3.mp4` için qualitative dark manual review sonucunu kaydet.
* [ ] `Test/video_1-3.mp4` için sayısal manual review counts kaydet.
* [ ] VD-EXP-008 YOLO11s pretrained zero-fine-tune benchmark koşusunu çalıştır.
* [ ] VD-EXP-009 YOLOv10n pretrained zero-fine-tune benchmark koşusunu çalıştır.
* [ ] VD-EXP-010 YOLOv8n pretrained zero-fine-tune benchmark koşusunu çalıştır.
* [ ] Pretrained benchmark sonuçlarını `models/benchmarks/vehicle_detection_comparison.csv` içine işleyip bir baseline seç.
* [x] `TrackingOutput` normalizer uygulama planını oluştur.
* [x] Track state store uygulama planını oluştur.
* [x] Track-level class voting, confidence smoothing ve `track_stability` hesaplamasını implementation planına bağla.
* [x] Target vehicle selection skorlamasını uygulama planına bağla.
* [x] İlk event/evidence JSON skeleton üretimini planla.
* [x] Target ROI crop extraction script'ini yaz.
* [x] Plaka v1 iş ürünlerini `archive/plate_ocr_v1/` altına taşı (sıfırdan başlangıç).
* [x] İki modelli plaka tespit smoke-test script'ini yaz (`run_plate_detection_smoke.py`, detector-only).
* [ ] (Kullanıcı/MacBook) `POCR-EXP-001` plate detector smoke test'i çalıştır: `--models yolo yolos`.
* [ ] İki plaka modelini overlay'ler üzerinden manuel karşılaştır ve birini seç.
* [ ] `POCR-EXP-002` için PaddleOCR baseline çalıştır.
* [ ] `POCR-EXP-003` için EasyOCR baseline comparison çalıştır.
* [ ] Plate/OCR sonuçlarını event/evidence JSON skeleton içine işle.
* [ ] Plate/OCR manual review sonuçlarını `testing/templates/manual_plate_ocr_review.csv` formatına göre kaydet.
* [ ] Relative speed baseline için `center_history_sample` üzerinden pixel displacement ve motion candidate skorunu üret. (Deferred)
* [ ] Tracking manual review sonuçlarını `testing/templates/manual_tracking_review.csv` formatına göre kaydet.
* [x] Plate detection pretrained/public baseline adaylarını araştırıp ilk license plate detector çağrısını seç.
* [x] PaddleOCR / EasyOCR plate OCR baseline kıyasını planla.
* [ ] Speed baseline için track displacement + relative speed hesaplama contractını yaz.
* [ ] Condition profile için CLIP/image-classifier baseline test planını yaz.
* [ ] "Plaka tabelası" ifadesinin trafik levhasını da kapsayıp kapsamadığını netleştir.
* [x] VD-EXP-002 ana fine-tune omurgasını seç: YOLO11n + BDD100K + Colab/Drive.
* [x] VD-EXP-002 notebook config'ini `.pt` mandatory, ONNX optional olacak şekilde son kontrol et.
* [ ] VD-EXP-002 notebook içinde BDD100K download yöntemini Colab/Drive pratikliğine göre çalıştır: Kaggle / manual Drive / direct URL / gdown.
* [ ] UA-DETRAC erişim/lisans doğrulamasını tamamla.
* [ ] Condition expert dataset kaynak/lisans checklist'ini tamamla.
* [x] Condition-aware general road-domain detector Colab fine-tune notebook skeleton'ını oluştur.
* [ ] VD-EXP-002 BDD100K Colab dönüşüm smoke test'ini küçük subset ile çalıştır.
* [ ] VD-EXP-002 BDD100K Colab YOLO11n fine-tune koşusunu çalıştır.
* [ ] (Deferred) `best_general` seçildikten sonra `night_low_light` specialist deneyini başlat.
* [x] GitHub repo oluştur, private görünürlüğe al ve commitleri pushla.

## 10) Bilinen Sorunlar / Teknik Borç / Riskler

* Hız için referans mesafe/kalibrasyon yöntemi final scope teknik tasarım kararı olarak duruyor; MVP için engelleyici değil.
* Ground truth hız için literatür/çalışma kaynakları henüz doğrulanmadı.
* Maskeleme yapılmayacağı için veri lisansı ve kişisel veri riski daha yüksek.
* Araç tespiti için ilk baseline YOLO11n seçildi; final model henüz seçilmedi ve benchmark sonrası belirlenecek.
* 3 dark video dark-specific model eğitimi için yeterli değildir; bu videolarla eğitim yapmak overfit ve savunulamaz sonuç riski taşır.
* `dark` ayrı specialist olarak hemen açılmamalı; başlangıçta `night_low_light` routing etiketi veya general fallback altında izlenmelidir.
* Mevcut false negative ve kısa class flicker gözlemleri frame-level detector kararından çok track-level smoothing, temporal voting ve condition-aware fine-tune ile ele alınmalıdır.
* Pretrained baseline sonuçları ground-truth mAP değildir; başlangıçta manual review + runtime + pipeline kullanılabilirliği ölçümü olarak yorumlanmalıdır.
* Tracking ground truth henüz yok; `Test/video_1-3.mp4` üstündeki ilk tracking metrikleri manual review ve proxy metrikler olacaktır.
* ID switch evidence ve plate OCR temporal voting'i yanlış araca bağlayabilir; bu yüzden `id_switch_suspected`, `track_stability` ve best-frame audit alanları zorunlu tutulmalıdır.
* Track-to-event scoring heuristic'tir; ground-truth olmadan mutlak doğruluk iddiası kurulamaz. Manuel review ile seçilen hedef aracın doğru olup olmadığı kontrol edilmelidir.
* Plate/OCR ilk araştırma kararı kaynaklıdır ama henüz lokal model koşusu yapılmadı; lisans/model card bilgisi model indirmeden önce tekrar doğrulanmalıdır.
* Ultralytics tabanlı plate detector modelleri AGPL-3.0/Enterprise etkisi taşıyabilir; private repo olmak lisans riskini otomatik çözmez.
* Plaka metni kişisel veri gibi ele alınmalı; raw plate crop ve OCR çıktıları Git'e eklenmemeli, demo/raporda maskeleme opsiyonu korunmalıdır.
* Vehicle detection fine-tune tekrar aktif planlamaya alındı; ilk resmi model `YOLO11n`, ana veri omurgası BDD100K, eğitim ortamı Colab + Drive, zorunlu model çıktısı `.pt`, ONNX ise opsiyonel deployment kanıtı olarak tutulacak.
* Arkadaş önerisindeki ACDC/DAWN/ExDark/Foggy Cityscapes kaynakları ilk eğitim merge'üne doğrudan alınmayacak; önce BDD100K general detector eğitilecek, condition breakdown zayıflık gösterirse specialist/evaluation fazına taşınacak.
* ReID şimdilik kapalıdır; ancak uzun occlusion veya yoğun trafik senaryosunda BoT-SORT ReID modu yeniden değerlendirilebilir.
* Fine-tune ertelendiği için domain gap tamamen çözülmüş sayılmaz; bu karar yalnız pipeline omurgasını hızlı ve ölçülebilir kurmak içindir.
* Deep research raporundaki ChatGPT citation placeholder'ları final rapor kaynağı değildir; final kaynaklar `research/03_condition_experts/dataset_source_checklist.md` ve ilgili official URL'lerle doğrulanmalıdır.
* Colab deney dosyaları henüz oluşturulmadı.
* MacBook runtime benchmark planı oluşturuldu; script/uygulama henüz yok.
* Deep research raporundan kaynaklanan model/dataset URL'leri `research/02_vehicle_detection/deep_research/sources.md` içinde tutuluyor; final rapor öncesi kaynaklar tekrar doğrulanmalı.
* Repo private olsa bile veri/checkpoint/API key/evidence dosyaları yanlışlıkla commit edilmemeli.
* `architecture/diagrams/*.drawio` dosyaları şu an placeholder; gerçek diyagram içeriği çizilmeli.
* Backend ve Android uygulama skeleton kodu henüz yok; repo hâlâ dokümantasyon/contract aşamasında.

## 11) Notlar ve Tuzaklar (Pitfalls)

* Resmi rapor 3-10 sayfa sınırında; dokümanlardaki uzun açıklamalar rapora özetlenerek aktarılmalı.
* PDR/ÖTR tasarım dilinde, PCR/FTR kanıt ve metrik dilinde yazılmalı.
* “30 FPS” tüm uzman modeller her karede çalışır anlamına gelmemeli.
* Plaka/yüz/veri saklama KVKK riski taşır.
* Eski demo prototipi bu yeni kapsamın ana çıktısı değildir.
* Notebook açıklama/metin blokları mutlaka `markdown` hücresi olmalı; Türkçe açıklama satırı `code` hücresinde kalırsa Colab ilk hücrede `SyntaxError` verir.
* Colab'da `/content/drive/MyDrive/...` altında klasörler boş görünürse önce Drive mount hücresinin çalıştığından ve doğru Google hesabına bağlanıldığından emin olun; mount edilmeden çalışan notebook aynı path altında boş lokal klasörler oluşturabilir.
* BDD100K label kaynaklarında öncelik `det_20/det_train.json` / `det_val.json`; fallback olarak `bdd100k_labels_images_train.json` / `bdd100k_labels_images_val.json` kabul edilir. Her iki format da condition metadata için kullanılabilir, ancak raporda kullanılan label sürümü açık yazılmalıdır.
* Archive.org `bdd100k_labels.zip` fallback'i tek büyük train/val JSON değil, image başına JSON dosyaları çıkarabilir (`labels/100k/train/*.json`). Notebook bu dizin formatını desteklemeli; aksi halde tek bir JSON dosyasını bütün dataset sanıp dönüşümü kırar.
* `outputs/` klasörü `.gitignore` altında; akademik figür çıktıları lokal dosya olarak hazırdır ama Git'e otomatik eklenmez. Script takip edilir, çıktılar gerekirse final rapor asset klasörüne bilinçli olarak kopyalanmalıdır.
* Colab/Drive üzerinde uzun süren BDD100K per-image label okuma tamamlandıysa `datasets/bdd100k_vehicle_yolo/metadata/train_label_entries_cache.json` tekrar kullanılmalı. YOLO dönüşümü tamamlandıktan sonra `bdd100k_vehicle_metadata.csv` oluşur; bu dosya varsa conversion hücresi tekrar çalıştırıldığında baştan dönmemelidir.
* `KeyError: 'split'` hatası, label cache'in değil YOLO conversion metadata'sının eksik/bozuk olduğunu gösterir. Çözüm: güncel notebook ile conversion hücresini tekrar çalıştırmak; `train_label_entries_cache.json` yeniden okunur ama 23K JSON tek tek tekrar okunmaz, partial conversion varsa kaldığı yerden devam eder.
* `skipped_no_image=23193` ve `(0, 0)` metadata çıktısı image/label mismatch göstergesidir. Bu durumda mevcut `bdd100k_vehicle_metadata.csv` silinmeli/yeniden yazılmalı ama asıl çözüm eşleşen BDD100K image paketi sağlamaktır; aksi halde conversion yine 0 satır üretir.
* Archive.org `bdd100k_images.zip` yaklaşık 6.5 GB'dir; Drive alanı ve indirme/çıkarma süresi GPU türünden çok Drive/network I/O hızına bağlıdır. İndirme başladıktan sonra runtime kesilirse `.part` dosyası kalabilir; notebook tekrar çalıştığında final zip yoksa yeniden indirir.
* BDD100K label entry `name` alanı bazen uzantısız stem olarak gelebilir. `train_image_index.csv` içinde 70K image görünmesine rağmen overlap 0 ise önce stem-vs-`.jpg` eşleştirme mantığını kontrol et; manuel yeniden indirme bu durumda çözüm değildir.
* `Loading cached train image index ... rows: 11124` görülürse bu eski Kaggle/mirror cache'idir; official Archive.org image extract sonrası beklenen train image index yaklaşık 70.000 satırdır. Güncel notebook bu cache'i stale sayar; eski notebook çalışıyorsa hücre durdurulup güncel notebook ile tekrar başlatılmalıdır.
* Distribution cell'de `metadata_df is missing required columns` hatası görülürse önceki conversion hücresi boş `(0, 0)` metadata üretmiştir. Bu genellikle eski notebook/runtime ile stale image index kullanıldığını gösterir; distribution cell'i tekrar tekrar çalıştırmak çözmez.
* Archive.org `bdd100k_images.zip` her ortamda BDD100K train/val split'lerini sağlamıyor olabilir; Drive kontrolünde `images/100k/test` görünüp train/val görünmezse detection fine-tune için resmi `100k_images_train.zip` ve `100k_images_val.zip` gerekir. Expected image index: train ~70.000, val ~10.000.
* Colab download çıktısında URL `[https://...](https://...)` gibi görünürse helper bunu sanitize eder; yine de `dl.cv.ethz.ch` DNS hatası devam ederse bu Colab network/host erişim sorunudur. Notebook önce mevcut `bdd100k_images.zip` içeriğini inspect ederek network download ihtiyacını azaltır.

### Güncelleme Kaydı

* Son güncelleme: 2026-06-14
