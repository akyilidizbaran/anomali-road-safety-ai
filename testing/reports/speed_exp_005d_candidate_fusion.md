# SPEED-EXP-005D Candidate Fusion

Bu rapor, hız modülünü mevcut proje fazı için kapatmak amacıyla 004A relative, 002 plate-scale ve 005A bbox-geometry adaylarını tek karar ağacında birleştirir.

## Kritik Not

* Bu çıktı hukuki/final hız ölçümü değildir.
* FTR `results.json` şeması hız alanı istemediği için bu modül submission ana çıktısı değildir.
* Hız bloğu yalnız risk/evidence ve `slalom` destek sinyali olarak kullanılmalıdır.

## Konfigürasyon

* Relative source: `models/benchmarks/artifacts/speed/SPEED-EXP-004A-relative-track-bbox/speed_exp_004a_relative_track_speed_summary.json`
* Plate source: `models/benchmarks/artifacts/speed/SPEED-EXP-002-plate-bbox-xyz/speed_exp_002_plate_bbox_xyz_summary.json`
* BBox geometry source: `models/benchmarks/artifacts/speed/SPEED-EXP-005A-bbox-geometry-auto/speed_exp_005a_bbox_geometry_summary.json`
* Max agreement ratio: `0.45`

## Final Hız Kararı

| Video | Track | Mode | Primary | km/h | Range | Relative | Plate km/h | Agreement | Conf | Decision |
|---|---|---|---|---:|---|---|---:|---:|---:|---|
| `video_1.mp4` | `TRK-001` | `approximate_candidate` | `bbox_geometry_auto` | 2.640442 | 1.89-3.50 | `normal` | 3.7806 | 0.301581 | 0.7072 | `use_bbox_geometry_with_plate_relative_support` |
| `video_2.mp4` | `TRK-001` | `approximate_candidate` | `bbox_geometry_auto` | 2.334246 | 1.47-3.21 | `normal` | 3.8768 | 0.397894 | 0.651 | `use_bbox_geometry_with_plate_relative_support` |
| `video_3.mp4` | `TRK-002` | `approximate_candidate` | `bbox_geometry_auto` | 15.064621 | 9.42-19.91 | `fast` | 12.8163 | 0.149245 | 0.72 | `use_bbox_geometry_with_plate_relative_support` |

## Yorum

* `video_1` ve `video_2` düşük hız/normal hareket sınıfında kalır.
* `video_3` hem relative fast hem de bbox/plate adaylarıyla daha hızlı aday üretir.
* Bu kapanış sonrası hız modülü ana FTR geliştirme yolunu bloklamamalıdır.
* Sonraki FTR odağı `arac_bilgisi` ve `tespitler` üretimidir.
