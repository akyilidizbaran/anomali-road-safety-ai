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

## FTR Submission Acceptance

* Root seviyesinde `Dockerfile` bulunur.
* Docker container otomatik olarak inference başlatır.
* Program `/app/data/input/video.mp4` yolundan okur.
* Program `/app/data/output/results.json` yoluna yazar.
* JSON `architecture/contracts/ftr_results_output_contract.md` ile uyumludur.
* Tüm kategori/etiket değerleri ASCII-safe, küçük harfli ve resmi FTR listesiyle birebir aynıdır.
* `arac_bilgisi` içinde `tip`, `plaka`, `renk`, `confidence_score` bulunur.
* `tespitler[]` elemanlarında `zaman_saniye`, `kategori`, `etiket`, `confidence_score` bulunur.
* Runtime internet erişimine bağlı değildir.
* Tesla T4 ve 10 dakika runtime limiti altında smoke test planı bulunur.
