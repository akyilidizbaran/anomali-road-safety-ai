# SPEED-EXP-004C Homography Calibration Preparation

Bu rapor `SPEED-EXP-004C` için yarı manuel homografi kalibrasyon hazırlığını özetler.
Bu aşama **mutlak km/s üretmez**; yalnız ölçülü referans noktaları seçilecek kareleri ve kalibrasyon profil şablonunu hazırlar.

## Karar

* Çalıştırma yeri: local MacBook.
* Gerekçe: Eğitim/GPU yok; işlem OpenCV frame extraction + manuel ölçüm noktası seçimi + homografi doğrulamasıdır.
* Colab gerekmez; Drive I/O ve küçük dosya yönetimi bu adım için gereksiz yavaşlık üretir.

## Üretilen Kalibrasyon Girdileri

* Kalibrasyon profil şablonu: `configs/speed_calibration/CALIB-DEMO-001.template.json`
* Frame çıktı klasörü: `runs/speed/SPEED-EXP-004C-homography`
* Summary JSON: `models/benchmarks/artifacts/speed/SPEED-EXP-004C-homography/speed_exp_004c_homography_calibration_prep_summary.json`

## Çıkarılan Kareler

| Video | Rol | Frame | Çözünürlük | Çıktı |
|---|---:|---:|---:|---|
| `video_1.mp4` | `first_track_frame` | 1 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_1_first_track_frame_frame_000001.jpg` |
| `video_1.mp4` | `mid_track_frame` | 172 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_1_mid_track_frame_frame_000172.jpg` |
| `video_1.mp4` | `best_target_frame` | 276 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_1_best_target_frame_frame_000276.jpg` |
| `video_1.mp4` | `last_track_frame` | 344 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_1_last_track_frame_frame_000344.jpg` |
| `video_2.mp4` | `first_track_frame` | 1 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_2_first_track_frame_frame_000001.jpg` |
| `video_2.mp4` | `mid_track_frame` | 172 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_2_mid_track_frame_frame_000172.jpg` |
| `video_2.mp4` | `best_target_frame` | 281 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_2_best_target_frame_frame_000281.jpg` |
| `video_2.mp4` | `last_track_frame` | 344 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_2_last_track_frame_frame_000344.jpg` |
| `video_3.mp4` | `first_track_frame` | 1 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_3_first_track_frame_frame_000001.jpg` |
| `video_3.mp4` | `mid_track_frame` | 144 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_3_mid_track_frame_frame_000144.jpg` |
| `video_3.mp4` | `best_target_frame` | 214 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_3_best_target_frame_frame_000214.jpg` |
| `video_3.mp4` | `last_track_frame` | 287 | 3840x2160 | `runs/speed/SPEED-EXP-004C-homography/calibration_frames/video_3_last_track_frame_frame_000287.jpg` |

## Manuel Doldurulacak Alanlar

1. `configs/speed_calibration/CALIB-DEMO-001.template.json` dosyasını kopyalayarak aktif bir profil oluştur.
2. En az dört adet yol düzlemi noktasını piksel koordinatı olarak gir: `image_points_px`.
3. Aynı noktaların gerçek dünyadaki metre koordinatlarını gir: `world_points_m`.
4. Kullanılacak yol bölgesini `road_roi_px` ile sınırla.
5. Homografi reprojection error kabul edilebilir değilse mutlak hız adayı üretme.

## Notlar

* Bu deney yasal/hukuki hız ölçümü değildir; yalnız karar destek için `absolute_candidate` üretmeye hazırlanır.
* Plaka ölçeği ve VATTR sinyalleri 004B'de sanity-check olarak kalır; 004C'nin ana katkısı yol düzlemi kalibrasyonudur.
* Ölçülü referans yoksa sistem 004A relative speed + 004B sanity-check fallback hattında kalmalıdır.
