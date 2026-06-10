# Decision - Defer Fine-Tune and Continue with Pretrained Baselines

Tarih: 2026-06-10

## Karar

Fine-tune kapsamı şimdilik TODO/backlog olarak kaydedilecek. Aktif model geliştirme sırası, fine-tune edilmemiş pretrained modellerle benchmark ve pipeline değerlendirmesi olacak.

## Gerekçe

Mevcut YOLO11n pretrained smoke test, genel araç yakalamanın kullanılabilir seviyede olduğunu gösterdi. Bu aşamada fine-tune'a geçmeden önce farklı pretrained detector ailelerini aynı test koşullarında ölçmek daha verimli:

* model aileleri arasında latency/FPS farkını hızlı görürüz,
* output contract ve evidence crop uyumunu erken test ederiz,
* tracking başlatma için hangi modelin daha stabil bbox/confidence ürettiğini görürüz,
* fine-tune öncesi doğru temel mimariyi seçeriz.

Fine-tune çalışmaları iptal edilmedi. BDD100K Colab hattı korunacak ve ileride tekrar açılacak.

## Aktif Sıra

1. Pretrained YOLO11n baseline zaten çalıştı: `VD-EXP-001`.
2. Aynı dark/manual test videoları üzerinde pretrained challenger modeller çalıştırılacak.
3. Her model için aynı confidence, image size, class filter ve output contract kullanılacak.
4. Manuel review + latency/FPS + detection count + class flicker + evidence crop usability karşılaştırılacak.
5. En iyi pretrained baseline seçildikten sonra tracking entegrasyonuna geçilecek.

## Fine-Tune Backlog

Fine-tune ileride şu kapsamla yapılacak:

* BDD100K download/Drive placement.
* BDD100K -> YOLO conversion.
* Condition-aware general detector fine-tune.
* Baseline vs fine-tuned delta.
* Condition breakdown validation.

Bu kapsamın ana notebook'u:

* `notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb`

## Etkilenen Dosyalar

* `research/02_vehicle_detection/pretrained_baseline_plan.md`
* `research/02_vehicle_detection/benchmark_plan.md`
* `research/02_vehicle_detection/finetune_plan.md`
* `PROJECT_MEMORY.md`

## Alternatifler

* Hemen BDD100K fine-tune'a başlamak.
* Önce condition profile modelini eğitmek.
* Sadece YOLO11n ile devam edip model kıyası yapmamak.
