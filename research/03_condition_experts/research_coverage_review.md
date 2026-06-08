# Condition Experts Deep Research Coverage Review

## Genel Değerlendirme

`deep_research/deep_research_report.md`, koşul uzmanı yaklaşımını karar vermeye yetecek seviyede cevaplıyor. Raporun en değerli çıktısı, üç stratejiyi karşılaştırıp Strateji 1'i seçmesidir:

> Önce genel vehicle detector fine-tune, sonra yalnız benchmark ile faydası kanıtlanan condition-specific specialist detector.

Ancak rapor tek başına final kaynak dosyası olarak kullanılmamalıdır. İçindeki `turn...` ve `filecite...` referansları ChatGPT/Deep Research oturumuna ait izlerdir; repo içinde kalıcı ve tıklanabilir kaynak linki sayılmaz. Bu yüzden `dataset_source_checklist.md` ile ayrı kaynak doğrulama listesi eklendi.

## Soru Kapsam Kontrolü

| Soru Alanı | Durum | Not |
|---|---|---|
| Genel detector mı önce, specialist mi önce? | Tam | Strateji 1 net seçilmiş. |
| Koşula özel detector fikri literatürde makul mü? | Tam | Domain shift, adverse weather, weather-aware routing ve enhancement çizgileriyle gerekçelendirilmiş. |
| Tek all-weather modelle kıyas | Tam | Strateji 3 baseline/challenger olarak konumlandırılmış. |
| Avantaj/dezavantaj analizi | Tam | Routing hatası, model yönetimi, veri parçalanması ve latency riskleri belirtilmiş. |
| Condition classifier yanlış dönerse risk | Tam | General fallback, hysteresis ve çift koşum önerilmiş. |
| General fallback tasarımı | Tam | Fallback her zaman açık olmalı kararı var. |
| General + specialist aynı frame'de çalışsın mı? | Tam | Normal modda tek detector, kritik/belirsiz durumda dual-run önerilmiş. |
| Dataset önerileri | Kısmi | Liste geniş ve iyi; fakat lisansların bir kısmı doğrulanmalı. |
| Her dataset için kaynak linki | Kısmi | Deep research içinde kalıcı URL yok; bu repo için ayrı checklist oluşturuldu. |
| Her dataset için lisans | Kısmi | BDD100K, ExDark, WEDGE, Waymo gibi bazıları net; UA-DETRAC, DAWN, NOD, SHIFT için doğrulama gerekir. |
| YOLO11/YOLOv10/RT-DETR adayları | Tam | Model rolleri ve başlangıç sırası önerilmiş. |
| MacBook edge gerçekliği | Kısmi | Rapor "ölçülmeli" diyor; repo içinde YOLO11n MPS smoke benchmark başladı. |
| Benchmark metrikleri | Tam | mAP, recall, FP/min, missed detection, bbox adequacy, confidence stability, track continuity önerilmiş. |
| Promotion threshold | Tam | +2 mAP / +3 AP@0.5 / +4 recall gibi proje içi kabul eşiği önerilmiş. |
| Dataset split stratejisi | Tam | Video-level split ve leakage önleme belirtilmiş. |
| Augmentation / synthetic data | Tam | Destekleyici ama ana çözüm değil denmiş. |
| Preprocessing vs specialist detector | Tam | Preprocessing ikincil ablation olarak konumlandırılmış. |
| Model registry | Tam | Registry alanları önerilmiş. |
| Event/evidence içinde specialist loglama | Tam | `detector_selected`, `routing_reason`, `fallback_used` gibi alanlar önerilmiş. |
| Colab deney planı | Tam | Deney aileleri verilmiş. |
| Repo klasör önerisi | Tam | Ayrı condition expert klasörü önerilmiş; bu klasörle uygulanmaya başlandı. |
| Nihai karar önerisi | Tam | Strateji 1, YOLO11n baseline, night_low_light ilk specialist. |

## Eksik veya Güçlendirilmesi Gereken Noktalar

1. **Kaynak formatı eksik:** Deep research raporundaki citation placeholder'ları final rapor için kullanılamaz.
2. **Lisans doğrulaması tamamlanmadı:** Özellikle UA-DETRAC, DAWN, NOD ve SHIFT için resmi lisans/erişim şartı ayrıca doğrulanmalı.
3. **Condition profile model tasarımı henüz uygulanabilir seviyede değil:** Hangi hafif modelle `condition_profile` üretileceği, hangi etiket setiyle eğitileceği ve threshold'lar netleşmeli.
4. **Genel detector fine-tune hattı henüz kurulmadı:** Şu an sadece YOLO11n zero-fine-tune smoke benchmark yapıldı.
5. **Manual review sonuçları yok:** `Test/video_1-3.mp4` çıktıları görsel olarak oluştu ama insan gözlemiyle accuracy/failure-case kayıtları girilmedi.
6. **Model registry ve routing config henüz gerçek dosya değil:** Rapor öneriyor; uygulama fazında eklenmeli.

## Sonuç

Deep research raporu strateji kararı için yeterli. Bundan sonra araştırmayı genişletmekten önce repo içinde uygulanabilir sıraya geçmek gerekir:

1. Kaynak/lisans checklist'i tamamla.
2. Mevcut dark video çıktılarının manuel review'ını yap.
3. General detector dataset ve Colab fine-tune pipeline'ını kur.
4. `best_general` oluşmadan condition-specific detector eğitme.
5. İlk specialist olarak `night_low_light` aç.
