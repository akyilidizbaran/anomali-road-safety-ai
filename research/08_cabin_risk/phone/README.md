# Phone Object Baseline

Tarih: 2026-06-14

## Amaç

Telefon nesnesi görünürlüğünü ve telefonla konuşma davranışını iki ayrı kanalda
ölçmek. İlk kanal telefon nesnesini arar; ikinci kanal telefon kapalı/görünmezken
anatomik kol zinciri ve zamansal el-kulak yakınlığını değerlendirir.

Zincir:

`CABIN-EXP-004 YuNet -> driver phone ROI -> YOLO11n COCO cell phone -> temporal candidate metadata`

## Deneyler

* `PHONE-EXP-001`: YOLO11n COCO `cell phone`, driver-focused ROI. `video_2`
  telefonla konuşma pozitifinde false-negative verdiği için seçilmedi.
* `PHONE-EXP-002`: küçük/cam arkası telefon için `video_2` face-near crop'larından
  hazırlanan YOLO11n seed kontrolü. Henüz kabul edilmiş baseline değildir.
* `PHONE-EXP-003`: YOLO26s-P2, 960 px face-near ROI. Yeni ana small-object
  challenger.
* `PHONE-EXP-004`: standard YOLO26s; ayni veride P2 katkisini olcen kontrol.

## Karar Sınırı

* `phone_detected=true` yalnız nesne candidate metadata'sıdır.
* `phone_risk=null` korunur.
* Telefon nesnesinin yokluğu, telefonla konuşma davranışını veto etmez.
* Aynı taraf elin kulak/yüz kenarında zamansal olarak sürmesi
  `phone_call_status=handheld_call_likely` üretebilir.
* Tek kare `hand_near_face` yeterli değildir; kısa yüz dokunmaları candidate kalır.
* Kontrollü negatif review tamamlanana kadar `phone_risk=null` korunur.

## PHONE-CALL-EXP-001 Sonucu

`video_2` icin ViTPose arm-focus + LK kaydi object detector sonucu ile fuse edildi.

* `phone_detected=false`
* `phone_call_status=handheld_call_likely`
* confidence `0.9649`
* hand-near-ear rate `0.9665`
* dominant side `right`, side consistency `0.7158`
* longest sustained interval `3.6 sn`
* causal activation: frame `49` (`~0.98 sn`), once `not_evaluable -> candidate -> likely`

Bu sonuc kullanicinin `video_2` pozitif etiketiyle uyumludur. Deney davranis
candidate'i olarak basarili, ancak kontrollu hard-negative set olmadan secilmis
risk baseline'i degildir.

`PHONE-CALL-EXP-001` generic hand-near-face kullandigi icin superseded'dir.
Sertlestirilmis aday `PHONE-CALL-EXP-002`dir. V2 explicit kulak bantlari, causal
pencere ve hysteresis kullanir. Uc-video sonucunda `video_2=likely`,
`video_1/3=candidate` uretti. Ayrintili karar:

* `decision_phone_call_baseline_v2.md`
* `phone_call_data_collection_plan.md`

## Veri Hazırlama

`prepare_phone_finetune_samples.py`, telefon pozitif aralıklarından full-frame,
driver-phone ROI ve face-near crop çıkarır; manuel bbox annotation CSV'si üretir.

`prepare_phone_specialist_yolo_dataset.py`, bu manuel CSV'yi YOLO detect formatına
çevirir. İlk seed çıktı:

* Dataset: `runs/phone/specialist_datasets/phone_windshield_seed_v1/`
* Kaynak: `runs/phone/finetune_samples/video_2_phone_manual_labels.csv`
* Split: 17 train / 4 val pozitif face-near crop

Bu set tek video ve yalnız pozitif örnek içerdiği için sadece overfit/smoke
challenger hazırlığıdır. Negatifler ve kontrollü telefon-yok/yansıma/yolcu telefonu
örnekleri eklenmeden model baseline seçilmeyecek.

Model arastirma karari ve veri kapisi:

* `deep_research_tiny_phone_detector.md`
