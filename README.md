# Anomali Road Safety AI

5G ve yapay zeka ile akıllı yol güvenliği için model geliştirme, veri işleme, rapor ve mimari dokümantasyon deposu.

Bu repo, resmi PDR/ÖTR ve PCR/FTR rapor şablonları ile proje kapsam metnine göre sıfırdan kurulmuştur. Önceki demo/prototip çalışmaları bu kapsamın ana çıktısı değildir.

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
5. Test verisinin gerçekleştirildiği ortam izole tutulur.

İlk odak **araç tespiti** olacak. Sonraki modüller araç tespiti çıktısı üzerine sırayla eklenecek.

## Tasarlanan Modül Sırası

1. Araç tespiti
2. Araç takibi ve hedef araç seçimi
3. Plaka tespiti ve OCR
4. Evidence package sistemi
5. Sahne, hava, ışık ve görüş koşulu analizi
6. Genel yol ve araç dışı kullanıcı/yaya durumu
7. Şerit / road marking analizi
8. Hız kestirimi
9. Sürücü/yolcu ve araç içi risk analizi
10. Risk skoru, kritik mod ve uzman model orkestrasyonu
11. 5G QoD ve Number Verification adapterları
12. LLM açıklama katmanı
13. Test, metrik ve rapor kanıt sistemi

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
* `docs/04_yapay_zeka/10_yol_ve_arac_disi_kullanici_durumu.md`
* `docs/06_mobil_uygulama/04_login_number_verification.md`
* `docs/10_test_metrikler/01_dengeli_basari_metrikleri.md`
* `docs/15_acik_sorular/00_acik_sorular.md`
* `PROJECT_MEMORY.md`

## Public Repo Notu

Bu repo public oluşturulmuştur. Büyük veri, model checkpointleri, kişisel veri içeren görüntüler ve gizli API anahtarları repoya eklenmemelidir.
