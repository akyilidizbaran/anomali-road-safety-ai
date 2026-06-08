# PROJECT_MEMORY

## 0) TL;DR (En güncel durum)

* Şu an ne yapıyoruz? Anomali Road Safety AI için resmi PDR/ÖTR, PCR/FTR ve `leD24n5kb...pdf` içindeki ana akışla uyumlu dokümantasyon-first proje reposu geliştiriliyor.
* Son değişiklik neydi? Runtime AI pipeline, model output contract, partial event schema, expert routing policy, frequency/latency budget, MVP/final/future scope, evidence UI logic ve AI risk register dokümanları eklendi.
* Bir sonraki net adım ne? Araç tespiti için model aday araştırması ve Colab baseline deney planı hazırlamak; `docs/04_yapay_zeka/research_required.md` içindeki araştırma gereksinimlerini doldurmak.

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

## 3) Mimari Özet

* Bileşenler: Login/Auth client, Number Verification adapter, Android mobil istemci, video aktarım katmanı, edge/backend inference server, normal mode pipeline, critical mode expert selector, QoD/5G adapter, event fusion, evidence store, explanation layer.
* Veri akışı: Kullanıcı adı/şifre girilir -> Number Verification API kullanıcı/cihaz/oturum eşleşmesini doğrular -> CameraX frame üretir -> edge/backend alır -> frame preprocessing/quality analysis -> normal mod ortam/sahne analizi -> araç detection root model -> tüm araçlar için hafif tracking -> target/risky vehicle selection -> target ROI generation -> context-gated expert routing -> riskli araçta QoD aday/request akışı -> kritik mod gerekiyorsa seçili uzman modeller -> event fusion -> event JSON -> evidence package -> mobil overlay/evidence ekranı.
* Önemli dizinler/modüller: `docs/` rapor ve teknik açıklamalar; `research/` derin araştırma başlıkları; `reports/` resmi rapor çalışma alanı; `architecture/` diyagram ve contract; `project/` karar/risk/gereksinim; `mobile/`, `backend/`, `data/`, `models/`, `testing/`, `governance/` geliştirme alanları.

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

## 7) Milestones / Dönüm Noktaları (append-only)

* 2026-06-06 — Milestone: İlk web demo prototipi oluşturuldu. | Sonuç: Kullanıcı 2026-06-07’de bu kapsamı istemediğini belirtti; yeni yapı sıfırdan kuruldu.
* 2026-06-07 — Milestone: Resmi rapor başlıkları çıkarıldı. | Sonuç: ÖTR/PDR ve FTR/PCR `.docx` şablon başlıkları Markdown dosyalarına ayrıldı.
* 2026-06-07 — Milestone: Kapsamlı proje klasör yapısı kuruldu. | Sonuç: Rapor, mimari, araştırma, veri, model, mobil, backend, test ve governance alanları oluşturuldu.
* 2026-06-07 — Milestone: PDF ana akışı repo dokümantasyonuna işlendi. | Sonuç: Number Verification, ortam analizi, riskli araçta QoD ve yol/araç dışı kullanıcı durumu README, mimari, AI ve event şemasına eklendi.
* 2026-06-07 — Milestone: Repo hygiene ve contract scaffold eklendi. | Sonuç: Status/roadmap/security, contract schema, section map, data/model/test/governance şablonları ve project requirements/risks/decisions dosyaları oluşturuldu.
* 2026-06-08 — Milestone: Context-gated routing policy eklendi. | Sonuç: Ortam bağlamına göre QoD/uzman model çağırma politikası ve normal/kritik mod kaynak ayrımı netleştirildi.
* 2026-06-08 — Milestone: Repo private yapıldı. | Sonuç: GitHub visibility `PRIVATE` olarak doğrulandı.
* 2026-06-08 — Milestone: Runtime AI architecture contract paketi eklendi. | Sonuç: Frame inputtan final event/evidence çıktısına kadar pipeline, output contractları, routing policy, latency planı, scope ayrımı ve evidence UI logic dokümante edildi.

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

## 9) Yapılacaklar (Next)

* [x] `docs/15_acik_sorular/00_acik_sorular.md` içindeki ilk soru seti kullanıcıyla netleştirildi.
* [ ] `reports/PDR_OTR` altında resmi Ön Tasarım Raporu taslağını yaz.
* [ ] Rapor için ilk sistem diyagramını `architecture/diagrams` altında gerçek içerikle üret.
* [x] Event JSON contractını `architecture/contracts` altında ayrı dosyaya taşı.
* [ ] Veri seti kaynaklarını lisanslarıyla doğrula.
* [ ] `docs/04_yapay_zeka/research_required.md` içindeki araştırma gereksinimlerini kaynak/link/lisans bilgileriyle doldur.
* [x] Model geliştirme ilk odağı belirlendi.
* [ ] Araç tespiti için Colab deney planı oluştur.
* [ ] YOLO/RT-DETR adayları için araştırma karşılaştırma tablosu oluştur.
* [x] GitHub repo oluştur, private görünürlüğe al ve commitleri pushla.

## 10) Bilinen Sorunlar / Teknik Borç / Riskler

* Hız için referans mesafe/kalibrasyon yöntemi halen teknik tasarım kararı gerektiriyor.
* Ground truth hız için literatür/çalışma kaynakları henüz doğrulanmadı.
* Maskeleme yapılmayacağı için veri lisansı ve kişisel veri riski daha yüksek.
* Araç tespiti için model ailesi henüz seçilmedi; araştırma sonrası karar verilecek.
* Colab deney dosyaları henüz oluşturulmadı.
* Repo private olsa bile veri/checkpoint/API key/evidence dosyaları yanlışlıkla commit edilmemeli.
* `architecture/diagrams/*.drawio` dosyaları şu an placeholder; gerçek diyagram içeriği çizilmeli.
* Backend ve Android uygulama skeleton kodu henüz yok; repo hâlâ dokümantasyon/contract aşamasında.

## 11) Notlar ve Tuzaklar (Pitfalls)

* Resmi rapor 3-10 sayfa sınırında; dokümanlardaki uzun açıklamalar rapora özetlenerek aktarılmalı.
* PDR/ÖTR tasarım dilinde, PCR/FTR kanıt ve metrik dilinde yazılmalı.
* “30 FPS” tüm uzman modeller her karede çalışır anlamına gelmemeli.
* Plaka/yüz/veri saklama KVKK riski taşır.
* Eski demo prototipi bu yeni kapsamın ana çıktısı değildir.

### Güncelleme Kaydı

* Son güncelleme: 2026-06-08
