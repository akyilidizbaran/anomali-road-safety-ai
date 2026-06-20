# Anomali Road Safety AI

5G ve yapay zeka ile akıllı yol güvenliği için model geliştirme, veri işleme, rapor ve mimari dokümantasyon deposu.

Bu repo, resmi PDR/ÖTR ve PCR/FTR rapor şablonları ile proje kapsam metnine göre sıfırdan kurulmuştur. Önceki demo/prototip çalışmaları bu kapsamın ana çıktısı değildir.

## Current Status

Bu repo şu anda **FTR teslim sözleşmesine hizalanmış model geliştirme ve submission hazırlığı** aşamasındadır.

2026-06-13 tarihli FTR teslim dokümanına göre bundan sonraki ana hedef, tek video girdisini
Docker içinde işleyip resmi formattaki `results.json` çıktısını üretmektir:

```text
/app/data/input/video.mp4 -> /app/data/output/results.json
```

FTR otomatik değerlendirme çıktısının ana contract dosyası:

* `architecture/contracts/ftr_results_output_contract.md`

FTR uyum matrisi:

* `reports/PCR_FTR/ftr_delivery_alignment_2026_06_20.md`

Hazır olanlar:

* Proje kapsamı ve sınırları.
* Sistem mimarisi dokümantasyonu.
* AI modül yol haritası.
* Number Verification, normal mod, QoD ve evidence akışı.
* Veri/model/test strateji taslakları.
* Contract, rapor ve metrik şablonları.
* Araç tespiti, tracking, plaka tespiti ve CCT-XS OCR için baseline/fine-tune deney kayıtları.
* FTR `results.json` contract ve teslim uyum matrisi.

Henüz uygulanmayanlar:

* Root Dockerfile ve otomatik `/app/data/input/video.mp4` inference entrypoint.
* FTR `results.json` adapter/validator.
* Araç renk tahmini.
* FTR etiket setine birebir uyan araç tipi mapping.
* Sürücü eylemi, `teknocan`/`bilgisayar` nesne ve yolcu tespit pipeline'ı.
* Tesla T4 / 10 dakika / 8 GB image limitleri altında runtime doğrulaması.

Detaylı durum için `STATUS.md`, geliştirme sırası için `ROADMAP.md` dosyasına bakılmalıdır.

## Proje Konumu

Anomali Road Safety AI; kullanıcı adı/şifre ve Number Verification doğrulaması sonrası telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka çıkarım hattında analiz eden geniş bir karar destek sistemi olarak tasarlanır.

Ancak FTR değerlendirme hedefi bu geniş mimarinin Docker tabanlı, tek video girdili ve resmi JSON çıktılı alt kümesidir. FTR için üretilmesi gereken temel bilgiler:

1. `arac_bilgisi`: `tip`, `plaka`, `renk`, `confidence_score`.
2. `tespitler`: zaman bazlı `sofor_eylemi`, `nesneler`, `yolcular` etiketleri.

Sistem hukuki karar veya otomatik ceza üretmez. Risk skoru, güven skoru, açıklama ve evidence package üretir.

## Model Geliştirme Yaklaşımı

Ana hedef sıfırdan büyük model eğitmek değildir.

Planlanan yaklaşım:

1. İnternet üzerinde erişilebilir public/pretrained modeller araştırılır.
2. Aday modeller doğruluk, hız, latency, model boyutu ve export kolaylığına göre karşılaştırılır.
3. Seçilen modeller proje amacına uygun veri işleme, fine-tune ve post-processing ile uyarlanır.
4. Deneyler Google Colab üzerinde yürütülür.
5. Canlı demo çıkarımı MacBook üzerinde local edge/backend olarak çalıştırılır.
6. Test verisinin gerçekleştirildiği ortam izole tutulur.

İlk odak **araç tespiti** olacak. Sonraki modüller araç tespiti çıktısı üzerine sırayla eklenecek.

Araç tespiti için ilk ölçülebilir baseline **YOLO11n** olarak kaydedilmiştir. Bu final model kararı değildir; final seçim Colab fine-tune sonuçları, MacBook runtime benchmark, output contract uyumu, tracking/evidence katkısı, export ve lisans değerlendirmesi sonrası yapılacaktır.

İlk yerel manuel test seti `Test/video_1-3.mp4` dark/low-light videolarıdır. Bu videolar eğitim verisi değildir ve Git'e eklenmez; yalnız VD-EXP-001 smoke/manual benchmark için kullanılır.

## FTR Teslim Hedefi

İlk çalışan FTR teslim paketi şu kapsama odaklanır:

1. Root `Dockerfile`.
2. `main.py` entrypoint.
3. `/app/data/input/video.mp4` okuma.
4. `/app/data/output/results.json` yazma.
5. Araç tipi + plaka + renk özetleme.
6. Sürücü eylemi, nesne ve yolcu tespitlerini saniye bazlı üretme.
7. Tüm kategori ve etiketleri ASCII-safe, küçük harf ve resmi FTR listesiyle birebir uyumlu tutma.
8. Tesla T4 üzerinde 10 dakika runtime limitine uygun inference.

Android canlı kamera, Number Verification, QoD, dashboard ve rich evidence katmanları proje
mimarisinde korunur; fakat FTR otomatik değerlendirme için ikincil/future entegrasyon kapsamıdır.

## Tasarlanan Modül Sırası

1. FTR output adapter ve validator
2. Docker submission paketi
3. Araç tespiti, tracking ve tek ana araç seçimi
4. Araç tipi mapping
5. Plaka tespiti ve OCR normalization
6. Araç rengi tahmini
7. Sürücü eylemi / nesne / yolcu tespitleri
8. `results.json` konsolidasyonu
9. T4 runtime ve image boyutu optimizasyonu
10. Rich evidence, QoD, Number Verification, dashboard ve LLM açıklama katmanı

## Klasörler

| Klasör | Açıklama |
|---|---|
| `docs/` | Resmi rapor başlıkları ve teknik açıklamalar |
| `research/` | Araştırma başlıkları ve model/yöntem inceleme alanı |
| `reports/` | PDR/ÖTR ve PCR/FTR rapor çalışma alanı |
| `architecture/` | Diyagram, flow ve contract alanı |
| `project/` | Gereksinimler, kararlar ve riskler |
| `data/` | Veri hazırlama alanı |
| `models/` | Model deney, export ve benchmark alanı |
| `mobile/` | Android mobil uygulama planı |
| `backend/` | Edge/backend ve inference server planı |
| `testing/` | Test senaryoları ve metrik raporları |
| `governance/` | KVKK, güvenlik ve açık soru takibi |

## Başlangıç Dosyaları

* `docs/README.md`
* `docs/03_sistem_mimarisi/05_auth_normal_mode_flow.md`
* `docs/04_yapay_zeka/08_model_gelistirme_yol_haritasi.md`
* `docs/04_yapay_zeka/09_pretrained_finetune_stratejisi.md`
* `docs/04_yapay_zeka/10_runtime_ai_pipeline_mimarisi.md`
* `docs/04_yapay_zeka/10_yol_ve_arac_disi_kullanici_durumu.md`
* `docs/04_yapay_zeka/11_context_gated_model_routing.md`
* `docs/04_yapay_zeka/11_model_frekans_latency_budget.md`
* `docs/04_yapay_zeka/12_mvp_final_future_scope.md`
* `docs/04_yapay_zeka/13_ai_module_risk_register.md`
* `docs/06_mobil_uygulama/04_login_number_verification.md`
* `docs/10_test_metrikler/01_dengeli_basari_metrikleri.md`
* `docs/15_acik_sorular/00_acik_sorular.md`
* `PROJECT_MEMORY.md`

## Repo Visibility Notu

Bu repo 2026-06-08 itibarıyla private yapılmıştır. Buna rağmen büyük veri, model checkpointleri, kişisel veri içeren görüntüler ve gizli API anahtarları repoya eklenmemelidir.
