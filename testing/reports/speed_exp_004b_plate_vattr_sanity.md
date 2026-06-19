# SPEED-EXP-004B Plate-Scale + VATTR Sanity-Check

## Özet

Bu rapor `SPEED-EXP-004A` relative speed block'unu, `SPEED-EXP-002` plate-scale adayını ve
`VATTR-EXP-001` vehicle dimension prior çıktısını aynı event/evidence contract'ında birleştirir.

Sonuç: Bu aşama da **kesin km/s üretmez**. Plate-scale ve VATTR sinyalleri, relative speed
sonucunu destekleyen/çürüten yardımcı evidence olarak kullanılır.

## Inputlar

* Events: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004a.json`
* Plate speed summary: `models/benchmarks/artifacts/speed/SPEED-EXP-002-plate-bbox-xyz/speed_exp_002_plate_bbox_xyz_summary.json`
* VATTR checkpoint: `models/checkpoints/vehicle_attribute/VATTR-EXP-001-efficientnet_b0-best.pth`
* VATTR label map: `models/checkpoints/vehicle_attribute/VATTR-EXP-001-label-map.json`
* VATTR dimension priors: `models/checkpoints/vehicle_attribute/VATTR-EXP-001-dimension-prior-table.json`
* Target ROI crops: `runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/sample_frames`

## Sonuç Tablosu

| Video | Track | Relative | Plate km/h | VATTR label | VATTR conf | Fusion conf | Warnings |
|---|---:|---|---:|---|---:|---:|---|
| video_1.mp4 | TRK-001 | normal | 3.7806 | suv | 0.463309 | 0.9 | not_absolute_kmh|not_for_legal_enforcement|plate_scale_low_confidence |
| video_2.mp4 | TRK-001 | normal | 3.8768 | suv | 0.418496 | 0.6677 | not_absolute_kmh|not_for_legal_enforcement|plate_scale_low_confidence |
| video_3.mp4 | TRK-002 | fast | 12.8163 | van | 0.425803 | 0.5898 | candidate_disagreement_high|not_absolute_kmh|not_for_legal_enforcement|plate_scale_low_confidence |

## Yorum

* `speed_mode` hâlâ `relative` kalır.
* Plate-scale adayları düşük güvenlidir; mevcut sonuçlar kalibrasyon yokken mutlak hız olarak yorumlanmamalıdır.
* VATTR doğrudan hız değil, gövde tipi ve yaklaşık wheelbase/length prior sağlar.
* `candidate_disagreement_high` varsa sonraki homography/manuel review adımı önceliklendirilmelidir.

## Sonraki Adım

`SPEED-EXP-004C` için sabit kamera görüntüsünde yarı manuel homografi / ölçülü referans noktaları belirlenirse
`absolute_candidate` üretilebilir. 4B çıktısı bu adım için sanity-check katmanı olarak kalmalıdır.
