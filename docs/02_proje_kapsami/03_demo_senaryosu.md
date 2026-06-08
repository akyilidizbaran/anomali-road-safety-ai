# Demo Senaryosu

## Ana Demo

Bir Android telefon yol kenarında sabit bir açıyla konumlandırılır. Kullanıcı kullanıcı adı/şifreyle giriş yapar, Number Verification eşleşmesi başarılıysa Camera ekranında canlı görüntü açılır. Görüntü edge/backend sistemine aktarılır. Edge sistemi önce ortam/sahne koşullarını değerlendirir, ardından araçları tespit eder, hedef aracı seçer, track ID üretir ve mobil ekrana overlay sonucu döndürür.

Demo çıkarım ortamı MacBook üzerinde çalışan local edge/backend olarak planlanır. Telefon canlı kamera ve kullanıcı arayüzü rolündedir; ağır model çıkarımı MacBook tarafında çalışır. Eğitim/fine-tune çalışmaları ise demo makinesinde değil, Google Colab GPU ortamında yürütülür.

## Mevcut Demo Kararı

* Demo gerçek yol kenarında yapılacak.
* Kamera sabitlenecek.
* Kamera normal bir insanın göğüs yüksekliğine yakın seviyeden dışarı/yol yönüne bakacak.
* Ana gösterim canlı kamera olacak.
* Canlı frame hedefi 720p seviyesinde alınacak ve model input boyutuna resize edilecek.
* Kontrollü video yalnız risk azaltma veya ek doğrulama materyali olarak kullanılabilir.
* MVP ve ana yarışma demosunda sistem single-target mode ile çalışır.
* Sistem görüntüdeki en önemli/hedef aracı seçer ve ağır uzman modelleri öncelikle bu hedef araç üzerinde çalıştırır.
* Multi-target mode, settings üzerinden açılabilen deneysel genişletme modudur.

## Normal Olay Akışı

1. Kamera canlı görüntü üretir.
2. Edge bağlantısı kurulur.
3. Ortam, hava, ışık ve görüş koşulu sınıflandırılır.
4. Genel yol durumu ve araç dışı kullanıcı/yaya sinyali çıkarılır.
5. Araç tespiti çalışır.
6. Araçlara track ID verilir.
7. Hedef araç seçilir.
8. Risk skoru düşükse normal mod devam eder.

## Kritik Olay Akışı

1. Hedef araç kararlı takip edilir.
2. Şerit yakınlığı, ani yanal hareket, plaka okunabilirliği düşüşü veya hız şüphesi oluşur.
3. Risk skoru eşik değerini aşar.
4. Kritik mod açılır.
5. Plaka OCR, hız, şerit veya cabin risk uzmanları çağrılır.
6. Riskli araç özelinde QoD aday/request akışı tetiklenir.
7. QoD karar güveni veya kanıt kalitesini artıracaksa kısa süreli aktif edilir.
8. Event JSON ve evidence package üretilir.
9. Evidence ekranında olay kartı oluşur.

## Offline Alternatif

Canlı demo teknik olarak riskliyse kontrollü video dosyasıyla aynı pipeline çalıştırılabilir. Rapor dili:

> Canlı sistem mimarisi korunmuş, doğrulama kontrollü video akışı üzerinde yapılmıştır.

## Sorulacak Noktalar

* Canlı yol kenarı demosunda güvenlik ve izin süreci nasıl yönetilecek?
