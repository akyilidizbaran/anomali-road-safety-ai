# 1. Proje Özeti

## Resmi Beklenti

Proje kapsamında yürütülecek faaliyetler hakkında kısa, net ve bütünlüklü özet verilmelidir.

## Bu Projedeki Karşılık

Anomali Road Safety AI; kullanıcı adı/şifre ve Number Verification doğrulaması sonrası mobil cihaz kamerasından alınan canlı yol görüntüsünü edge destekli çok görevli yapay zeka analiz hattına aktararak ortam/sahne koşulu, araç, plaka, hız, şerit, sürücü/yolcu, araç dışı kullanıcı/yaya durumu ve genel yol-hava koşullarını birlikte değerlendiren bir karar destek sistemi olarak anlatılmalıdır.

## Raporda Yer Alması Gereken Noktalar

* Mobil uygulama görüntünün kaynağı ve kullanıcı arayüzüdür.
* Kullanıcı sisteme Number Verification doğrulaması sonrası alınır.
* Edge/backend sistemi ağır yapay zeka çıkarımını yürütür.
* Normal mod önce ortam/sahne bağlamını üretir, ardından detection/tracking hattı çalışır.
* Kritik mod yalnız riskli olay penceresinde ilgili uzman modelleri çağırır.
* Riskli araçta QoD aday/request akışı tetiklenir; aktiflik seçici kararla belirlenir.
* QoD seçici kullanılır; her olayda otomatik aktif olmaz.
* Evidence sistemi kritik olayları denetlenebilir kayıt paketlerine dönüştürür.

## Örnek Paragraf

> Bu proje, Number Verification doğrulaması sonrası telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka çıkarım hattında analiz ederek ortam/sahne koşulu, araç, plaka, hız, şerit, araç dışı kullanıcı/yaya ve yol-hava koşulu sinyallerini birlikte değerlendiren mobil tabanlı bir akıllı yol güvenliği karar destek sistemi olarak tasarlanmıştır. Sistem normal modda önce ortam bağlamını üretir, ardından hafif araç tespiti ve takip yaparak hedef aracı belirler; riskli araç sinyali oluştuğunda QoD aday/request akışını tetikleyip kritik moda geçerek plaka OCR, hız kestirimi, şerit analizi, araç dışı kullanıcı yakınlığı ve koşullu araç içi risk gibi uzman modelleri seçici şekilde çalıştırır. Her kritik olay görüntü kesiti, model çıktıları, güven skorları, QoD durumu ve model versiyonlarını içeren kanıt paketine dönüştürülür.

## Sorulacak Noktalar

* Resmi takım adı, takım ID ve başvuru ID nedir?
* Rapor özetinde “Anomali Road Safety AI” proje adı kesin kullanılacak mı?
