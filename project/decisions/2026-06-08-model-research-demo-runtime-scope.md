# Model Research, Demo Runtime and Scope Boundaries

Tarih: 2026-06-08

Karar:

* Model egitimi ve fine-tune deneyleri Google Colab GPU ortaminda yurutulecek.
* Canli demo/inference runtime MacBook uzerinde calisan local edge/backend olacak.
* Android cihaz ilk asamada kamera ve mobil UI istemcisi olarak konumlanacak.
* Canli input hedefi 720p frame/stream olacak; modeller preprocessing asamasinda kendi input boyutuna resize edilecek.
* Demo kamera acisi normal bir insanin gogus yuksekligine yakin seviyeden disari/yol yonune bakacak sekilde tasarlanacak.
* Testler oncelikle internet uzerindeki acik veri setleri, makale/proje ekleri ve acik kaynak benchmark materyalleriyle yurutulecek.
* Veri seti lisanslari makale, proje sayfasi, dataset card veya acik kaynak lisans metniyle dogrulanacak.
* Turk plaka format dogrulamasi icin ilk yaklasim regex + il kodu kontrolu + OCR post-processing + temporal voting olacak.
* Hiz kalibrasyon denemesi final scope'ta tutulacak; MVP'de relative speed / motion anomaly sinyali yeterli kabul edilecek.
* Serit/road marking modulu plate/OCR ve evidence hatti kurulduktan sonra ele alinacak.
* QoD icin hedef gercek API/adapter entegrasyonudur; API erisimi gecikirse mock/status-policy fallback korunur.

Gerekce:

Bu kararlar, sistemin ilk asamada gercekci bir uc-tan-uca model gelistirme ve demo rotasina sahip olmasini saglar. Colab GPU model arastirmasi icin uygundur, MacBook ise saha demosunda edge inference rolunu pratik sekilde ustlenir. 720p kaynak frame ve resize ayrimi benchmark tekrar edilebilirligini artirir. Hiz, lane ve QoD gibi riskli kapsamlar kosullu/fazli ilerletilerek proje fazla iddiali gosterilmez.

Etkilenen Alanlar:

* `README.md`
* `ROADMAP.md`
* `STATUS.md`
* `docs/02_proje_kapsami/03_demo_senaryosu.md`
* `docs/04_yapay_zeka/08_model_gelistirme_yol_haritasi.md`
* `docs/04_yapay_zeka/09_pretrained_finetune_stratejisi.md`
* `docs/04_yapay_zeka/10_runtime_ai_pipeline_mimarisi.md`
* `docs/04_yapay_zeka/12_mvp_final_future_scope.md`
* `docs/05_veri_seti/00_veri_stratejisi.md`
* `docs/07_edge_backend/00_edge_backend_mimarisi.md`
* `docs/08_5g_qod/00_5g_qod_omurga.md`
* `docs/15_acik_sorular/00_acik_sorular.md`
* `research/`
* `data/DATA_POLICY.md`

Alternatifler:

* Android cihazda dogrudan agir inference calistirmak.
* Tum egitim ve inference islerini Colab uzerinde gostermek.
* Hiz kalibrasyonunu MVP sarti yapmak.
* Lane modelini plate/evidence hattindan once gelistirmek.
* QoD'yi yalniz mock gosterge olarak birakmak.

Geri Donus Plani:

MacBook runtime yeterli olmazsa inference server daha guclu bir local workstation veya cloud edge ortaminda calistirilabilir. Android on-device inference ihtiyaci dogarsa export ve quantization arastirmasi tekrar onceliklendirilir. Hiz kalibrasyonu yetismese relative speed fallback korunur.

Durum: Accepted
