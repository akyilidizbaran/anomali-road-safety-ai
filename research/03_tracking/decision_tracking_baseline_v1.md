# Decision - Vehicle Tracking Baseline v1

Tarih: 2026-06-10

## Karar

Anomali Road Safety AI için ilk vehicle tracking baseline **ByteTrack** olacak.

İkinci alternatif **BoT-SORT** olacak ve ilk karşılaştırmada ReID kapalı çalıştırılacak.

## Gerekçe

Vehicle detection baseline aşamasında bazı false negative'ler ve kısa süreli `car -> motorcycle` class flicker gözlemlendi. Bu hatalar ilk etapta yeni model eğitimiyle değil, tracking sürekliliği, class voting ve confidence smoothing ile ele alınmalıdır.

ByteTrack:

* eğitim gerektirmez,
* detector çıktısına doğrudan bağlanır,
* düşük confidence detection'ları association sürecinde değerlendirdiği için kısa detection düşmelerine uygundur,
* MacBook local runtime için düşük karmaşıklık sağlar,
* MIT lisanslı resmi repo ve Ultralytics track mode entegrasyonu vardır.

BoT-SORT:

* daha güçlü ikinci alternatiftir,
* Ultralytics içinde kolay denenebilir,
* ReID/GMC seçenekleri sunar,
* ancak ilk MVP'de ReID latency ve karmaşıklık ekleyebileceği için kapalı başlanmalıdır.

## Ertelenenler

* DeepSORT: ReID maliyeti ve GPL-3.0 lisans riski.
* StrongSORT: ReID/akademik kurulum karmaşıklığı ve GPL-3.0 lisans riski.
* OC-SORT: iyi adaydır, ancak ilk iki deneyden sonra gerekirse denenmelidir.

## Etki

* `research/03_tracking/deep_research/deep_research_report.md`
* `research/03_tracking/benchmark_plan.md`
* `models/benchmarks/tracking/tracking_baseline_comparison.csv`
* `testing/templates/manual_tracking_review.csv`
* `architecture/contracts/model_output_contract.md`

## Yeniden Karar Koşulları

Bu karar şu koşullarda yeniden açılır:

* ByteTrack ID switch sayısı evidence veya OCR temporal voting'i bozarsa.
* BoT-SORT ReID kapalı mod açık şekilde daha stabil çıkarsa.
* Uzun occlusion senaryoları demo kapsamına girerse.
* Tracking latency hedefleri ByteTrack dışında daha iyi karşılanırsa.
* Lisans veya deployment koşulları değişirse.
