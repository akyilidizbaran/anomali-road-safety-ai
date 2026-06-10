# Pretrained Vehicle Detector Baseline Plan

## Amaç

Fine-tune'a geçmeden önce pretrained detector modellerinin proje pipeline'ı içindeki gerçek davranışını ölçmek.

Bu faz, model eğitimi yapmaz. Sadece hazır ağırlıklarla inference, latency, output contract, manual review ve evidence/tracking uygunluğu ölçer.

## Neden Şimdi?

VD-EXP-001 YOLO11n pretrained testinde genel araç yakalama kullanılabilir göründü. Bazı false negative ve kısa süreli `car -> motorcycle` flicker var, ancak bu hatalar fine-tune'a başlamadan önce farklı pretrained modellerle kıyaslanmalı.

Bu kıyas şunları belirler:

* hangi model ailesi daha stabil bbox/confidence üretiyor,
* hangi model MacBook üzerinde daha iyi latency/FPS veriyor,
* hangi model evidence crop ve tracking init için daha uygun,
* fine-tune ileride hangi model ailesinden başlamalı.

## Test Verisi

Başlangıç test seti:

* `Test/video_1.mp4`
* `Test/video_2.mp4`
* `Test/video_3.mp4`

Bu videolar:

* Git'e eklenmez,
* training verisi değildir,
* dark/low-light smoke test ve manual review materyalidir,
* gerektiğinde benchmark sonrası silinebilir.

## Sabit Inference Protokolü

Tüm modeller aynı protokolle çalıştırılır:

| Alan | Değer |
|---|---|
| Source | `Test/video_1-3.mp4` |
| Input size | `640` |
| Confidence | `0.25` başlangıç |
| Classes | `car`, `motorcycle`, `bus`, `truck` |
| Device | MacBook MPS varsa `mps`, yoksa CPU |
| Save video | Evet, local `runs/` altında |
| Save labels/conf | Evet |
| Git storage | Hayır, yalnız küçük özet JSON/CSV |

## Pretrained Model Deneyleri

| Deney | Model | Durum | Amaç |
|---|---|---|---|
| `VD-EXP-001` | `YOLO11n` | Completed | İlk pretrained baseline |
| `VD-EXP-008` | `YOLO11s` | Planned | Daha yüksek kalite, latency tradeoff |
| `VD-EXP-009` | `YOLOv10n` | Planned | NMS-free / low-latency challenger |
| `VD-EXP-010` | `YOLOv8n` | Planned | Stabil fallback kıyası |
| `VD-EXP-011` | `RT-DETR` lightweight/available variant | Optional | Farklı mimari sanity check |

`YOLOv10s` ve daha büyük modeller yalnız ilk tur sonuçları düşük kalırsa denenir.

## Ölçülecek Metrikler

Makine ölçümü:

* processed frame count,
* frames with detection,
* detection frame ratio,
* total detection count,
* class counts,
* min/max/mean confidence,
* mean inference ms,
* p95 inference ms,
* wall-time FPS,
* output video/label path.

Manuel review:

* visible vehicle count,
* correct detection count,
* missed vehicle count,
* false positive count,
* wrong class flicker,
* bbox usable count,
* evidence crop usable count,
* tracking init usable,
* short qualitative notes.

## Karar Kriteri

Pretrained baseline seçimi yalnız en yüksek detection count'a göre yapılmaz.

Öncelik sırası:

1. Araç varlığını kaçırmama / recall hissi.
2. BBox'un evidence ve tracking için kullanılabilir olması.
3. Class flicker'ın kısa ve temporal voting ile yönetilebilir olması.
4. False positive seviyesinin düşük kalması.
5. MacBook p95 latency ve FPS.
6. Output contract dönüşümünün kolay olması.
7. Lisans/export riski.

## Sonraki Faz

Pretrained baseline seçildikten sonra sıradaki önerilen faz:

1. ByteTrack benzeri tracking entegrasyonu.
2. Track-level class voting ve confidence smoothing.
3. Single target / risk candidate selection.
4. Event/evidence JSON üretimi.
5. Sonra fine-tune backlog'a dönüş.

Bu sıra, mevcut manuel review'da görülen kısa `car -> motorcycle` flicker'ı doğrudan hedefler.
