# Yönetici Özeti

**Anomali Road Safety AI**, kullanıcı adı/şifre ve Number Verification doğrulaması sonrası Android telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka çıkarım hattına aktararak ortam/sahne koşulu, araç, plaka, hız, şerit, sürücü/yolcu, genel yol durumu ve araç dışı kullanıcı/yaya durumunu birlikte değerlendiren mobil tabanlı bir akıllı yol güvenliği karar destek sistemidir.

Sistem normal modda önce ortam, hava, ışık ve görüş bağlamını üretir; ardından araç tespiti, araç takibi, hedef araç seçimi, genel yol durumu ve araç dışı kullanıcı/yaya sinyallerini izler. Riskli araç sinyali oluştuğunda QoD aday/request akışı tetiklenir, kritik moda geçilir ve yalnız ilgili uzman modeller çağırılır. Bu uzman modeller plaka/OCR, hız kestirimi, şerit analizi, araç dışı kullanıcı yakınlığı, sürücü/yolcu veya araç içi risk gibi görevleri olay bazlı yürütür.

Her kritik olay yalnız ekranda uyarı olarak kalmaz. Sistem, olay için görüntü kesiti, overlay screenshot, event ID, timestamp, track ID, bbox koordinatları, model versiyonları, güven skorları, risk seviyesi, QoD durumu ve karar gerekçesini içeren **denetlenebilir kanıt paketi** üretir.

QoD her riskli olayda otomatik açılmaz. Yalnız karar güvenini veya kanıt kalitesini artıracağı değerlendirilen durumlarda kısa süreli aday/aktif hale getirilir. Number Verification ve QoD servisleri API key gelene kadar mock/stub adapter olarak tasarlanır; gerçek servis geldiğinde ana yapay zeka pipeline bozulmadan entegre edilir.

Proje raporlarında sistem “kesin ceza kesen” veya “hukuki karar veren” yapı olarak değil; erken uyarı, risk sınıflandırma, karar destek ve kanıt üretim sistemi olarak anlatılmalıdır.
