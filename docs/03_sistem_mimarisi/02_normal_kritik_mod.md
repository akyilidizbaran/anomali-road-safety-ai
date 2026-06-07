# Normal Mod ve Kritik Mod

## Neden Gerekli?

Proje çok görevli olduğu için tüm modellerin her karede çalıştırılması gerçekçi değildir. Normal/kritik mod ayrımı kaynak kullanımını azaltır, gecikmeyi kontrol eder ve önemli olaylarda daha güçlü analiz yapılmasını sağlar.

## Normal Mod

Sürekli çalışan hafif analiz hattıdır.

Çalışabilecek bileşenler:

* Araç tespiti.
* Araç takibi.
* Hedef araç seçimi.
* Temel araç tipi.
* Sahne/görüş koşulu.
* Görüntü kalitesi.
* Risk ön sinyali.

Normal modun amacı tüm detayları çıkarmak değil, hangi olayın kritikleşebileceğini anlamaktır.

## Kritik Mod

Risk sinyali oluştuğunda devreye girer.

Tetikleyiciler:

* Track stability yüksek.
* Plaka okunabilir veya plaka kritik ama bulanık.
* Araç şerit çizgisine yaklaşıyor.
* Ani yanal hareket var.
* Hız aykırılığı var.
* Görüş düşük.
* OCR güveni düşük.
* Cabin risk görünürlüğü yeterli.

Kritik modda çağrılabilecek uzmanlar:

* Plate detector.
* OCR.
* Lane detection.
* Speed estimation.
* Cabin risk analysis.
* QoD decision module.
* Evidence quality selector.

## Risk

Kritik mod çok sık açılırsa sistem yavaşlar. Bu nedenle threshold ve hysteresis mantığı gerekir.
