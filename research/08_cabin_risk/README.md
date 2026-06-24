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
* `driver_action/RUN_DACT_EXP_020B.md`: State Farm tabanlı ilk driver-action
  classifier notebook'unun çalıştırma planı, sınıf eşlemesi, çıktı path'leri ve
  başarı kriterleri.
* `driver_action/RUN_DACT_EXP_020C_EXTERNAL_VIDEO_SMOKE.md`: İç-kabin
  verisiyle eğitilen `DACT-EXP-020B` modelini 3 yol/dış-kamera demo videosunda
  domain-transfer smoke test olarak çalıştırma planı.
* `../../testing/reports/dact_exp_020c_external_video_smoke.md`:
  `DACT-EXP-020C` dış-kamera smoke test sonucu. Karar:
  `should_emit_driver_action=false`; skorlar yalnız cabin/driver visibility +
  temporal gate sonrası diagnostic specialist olarak kullanılabilir.
* `../../testing/reports/dact_exp_020b_full_run_review.md`: `DACT-EXP-020B`
  full run incelemesi ve baseline kilit kararı. Aktif checkpoint:
  `DACT-EXP-020B-efficientnet_b0-best.pth`.
* `driver_detection/`: Sürücü var/yok ve role-assignment modülü. İlk baseline
  `DRIVER-EXP-001` olarak `CABIN-EXP-004` YuNet summary çıktısından ayrıştırıldı.
* `slalom` cabin-view modeli değildir; dış kamera target-track hareket heuristiği
  olarak `DACT-EXP-001` ile kilitlenir.
* İlk cabin/action baseline `DACT-EXP-020B` olarak kilitlendi: State Farm
  tabanlı EfficientNet-B0 classifier, `telefonla_konusma`, `su_icme`,
  `arkaya_bakma_candidate` ve hard-negative sınıflarını üretir.
* `DACT-EXP-020B` dış kamera videolarında doğrudan final eylem kararı olarak
  kullanılmayacak. `DACT-EXP-020C` sonucu full-frame / target-vehicle /
  cabin-candidate modlarında domain transfer riskini doğruladı; dış kamera
  event/evidence JSON'a final action yazmak için cabin/driver görünürlük kapısı
  zorunlu.
* `sigara_icme`, `esneme`, `emniyet_kemeri_ihlali` ve `etrafa_bakinma` ayrı
  uzman veri/model fazları gerektirir; State Farm ile tek başına kapatılmamalıdır.
