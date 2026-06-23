# Decision - Cabin / Driver Baseline v1

Tarih: 2026-06-12

## İlk Aday Kararı

İlk Cabin/Driver baseline, risk sınıflandırması yerine **visibility-gated face/occupant
detection** olarak kurulacaktır.

* Ana model: MediaPipe BlazeFace full-range.
* Challenger: MediaPipe BlazeFace short-range.
* Driver rolü: açık view-profile policy.
* Temporal eşik: en az 3 driver candidate kare ve görünür karelerde en az 0.30 oran.
* Telefon/kemer/sigara: `not_run`.

## Benchmark Sonucu

`CABIN-EXP-001` ve `CABIN-EXP-002`, aynı üç video ve aynı protokolle tamamlandı.

| Model | Face detection rate | Driver bulunan video | Mean ms | P95 ms | Manuel sonuç |
|---|---:|---:|---:|---:|---|
| BlazeFace full-range | 0.5769 | 3/3 | 2.799 | 3.286 | Stride-5 ön sonuç |
| BlazeFace short-range | 0.2462 | 1/3 | 1.242 | 2.045 | Stride-5 ön sonuç |

Full-range örneklenen karelerde göreli olarak daha iyi olsa da arka koltuktaki
yolcular güvenilir biçimde tespit edilmemektedir. Overlay'deki düzenli kutu kaybının
önemli bölümü stride kaynaklıdır ve model devamlılığı olarak yorumlanamaz.
Short-range özellikle `video_1` ve `video_2` üzerinde sırasıyla `0.1489` ve `0.16`
yüz tespit oranında kalmıştır.

## Nihai BlazeFace Kararı

İlk koşular `frame_stride=5` ile yapıldığı için overlay devamlılığı doğru
değerlendirilememiştir. Full-range model daha sonra `frame_stride=1` ile `968`
hedef kare üzerinde tekrar çalıştırılmıştır.

Full-rate sonuçta aggregate yüz tespit oranı `0.6136` kalmış, `video_2` üzerinde
görünür karelerde `39` karelik kesintisiz yüz kaçırma serisi oluşmuş ve tüm
videolarda occupant tahmini `1` kalmıştır. Manuel inceleme de arka yolcuların
kaçırıldığını doğrulamıştır.

**BlazeFace full-range reddedildi.** Short-range stride-5 sonucu `0.2462` ile
full-range'in çok altında kaldığı için ek full-rate koşu yapılmadan reddedildi.
Yeni ana challenger OpenCV YuNet 2026may modelidir. `CABIN-EXP-003`, kabul edilen
model belirlenene kadar çalıştırılmayacaktır.

## YuNet Sonucu

`CABIN-EXP-004` üç videoda ve `frame_stride=1` ile tamamlandı.

| Metrik | BlazeFace full-range | YuNet 2026may |
|---|---:|---:|
| Aggregate face detection rate | 0.6136 | 0.9101 |
| Driver detected video | 3/3 | 3/3 |
| Mean face latency | 2.635 ms | 25.802 ms |
| Global P95 face latency | 2.902 ms | 62.056 ms |

YuNet gerçek arka yolcu yüzlerini de tekrar eden karelerde yakalamıştır. Destekli
temporal occupant hesabıyla `video_1=2`, `video_2=2`, `video_3=1` sonucu oluşmuştur.
Yan görünümde birden fazla yüz olduğunda sürücü rolü zorla atanmaz; bu kareler
`side_view_multiple_faces_role_ambiguous` olarak tutulur.

## Nihai Baseline Kararı

**OpenCV YuNet 2026may, Cabin/Driver pretrained baseline olarak seçildi.**

Karar dayanakları:

* Aggregate face detection rate `0.9101`.
* Üç videoda temporal driver candidate üretmesi.
* `video_1/2` üzerinde gerçek ikinci occupant yüzlerini yakalaması.
* Kullanıcının üç overlay videosunda sonucu kullanılabilir bulması.
* MIT lisansı ve mevcut OpenCV runtime'ına doğrudan uyumu.

YuNet'in `poor` görünürlük karelerinde ürettiği tespitler yalnız overlay/evidence
devamlılığı için tutulur; temporal driver veya risk kararına katılmaz. SCRFD artık
aktif challenger değil, YuNet'in kontrollü veri veya yeni kamera koşullarında
yetersiz kaldığı kanıtlanırsa açılacak yedek adaydır.

Fine-tune hedefi doğrudan bu ONNX dosyasını eğitmek zorunda değildir. Gelecekte
YuNet baseline metriklerini aşması gereken domain-adapted bir face/upper-body
detector eğitilebilir veya SCRFD gibi eğitilebilir bir aileye geçilebilir.

## Gerekçe

Mevcut kamera dışarıdandır. Sürücü görünürlüğü koşullu olduğu için görünürlük kapısı
olmadan telefon veya kemer kararı üretmek yanlış pozitif riskini yükseltir. Full-range
model dış kamera ve geniş görüntü için daha uygun başlangıç adayıdır; short-range aynı
protokolde ölçülebilir challenger olarak tutulur.

## Event Etkisi

`driver_cabin` alanı visibility, occupant ve driver candidate metadata ile
zenginleştirilir. Occupant varlığı risk skorunu veya fusion confidence değerini
değiştirmez.

## Yeniden Karar Koşulları

Yeniden model seçimi için:

* Driver yüz kutusu temporal olarak kararlı olmalı.
* Görünür arka yolcular occupant sayımına dahil edilmeli.
* `video_1-3` manuel overlay incelemesi geçilmeli.
* Görünürlük yetersiz karelerden driver kararı üretilmemeli.
* Kontrollü veri setinde YuNet baseline'ın altında kalmayan bir challenger bulunmalı.
