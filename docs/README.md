# Anomali Road Safety AI - Dokümantasyon Ana Dizini

Bu klasör, **Anomali Road Safety AI** projesinin resmi yarışma raporları ve teknik geliştirme süreci için sıfırdan kurulmuş proje dokümantasyon omurgasıdır.

Kaynak alınan resmi dosyalar:

* `2026_5G_Yapay_Zeka_ile_Akıllı_Yol_Güvenliği_ÖTR_şablon_TR_rYLTN.docx`
* `2026_5G_Yapay_Zeka_ile_Akıllı_Yol_Güvenliği_FTR_şablon_TR_1_e4PVw.docx`
* `leD24n5kbHaXp0eczbnAt7N3hhcN6MxU.pdf`

Not: Kullanıcının ifadesindeki **PDR** burada resmi dosya karşılığı olan **Ön Tasarım Raporu / ÖTR** ile birlikte `PDR_OTR` adıyla tutuldu. Kullanıcının ifadesindeki **PCR** ise resmi final rapor şablonu karşılığı olan **Final Tasarım Raporu / FTR** ile birlikte `PCR_FTR` adıyla tutuldu.

## Ana Klasörler

| Klasör | Amaç |
|---|---|
| `docs/01_resmi_raporlar/PDR_OTR` | Ön tasarım raporundaki tüm resmi başlıkların proje özelinde açıklaması |
| `docs/01_resmi_raporlar/PCR_FTR` | Final raporundaki tüm resmi başlıkların proje özelinde açıklaması |
| `docs/02_proje_kapsami` | Proje vizyonu, kapsam, demo senaryosu, kırmızı çizgiler |
| `docs/03_sistem_mimarisi` | Auth, Number Verification, mobil-edge-backend-5G veri akışı, normal/kritik mod, hedef araç stratejisi |
| `docs/04_yapay_zeka` | Araç, takip, plaka, OCR, hız, şerit, sahne, yol/araç dışı kullanıcı, cabin risk, risk skoru |
| `docs/05_veri_seti` | Görev bazlı veri seti, etiketleme, split, augmentation, veri yönetimi |
| `docs/06_mobil_uygulama` | Login, Camera, Evidence, System, Settings ekran gereksinimleri |
| `docs/07_edge_backend` | FastAPI/WebSocket edge inference, event fusion, evidence storage |
| `docs/08_5g_qod` | Number Verification, QoD, ağ kalitesi ve adapter yaklaşımı |
| `docs/09_evidence_aciklanabilirlik` | Kanıt paketi, event JSON, LLM açıklama katmanı |
| `docs/10_test_metrikler` | Model, sistem, event ve demo test planları |
| `docs/11_arastirma_basliklari` | Derin araştırma konuları ve alt başlıkları |
| `docs/12_proje_yonetimi` | Fazlar, zaman planı, görev dağılımı, milestone mantığı |
| `docs/13_etik_kvkk_guvenlik` | KVKK, kişisel veri, güvenlik, karar destek sınırları |
| `docs/14_rapor_yazim_kilavuzu` | Rapor formatı, kaynakça ve şekil/tablo önerileri |
| `docs/15_acik_sorular` | Cevaplanması gereken karar noktaları |

## Çalışma Prensibi

Bu yapı final raporun birebir kendisi değildir. Resmi raporlar 3-10 sayfa sınırında olacağı için bu dosyalar, rapora aktarılacak içeriği ayrıntılı biçimde hazırlayan bilgi bankasıdır.

Her dosya şu amaçla yazılmıştır:

* Resmi şablonun ne istediğini netleştirmek.
* Bu projenin o başlıktaki karşılığını açıklamak.
* Rapor, sunum ve geliştirme için kullanılacak teknik detayları ayrıştırmak.
* Açık kalan karar noktalarını ayrıca sormak.

## Kritik Konumlandırma

Proje hiçbir belgede kesin ceza kesen veya hukuki hüküm veren bir sistem olarak anlatılmamalıdır. Doğru konumlandırma:

> Mobil ve edge destekli, 5G/QoD kullanımını seçici değerlendiren, riskli yol güvenliği olaylarını tespit eden, açıklayan ve denetlenebilir kanıt paketine dönüştüren karar destek sistemi.

## Ana Akış Dosyaları

* `docs/03_sistem_mimarisi/05_auth_normal_mode_flow.md`: Login, Number Verification, normal mod, riskli araç ve QoD tetikleme sırası.
* `docs/06_mobil_uygulama/04_login_number_verification.md`: Kullanıcı adı/şifre ve Number Verification giriş kapısı.
* `docs/04_yapay_zeka/10_yol_ve_arac_disi_kullanici_durumu.md`: Genel yol, yaya/bisikletli/motosikletli ve araç dışı kullanıcı bağlamı.
* `docs/00_baslangic/02_glossary.md`: Teknik terimler sözlüğü.
* `reports/PCR_FTR/section_map.md`: Final rapor bölümleri ile kaynak doküman eşlemesi.
* `architecture/contracts/`: Backend, event JSON, overlay response ve QoD status teknik contract dosyaları.

## Model Geliştirme Notu

Bu proje kapsamında model geliştirme, sıfırdan büyük model eğitmekten çok public/pretrained modellerin araştırılması, Colab üzerinde fine-tune edilmesi, veri işleme/post-processing ile proje amacına uyarlanması ve dengeli metrik paketiyle değerlendirilmesi üzerine kuruludur.
