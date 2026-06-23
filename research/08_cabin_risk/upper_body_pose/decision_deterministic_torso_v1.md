# Decision - Deterministic Driver Torso Baseline v1

Tarih: 2026-06-12

## Gerekçe

YOLO11n-pose ve MediaPipe Pose Landmarker Full, dış-kamera ve cam arkası kısmi
driver görüntülerinde reddedildi. Genel full-body pose modelleri seatbelt/phone
specialist modülleri için güvenilir omuz, dirsek ve bilek anchor'ları üretmedi.

Yeni baseline insan pozu tahmin etmez:

`YuNet driver face -> view-profile torso geometry -> quality gate -> temporal torso ROI`

## `TORSO-EXP-001`

* Driver kimliği: seçilen YuNet yüzü ve mevcut view-profile role assignment.
* Geometri: yüz genişliği/yüksekliği katsayıları.
* Sınır: target vehicle bbox ve frame sınırı.
* Kalite: yüz çözünürlüğü, torso crop çözünürlüğü, kırpılmadan kalan alan ve yüz
  confidence.
* Temporal davranış: responsive bbox smoothing, usable/limited oranı ve kesintisiz
  miss serisi.

Bu ROI yalnız specialist model girdisidir. Yeşil kutu:

* sürücünün anatomik pose'unu,
* emniyet kemeri taktığını,
* telefon kullandığını

iddia etmez.

## Seçim Kriterleri

Üç overlay manuel incelenmeden baseline seçilmiş sayılmaz:

* göğüs ve iki omuz bölgesi yeterince kapsanmalı,
* seatbelt diyagonalinin geçeceği bölge crop içinde olmalı,
* yolcu mümkün olduğunca dışarıda kalmalı,
* kapı/kaput gibi araç dış yüzeyi crop'u baskılamamalı,
* hareket boyunca kutu sürücünün arkasında kalmamalı,
* küçük/uzak yüzler güvenli biçimde `not_usable` olmalı.

## Sonraki Kullanım

Baseline kabul edilirse:

1. Kontrollü kemerli/kemersiz videolar torso crop olarak etiketlenir.
2. Seatbelt specialist detector/classifier aynı crop sözleşmesi üzerinde benchmark edilir.
3. Telefon için torso crop, YuNet yüzü ve ayrı phone/hand detector ilişkisi kullanılır.

## İlk Üç-Video Koşusu Sonrası Düzeltme

İlk koşu üç videoda `usable_torso_rate=1.0` üretti. Manuel örnek incelemesi bunun
geçerli bir başarı olmadığını gösterdi: torso alt sınırı yalnız target vehicle bbox'a
göre clamp edildiği için özellikle yakın karelerde kaput/kapı dış yüzeyi crop'a fazla
giriyordu.

Geometri şu şekilde düzeltildi:

* Alt sınır cabin ROI altı + profil bazlı yüz yüksekliği ile sınırlandı.
* Cabin dışındaki dikey crop oranı kalite metriğine eklendi.
* `side_driver_window` dış-taşma eşiği `0.45`.
* `front_lhd` kısa windshield ROI nedeniyle `0.80`.

İlk summary model-selection için geçersizdir; düzeltilmiş runner ile yeniden
üretilmelidir.

İkinci üç-video koşusu cabin sınır düzeltmesini doğruladı. Ancak manuel uzak/orta/yakın
örnek incelemesi iki ek kalibrasyon gerektirdi:

* `min_face_dimension`: `20 -> 40` piksel. Bu eşik `video_1/2` evaluable karelerini
  korurken `video_3` üzerindeki kemer detayının çözülemediği uzak yüzleri reddeder.
* Torso alt ölçeği: side `4.2 -> 2.7`, front `4.4 -> 2.9` yüz yüksekliği. Göğüs ve
  seatbelt hattı korunurken kapı/kaput alanı azaltılır.

Bu değerler deterministic torso v1 final kalibrasyonudur. İkinci summary de
model-selection için final değildir; son bir yeniden koşu gerekir.

## Final v1 Sonucu

Final üç-video koşusu `40 px` yüz kapısı ve `2.7/2.9` torso yüksekliğiyle tamamlandı.

| Video | Evaluable | Usable | Usable rate | Longest miss |
|---|---:|---:|---:|---:|
| `video_1` | 187 | 187 | 1.0000 | 0 |
| `video_2` | 209 | 209 | 1.0000 | 0 |
| `video_3` | 134 | 57 | 0.4254 | 69 |

Toplam usable oranı `453/530 = 0.8547` oldu. `video_3` üzerinde `36 px` yüz
reddedilirken `40 px` sınırında torso penceresi açıldı. Yakın sahnede cabin/vehicle
kırpılması arttığında sonuç tekrar `not_usable` oldu.

Uzak, orta ve yakın örneklerin görsel incelemesinde:

* `video_1/2` torso kutusu sürücünün göğüs ve seatbelt bölgesini takip etti,
* final kutu yüksekliği kapı/kaput kontaminasyonunu azalttı,
* `video_3` çözülemeyen uzak kareleri güvenli biçimde reddetti,
* usable sonucu seatbelt var/yok kararı olarak yorumlanmadı.

## Nihai Manuel Karar

Sampled kare incelemesi tam video davranışını temsil etmedi. Kullanıcı üç overlay
videosunun tamamında kesintiler, yanlış yerleşimler ve videolar arasında belirgin
tutarsızlık gözlemledi.

**Deterministic torso v1 reddedildi.** Bu deney pose baseline yerine geçmez ve
seatbelt/phone specialist aşamasına geçiş için yeterli anchor kabul edilmeyecektir.
Aktif çalışma yeniden upper-body/pose model araştırmasına döner.
