# Demo Senaryosu

## Ana Demo

Bir Android telefon yol kenarında sabit bir açıyla konumlandırılır. Camera ekranında canlı görüntü açılır. Görüntü edge/backend sistemine aktarılır. Edge sistemi araçları tespit eder, hedef aracı seçer, track ID üretir ve mobil ekrana overlay sonucu döndürür.

## Mevcut Demo Kararı

* Demo gerçek yol kenarında yapılacak.
* Kamera sabitlenecek.
* Ana gösterim canlı kamera olacak.
* Kontrollü video yalnız risk azaltma veya ek doğrulama materyali olarak kullanılabilir.

## Normal Olay Akışı

1. Kamera canlı görüntü üretir.
2. Edge bağlantısı kurulur.
3. Araç tespiti çalışır.
4. Araçlara track ID verilir.
5. Hedef araç seçilir.
6. Sahne/görüş koşulu sınıflandırılır.
7. Risk skoru düşükse normal mod devam eder.

## Kritik Olay Akışı

1. Hedef araç kararlı takip edilir.
2. Şerit yakınlığı, ani yanal hareket, plaka okunabilirliği düşüşü veya hız şüphesi oluşur.
3. Risk skoru eşik değerini aşar.
4. Kritik mod açılır.
5. Plaka OCR, hız, şerit veya cabin risk uzmanları çağrılır.
6. QoD adaylığı değerlendirilir.
7. Event JSON ve evidence package üretilir.
8. Evidence ekranında olay kartı oluşur.

## Offline Alternatif

Canlı demo teknik olarak riskliyse kontrollü video dosyasıyla aynı pipeline çalıştırılabilir. Rapor dili:

> Canlı sistem mimarisi korunmuş, doğrulama kontrollü video akışı üzerinde yapılmıştır.

## Sorulacak Noktalar

* Sabitleme için tripod, araç içi/kenarı aparat veya başka bir düzenek mi kullanılacak?
* Canlı yol kenarı demosunda güvenlik ve izin süreci nasıl yönetilecek?
