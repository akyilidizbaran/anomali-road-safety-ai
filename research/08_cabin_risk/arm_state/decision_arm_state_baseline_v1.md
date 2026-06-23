# Driver Arm-State Baseline Kararı

Tarih: 2026-06-14

## Karar

`POSE-EXP-009` torso baseline olarak sabit kalır. Action-grade kol takibi için
ayrı `POSE-EXP-010 -> ARM-EXP-001` hattı açılmıştır.

Eski geniş-ROI `POSE-EXP-005` gözlemleriyle yapılan ilk entegrasyon smoke testi
reddedildi: `video_3` üzerinde bazı iskeletler sürücü yerine kaporta/gövde
bölgesine yerleşti. Optical flow bu yanlış geometrinin sürekliliğini artırdığı
için seçim metriği olarak kullanılamaz.

Yeni candidate şu düzeltmeleri içerir:

* arm-focus face-relative ROI,
* forward/backward optical-flow doğrulaması,
* 12 kare maksimum flow taşıma,
* driver identity reset,
* face-relative beden bölgesi kapısı,
* anatomik zincir kapısı,
* visibility ile evidence/decision ayrımı.

## Seçim Durumu

Kod ve otomatik testler tamamlandı. `video_3` smoke sonucunda ViTPose arm-focus
gözlemiyle çalışan `ARM-EXP-001`, YOLO11n-pose arm-focus tekrarından belirgin
daha güçlüdür:

| Observation | Available State | Longest Miss |
|---|---:|---:|
| `POSE-EXP-010` ViTPose-B arm-focus | 0.9851 | 0.04 sn |
| `POSE-EXP-011` YOLO11n-pose arm-focus | 0.3209 | 0.94 sn |

Bu nedenle YOLO11n-pose sürekli arm-state baseline olarak seçilmez.

Arkadaş ekip bilgisinden gelen önemli ayrım: `yolo11n-pose.pt` doğrudan kol
takip baseline'ı değil, telefon/sigara nesnesi bulunamadığında veya bulunduğunda
sürücü ilişkisini destekleyen yardımcı sinyal olarak kullanılmıştır. Bu kullanım
doğrudur: object-first specialist sonrasında conditional pose/hand association.

## Final Kapatma - 17 Haziran 2026

Kullanici karariyla on kolun direksiyonda, havada veya off-wheel olmasini genel
pose iskeletinden siniflandirma calismasi durduruldu.

* `POSE-EXP-009` kesintisiz omuz/torso iskelet baseline olarak sabittir.
* `POSE-EXP-010 -> ARM-EXP-001` reference/candidate olarak tutulur.
* `near_face`, `raised`, `wheel_candidate` ve `off_wheel_candidate` alanlari risk
  karari veya specialist kabul kapisi olmayacaktir.
* Phone/smoking object-first ilerler; hand/pose yalniz nesne adayi sonrasinda
  iliskilendirme yardimcisi olabilir.

Bu karar `decision_driver_skeleton_freeze_v1.md` dosyasinda sabitlenmistir.
