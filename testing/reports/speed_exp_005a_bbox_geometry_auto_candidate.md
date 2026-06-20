# SPEED-EXP-005A BBox Geometry Auto Candidate

Bu rapor, manuel yol referans noktası olmadan bbox geometry + araç boyutu prior ile üretilen ilk otomatik hız adayını özetler.

## Kritik Not

Bu deney hukuki/final hız ölçümü değildir. `estimated_kmh` alanı yalnız `approximate_candidate` olarak yorumlanmalıdır.

## Konfigürasyon

* Model: `yolo11n.pt`
* Tracker: `bytetrack.yaml`
* Horizontal FOV varsayımı: `70.0` derece
* Rolling median window: `7` frame
* Moving average window: `25` frame
* Post-peak bbox shrink gate: `0.85`
* Plate comparison source: `models/benchmarks/artifacts/speed/SPEED-EXP-002-plate-bbox-xyz/speed_exp_002_plate_bbox_xyz_summary.json`

## Sonuç Tablosu

| Video | Track | Mode | Moving avg km/h | Rolling median km/h | Range km/h | Conf | Plate geomean km/h | Warnings | Plot |
|---|---:|---|---:|---:|---:|---:|---:|---|---|
| `video_1.mp4` | 1 | `approximate_candidate` | 2.640442 | 2.494712 | 1.89-3.50 | 0.72 | 3.7806 | approximate_monocular_speed, auto_scale_approximation, not_for_legal_enforcement, invalid_segments_filtered | `runs/speed/SPEED-EXP-005A-bbox-geometry-auto/plots/video_1_speed_time_plot.png` |
| `video_2.mp4` | 1 | `approximate_candidate` | 2.334246 | 2.019522 | 1.47-3.21 | 0.72 | 3.8768 | approximate_monocular_speed, auto_scale_approximation, not_for_legal_enforcement, invalid_segments_filtered | `runs/speed/SPEED-EXP-005A-bbox-geometry-auto/plots/video_2_speed_time_plot.png` |
| `video_3.mp4` | 2 | `approximate_candidate` | 15.064621 | 11.514959 | 9.42-19.91 | 0.72 | 12.8163 | approximate_monocular_speed, auto_scale_approximation, not_for_legal_enforcement, invalid_segments_filtered | `runs/speed/SPEED-EXP-005A-bbox-geometry-auto/plots/video_3_speed_time_plot.png` |

## Yorum

* Bu sonuçlar otomatik yaklaşık hız adayıdır; sahada gerçek km/s doğrulaması yoktur.
* Ana `estimated_kmh` değeri pikleri bastırmak için moving average serisinin ortalaması olarak raporlanır.
* `video_3` yüksek/oynak aday üretirse bu, 004A relative fast sinyaliyle birlikte incelenmelidir.
* Plate-scale ile büyük fark varsa `candidate_disagreement_high` sonraki fusion adımında işaretlenmelidir.
* Grafikler `runs/` altında tutulur ve Git'e eklenmez.

## Sonraki Adım

1. PNG hız grafiklerini manuel incele.
2. Bbox geometry adayının plate-scale ve relative speed ile çelişkisini değerlendir.
3. Gerekirse FOV/prior sensitivity sweep ekle.
4. Sonra `SPEED-EXP-005B` FARSEC-lite depth adayına geç.
