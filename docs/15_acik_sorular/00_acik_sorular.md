# Açık Sorular ve Cevaplanan Kararlar

Bu dosya, proje için sorulan karar noktalarını ve verilen cevapları merkezi olarak tutar.

## Cevaplandı - Resmi Bilgiler

* Takım adı, takım ID ve başvuru ID bu aşamada boş bırakılacak.
* Takım rol dağılımı rapor yazımı aşamasında anonim şekilde doldurulacak.

## Cevaplandı - Demo

* Demo alanı gerçek yol kenarı olacak.
* Kamera sabitlenecek.
* Demo canlı kamera üzerinden yapılacak.
* Kontrollü video yalnız risk azaltma veya offline doğrulama alternatifi olarak kalabilir.

## Cevaplandı - Hız

* Hedef mutlak km/s tahmini yapmak.
* Bu başarılamazsa göreli hız/risk sınıflandırmasına düşülecek.
* Ground truth hız için doğrudan yerel ölçüm yerine literatürdeki/internette yayımlanmış çalışmalardan yöntem ve değerlendirme fikri türetilecek.
* Referans mesafe için tam otomatik tek kamera ölçümü güvenilir kabul edilmeyecek. Tasarım yönü: yarı otomatik kalibrasyon, sahaya konulan referans marker/mesafe, kullanıcı tarafından seçilen referans noktaları veya yol/lane genişliği gibi bilinen ölçek varsayımları.

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
* QoD yine her riskte otomatik açılmayacak; kalite/güven artışı beklenen durumda seçici kullanılacak.

## Cevaplandı - Veri

* Kullanılacak veri setleri yapılacak literatür/uygulama çalışmalarından saptanacak.
* Yerel veri mümkünse toplanmayacak.
* Maskeleme yapılmayacak.
* KVKK/etik riskleri raporda açıkça tartışılmalı; maskeleme yapılmayacaksa veri kaynağı ve kullanım izni daha kritik hale gelir.

## Yeni Sorular - Model Geliştirme İçin Netleştirilmeli

* İlk model geliştirme odağı: Araç tespiti.
* Sıralama: Araç tespiti tamamlandıktan sonra diğer modüller faz sırasıyla eklenecek.
* Eğitim/deney ortamı: Google Colab.
* Başlangıç model ailesi: Araştırma sonrası seçilecek.
* Başarı metriği: Tek bir metrik değil; doğruluk, hız, gecikme, model boyutu ve event/evidence katkısını birlikte değerlendiren dengeli metrik paketi.
* Test ortamı: Test verisinin gerçekleştirildiği ortam izole olacak.
* Yerel veri: Mümkünse toplanmayacak.
* Maskeleme: Yapılmayacak; bu nedenle izole test ortamı, veri erişim sınırları ve kaynak/lisans doğrulaması kritik kalır.

## Bu Aşamada Kalan Engelleyici Soru

* Yok. Mevcut bilgilerle model geliştirme yol haritası ve PDR/ÖTR rapor taslağı hazırlanabilir.
