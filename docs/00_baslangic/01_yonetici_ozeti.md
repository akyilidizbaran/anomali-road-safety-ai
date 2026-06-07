# Yönetici Özeti

**Anomali Road Safety AI**, Android telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka çıkarım hattına aktararak araç, plaka, hız, şerit, sürücü/yolcu, yol-hava koşulu ve çevre insanlarını birlikte değerlendiren mobil tabanlı bir akıllı yol güvenliği karar destek sistemidir.

Sistem normal modda sürekli çalışan hafif analiz hattı ile araç tespiti, araç takibi, hedef araç seçimi ve temel sahne/koşul analizi yapar. Risk sinyali oluştuğunda kritik moda geçer ve yalnız ilgili uzman modelleri çağırır. Bu uzman modeller plaka/OCR, hız kestirimi, şerit analizi, sürücü/yolcu veya araç içi risk gibi görevleri olay bazlı yürütür.

Her kritik olay yalnız ekranda uyarı olarak kalmaz. Sistem, olay için görüntü kesiti, overlay screenshot, event ID, timestamp, track ID, bbox koordinatları, model versiyonları, güven skorları, risk seviyesi, QoD durumu ve karar gerekçesini içeren **denetlenebilir kanıt paketi** üretir.

QoD her riskli olayda otomatik açılmaz. Yalnız karar güvenini veya kanıt kalitesini artıracağı değerlendirilen durumlarda kısa süreli aday/aktif hale getirilir. Number Verification ve QoD servisleri API key gelene kadar mock/stub adapter olarak tasarlanır; gerçek servis geldiğinde ana yapay zeka pipeline bozulmadan entegre edilir.

Proje raporlarında sistem “kesin ceza kesen” veya “hukuki karar veren” yapı olarak değil; erken uyarı, risk sınıflandırma, karar destek ve kanıt üretim sistemi olarak anlatılmalıdır.
