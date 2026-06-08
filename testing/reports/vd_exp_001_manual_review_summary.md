# VD-EXP-001 Manual Review Summary

## Kapsam

* Experiment: `VD-EXP-001`
* Model: `YOLO11n pretrained, zero fine-tune`
* Test set: `Test/video_1-3.mp4`
* Condition: dark / low-light smoke test
* Output: `runs/detect/runs/detect/VD-EXP-001-yolo11n-dark/`
* Review type: qualitative manual review

## Kullanıcı Gözlemi

Manuel kontrolde modelin genel araç varlığını doğru yakaladığı görüldü. Bazı false negative durumları var, ancak genel araç detection davranışı kullanılabilir seviyede.

Gözlenen küçük hata:

* Araç bazı kısa aralıklarda `motorcycle` olarak sınıflandırılıyor.
* Bu yanlış sınıf tahmini yaklaşık 2-3 frame seviyesinde ve track-level smoothing / temporal voting ile göz ardı edilebilir düzeyde.

## Teknik Yorum

Bu sonuç, YOLO11n zero fine-tune baseline'ın düşük ışık smoke test için başlangıç olarak yeterli olduğunu gösterir; ancak frame-level classification kararlılığı ve düşük ışıkta false negative davranışı fine-tune sonrası tekrar ölçülmelidir.

Bu video seti eğitim verisi olarak kullanılmamalıdır. Mevcut rolü:

* smoke test,
* qualitative manual review,
* low-light failure-case çıkarımı,
* future night/low-light specialist acceptance check.

## Karar

* Genel araç yakalama: qualitative pass.
* Sayısal manual accuracy: pending.
* Fine-tune yönü: önce condition-balanced general road-domain vehicle detector.
* Specialist yönü: `night_low_light` yalnız `best_general` seçildikten sonra açılır.

## Takip Edilecek Hata Tipleri

* False negative frame aralıkları.
* Kısa süreli wrong-class flicker (`car` -> `motorcycle`).
* BBox crop'un downstream plate/evidence için yeterliliği.
* Track continuity üzerindeki etkisi.
* Confidence stability.
