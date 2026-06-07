# 3.1 Problemin Analizi

## Resmi Beklenti

Video üzerinden araç, plaka, hız veya riskli durum tespiti yaparken karşılaşılan temel problemler ve seçilen çözüm yolunun gerekçesi açıklanmalıdır.

## Problem Alanları

### Işık ve Hava

Gece, düşük ışık, yağmur, sis, gölge ve far parlaması tespit ve OCR güvenini düşürür. Çözüm olarak sahne/koşul sınıflandırması ve QoD adaylığı kullanılır.

### Hareket Bulanıklığı

Araç hızı veya kamera sarsıntısı plaka ve küçük nesne tespitini zorlaştırır. Çözüm olarak temporal voting ve evidence quality score kullanılır.

### Oklüzyon

Araçların birbirini kapatması track ID kararlılığını bozar. Çözüm olarak tracking-by-detection ve track stability metriği kullanılır.

### Küçük Nesneler

Plaka, telefon, sigara ve kemer küçük nesnelerdir. Çözüm olarak ROI crop ve kritik mod uzman modeli kullanılır.

### Hız Kalibrasyonu

Tek kamera ile gerçek km/s ölçümü sabit kamera ve referans mesafe ister. Çözüm olarak kalibrasyon varsa homografi, yoksa göreli hız/risk skoru kullanılır.

### Sürücü Görünürlüğü

Dış kameradan sürücü/yolcu her zaman görünmez. Çözüm olarak görünürlük skoru ve analiz yapmama politikası kullanılır.

## Tercih Edilen Çözüm

Modüler, seçici uzman model mimarisi seçilmiştir. Bu yaklaşım hem gerçek zamanlılığı korur hem de her görev için uygun veri, model ve metrik tanımlanmasına izin verir.
