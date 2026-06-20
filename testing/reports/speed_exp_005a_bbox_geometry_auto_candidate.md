# SPEED-EXP-005A BBox Geometry Auto Candidate

Bu rapor, manuel yol referans noktası olmadan bbox geometry + araç boyutu prior ile üretilen ilk otomatik hız adayını özetler.

## Kritik Not

Bu deney hukuki/final hız ölçümü değildir. `estimated_kmh` alanı yalnız `approximate_candidate` olarak yorumlanmalıdır.

## Konfigürasyon

* Model: `yolo11n.pt`
* Tracker: `bytetrack.yaml`
* Horizontal FOV varsayımı: `70.0` derece
* Smoothing window: `7` frame
* Plate comparison source: `models/benchmarks/artifacts/speed/SPEED-EXP-002-plate-bbox-xyz/speed_exp_002_plate_bbox_xyz_summary.json`

## Sonuç Tablosu

| Video | Track | Mode | BBox geom km/h | Range km/h | Conf | Plate geomean km/h | Warnings | Plot |
|---|---:|---|---:|---:|---:|---:|---|---|
| `video_1.mp4` | 1 | `approximate_candidate` | 2.731578 | 1.73-3.77 | 0.6635 | 3.7806 | approximate_monocular_speed|auto_scale_approximation|not_for_legal_enforcement|speed_candidate_jitter_high|invalid_segments_filtered | `runs/speed/SPEED-EXP-005A-bbox-geometry-auto/plots/video_1_speed_time_plot.png` |
| `video_2.mp4` | 1 | `approximate_candidate` | 2.487242 | 1.45-3.78 | 0.6342 | 3.8768 | approximate_monocular_speed|auto_scale_approximation|not_for_legal_enforcement|speed_candidate_jitter_high|invalid_segments_filtered | `runs/speed/SPEED-EXP-005A-bbox-geometry-auto/plots/video_2_speed_time_plot.png` |
| `video_3.mp4` | 2 | `approximate_candidate` | 11.514959 | 8.12-17.72 | 0.72 | 12.8163 | approximate_monocular_speed|auto_scale_approximation|not_for_legal_enforcement|invalid_segments_filtered | `runs/speed/SPEED-EXP-005A-bbox-geometry-auto/plots/video_3_speed_time_plot.png` |

## Yorum

* Bu sonuçlar otomatik yaklaşık hız adayıdır; sahada gerçek km/s doğrulaması yoktur.
* `video_3` yüksek/oynak aday üretirse bu, 004A relative fast sinyaliyle birlikte incelenmelidir.
* Plate-scale ile büyük fark varsa `candidate_disagreement_high` sonraki fusion adımında işaretlenmelidir.
* Grafikler `runs/` altında tutulur ve Git'e eklenmez.

## Sonraki Adım

1. PNG hız grafiklerini manuel incele.
2. Bbox geometry adayının plate-scale ve relative speed ile çelişkisini değerlendir.
3. Gerekirse FOV/prior sensitivity sweep ekle.
4. Sonra `SPEED-EXP-005B` FARSEC-lite depth adayına geç.
