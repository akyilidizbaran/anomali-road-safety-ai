# 5. Özgünlük

## Resmi Beklenti

Mevcut piyasa çözümleri ve literatüre kıyasla tasarımın yenilikçi tarafı açıklanmalıdır. Mimari verimlilik ve gelecek ürün fikirleri de değerlendirilebilir.

## Özgünlük Noktaları

### Seçici Uzman Model Mimarisi

Sistem tüm modelleri her karede çalıştırmaz. Normal mod hafif analiz üretir; kritik mod yalnız ilgili uzmanları çağırır. Bu yaklaşım gerçek zamanlılık ve doğruluk arasında kontrollü denge kurar.

### QoD’nin Seçici Kullanımı

QoD her olayda otomatik açılmaz. Yalnız karar güveni veya kanıt kalitesi artacaksa kısa süreli kullanılır. Bu, ağ kaynağının gereksiz tüketilmesini engeller.

### Denetlenebilir Evidence Package

Sistem sadece alarm üretmez. Olayı event ID, timestamp, bbox, confidence, model version, QoD status, risk gerekçesi ve görsel kesitle birlikte kayıt altına alır.

### LLM’in Sınırlandırılmış Rolü

LLM karar verici değildir. Model pipeline çıktısını insan tarafından anlaşılır açıklama metnine dönüştüren yardımcı katmandır.

### Kalibrasyon Duyarlı Hız

Kalibrasyon varsa gerçek km/s; yoksa göreli hız/risk skoru sunulur. Böylece yanlış kesinlik iddiası azaltılır.

## Gelecek Ürün Fikirleri

* Yol kenarı geçici denetim cihazı.
* Belediye trafik güvenliği paneli.
* Filo güvenliği karar destek sistemi.
* Akıllı kavşak edge modülü.
* Olay bazlı veri toplama ve model geliştirme sistemi.
