# Anomali Road Safety AI

5G ve yapay zeka ile akıllı yol güvenliği için model geliştirme, veri işleme, rapor ve mimari dokümantasyon deposu.

Bu repo, resmi PDR/ÖTR ve PCR/FTR rapor şablonları ile proje kapsam metnine göre sıfırdan kurulmuştur. Önceki demo/prototip çalışmaları bu kapsamın ana çıktısı değildir.

## Current Status

Bu repo şu anda **planning, documentation, research scaffolding ve technical contract definition** aşamasındadır.

Hazır olanlar:

* Proje kapsamı ve sınırları.
* Sistem mimarisi dokümantasyonu.
* AI modül yol haritası.
* Number Verification, normal mod, QoD ve evidence akışı.
* Veri/model/test strateji taslakları.
* Contract, rapor ve metrik şablonları.

Henüz uygulanmayanlar:

* Android canlı kamera uygulaması.
* Backend inference server.
* Gerçek zamanlı streaming pipeline.
* Fine-tuned model ağırlıkları.
* Evidence storage servisi.
* Gerçek 5G/QoD ve Number Verification API entegrasyonu.

Detaylı durum için `STATUS.md`, geliştirme sırası için `ROADMAP.md` dosyasına bakılmalıdır.

## Proje Konumu

Anomali Road Safety AI; kullanıcı adı/şifre ve Number Verification doğrulaması sonrası telefon kamerasından alınan canlı yol görüntüsünü edge destekli yapay zeka çıkarım hattında analiz ederek araç, plaka, hız, şerit, sahne/görüş, genel yol durumu, araç dışı kullanıcı/yaya durumu ve koşullu cabin risk sinyallerini değerlendiren bir karar destek sistemi olarak tasarlanır.

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

## MVP Hedefi

İlk çalışan MVP şu kapsama odaklanır:

1. Android canlı kamera preview.
2. Edge frame streaming.
3. Araç tespiti.
4. Hedef araç takibi.
5. Plaka tespiti/OCR.
6. Hafif frame quality / ortam bağlamı.
7. Evidence card generation.
8. Temel system health ekranı.

Şerit, hız kalibrasyonu, tam sahne/hava modeli, araç dışı kullanıcı, cabin risk ve gerçek QoD entegrasyonu kademeli olarak eklenecektir.

Canlı frame hedefi 720p seviyesinde alınacak, model input boyutu preprocessing aşamasında seçilen modele göre resize edilecektir.

## Tasarlanan Modül Sırası

1. Araç tespiti
2. Araç takibi ve hedef araç seçimi
3. Plaka tespiti ve OCR
4. Evidence package sistemi
5. Sahne, hava, ışık ve görüş koşulu analizi
6. Genel yol ve araç dışı kullanıcı/yaya durumu
7. Context-gated model routing ve uzman model seçimi
8. Şerit / road marking analizi
9. Hız kestirimi
10. Sürücü/yolcu ve araç içi risk analizi
11. Risk skoru, kritik mod ve uzman model orkestrasyonu
12. 5G QoD ve Number Verification adapterları
13. LLM açıklama katmanı
14. Test, metrik ve rapor kanıt sistemi

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
