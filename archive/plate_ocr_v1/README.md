# Plate/OCR v1 Archive

Tarih: 2026-06-11

Bu klasör, plaka/OCR hattının **ilk denemesinde** üretilen iş ürünlerini saklar. Kullanıcı kararıyla plaka tarafına **sıfırdan** başlandığı için bu materyaller aktif `scripts/` ve `models/benchmarks/artifacts/` ağaçlarından buraya taşınmıştır. Referans/iz amaçlı tutulurlar; aktif değildirler.

## İçerik

* `scripts/extract_plate_ocr_target_rois.py` — eski target ROI crop/sample/clip çıkarma script'i. Tek `best_frame` + örneklenmiş (interpolasyonlu) `bbox_history_sample` üzerinden crop üretiyordu.
* `artifacts/POCR-EXP-001-target-roi-crops-summary.json` — eski crop extraction smoke-test özeti.
* `reports/pocr_exp_001_target_roi_crops_summary.md` — eski crop extraction raporu.

## Ham görseller / klipler

Crop görselleri ve ROI klipleri KVKK gereği Git'e eklenmez. Bu yüzden ham çıktılar burada değil, git-ignore'lu yolda saklanır:

```
runs/_archive/plate_ocr_v1_POCR-EXP-001-target-roi-crops/
```

## Neden yeni yaklaşım

* Eski yaklaşım hedef aracın yalnız `best_frame` + örneklenmiş kareleri üzerinde çalışıyordu; bbox'lar tam değil, interpolasyonluydu.
* Manuel incelemede 3 hedef event'in 2'sinde (video_1, video_2) `best_frame` aracın **yan profilini** gösteriyor ve plaka hiç görünmüyordu. Yalnız `best_frame` plaka görünürlüğünü temsil etmiyor.
* Yeni yaklaşım: hedef track'in **tespit edildiği her karede** araç ROI'sini yeniden çalıştırılan detector+tracker'dan alıp doğrudan plaka tespiti yapar; iki plaka modelini karşılaştırır (`scripts/benchmarks/run_plate_detection_smoke.py`).
