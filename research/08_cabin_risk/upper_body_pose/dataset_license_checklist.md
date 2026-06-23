# Driver Pose Dataset and License Checklist

Tarih: 2026-06-12

| Kaynak | Lisans/Erişim | Rol | Karar |
|---|---|---|---|
| YOLO11n-pose weights/runtime | Ultralytics AGPL-3.0 veya commercial terms | Ana pretrained aday | Yarışma/prototip kullanımında kayıtlı tut |
| MediaPipe Pose Landmarker Full | MediaPipe Apache-2.0 code; model bundle kaynağı kayıtlı | Challenger | Kullan |
| MMPose / RTMPose | Apache-2.0 code; Body7 kaynak dataset koşulları ayrıca kontrol | Yeni ana challenger | `POSE-EXP-003` benchmark |
| ViTPose | Apache-2.0 code; checkpoint kaynakları ayrıca kontrol | İkinci challenger | RTMPose yetersizse ayrı ortam |
| COCO Keypoints | COCO dataset terms | Pretraining provenance | Yeniden dağıtım öncesi kontrol |
| Lokal `Test/video_1-3.mp4` | Ekip içi izinli, Git dışı | Smoke ve baseline benchmark | Kullan |
| Kontrollü driver videoları | Açık rıza, saklama süresi ve erişim kaydı gerekli | Seatbelt/phone ground truth | Sonraki faz |

## Veri Güvenliği

* Yüz, upper-body crop ve overlay videoları `runs/` altında ve Git dışında kalır.
* Kimlik tanıma, face embedding veya biyometrik eşleştirme yapılmaz.
* Manuel review çıktıları kişi adı içermez.
* Rapor görseli kullanılmadan önce ayrıca izin kontrolü yapılır.
