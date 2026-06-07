# PROJECT_MEMORY

## 0) TL;DR (En güncel durum)

* Şu an ne yapıyoruz? Anomali Road Safety AI için resmi PDR/ÖTR ve PCR/FTR şablonlarına dayalı, sıfırdan kurulmuş kapsamlı Markdown proje dokümantasyon ve klasör yapısı hazırlandı.
* Son değişiklik neydi? Public/pretrained model + fine-tune/adaptation yaklaşımı dokümanlara eklendi; kök `README.md` ve `.gitignore` oluşturuldu.
* Bir sonraki net adım ne? Araç tespiti için araştırma karşılaştırma tablosu ve Colab deney planı hazırlamak.

## 1) Proje Amacı ve Kapsam

* Amaç: Telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka çıkarım hattında analiz ederek araç, plaka, hız, şerit, sürücü/yolcu, yol-hava koşulu ve çevre insanlarını değerlendiren; riskli olayları mobil arayüzde gösteren ve kritik olayları denetlenebilir evidence paketlerine dönüştüren karar destek sistemi geliştirmek.
* Kapsam içi: Mobil kamera, edge/backend çıkarım, araç tespiti, tracking, tek hedef araç, plaka/OCR, hız yaklaşımı, şerit/road marking, sahne/hava/görüş, cabin risk koşullu analizi, normal/kritik mod, QoD seçici karar, Number Verification adapter, event JSON, evidence package, test metrikleri, KVKK/etik.
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

* Bileşenler: Android mobil istemci, video aktarım katmanı, edge/backend inference server, normal mode pipeline, critical mode expert selector, QoD/Number Verification adapter, event fusion, evidence store, explanation layer.
* Veri akışı: CameraX frame üretir -> edge/backend alır -> preprocess -> normal mod araç tespiti/takip/sahne analizi -> risk pre-score -> kritik mod gerekiyorsa uzman modeller -> event JSON -> evidence store -> mobil overlay/evidence ekranı.
* Önemli dizinler/modüller: `docs/` rapor ve teknik açıklamalar; `research/` derin araştırma başlıkları; `reports/` resmi rapor çalışma alanı; `architecture/` diyagram ve contract; `project/` karar/risk/gereksinim; `mobile/`, `backend/`, `data/`, `models/`, `testing/`, `governance/` geliştirme alanları.

## 4) Konvansiyonlar ve Standartlar

* Kod stili / lint / format: Henüz kod projesi kurulmadı; bu aşama dokümantasyon ve planlama aşamasıdır.
* Branch/commit yaklaşımı: Git repo yok; kararlar `PROJECT_MEMORY.md` ve `project/decisions/README.md` üzerinden takip edilecek.
* İsimlendirme/klasör düzeni: Resmi raporlar `PDR_OTR` ve `PCR_FTR` adlarıyla tutulur; PDR=ÖTR, PCR=FTR karşılığı olarak not edilmiştir.

## 5) Kurulum & Çalıştırma

* Gereksinimler: Bu aşamada yalnız Markdown dosyalarını okuyacak/edit edecek bir editör yeterlidir.
* Komutlar: Yok.
* Ortam değişkenleri (sadece İSİMLER): Yok.
* Lokal geliştirme notları: Kod geliştirme başladığında mobil/backend için ayrı kurulum dosyaları eklenmelidir.
* Public repo: `https://github.com/akyilidizbaran/anomali-road-safety-ai`

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

## 7) Milestones / Dönüm Noktaları (append-only)

* 2026-06-06 — Milestone: İlk web demo prototipi oluşturuldu. | Sonuç: Kullanıcı 2026-06-07’de bu kapsamı istemediğini belirtti; yeni yapı sıfırdan kuruldu.
* 2026-06-07 — Milestone: Resmi rapor başlıkları çıkarıldı. | Sonuç: ÖTR/PDR ve FTR/PCR `.docx` şablon başlıkları Markdown dosyalarına ayrıldı.
* 2026-06-07 — Milestone: Kapsamlı proje klasör yapısı kuruldu. | Sonuç: Rapor, mimari, araştırma, veri, model, mobil, backend, test ve governance alanları oluşturuldu.

## 8) Yapılanlar

* [x] Yeni `.txt` kapsamı okundu.
* [x] Resmi ÖTR/PDR ve FTR/PCR `.docx` başlıkları çıkarıldı.
* [x] `docs/01_resmi_raporlar/PDR_OTR` altında tüm PDR/ÖTR başlık dosyaları oluşturuldu.
* [x] `docs/01_resmi_raporlar/PCR_FTR` altında tüm PCR/FTR başlık dosyaları oluşturuldu.
* [x] Proje kapsamı, sistem mimarisi, AI, veri seti, mobil, backend, 5G/QoD, evidence, test, etik ve rapor yazımı dokümanları oluşturuldu.
* [x] 14 araştırma başlığı `research/` altında ayrı klasörlere ayrıldı.
* [x] Açık sorular merkezi dosyada toplandı.

## 9) Yapılacaklar (Next)

* [x] `docs/15_acik_sorular/00_acik_sorular.md` içindeki ilk soru seti kullanıcıyla netleştirildi.
* [ ] `reports/PDR_OTR` altında resmi Ön Tasarım Raporu taslağını yaz.
* [ ] Rapor için ilk sistem diyagramını `architecture/diagrams` altında üret.
* [ ] Event JSON contractını `architecture/contracts` altında ayrı dosyaya taşı.
* [ ] Veri seti kaynaklarını lisanslarıyla doğrula.
* [x] Model geliştirme ilk odağı belirlendi.
* [ ] Araç tespiti için Colab deney planı oluştur.
* [ ] YOLO/RT-DETR adayları için araştırma karşılaştırma tablosu oluştur.
* [x] Public GitHub repo oluştur ve ilk commit’i pushla.

## 10) Bilinen Sorunlar / Teknik Borç / Riskler

* Hız için referans mesafe/kalibrasyon yöntemi halen teknik tasarım kararı gerektiriyor.
* Ground truth hız için literatür/çalışma kaynakları henüz doğrulanmadı.
* Maskeleme yapılmayacağı için veri lisansı ve kişisel veri riski daha yüksek.
* Araç tespiti için model ailesi henüz seçilmedi; araştırma sonrası karar verilecek.
* Colab deney dosyaları henüz oluşturulmadı.
* Public repo olduğu için ileride veri/checkpoint/API key yanlışlıkla commit edilmemeli.

## 11) Notlar ve Tuzaklar (Pitfalls)

* Resmi rapor 3-10 sayfa sınırında; dokümanlardaki uzun açıklamalar rapora özetlenerek aktarılmalı.
* PDR/ÖTR tasarım dilinde, PCR/FTR kanıt ve metrik dilinde yazılmalı.
* “30 FPS” tüm uzman modeller her karede çalışır anlamına gelmemeli.
* Plaka/yüz/veri saklama KVKK riski taşır.
* Eski demo prototipi bu yeni kapsamın ana çıktısı değildir.

### Güncelleme Kaydı

* Son güncelleme: 2026-06-07
