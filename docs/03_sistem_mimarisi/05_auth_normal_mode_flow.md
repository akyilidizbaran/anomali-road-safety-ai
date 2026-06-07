# Auth, Normal Mod ve QoD Tetikleme Akışı

## Ana Akış

Bu dosya, PDF’teki ana istekle uyumlu nihai çalışma sırasını netleştirir.

1. Kullanıcı kullanıcı adı ve şifreyle giriş yapar.
2. Number Verification API’ye request gönderilir.
3. Kullanıcı/cihaz/oturum eşleşirse sistem açılır.
4. Kamera canlı görüntü üretir.
5. Normal mod başlar.
6. Normal modda ilk erken sinyal olarak ortam/sahne analizi çalışır.
7. Ardından normal detection ve takip hattı çalışır.
8. Riskli araç veya riskli yol olayı sinyali oluşursa kritik mod adayı üretilir.
9. QoD karar/tetikleme akışı başlar.
10. QoD aktif olduğunda riskli araç özelinde video kalitesi artırılır.
11. Daha detaylı çıkarım için ilgili uzman modeller çağrılır.
12. Sonuç event JSON ve evidence package olarak kaydedilir.

## Normal Modda Ortam Analizi

Normal modun ilk sinyal katmanı ortam analizidir. Amaç, detection başlamadan veya detection ile paralel şekilde görüntü koşulunu anlamaktır.

Ortam analizi çıktıları:

* Hava durumu.
* Işık durumu.
* Görüş kalitesi.
* Yağmur/sis/düşük ışık gibi belirsizlik artıran koşullar.
* Yol yüzeyi ve genel yol durumu için erken sinyal.

Bu çıktı detection, OCR, lane, hız ve QoD kararlarının yorumlanmasına bağlamsal sinyal sağlar.

## Riskli Araç Tespitinde QoD

Riskli araç tespit edildiğinde sistem QoD karar akışını tetikler. Burada “tetikleme”, QoD’nin mutlaka her olayda aktif olacağı anlamına gelmez; QoD request/candidate akışı başlar ve politika şu soruyu cevaplar:

> QoD bu olayda karar güvenini veya kanıt kalitesini anlamlı şekilde artırır mı?

Eğer cevap evetse QoD aktif edilir ve ilgili araç özelinde daha yüksek kaliteli video/kare alınarak detaylı çıkarım yapılır.

## Araç Özelinde Detaylı Çıkarım

QoD ve kritik mod penceresinde çağrılabilecek uzmanlar:

* Plaka tespiti ve OCR.
* Hız kestirimi.
* Şerit/road marking analizi.
* Araç dışı kullanıcı/yaya durumu.
* Cabin risk, görünürlük yeterliyse.
* Evidence quality selector.

## Genel Yol ve Araç Dışı Kullanıcı Durumu

Sistem yalnız hedef aracı değil, genel yol bağlamını da raporlamalıdır:

* Yol yüzeyi ve görüş durumu.
* Şerit/road marking görünürlüğü.
* Araç dışı kullanıcı/yaya varlığı.
* Yol kenarı veya çevre insanları.
* Araç dışı kullanıcıların riskli araca yakınlığı.

Bu bilgiler risk skoruna ve event explanation katmanına bağlamsal katkı sağlar.
