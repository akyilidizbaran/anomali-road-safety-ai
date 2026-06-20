# Yapay Zeka Omurgası

## Temel Karar

Proje tek bir modelle değil, görev bazlı uzman modellerle ilerlemelidir. Çünkü araç tespiti, plaka OCR, şerit, hız, hava/görüş ve cabin risk birbirinden farklı veri, model ve metrik ister.

Runtime hattın detaylı uçtan uca açıklaması için `docs/04_yapay_zeka/10_runtime_ai_pipeline_mimarisi.md` ana referans kabul edilir.

## FTR Teslim Önceliği

2026-06-13 tarihli FTR teslim dokümanına göre otomatik değerlendirme için ana çıktı
`/app/data/output/results.json` dosyasıdır. Bu dosya proje içi zengin event/evidence JSON'u
değil, yarışma formatındaki konsolide sonuç dosyasıdır.

Bu nedenle AI omurgasının FTR önceliği şudur:

1. Tek ana araç için `arac_bilgisi.tip`.
2. Tek ana araç için `arac_bilgisi.plaka`.
3. Tek ana araç için `arac_bilgisi.renk`.
4. Ortak `arac_bilgisi.confidence_score`.
5. Zaman bazlı `tespitler[]`: `sofor_eylemi`, `nesneler`, `yolcular`.

Detaylı output contract: `architecture/contracts/ftr_results_output_contract.md`.

## Model Geliştirme Önceliği

İlk model geliştirme odağı araç tespiti olarak başlamıştır. FTR dokümanı sonrası sıradaki
öncelik, mevcut araç/plaka omurgasını FTR `results.json` contract'ına bağlamak ve eksik
FTR alanlarını tamamlamaktır: araç rengi, FTR araç tipi mapping, sürücü eylemleri,
nesneler ve yolcu konumları.

Eğitim ve deney ortamı Google Colab olacak. Başlangıç model ailesi araştırma sonrası seçilecek. Başarı, tek bir metrikle değil doğruluk, hız, latency, model boyutu ve sistem entegrasyonunu birlikte değerlendiren dengeli metrik paketiyle ölçülecektir.

Eğitimin ana yükü sıfırdan model eğitmek değildir. İnternet üzerinden elde edilen public/pretrained modeller kullanılacak; gerektiğinde fine-tune, veri işleme, post-processing ve proje hedeflerine göre output uyarlaması yapılacaktır.

## Pipeline

1. Video input read: `/app/data/input/video.mp4`.
2. Frame preprocessing and sampling.
3. Vehicle detection.
4. Tracking and single main vehicle selection.
5. Vehicle info experts: type, plate/OCR, color.
6. Timed detection experts: driver action, object, passenger.
7. Internal event/evidence fusion if needed.
8. FTR output adapter.
9. `results.json` write: `/app/data/output/results.json`.

QoD, Number Verification, dashboard ve rich evidence katmanları geniş proje mimarisinde
korunur; fakat FTR otomatik değerlendirmesinde zorunlu alan değildir.

Detaylı routing politikası için `docs/04_yapay_zeka/11_context_gated_model_routing.md` kullanılmalıdır.

Model output contractları için `architecture/contracts/model_output_contract.md` kullanılmalıdır.

## Neden Rule-Based Başlangıç Kabul Edilebilir?

Risk skoru ve uzman model seçimi başlangıçta rule-based olabilir. Bunun avantajları:

* Açıklanabilir.
* Debug etmesi kolaydır.
* Rapor anlatısı nettir.
* Yanlış alarm kaynakları daha kolay bulunur.

Daha sonra öğrenilebilir risk modeli geliştirilebilir.

## Uzman Model Frekansları

| Modül | Frekans |
|---|---|
| Kamera preview | 30 FPS hedef |
| Vehicle detection | 15-30 FPS |
| Tracking | Her frame veya yüksek frekans |
| Context/scene routing | 1-2 Hz veya olay penceresi |
| OCR | Her 5-10 frame veya plaka netleşince |
| Scene analysis | 1-2 Hz |
| Lane | 10-15 FPS veya risk penceresi |
| Cabin risk | Kritik ROI varsa |
| Evidence | Olay bazlı |
| FTR output adapter | Video sonunda |
