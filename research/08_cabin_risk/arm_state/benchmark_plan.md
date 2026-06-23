# Driver Arm-State Benchmark Plan

Tarih: 2026-06-14

## Sabit Girdiler

* Driver identity: `CABIN-EXP-004` OpenCV YuNet 2026may.
* Torso baseline: `POSE-EXP-009`; yalnız torso kapsamı değişmez.
* Arm observations: `POSE-EXP-010`, arm-focus ViTPose-B.
* Video seçimi için `frame_stride=1`.

## Deneyler

### `POSE-EXP-010`

YuNet yüzüne göre daraltılmış arm-focus ROI üzerinde ViTPose-B ham gözlemleri.
Amaç, geniş cabin crop'unda kaporta/koltuk üzerinde oluşan yanlış insan geometrisini
azaltmaktır. Bu deney tek başına baseline değildir.

### `POSE-EXP-011`

Model: `yolo11n-pose.pt`, tek sınıf `person`, COCO-17 keypoint.

İlk `POSE-EXP-001` YOLO11n-pose deneyi genel upper-body ROI ile reddedilmişti.
Arkadaş ekipten gelen başarılı görünen örneğin YOLO11n-pose + farklı ROI/post-process
olabileceği anlaşıldığı için aynı ağırlık yeni `driver_arm_focus` ROI ile yeniden
ölçülür. Eski reddedilen deneyin üzerine yazılmaz.

`video_3` sonucunda continuous arm-state için uygun bulunmadı:
available state `0.3209`, longest miss `0.94 sn`. Ancak arkadaş ekip bilgisindeki
kullanım biçimi doğru not edildi: YOLO pose doğrudan karar modeli değil, telefon
veya sigara nesne adayı sonrasında ilişkilendirme yardımcısıdır.

### `ARM-EXP-001`

`POSE-EXP-010` veya seçilecek başka arm observation kaynağını ileri-geri sparse
Lucas-Kanade optical flow ile
birleştirir. Kimlik, sürücü bölgesi, kemik uzunluğu ve kısa taşıma kapıları
uygulanır; 9 karelik temporal state voting yapılır.

### VLM / Llama Adayı

Arkadaş ekipten gelen tek-kare overlay, Llama ailesiyle görsel yorumlama yapıldığını
gösteriyor olabilir. Bu hat pose yerine doğrudan seçilmeyecek; önce exact model,
prompt, input crop ve JSON çıktısı istenir. Uygunsa VLM teacher/audit ya da
object+arm challenger olarak ayrı deney açılır.

## Otomatik Metrikler

* decision-evaluable frame count,
* available state rate,
* state başına temporal oran,
* optical-flow recovered frame count,
* longest unavailable run,
* state transition count,
* identity reset count,
* mean/P95 ek arm-state latency.

## Kabul Kapısı

* Üç video full-rate tamamlanmalı.
* Her video manuel `overall_pass=yes` almalı.
* Görünür sürücü kolu varken açıklanamayan kayıp 0.5 saniyeyi aşmamalı.
* Kaporta, koltuk, yolcu veya yansıma üzerinde kalıcı kol zinciri olmamalı.
* El-yüz ve kol-yukarı durumları gerçek hareketle zamansal olarak uyuşmalı.
* Beklenen wheel zone çıktısı direksiyon teması olarak raporlanmamalı.
* Tek bir videodaki başarı diğer videoları ortalamayla maskelememeli.

Kabul edilene kadar karar:
`candidate_not_selected_pending_manual_review`.
