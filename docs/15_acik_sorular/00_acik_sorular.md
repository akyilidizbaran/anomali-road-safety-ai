# Açık Sorular ve Cevaplanan Kararlar

Bu dosya, proje için sorulan karar noktalarını ve verilen cevapları merkezi olarak tutar.

## Cevaplandı - Resmi Bilgiler

* Takım adı, takım ID ve başvuru ID bu aşamada boş bırakılacak.
* Takım rol dağılımı rapor yazımı aşamasında anonim şekilde doldurulacak.

## Cevaplandı - Demo

* Demo alanı gerçek yol kenarı olacak.
* Kamera sabitlenecek.
* Demo canlı kamera üzerinden yapılacak.
* Kamera açısı normal bir insanın göğüs yüksekliğine yakın seviyeden dışarı/yol yönüne bakacak şekilde tasarlanacak.
* Ağır model çıkarımı için edge çalışma ortamı MacBook olacak; telefon kamera/istemci rolünde kalacak.
* Kontrollü video yalnız risk azaltma veya offline doğrulama alternatifi olarak kalabilir.

## Cevaplandı - Hız

* Hedef mutlak km/s tahmini yapmak.
* Bu başarılamazsa göreli hız/risk sınıflandırmasına düşülecek.
* Ground truth hız için doğrudan yerel ölçüm yerine literatürdeki/internette yayımlanmış çalışmalardan yöntem ve değerlendirme fikri türetilecek.
* Referans mesafe için tam otomatik tek kamera ölçümü güvenilir kabul edilmeyecek. Tasarım yönü: yarı otomatik kalibrasyon, sahaya konulan referans marker/mesafe, kullanıcı tarafından seçilen referans noktaları veya yol/lane genişliği gibi bilinen ölçek varsayımları.
* Hız kalibrasyonu MVP değil, final scope denemesi olarak tutulacak.
* MVP aşamasında hız çıktısı mutlak km/s iddiası yerine relative speed / motion anomaly sinyali olarak kalabilir.

## Cevaplandı - Cabin Risk

* Kontrollü sürücü/yolcu videosu çekilecek.
* Sürücü/yolcu/cabin risk final genişletme gibi tasarlanacak.
* Ana MVP araç, takip, plaka/OCR, hız/şerit/evidence hattına odaklanacak.

## Cevaplandı - LLM

* LLM API ile bağlanabilir.
* Alternatif olarak bilgisayar üzerinde çalışan local LLM, domain/sunucu üzerinden servis edilebilir.
* Fallback durumunda sabit/template açıklama metinleri kullanılabilir.
* LLM karar verici değil, event JSON açıklama katmanı olarak kalacak.

## Cevaplandı - 5G/QoD

* API keyler model geliştirmesi tamamlanmadan sağlanacak varsayımıyla ilerlenir.
* QoD sağlandığında gerçek video kalitesi artırılacak.
* Riskli araç tespit edildiğinde QoD aday/request akışı tetiklenecek.
* QoD yine her riskte otomatik açılmayacak; kalite/güven artışı beklenen durumda seçici kullanılacak.
* QoD için hedef gerçek API/adapter entegrasyonudur; API erişimi gelene kadar mock/status-policy fallback korunur.

## Cevaplandı - Auth ve Normal Mod Akışı

* Kullanıcı sisteme kullanıcı adı ve şifreyle giriş yapacak.
* Başarılı credential kontrolünden sonra Number Verification API’ye request gidecek.
* Kullanıcı/cihaz/oturum eşleşirse canlı analiz ekranlarına erişim verilecek.
* Normal modda ilk bağlam katmanı ortam/sahne analizi olacak; hava, ışık, görüş ve yol koşulu detection/tracking yorumunu etkileyecek.
* Normal detection ve tracking ortam analizinden sonra veya onunla paralel çalışacak.
* Ortam analizi detection/tracking hattını bloklamayacak; düşük frekansta bağlam sinyali üreten context-gated routing katmanı olarak çalışacak.
* Normal modda tüm araçlar hafif takip edilecek, ağır uzman modeller yalnız riskli/hedef araç üzerinde çalışacak.

## Cevaplandı - Genel Yol ve Araç Dışı Kullanıcı

* Sistem yalnız hedef aracı değil, genel yol durumunu da raporlayacak.
* Araç dışı kullanıcı/yaya durumu bağlamsal risk sinyali olarak tutulacak.
* İlk yaklaşım public/pretrained object detection modellerindeki person/bicycle/motorcycle sınıflarından yararlanmak olacak.
* Riskli araca yakınlık, düşük görüş ve yol kenarı aktivitesi risk açıklamasına bağlanacak.

## Cevaplandı - Veri

* Kullanılacak veri setleri yapılacak literatür/uygulama çalışmalarından saptanacak.
* Testler öncelikle internet üzerindeki açık veri setleri, makale ekleri veya açık kaynak çalışma verileri üzerinden yürütülecek.
* Veri seti lisansları ilgili makale, proje sayfası veya açık kaynak veri seti kartından doğrulanacak.
* Yerel veri mümkünse toplanmayacak.
* Maskeleme yapılmayacak.
* KVKK/etik riskleri raporda açıkça tartışılmalı; maskeleme yapılmayacaksa veri kaynağı ve kullanım izni daha kritik hale gelir.

## Cevaplandı - Model Geliştirme ve Çalışma Ortamı

* İlk model geliştirme odağı: Araç tespiti.
* Sıralama: Araç tespiti tamamlandıktan sonra diğer modüller faz sırasıyla eklenecek.
* Eğitim/fine-tune/deney ortamı: Google Colab GPU.
* Çalışan demo/inference ortamı: MacBook edge runtime.
* Giriş frame hedefi: 720p frame alınır, model input boyutuna resize edilir.
* Başlangıç model ailesi: Araştırma sonrası seçilecek.
* Başarı metriği: Tek bir metrik değil; doğruluk, hız, gecikme, model boyutu ve event/evidence katkısını birlikte değerlendiren dengeli metrik paketi.
* Test ortamı: Test verisinin gerçekleştirildiği ortam izole olacak.
* Yerel veri: Mümkünse toplanmayacak.
* Maskeleme: Yapılmayacak; bu nedenle izole test ortamı, veri erişim sınırları ve kaynak/lisans doğrulaması kritik kalır.
* Türk plaka format doğrulaması için başlangıç yaklaşımı: açık kaynak/literatür çalışmalarına uygun regex, il kodu kontrolü, OCR post-processing ve temporal voting birleşimi.
* Şerit/road marking modülü plate/evidence hattından sonra ele alınacak.

## Bu Aşamada Kalan Engelleyici Soru

* Yok. Mevcut bilgilerle model geliştirme yol haritası ve PDR/ÖTR rapor taslağı hazırlanabilir.
