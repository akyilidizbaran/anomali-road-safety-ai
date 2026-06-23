# Cabin Dataset and License Checklist

Tarih: 2026-06-12

| Kaynak | Lisans/Erişim | Bu Fazdaki Rol | Karar |
|---|---|---|---|
| MediaPipe BlazeFace | Apache-2.0 code; model card koşulları kontrol edilir | Face baseline | Kullan |
| OpenCV Zoo YuNet | Model dizini MIT | Small/distant multi-face challenger | `CABIN-EXP-004` kullan |
| InsightFace SCRFD | Kod ve pretrained model koşulları ayrı doğrulanmalı | Güçlü WIDER hard challenger | Lisans doğrulamasından sonra |
| PyTorch RetinaFace | MIT repo; checkpoint kaynağı ayrıca kaydedilmeli | Fallback challenger | Gerekirse |
| Mevcut `Test/video_1-3.mp4` | Lokal, izinli ve Git dışı | Visibility/driver smoke test | Kullan |
| Kontrollü ekip videoları | Yazılı/izlenebilir izin, lokal kısıtlı storage | Phone/seatbelt pozitif-negatif test | Sonraki faz |
| State Farm | Kaggle competition terms | Distracted-driver araştırması | Erişim koşulunu doğrula |
| AUC Distracted Driver | Akademik kaynak koşulları | Challenger/fine-tune araştırması | Lisansı doğrula |
| Drive&Act | Dataset agreement | Multi-action araştırması | Lisansı doğrula |

## Güvenlik Kuralları

* Yüz/cabin crop ve overlay videoları Git'e eklenmez.
* Kişi kimliği çıkarımı yapılmaz.
* Face embedding veya biometric identification tutulmaz.
* Minimum saklama ve kontrollü erişim uygulanır.
* Rapor görseli kullanılacaksa ayrıca izin kontrolü yapılır.
