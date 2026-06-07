# Tek Hedef Araç Stratejisi

## Gerekçe

Sistem çok kapsamlı olduğu için MVP’de tüm araçları tam uzman analizden geçirmek gerçekçi değildir. Tek hedef araç stratejisi kaynakları en önemli araca odaklar.

## Target Vehicle Score

Hedef araç skoru şu sinyallerle hesaplanabilir:

* Bounding box büyüklüğü.
* Ekran merkezine yakınlık.
* Detection confidence.
* Track stability.
* Plaka görünürlüğü.
* Şerit/konum önemi.
* Risk ön skoru.

## Örnek Formül

```text
target_score =
  0.25 * bbox_size_score +
  0.20 * center_score +
  0.20 * detection_confidence +
  0.15 * track_stability +
  0.10 * plate_visibility +
  0.10 * preliminary_risk
```

Bu formül başlangıç için rule-based olabilir. Daha sonra öğrenilebilir hedef seçici modele dönüştürülebilir.

## Multi-target Mode

Settings ekranında multi-target mode opsiyonel olarak açılabilir. Bu modda sistem birden fazla araç için hafif analiz yapar, ancak ağır uzman modeller yine seçici çalışır.

## Mevcut Karar

* MVP ve ana yarışma demosu single-target mode ile tasarlanır.
* Multi-target mode deneysel genişletme olarak tutulur.
* Final sunumda multi-target gösterimi zorunlu değildir; gösterilirse sistem kapasite genişletmesi olarak anlatılmalıdır.
