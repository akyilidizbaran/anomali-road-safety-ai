# Vehicle Detection Model Candidates

## Amaç

Araç tespiti için ilk benchmark kısa listesini, model rollerini, lisans risklerini ve neden seçildiklerini kaydetmek.

Bu dosya final model kararı değildir. Final karar `decision_vehicle_detector_v1.md` içinde, proje benchmark sonuçları geldikten sonra verilecektir.

## Kısa Liste

| Model | Varyant | Rol | Neden Dahil | Lisans / Risk | Kaynak |
|---|---|---|---|---|---|
| YOLO11 | `yolo11n` | İlk baseline | Hızlı iterasyon, küçük model, Colab ve MacBook benchmark için pratik başlangıç | AGPL-3.0 / Enterprise; ürünleşme öncesi lisans değerlendirilmeli | https://docs.ultralytics.com/models/yolo11/ |
| YOLO11 | `yolo11s` | Dengeli final adayı | `n` varyantına göre daha yüksek kalite potansiyeli, halen edge için makul boyut | AGPL-3.0 / Enterprise | https://docs.ultralytics.com/models/yolo11/ |
| YOLOv10 | `yolov10n` | Düşük latency baseline | NMS-free yaklaşımın gerçek pipeline etkisini ölçmek için | AGPL-3.0 | https://docs.ultralytics.com/models/yolov10/ |
| YOLOv10 | `yolov10s` | Düşük latency challenger | YOLO11s'e karşı latency/quality rakibi | AGPL-3.0 | https://docs.ultralytics.com/models/yolov10/ |
| YOLOv8 | `yolov8n` | Stabil fallback | Olgun ekosistem ve yaygın kullanım; YOLO11/YOLOv10 sorun çıkarırsa güvenli taban | AGPL-3.0 / Enterprise | https://docs.ultralytics.com/models/yolov8/ |
| RT-DETR | `rtdetr-l` | Transformer challenger | YOLO ailesine karşı farklı mimari ve NMS-free kıyas | Export/latency ve mobil geçiş riski ayrıca ölçülmeli | https://docs.ultralytics.com/models/rtdetr/ |
| NanoDet-Plus | `m` | On-device fallback | Android/on-device zorunluluğu doğarsa hafif alternatif | Lisans resmi repo üzerinden doğrulanmalı | https://github.com/RangiLyu/nanodet |
| YOLOv6Lite | `m` veya `s` | On-device / non-Ultralytics fallback | Ultralytics dışı deploy çizgisini görmek için | GPL-3.0 | https://github.com/meituan/YOLOv6 |

## Kısa Liste Dışında Tutulanlar

| Model | Neden İlk MVP Kısa Listesinde Değil |
|---|---|
| YOLOv7 | Daha eski kod tabanı ve GPL-3.0 lisans yükü; araştırma referansı olabilir ama ilk MVP hattını yavaşlatır. |
| YOLOv9 | Araştırma değeri var, ancak ilk iterasyon için YOLO11/YOLOv10 kadar pratik değil. |
| YOLO-NAS | Güçlü challenger olabilir; pretrained weight kullanım şartları ve non-commercial risk nedeniyle ilk kısa listede tutulmamalı. |
| Faster R-CNN / Cascade R-CNN | Canlı edge pipeline için ağır; research-only referans. |
| DINO / Deformable DETR | Akademik değer yüksek, fakat eğitim/inference karmaşıklığı MVP kapsamına göre fazla. |
| SSD MobileNet / EfficientDet | Mobil klasik baseline olabilir; root vehicle detector kalitesi için ana aday değil. |

## Başlangıç Kararı

İlk çalıştırılacak model: **YOLO11n**.

Gerekçe:

* Colab üzerinde hızlı fine-tune edilir.
* MacBook runtime benchmark için küçük ve pratik başlangıç sağlar.
* Export zinciri güçlüdür.
* İlk hedef final kalite değil, uçtan uca pipeline'ı ölçülebilir hale getirmektir.

## Yeniden Karar Verme Koşulları

YOLO11n aşağıdaki durumlarda baseline olarak değiştirilir:

* MacBook p95 inference latency pipeline bütçesini bozarsa.
* Vehicle ROI crop kalitesi tracking/plaka/evidence için yetersiz kalırsa.
* Export veya runtime bağımlılıkları beklenenden kırılgan çıkarsa.
* Lisans değerlendirmesi yarışma/proje kullanımına uygun bulunmazsa.

## Kaynak Notu

Kaynak URL listesi için `deep_research/sources.md` dosyasına bakılmalıdır.
