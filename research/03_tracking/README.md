# Araştırma 3 - Araç Takibi ve Olay Sürekliliği

## Amaç

Hedef aracın zaman boyunca takip edilmesi, track ID kararlılığı ve event sürekliliğini sağlamak.

## Alt Başlıklar

* ByteTrack, BoT-SORT, DeepSORT, OC-SORT karşılaştırması.
* StrongSORT, Norfair ve Kalman + IoU fallback değerlendirmesi.
* Tracking-by-detection yaklaşımı.
* Track ID üretimi.
* ID switch problemi.
* Takip kararlılığı.
* Kısa süreli kaybolma ve yeniden yakalama.
* Tracking çıktısının hız kestirimine etkisi.
* Tracking çıktısının evidence üretimine etkisi.
* Track confidence.
* Single-target tracking.
* Multi-target settings modu.
* MOTA, IDF1, ID switch metrikleri.

## Aktif Karar

İlk baseline tracker: **ByteTrack**

İkinci alternatif: **BoT-SORT**, ilk denemede ReID kapalı.

Ertelenenler: DeepSORT, StrongSORT ve ağır ReID tabanlı tracker'lar.

Karar gerekçesi: Mevcut ihtiyaç, vehicle detector çıktısını hızlı şekilde kararlı `track_id`, class voting, confidence smoothing, speed trail ve evidence history çıktısına dönüştürmektir. ReID ilk MVP için zorunlu değildir.

## Dosyalar

* `deep_research/deep_research_report.md`: kaynaklı tracking deep research raporu.
* `benchmark_plan.md`: ByteTrack / BoT-SORT benchmark planı.
* `decision_tracking_baseline_v1.md`: ilk tracking baseline kararı.
* `next_phase_track_to_event_plan.md`: ByteTrack çıktısını target/event/evidence hattına bağlama planı.
* `../../models/benchmarks/tracking/tracking_baseline_comparison.csv`: tracking deney kayıt tablosu.
* `../../testing/templates/manual_tracking_review.csv`: ground truth olmayan videolar için manuel review şablonu.

## Çıktı

Tracker seçimi ve track stability metriği tanımı.
