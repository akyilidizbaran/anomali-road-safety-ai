# 5G, Number Verification ve QoD Omurgası

## Number Verification

Amaç, kullanıcı/cihaz oturum doğrulamasını temsil etmektir. Kullanıcı mobil uygulamada kullanıcı adı ve şifreyle giriş yaptıktan sonra Number Verification API’ye request gönderilir. Kullanıcı/cihaz/oturum eşleşmesi başarılıysa sistem canlı analiz ekranlarına erişim verir; başarısızsa erişim reddedilir.

API key gelene kadar mock verified state kullanılabilir. Ancak mock doğrulama raporda ve demo notlarında açıkça belirtilmelidir.

## QoD

QoD her olayda otomatik açılmaz. Yalnız şu durumlarda aday olmalıdır:

* OCR güveni düşük ama plaka kritik.
* Görüş koşulu düşük.
* Evidence kalitesi yetersiz.
* Hedef araç kısa süre içinde kaybolabilir.
* Model belirsizliği artmış.

## QoD Durumları

* Not Needed.
* Candidate.
* Requested.
* Active.
* Expired.
* Failed.

## Rapor Dili

QoD sistemin çalışması için zorunlu değil, kaliteyi artırabilecek seçici bir ağ kaynağıdır.

## Mevcut Karar

* API keylerin model geliştirmesi tamamlanmadan sağlanacağı varsayımıyla ilerlenir.
* QoD sağlandığında gerçek video kalitesi artırılacak.
* Riskli araç tespit edildiğinde QoD aday/request akışı tetiklenecek.
* QoD buna rağmen her riskte otomatik açılmayacak; karar güveni veya kanıt kalitesini artıracağı durumlarda kısa süreli devreye alınacak.

## Sorulacak Noktalar

* QoD aktif olduğunda artırılacak kalite parametresi ne olacak: bitrate, çözünürlük, FPS veya öncelik?
* QoD oturum süresi için üst sınır kaç saniye olacak?
