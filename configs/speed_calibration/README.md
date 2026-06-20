# Speed Calibration Profiles

Bu klasör `SPEED-EXP-004C` ve sonraki homografi tabanlı hız denemeleri için kalibrasyon
profillerini tutar.

## Aktif Akış

1. `scripts/benchmarks/prepare_speed_004c_homography_calibration.py` çalıştırılır.
2. `runs/speed/SPEED-EXP-004C-homography/calibration_frames/` altındaki kareler manuel incelenir.
3. `CALIB-DEMO-001.template.json` kopyalanır ve aktif profil dosyasına dönüştürülür.
4. En az dört yol düzlemi noktası için:
   * `image_points_px`: görüntüdeki piksel koordinatları
   * `world_points_m`: aynı noktaların metre cinsinden gerçek dünya koordinatları
   girilir.
5. Reprojection error doğrulanmadan `absolute_candidate` hız değeri üretilmez.

## Kırmızı Çizgiler

* Bu profil hukuki hız ölçüm profili değildir.
* Ölçülü yol referansı yoksa sistem `SPEED-EXP-004A` relative speed ve `SPEED-EXP-004B`
  sanity-check fallback çıktılarıyla kalmalıdır.
* Plaka köşeleri veya araç gövdesi köşeleri yol düzlemi referans noktası değildir; yalnız
  zemine izdüşümü güvenilir şekilde biliniyorsa kullanılabilir.
