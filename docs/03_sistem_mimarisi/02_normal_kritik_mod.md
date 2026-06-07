# Normal Mod ve Kritik Mod

## Neden Gerekli?

Proje çok görevli olduğu için tüm modellerin her karede çalıştırılması gerçekçi değildir. Normal/kritik mod ayrımı kaynak kullanımını azaltır, gecikmeyi kontrol eder ve önemli olaylarda daha güçlü analiz yapılmasını sağlar.

## Normal Mod

Sürekli çalışan hafif analiz hattıdır.

Çalışabilecek bileşenler:

* Ortam/sahne analizi.
* Hava, ışık ve görüş koşulu.
* Genel yol durumu.
* Araç dışı kullanıcı/yaya durumu.
* Araç tespiti.
* Araç takibi.
* Hedef araç seçimi.
* Temel araç tipi.
* Görüntü kalitesi.
* Risk ön sinyali.

Normal modda ilk bağlam sinyali ortam analizidir. Hava, ışık, görüş ve yol koşulu detection/tracking çıktılarının nasıl yorumlanacağını belirler. Normal modun amacı tüm detayları çıkarmak değil, hangi aracın veya yol olayının kritikleşebileceğini anlamaktır.

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
* Riskli araç, yaya/bisikletli veya yol kenarındaki araç dışı kullanıcıya yakın.

Kritik modda çağrılabilecek uzmanlar:

* Plate detector.
* OCR.
* Lane detection.
* Speed estimation.
* Road/external user risk analysis.
* Cabin risk analysis.
* QoD decision module.
* Evidence quality selector.

## Risk

Kritik mod çok sık açılırsa sistem yavaşlar. Bu nedenle threshold ve hysteresis mantığı gerekir.
