# Araştırma 8 - Sürücü, Yolcu ve Araç İçi Risk Analizi

## Amaç

Görünürlük yeterliyse sürücü/yolcu ve araç içi risk sinyallerini tespit etmek; görünürlük yetersizse analiz yapmama politikasını tanımlamak.

## Alt Başlıklar

* Dışarıdan görünen sürücü tespiti.
* Cam/ön bölge ROI çıkarımı.
* Görünürlük skoru.
* Görünürlük yetersizse analiz yapmama politikası.
* Sürücü var/yok.
* Yolcu sayımı.
* Telefon, sigara, emniyet kemeri.
* Baş/yüz/el konumu.
* Ön camda görüş engelleyici nesne.
* FTR sürücü eylemleri: `telefonla_konusma`, `su_icme`, `arkaya_bakma`,
  `etrafa_bakinma`, `esneme`, `sigara_icme`, `emniyet_kemeri_ihlali`, `slalom`.
* State Farm Distracted Driver.
* AUC Distracted Driver.
* Drive&Act.
* Pose estimation vs object detection.
* False positive riski.

## Çıktı

Cabin risk modülünün MVP mi opsiyonel mi olacağına dair karar.

## Aktif Driver Action Kararı

* `driver_action/driver_action_model_data_research_2026_06_23.md`: FTR
  `sofor_eylemi` alanı için veri/model araştırması ve deney sıralaması.
* `driver_detection/`: Sürücü var/yok ve role-assignment modülü. İlk baseline
  `DRIVER-EXP-001` olarak `CABIN-EXP-004` YuNet summary çıktısından ayrıştırıldı.
* `slalom` cabin-view modeli değildir; dış kamera target-track hareket heuristiği
  olarak `DACT-EXP-001` ile kilitlenir.
* İlk cabin/action deney adayı `DACT-EXP-020B` olmalıdır: State Farm tabanlı
  `telefonla_konusma`, `su_icme`, `arkaya_bakma_candidate` ve hard-negative
  classifier.
* `sigara_icme`, `esneme`, `emniyet_kemeri_ihlali` ve `etrafa_bakinma` ayrı
  uzman veri/model fazları gerektirir; State Farm ile tek başına kapatılmamalıdır.
