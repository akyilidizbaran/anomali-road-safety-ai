# Driver Upper-Body / Pose Benchmark Plan

Tarih: 2026-06-13

## Sabit Girdi

* Cabin artifact:
  `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* Driver face baseline: OpenCV YuNet 2026may.
* Source videos: `Test/video_1.mp4`, `video_2.mp4`, `video_3.mp4`.
* Final model-selection koşuları: `frame_stride=1`.
* Smoke test için stride kullanılabilir; seçim kararı için kullanılamaz.

## Deneyler

### `POSE-EXP-001`

* Model: `yolo11n-pose.pt`
* Keypoint contract: COCO-17.
* Amaç: çok kişili, instance-bbox tabanlı upper-body ana baseline.

### `POSE-EXP-002`

* Model: MediaPipe Pose Landmarker Full.
* Keypoint contract: 33 landmark; benchmark ortak alanlara normalize edilir.
* Amaç: dense landmark ve video tracking challenger.

### `POSE-EXP-003`

* Model: RTMPose-L Body7, 384x288, SimCC, ONNXRuntime.
* Keypoint contract: COCO-17.
* Girdi: YuNet yüz-anchor'lı tek-driver upper-body ROI.
* Amaç: kısmi/örtülü ve küçük sürücü görünümü için ana yeni challenger.

Üç-video tam inceleme sonucu: yüz/omuz/torso devamlılığı önceki modellerden daha
iyi olsa da action-grade kol zinciri videolar arasında tutarlı değildir. Phone
arm-chain oranları `video_1=0.1070`, `video_2=0.8134`, `video_3=0.2015` olduğu için
reddedildi.

### `POSE-EXP-004`

* Model: RTMW-L Cocktail14 WholeBody, 384x288, ONNXRuntime.
* Keypoint contract: COCO-WholeBody 133.
* Eğitim kapsamı: UBody ve InterHand dahil Cocktail14.
* Ek metrikler: güvenilir hand landmark frame rate ve hand-near-face frame rate.
* Amaç: bükülmüş kol, telefon eli ve yüz yakınındaki el hareketleri için action-grade
  upper-body/hand challenger.

### Sonraki Adaylar

`POSE-EXP-004` üç-video manuel review sonrasında action-grade baseline olarak
reddedildi. Upper-body/driver torso baseline araştırması kapanmamıştır.

Yeni pose adayı ancak aşağıdaki durumlarda açılacak:

* aday modelin cabin/driver/hand senaryosunda RTMW'den belirgin farklı bir yeteneği
  resmi model card veya ön testle gösterilebiliyorsa,
* partial-body, occlusion ve küçük driver görünümüne yönelikse,
* el-kol devamlılığı ve anatomik doğruluk üç videoda doğrudan ölçülebiliyorsa,
* fine-tune gereksinimi ve veri ihtiyacı açıkça belgelenebiliyorsa.

ViTPose-B, RTMO-L ve driver-monitoring odaklı upper-body modelleri yeniden
karşılaştırılacaktır. Sıradaki deney, araştırma ve kabul kriterleri kaydedilmeden
başlatılmayacaktır. Phone/seatbelt/smoking downstream fazları bu kararın sonrasındadır.

### `POSE-EXP-005`

* Model: Hugging Face `usyd-community/vitpose-base-simple`, COCO-17.
* Girdi: YuNet yüz-anchor'lı, cabin alanına clamp edilmiş tek-driver ROI.
* Sonuç: üç-video full-rate incelemede torso/omuz anchor'ı önceki adaylardan daha
  kararlı bulundu; ancak `video_1/3` kol zincirlerinde kısa confidence kayıpları var.
* Rol: ham ViTPose-B referansı; phone/smoking hand modeli değildir.

### `POSE-EXP-006`

* Model: `POSE-EXP-005` ile aynı ViTPose-B ağırlıkları.
* Ek katman: yüz-relative EMA smoothing, en fazla 200 ms confidence dropout taşıma
  ve frame başına 1.25 yüz genişliğini aşan keypoint sıçramasını reddetme.
* Ham pose varlığı, taşınan keypoint sayısı ve reddedilen sıçrama sayısı ayrı
  kaydedilir; stabilizasyon yeni action kanıtı üretmiş sayılmaz.
* Kabul: üç video `frame_stride=1`, ham/stabilize overlay karşılaştırması, torso
  kopmalarında azalma ve yanlış kol pozunun 200 ms'den uzun taşınmaması.

### `POSE-EXP-007`

* Kök neden: `video_3` kopmalarında ham ViTPose bilek skorları çoğunlukla
  `0.08-0.29` aralığına düşüyor; koordinatlar tamamen kaybolmuyor.
* Yöntem: yalnız yüksek güvenle başlatılmış eklem için `0.10` hysteresis devam
  eşiği, frame başına `0.45` yüz genişliği hareket kapısı ve 500 ms üst sınır.
* Görselleştirme: düşük-confidence takip turuncu, ham güvenilir pose mor çizilir.
  Cabin sınırı dışındaki eklemler çizilmez ve action anchor sayılmaz.
* `video_3` ilk sonuç: phone arm-chain `0.7015 -> 0.9254`; orta mesafedeki
  47-55 ve 133-153 kopmaları kapandı. 232-239 yakın/partial-view aralığı güvenli
  biçimde unavailable kalır.

### `POSE-EXP-008`

* Kök neden: `video_3` 169-224. karelerde YuNet yüz confidence değeri
  `0.90-0.94` iken cabin visibility `poor` olduğu için pose inference tamamen
  kapatılıyordu.
* Düzeltme: güvenilir driver yüzü (`>=0.80`) bulunan `poor` karelerde pose
  evidence-only çalışır; visibility gate risk/seatbelt/phone kararını kapalı tutar.
* Overlay etiketi `pose: evidence-only` olur. Bu kareler temporal risk oranlarının
  paydasına veya pozitif kararına girmez.

### `POSE-EXP-009` - Seçilen Final Kapsam

* Model: ViTPose-B + YuNet face anchor + cabin-clamped ROI.
* Temporal: omuz/torso için 200 ms hold ve yüz-relative smoothing.
* Görünürlük: güvenilir yüz bulunan poor karelerde evidence-only inference.
* Render: yalnız omuz-kalça torso geometrisi; dirsek/bilek çizilmez.
* Arm/hand kararları: devre dışı; phone/smoking kanıtı sayılmaz.
* Seçim kapsamı: driver upper-body/torso ve sonraki seatbelt ROI üretimi.

Üç-video full-rate sonucu:

| Video | Torso Anchor | Longest Miss | P95 Jitter | Evidence-only |
|---|---:|---:|---:|---:|
| `video_1` | 0.9305 | 0.12 sn | 0.1459 | 38 |
| `video_2` | 1.0000 | 0.00 sn | 0.0827 | 43 |
| `video_3` | 1.0000 | 0.00 sn | 0.0954 | 88 |

Bu scoped baseline seçilmiştir. Torso araştırması kapatılır; action-grade kol
problemi ayrı driver arm-state fazında ele alınır.

### `POSE-EXP-010` - Arm-Focus Gözlem Modeli

* Model: ViTPose-B.
* ROI: YuNet yüzüne göre daraltılmış, cabin içine clamp edilmiş arm-focus bölgesi.
* Rol: `ARM-EXP-001` için ham omuz/dirsek/bilek gözlemi üretmek.
* Seçim kapsamı: torso baseline'ı değiştirmez ve tek başına risk üretmez.

### `POSE-EXP-011` - YOLO11n-Pose Arm-Focus Retest

* Model: `yolo11n-pose.pt`.
* Sınıf: `person`.
* Keypoint: COCO-17.
* ROI: `driver_arm_focus`.
* Gerekçe: `POSE-EXP-001` aynı ağırlığı genel ROI ile reddetti; arkadaş ekip
  örneğinin başarısı ROI/post-process farkından kaynaklanıyor olabilir.
* Rol: arm-state observation challenger; seçilmiş baseline değildir.

## Otomatik Metrikler

* processed/evaluable frame count,
* driver pose frame count ve rate,
* analysis-ready frame count ve rate,
* longest analysis miss run,
* longest analysis miss seconds,
* ardışık güvenilir omuz orta noktalarının yüz genişliğine normalize mean/P95 jitter'ı,
* shoulder/hip visibility,
* best frame, torso bbox ve upper-body ROI,
* mean/P95 pose latency.

## Manuel Review

`testing/templates/manual_driver_pose_review.csv` ile:

* upper-body ROI driver gövdesini kapsıyor mu,
* yolcu pose'u driver yüzüne yanlış eşleniyor mu,
* omuz ve torso kutusu gerçek anatomiyle uyumlu mu,
* dirsek/bilek anchor'ları phone specialist için kullanılabilir mi,
* torso ROI seatbelt specialist için yeterli mi,
* uzun kopmalar ve false positive sayıları kabul edilebilir mi.

## Zorunlu Kabul Kapısı

Bir model ancak aşağıdaki koşulların tamamında baseline olabilir:

* üç videoda `frame_stride=1` koşusu tamamlanmış olmalı,
* üç videonun her biri manuel `overall_pass=yes` almalı,
* hiçbir videoda 0.5 saniyeden uzun açıklanamayan analysis kopması olmamalı,
* anatomik olarak yanlış iskeletler yüksek detection rate ile maskelenmemeli,
* videoların birindeki başarı diğer iki videodaki başarısızlığı ortalamayla
  kapatmamalı; karar per-video minimum üzerinden verilmeli,
* model seçilmeden deterministic torso, seatbelt veya phone fazına geçilmemeli.

## Çıktılar

* `models/benchmarks/artifacts/POSE-EXP-00X-*-summary.json`
* `testing/reports/pose_exp_00X_pose_summary.md`
* `runs/cabin_pose/pose_exp_00X/annotated/`
* `runs/cabin_pose/pose_exp_00X/rois/`
* `models/benchmarks/cabin/driver_pose_baseline_comparison.csv`
