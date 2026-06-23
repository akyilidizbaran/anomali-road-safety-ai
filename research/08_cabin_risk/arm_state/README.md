# Driver Arm-State Baseline

Tarih: 2026-06-14

## Amaç

Sürücü kimliğini YuNet yüz anchor'ıyla koruyarak iki kolun zamansal durumunu
izlemek. Bu faz telefon, sigara veya ihlal kararı üretmez.

Zincir:

`CABIN-EXP-004 YuNet -> POSE-EXP-010 arm-focus ViTPose -> ARM-EXP-001 hybrid tracker -> temporal state`

## Durumlar

* `hand_near_face`
* `arm_raised`
* `hands_on_wheel_candidate`
* `hand_off_wheel_candidate`
* `arms_visible_other`
* `unknown`
* `not_evaluable`

`hands_on_wheel_candidate`, tespit edilmiş direksiyon teması anlamına gelmez.
Yalnız view-profile içindeki beklenen direksiyon bölgesine göre geometrik adaydır.

## Güvenlik Kuralları

* Yüz/cabin kimliği sıçrarsa tracker sıfırlanır.
* Optical flow yalnız kısa kesintileri en fazla 12 kare taşır.
* İleri-geri Lucas-Kanade hatası yüksek noktalar reddedilir.
* Yüz-relative sürücü beden bölgesi dışındaki zincirler reddedilir.
* Anatomik kemik uzunluğu kapısını geçmeyen kollar state üretmez.
* `poor/not_visible` kareler evidence olabilir, karar oranına girmez.
* Bu baseline hiçbir koşulda risk skorunu artırmaz.

## Dosyalar

* `benchmark_plan.md`
* `decision_arm_state_baseline_v1.md`
* `RUN_DRIVER_ARM_STATE_BASELINE.md`
* `sources.md`
