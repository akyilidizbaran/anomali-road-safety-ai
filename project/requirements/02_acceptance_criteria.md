# Acceptance Criteria

## MVP Acceptance

* Login sonrası Number Verification mock/real adapter durumu görülebilir.
* Camera screen canlı preview ve overlay durumlarını temsil eder.
* Vehicle detection çıktısı bbox, class ve confidence içerir.
* Target vehicle seçimi track ID ile temsil edilir.
* Riskli araç durumunda QoD status `CANDIDATE` veya `REQUESTED` olabilir.
* Event JSON `architecture/contracts/event.schema.json` ile uyumlu üretilir.
* Evidence card event ID ve decision reason gösterir.

## Report Acceptance

* Kullanılan veri setleri lisans checklist ile izlenir.
* Model seçimi benchmark tablosuyla gerekçelendirilir.
* Hız için kalibrasyon yoksa göreli hız/risk sınıfı fallback olarak yazılır.
