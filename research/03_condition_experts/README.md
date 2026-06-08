# Research 03 - Condition-Specific Vehicle Detector Experts

## Amaç

Bu araştırma alanı, araç tespiti görevini farklı çevresel koşullara göre uzman detector profillerine ayırma yaklaşımını yönetir.

Buradaki "koşul uzmanı" bir ortam sınıflandırıcısı değildir. Koşul uzmanı, aynı araç tespiti görevini belirli bir koşul altında daha iyi yapması beklenen ayrı fine-tune edilmiş detector profilidir.

## Kritik Ayrım

İki ayrı model tipi vardır:

| Tip | Görev | Örnek Çıktı |
|---|---|---|
| Condition profile model | Frame veya kısa pencerenin ortam koşulunu belirler | `condition_profile=night_low_light` |
| Condition-specific vehicle detector | Belirli koşulda araç bbox/class/confidence üretir | `vehicle_detector_night_low_light_v1` |

Bu klasörün ana odağı ikinci tiptir. Ancak detector routing'in güvenli çalışması için condition profile modelinin çıktısı, güven skoru ve temporal kararlılığı da burada politika düzeyinde tanımlanır.

## Deep Research Sonucu

Köke eklenen deep research raporu bu klasöre taşındı:

* `deep_research/deep_research_report.md`

Raporun ana kararı:

* Doğrudan her koşul için ayrı detector eğiterek başlamak MVP için risklidir.
* Önce genel road-domain detector kurulmalı ve benchmark edilmelidir.
* Koşul uzmanları, kanıtlanmış genel checkpoint'ten türetilmelidir.
* İlk ayrı uzman `night_low_light` olmalıdır.
* `rain` ve `fog_low_visibility`, night specialist anlamlı fayda sağladıktan sonra açılmalıdır.
* `dark`, `tunnel_or_parking_dark`, `glare`, `low_contrast` başlangıçta ayrı detector değil, condition label/routing sinyali olarak izlenmelidir.

## Tavsiye Edilen MVP Expert Seti

| Expert | Başlangıç Durumu | Gerekçe |
|---|---|---|
| `vehicle_detector_general` | Zorunlu | Her koşul için güvenli fallback ve ana baseline |
| `vehicle_detector_night_low_light` | İlk specialist | Mevcut dark/low-light smoke test videoları ve literatürde net zorluk |
| `vehicle_detector_rain` | İkinci specialist adayı | Public condition split daha bulunabilir |
| `vehicle_detector_fog_low_visibility` | Üçüncü specialist adayı | ACDC/Foggy Cityscapes çizgisiyle test edilebilir |

## Bu Klasördeki Dosyalar

* `research_coverage_review.md`: deep research raporu, sorduğumuz soruları ne kadar cevaplamış kontrolü.
* `dataset_source_checklist.md`: veri seti/link/lisans doğrulama listesi.
* `action_roadmap.md`: bundan sonraki model geliştirme yol haritası.
* `deep_research/`: orijinal deep research raporu.

## Karar

Bu aşamadaki uygulanabilir yol:

1. Mevcut YOLO11n dark video smoke test sonuçlarını manuel kontrol et.
2. Public veri seti kaynak ve lisanslarını doğrula.
3. BDD100K + UA-DETRAC ile genel road-domain detector fine-tune hattını hazırla.
4. Genel model benchmark edilmeden specialist detector açma.
5. İlk specialist'i `night_low_light` olarak `best_general` checkpoint'inden başlat.
6. Specialist ancak general'e göre ölçülebilir fayda sağlıyorsa runtime routing'e aktif ekle.
