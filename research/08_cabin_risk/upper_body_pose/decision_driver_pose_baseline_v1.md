# Decision - Driver Upper-Body / Pose Baseline v1

Tarih: 2026-06-12

## Başlangıç Kararı

Henüz model seçilmedi. İki pretrained aday aynı YuNet cabin artifact'i üzerinde
karşılaştırılacaktır:

| Deney | Model | Rol | Durum |
|---|---|---|---|
| `POSE-EXP-001` | YOLO11n-pose COCO-17 | ana aday | script_ready |
| `POSE-EXP-002` | MediaPipe Pose Landmarker Full | challenger | script_ready |

YOLO11n-pose ilk adaydır; bu ifade seçilmiş baseline anlamına gelmez. Nihai seçim
üç videonun full-rate otomatik sonuçları ve manuel overlay review sonrasında yapılır.

## `POSE-EXP-001` Sonucu

Üç video full-rate çalıştırıldı. İlk otomatik metrik iki omuz confidence eşiğine
dayandığı için `video_1=1.0`, `video_2=0.9617`, `video_3=0.8955` gibi yanıltıcı
analysis-ready oranları üretti.

Tam overlay manuel incelemesi bu sonucu reddetti:

* Uzak karelerde birkaç yüz pikselinden anatomik olarak hatalı pose üretildi.
* Omuz noktaları sık görülse de dirsek ve bilek confidence değerleri çoğu karede
  specialist kullanımı için yetersizdi.
* Yakın karelerde dahi kol çizgileri ve torso geometrisi kararsızdı.
* Otomatik face-pose association, doğru kişiye yakın bir pose kutusu bulmayı ölçtü;
  iskeletin anatomik doğruluğunu ölçmedi.

**YOLO11n-pose COCO-17 reddedildi.** `POSE-EXP-002` öncesinde metrik sözleşmesi
güncellendi:

* `seatbelt_anchor_ready`: yüz-omuz geometrisi + güvenilir torso,
* `phone_anchor_ready`: buna ek olarak en az bir omuz-dirsek-bilek zinciri,
* manuel full-video review zorunluluğu.

## `POSE-EXP-002` İlk Smoke Protokol Düzeltmesi

İlk MediaPipe `video_3` smoke koşusu model seçimi için geçersiz sayıldı. Runner,
MediaPipe `VIDEO` tracking moduna her karede konumu ve boyutu değişen face-anchored
upper-body crop veriyordu. VIDEO mode sabit görüntü koordinat sistemi varsaydığı için
tracker landmark'ları yeni crop koordinatlarına hatalı taşıyabilir.

Runner `IMAGE` mode, yani her dinamik ROI için bağımsız inference kullanacak şekilde
düzeltildi. İlk koşunun `%26.12` seatbelt ve `%21.64` phone anchor oranları
`invalid_protocol` olarak tutulmalı; model kabul veya ret kararı düzeltilmiş smoke
koşusundan sonra verilmelidir.

## `POSE-EXP-002` Düzeltilmiş Smoke Sonucu

MediaPipe Full, bağımsız `IMAGE` inference ile `video_3` üzerinde yeniden çalıştırıldı:

| Metrik | Sonuç |
|---|---:|
| Pose detection rate | 0.7388 |
| Seatbelt anchor rate | 0.2687 |
| Phone anchor rate | 0.2015 |
| Longest analysis miss | 91 kare |
| Mean latency | 41.350 ms |
| P95 latency | 73.716 ms |

Manuel overlay incelemesinde başarılı sayılan yakın karelerde bile iskelet gövde ve
kollara güvenilir biçimde oturmadı. Uzak karelerde anatomik olmayan pose üretimi devam
etti. Bu nedenle düşük anchor oranları yalnız katı eşik kaynaklı değildir.

**MediaPipe Pose Landmarker Full reddedildi.** Üç videoluk full benchmark
çalıştırılmayacaktır.

## İlk Faz Sonucu

Mevcut dış-kamera, cam arkası, küçük ve kısmi driver görüntülerinde iki genel amaçlı
full-body pretrained pose ailesi kabul edilebilir baseline üretmedi:

* YOLO11n-pose: yüksek ama yanıltıcı pose/shoulder oranı, anatomik kararsızlık.
* MediaPipe Full: düşük specialist-anchor coverage ve uzun kopmalar.

Bu sonuç pose probleminin yalnız threshold ayarıyla çözülemeyeceğini gösterdi.
Face-anchored deterministic torso fallback'i denendi; ancak üç videonun tam overlay
incelemesinde kesinti, yanlış geometri ve videolar arası tutarsızlık nedeniyle o da
reddedildi. Bu nedenle torso/seatbelt/phone ilerlemesi durduruldu ve pose araştırması
yeniden açıldı.

## Yeniden Açılan Araştırma - 13 Haziran 2026

Yeni ilk challenger `POSE-EXP-003`, RTMPose-L Body7 384x288 ONNX'tir. Bu seçim:

* YuNet ile zaten belirlenmiş tek sürücü ROI'sine uygun top-down mimari,
* Body7 çoklu veri kümesi eğitimi,
* OCHuman dahil Body8 değerlendirme sonucu,
* küçük hedef için daha yüksek 384x288 giriş çözünürlüğü,
* mevcut ortama MMCV eklemeden resmi ONNXRuntime inference yolu

gerekçelerine dayanır. Bu aday henüz baseline değildir.

İlk araştırma planında RTMPose geçemezse `ViTPose-B`, ardından `RTMO-L Body7`
denenmesi öngörülmüştü. Bu sıra `POSE-EXP-004` RTMW-L üç-video review sonrasında
superseded kabul edildi: generic pose araması artık ana yol değildir. Hiçbir
downstream risk kararı, pose modeli tek başına action anchor ürettiği varsayımıyla
yeniden başlatılmayacaktır.

### `POSE-EXP-003` İlk `video_3` Koşusu

İlk full-rate koşu model açısından umut verici, seçim protokolü açısından geçersizdir:

* 134 evaluable karede 133 driver pose (`0.9925`) üretildi,
* gerçek pose kaybı yalnız 76. karede tek karedir,
* omuz/torso anchor oranı `0.9179` görünse de torso ROI görünür cabin dışındaki
  tahmini kalça noktalarını kullanarak kaportaya taşıyordu,
* `Upper Body=False` ve `0.7 sn miss`, pose kaybını değil phone için gereken
  omuz-dirsek-bilek zincirinin bulunmamasını ölçüyordu.

Runner düzeltildi: upper-body kararı seatbelt/torso anchor'ına bağlandı, phone
zinciri ayrı tutuldu, cabin dışı keypoint'ler anchor sayılmıyor ve torso ROI cabin
alanına clamp ediliyor. Aynı `video_3` komutu yeniden çalıştırılmadan kabul/ret
kararı verilmeyecektir.

### `POSE-EXP-003` Düzeltilmiş `video_3` Sonucu

| Metrik | Sonuç |
|---|---:|
| Pose detection rate | 0.9925 |
| Cabin-clamped upper-body readiness | 0.9179 |
| Phone arm-chain rate | 0.2015 |
| Longest upper-body miss | 2 kare / 0.04 sn |
| Mean / P95 latency | 37.137 / 44.763 ms |
| P95 shoulder jitter | 0.2731 face-width |

Örneklenmiş uzak, orta ve yakın overlay incelemesinde omuzlar önceki modellerden
daha devamlı kaldı. Torso kutusu görünür cabin alanına clamp edildi. Yakın yan açıda
ikinci omuz örtüldüğünde modelin `shoulders_not_visible` ile güvenli biçimde
reddetmesi kabul edildi.

`video_3` smoke aşaması geçici olarak geçti. Bu sonuç baseline seçimi değildir;
`video_1/2/3` full-rate koşusu ve üç tam overlay'in kullanıcı manuel incelemesi
zorunludur.

### `POSE-EXP-003` Üç-Video Nihai Kararı

Tam overlay kullanıcı incelemesinde önceki modellere göre iyileşme görüldü; ancak
kol çizgileri tekrar tekrar kayboldu ve telefonla konuşma pozundaki bükülmüş kol
videolar arasında güvenilir biçimde korunmadı.

| Video | Upper Body | Phone Arm Chain |
|---|---:|---:|
| `video_1` | 0.6684 | 0.1070 |
| `video_2` | 0.9617 | 0.8134 |
| `video_3` | 0.9179 | 0.2015 |

Bu değişkenlik eşik veya temporal smoothing ile güvenli biçimde düzeltilemez:
`video_1/3` karelerinde görünür telefon eli varken dirsek/bilek confidence değerleri
model tarafından düşük üretilmektedir. Smoothing eksik anatomik kanıtı uydurur.

**RTMPose-L Body7 action-grade cabin pose baseline olarak reddedildi.** Torso/seatbelt
ROI açısından güçlü bir referans olarak kalabilir; ortak phone/smoking/seatbelt pose
contract'ının seçilmiş modeli değildir.

### `POSE-EXP-004` Kararı

Sıradaki challenger RTMW-L Cocktail14 WholeBody 384x288 ONNX'tir:

* COCO-WholeBody 133 keypoint üretir,
* UBody ve InterHand dahil Cocktail14 üzerinde eğitilmiştir,
* el landmark ve yüz-yakını el coverage'ı ayrı raporlanacaktır,
* eksik kol noktalarına temporal interpolation uygulanmadan önce ham model kalitesi
  ölçülecektir.

İlk `video_1` koşusunun overlay'i bükülmüş telefon kolunda önceki modelden belirgin
daha iyi geometri gösterdi. Ancak otomatik `%99-100` oranları geçersiz sayıldı:
RTMW body ve hand SimCC başlıklarının ham skor ölçekleri farklı olmasına rağmen ortak
`0.35/0.30` eşikleri kullanılmıştı. Resmi MMPose decoder ham SimCC maksimumlarını
keypoint score olarak korur; bu nedenle skorların 1'i aşması normaldir.

Runner model-spesifik `body=1.5`, `hand=4.5` eşikleri, `1.6` face-width yakınlık ve
hand-root/wrist association ile düzeltildi. Aynı `video_1` koşusu tekrarlanmadan
model kararı verilmeyecektir.

### `POSE-EXP-004` Düzeltilmiş `video_1` Sonucu

`video_1` düzeltilmiş eşiklerle tekrar koşuldu ve smoke aşamasını geçti:

| Metrik | Değer |
|---|---:|
| Evaluable driver frame | 187 |
| Pose detection rate | 1.0000 |
| Seatbelt anchor rate | 0.9679 |
| Phone arm-chain rate | 0.8342 |
| Hand anchor rate | 0.7005 |
| Hand near face rate | 0.5668 |
| Longest upper-body miss | 2 kare / 0.04 sn |
| Mean / P95 latency | 128.548 ms / 211.738 ms |

Overlay incelemesi telefonla konuşma kol geometrisinde RTMPose'a göre belirgin
iyileşme gösterdi. Bu sonuç yalnız `video_1` smoke geçişidir; baseline seçimi için
`video_2` ve `video_3` de aynı protokolle full-rate koşulup tam overlay manuel
review ile incelenecektir.

### `POSE-EXP-004` Üç-Video Kararı

Düzeltilmiş RTMW koşusu üç videoda tamamlandı:

| Video | Pose Rate | Seatbelt Anchor | Phone Arm-Chain | Hand Anchor | Hand Near Face | P95 Jitter |
|---|---:|---:|---:|---:|---:|---:|
| `video_1` | 1.0000 | 0.9679 | 0.8342 | 0.7005 | 0.5668 | 0.2101 |
| `video_2` | 1.0000 | 0.9856 | 0.9856 | 0.9856 | 0.9856 | 0.1952 |
| `video_3` | 1.0000 | 0.9552 | 0.6343 | 0.2388 | 0.0746 | 0.3092 |

Manuel full-overlay review sonucu model action-grade baseline olarak reddedildi.
`video_3` hand ve hand-near-face oranları telefon/sigara anchor'ı için yetersizdir.
`video_2`deki çok yüksek hand-near-face oranları ise manuel görüntüyle uyumlu olmayan
fazla iyimser landmark üretimine işaret eder. Bu nedenle RTMW-L Cocktail14 pretrained
modeli doğrudan downstream phone/smoking/seatbelt pipeline'ına temel yapılmayacaktır.

Model yalnız fine-tune adayı ve karşılaştırma referansı olarak tutulacaktır. Sonraki
adım generic pose modeli aramaya devam etmek yerine kontrollü pozitif-negatif veri,
driver/hand/phone/cigarette/seatbelt etiketleri ve specialist detection/action
benchmark'ıdır.

### `POSE-EXP-005` ViTPose-B Kararı

ViTPose-B, YuNet yüz-anchor'lı ve cabin-clamped ROI üzerinde üç videoda çalıştırıldı.
Manuel incelemede omuz/torso geometrisi önceki pretrained adaylardan daha kararlıydı.
Ancak `video_1/3`te dirsek ve bilek confidence düşüşleri kısa kesintiler üretti.

Bu nedenle model **ham upper-body/torso adayı** olarak tutulur; hand/phone/smoking
baseline'ı sayılmaz. Torso kararını action-grade el takibine bağlamamak gerekir.

### `POSE-EXP-006` Temporal Stabilizasyon Kapısı

`POSE-EXP-006`, yeni bir model değil `POSE-EXP-005` üzerine uygulanan kontrollü
temporal katmandır:

* koordinatlar YuNet yüz merkezine ve yüz genişliğine göre normalize edilir,
* düşük-confidence kayıplar en fazla 200 ms taşınır,
* EMA ile kısa titreşim azaltılır,
* frame başına 1.25 yüz genişliğini aşan sıçramalar reddedilir,
* ham pose varlığı ile taşınmış keypoint sayısı ayrı kaydedilir.

`video_3` stride-10 smoke testi entegrasyon açısından geçti. Final karar ancak üç
video full-rate koşusu ve `POSE-EXP-005/006` tam overlay karşılaştırması sonrasında
verilecektir. Stabilize keypoint, nesne veya risk kanıtı olarak yorumlanmayacaktır.

## Final Karar - `POSE-EXP-009`

ViTPose-B, **driver upper-body/torso baseline** olarak scoped biçimde seçildi.
Tam iskelet veya action-grade pose baseline olarak seçilmedi.

Kabul edilen kullanım:

* YuNet yüzüne bağlı driver kimliği,
* cabin-clamped upper-body ROI,
* omuz ve torso geometrisi,
* seatbelt specialist için torso ROI,
* poor visibility karelerinde evidence-only süreklilik.

Kabul edilmeyen kullanım:

* dirsek/bilekten telefon veya sigara kararı,
* hand landmark yerine pose keypoint kullanımı,
* düşük görünürlük karesinden risk artırımı,
* anatomik olarak kararsız kol çizgilerini temporal olarak uydurma.

Üç-video full-rate torso anchor oranları `0.9305 / 1.0000 / 1.0000`, en uzun
karar-kapsamı kopmaları `0.12 / 0.00 / 0.00 sn` oldu. Arm anchor kapalıdır.
Cabin pose araştırması bu kapsamla kapatılır.

## Karar Metrikleri

* driver-face/pose association doğruluğu,
* pose detection rate,
* analysis-ready rate,
* longest analysis miss run,
* longest analysis miss seconds,
* face-width normalized shoulder jitter,
* omuz ve torso ROI doğruluğu,
* arm keypoint usability,
* mean ve P95 latency,
* false driver-pose association,
* seatbelt ve phone anchor kullanılabilirliği.

## Kabul Eşiği

* Üç videoda sonuç artifact'i üretilmeli.
* `video_3` driver omuzları ve torso ROI tekrar eden karelerde yakalanmalı.
* Yan görünümde yolcu pose'u driver olarak zorla eşlenmemeli.
* `poor/not_visible` ve driver rolü belirsiz kareler final karara katılmamalı.
* Tek kare pose final upper-body kararı sayılmamalı.
* Manuel review olmadan model `selected` yapılmamalı.
* Karar aggregate ortalama yerine üç videonun per-video minimum kalitesine dayanmalı.
