# Condition-Specific Vehicle Detector Routing

Tarih: 2026-06-08

Karar:

Araç tespiti hattı, ortam koşuluna göre detector profile seçebilen bir router ile tasarlanacak.

Başlangıç profilleri:

* `general`
* `dark`
* `rain`
* `fog_low_visibility`
* `night_low_light`

İlk local test seti yalnız dark/low-light koşulundaki `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4` dosyalarıdır. Bu videolar training set değil, manuel benchmark ve smoke-test materyalidir.

Gerekçe:

* Projenin ana fikri, ortam/sahne koşulunun detection güvenini ve uzman model seçimini etkilemesidir.
* Karanlık, yağmur ve düşük görüş koşulları tek bir genel detector'ın hata profilini ciddi şekilde değiştirebilir.
* Ancak 3 dark video, dark-specific model eğitmek için yeterli değildir; önce general YOLO11n detector dark profile altında ölçülmelidir.
* Yeterli condition-specific veri oluşunca dark/rain/fog specialist detector fine-tune edilebilir.

Etkilenen Alanlar:

* `Test/README.md`
* `.gitignore`
* `research/02_vehicle_detection/condition_specific_detector_routing.md`
* `research/02_vehicle_detection/benchmark_plan.md`
* `research/02_vehicle_detection/finetune_plan.md`
* `testing/templates/manual_video_benchmark_review.csv`
* `architecture/contracts/model_output_contract.md`
* `architecture/contracts/event.schema.json`
* `architecture/contracts/mobile_overlay_response.schema.json`

Alternatifler:

* Tek general detector ile devam etmek.
* 3 dark video üzerinden hemen dark-specific model eğitmek.
* Her frame için modeli yeniden eğitmek.

Reddedilen Yaklaşım:

Her frame veya her video için modeli yeniden eğitmek reddedildi. Doğru yaklaşım, scene/condition classifier ile profile seçmek ve önceden eğitilmiş/fine-tune edilmiş detector'ı çağırmaktır.

Geri Dönüş Planı:

Condition router güvenilir çalışmazsa `general` detector fallback olur. Specialist modeller yalnız general detector'a göre anlamlı kazanım gösterirse aktif profile olarak kullanılır.

Durum: Accepted
