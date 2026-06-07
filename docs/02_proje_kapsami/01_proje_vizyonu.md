# Proje Vizyonu

Anomali Road Safety AI, kullanıcı adı/şifre ve Number Verification doğrulaması sonrası telefon kamerasını geçici veya sabit bir yol güvenliği gözlem cihazı gibi kullanarak canlı yol görüntüsünü edge destekli yapay zeka hattına aktarır. Sistem görüntüden ortam/sahne koşulu, araç, plaka, hız, şerit davranışı, genel yol durumu, araç dışı kullanıcı/yaya durumu ve mümkün olduğunda sürücü/yolcu risk sinyallerini çıkarır.

Projenin ana değeri tek bir modelin çıktısı değildir. Değer, mobil uygulamadan edge inference sistemine, 5G/QoD kararından evidence storage yapısına kadar uzanan uçtan uca karar zinciridir.

## Temel Amaç

* Riskli yol güvenliği olaylarını gerçek zamanlı veya gerçek zamana yakın tespit etmek.
* Kritik olayları açıklanabilir risk gerekçesiyle sınıflandırmak.
* Her kritik olayı görsel ve metadata destekli kanıt paketine dönüştürmek.
* 5G/QoD kaynaklarını yalnız gerekli olduğunda seçici kullanmak.
* Mobil arayüzde canlı overlay, evidence ve sistem sağlığı göstermek.
* Kullanıcı/cihaz/oturum eşleşmesini Number Verification akışıyla doğrulamak.

## Ana Ürün Cümlesi

> Number Verification doğrulaması sonrası telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka pipeline’ında analiz eden, normal/kritik mod ayrımıyla uzman modelleri seçici çalıştıran ve kritik olayları denetlenebilir evidence paketlerine dönüştüren mobil yol güvenliği karar destek sistemi.

## Stratejik Ayrım

Bu proje “tek model + kamera” değildir. Şu alt sistemleri birlikte ele alır:

* Mobil kamera ve kullanıcı arayüzü.
* Login ve Number Verification.
* Video aktarımı.
* Edge/backend inference.
* Ortam, yol ve araç dışı kullanıcı bağlamı.
* Görev bazlı uzman modeller.
* Risk scoring.
* QoD decision.
* Event fusion.
* Evidence store.
* LLM açıklama katmanı.
* Test ve metrik sistemi.

## Kesin Sınır

Sistem hukuki karar vermez. Ceza kesmez. Olasılık, güven skoru ve risk seviyesiyle karar destek sağlar.
