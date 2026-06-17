# 2. Veriseti Oluşturulması

## Resmi Beklenti

Model eğitimi ve testi için verilerin nasıl toplandığı, etiketlendiği, dengelendiği ve artırıldığı açıklanmalıdır. Eğitim/doğrulama/test dağılım oranları gerekçeleriyle verilmelidir.

## Görev Bazlı Veri Stratejisi

| Görev | Veri Kaynağı Adayları | Etiket Türü | Metrik |
|---|---|---|---|
| Araç tespiti | BDD100K, COCO, KITTI, UA-DETRAC | bbox + sınıf | mAP, precision, recall |
| Plaka | CCPD, UFPR-ALPR, AOLP, yerel kontrollü veri | plate bbox | mAP |
| OCR | Plaka crop + sentetik Türk plaka | karakter/metin | plate accuracy, edit distance |
| Şerit | TuSimple, CULane, BDD100K lane | line/mask | IoU, F1 |
| Hava/görüş | ACDC, DAWN, BDD100K weather | sınıf | accuracy, macro F1 |
| Sürücü/cabin | State Farm, AUC Distracted Driver, kontrollü video | sınıf/bbox | F1 |
| Hız | BrnoCompSpeed, AI City, kontrollü video | hız değeri | MAE, RMSE |

## Split

* Önerilen oran: %70 eğitim, %15 doğrulama, %15 test.
* Video-level split zorunludur.
* Aynı videodan çıkan benzer kareler train ve test’e karışmamalıdır.

## Etiketleme

* CVAT: Kontrollü ve akademik veri yönetimi için.
* Roboflow: Hızlı takım çalışması ve YOLO export için.
* Label Studio: Çok görevli etiket yönetimi için.

## Augmentation

* Motion blur.
* Brightness/contrast.
* Fog/rain simulation.
* Compression artifact.
* Perspective transform.
* Random crop.

## COND-EXP-001 Kondisyon Profili Veri Seti Notu

Kondisyon profili sınıflandırıcısı için ilk deneyde BDD100K görüntü metadata alanları kullanılmıştır:

* `weather`
* `timeofday`
* `scene`

Bu alanlar aşağıdaki `condition_profile` sınıflarına dönüştürülür:

| Condition profile | Anlam |
|---|---|
| `day_clear` | Gündüz / normal görüş |
| `night_low_light` | Gece / düşük ışık |
| `low_light_transition` | Şafak, alacakaranlık veya geçiş ışığı |
| `rain` | Yağmur / ıslak görüş koşulu |
| `fog_low_visibility` | Sis / düşük görüş |
| `adverse_other` | Kar, fırtına, tünel/parking gibi karma kötü koşullar |
| `unknown` | Belirsiz veya eksik metadata |

İlk Colab koşusunda MobileNetV3-Small için dengeli örnekleme kullanılmıştır. `fog_low_visibility` sınıfı düşük örnek sayısı nedeniyle FTR'de güçlü performans iddiası için yeterli görülmemelidir; bu sınıf ACDC/DAWN gibi ek adverse-condition veri kaynaklarıyla desteklenmelidir.

Kaynak koşu incelemesi:

* `testing/reports/cond_exp_001_condition_classifier_run_review.md`
* `models/experiments/COND_EXP_001_bdd100k_condition_classifier.md`

## POCR-EXP-005 Plaka Tespiti Veri Seti Notu

Plaka tespiti için ilk kapsamlı fine-tune koşusunda Turkish Number Plates Roboflow v2 ve Roboflow License Plate Recognition v13 kaynakları birleştirilmiştir. Etiketler tek sınıf `license_plate` olarak normalize edilmiş, duplicate/near-duplicate temizliği sonrası deterministik train/validation/test ayrımı üretilmiştir.

| Split | Görüntü | Label |
|---|---:|---:|
| train | 85,039 | 85,039 |
| val | 10,636 | 10,636 |
| test | 10,757 | 10,757 |

Bu veri seti plate bbox tespiti içindir; OCR metni/karakter etiketi içerdiği varsayımıyla raporlanmamalıdır. OCR doğruluğu için ayrı plate crop + metin etiketi veya manuel review süreci gerekir.

Kaynak koşu incelemesi:

* `models/experiments/POCR_EXP_005_plate_detector_report.md`
* `testing/reports/pocr_exp_005_plate_detector_ftr_summary.md`

## POCR-EXP-006/007 OCR Veri Notu

OCR baseline seçimi, ayrı bir OCR eğitim veri setiyle değil, `POCR-EXP-005` plate detector'ın lokal demo videolarından çıkardığı plate crop'lar üzerinde yapılmıştır. Bu aşama model fine-tune değil, OCR motoru seçimi ve temporal voting kullanılabilirlik testidir.

| Kapsam | Değer |
|---|---:|
| Kaynak video | 3 |
| Target track | 3 |
| Plate crop | 613 |
| Ground-truth OCR etiketi | Yok |
| Değerlendirme türü | Local baseline + manual review hazırlığı |

OCR tarafında final doğruluk iddiası için daha sonra etiketli plate crop + metin ground truth veri seti gerekir. Bu aşamada kullanılan 613 crop, CCT-XS / CCT-S / PaddleOCR / EasyOCR karşılaştırması ve temporal stability gate tasarımı için yeterli bir smoke-test materyalidir; geniş genelleme iddiası kurmak için yeterli değildir.

Kaynak koşu incelemesi:

* `models/experiments/POCR_EXP_006_007_cct_xs_ocr_baseline.md`
* `testing/reports/pocr_exp_006_local_ocr_baseline_comparison.md`
* `testing/reports/pocr_exp_007_cct_xs_stability.md`

## Sorulacak Noktalar

* Hangi veri setleri kesin kullanılacak?
* Yerel video çekimi yapılacak mı?
* Türk plaka için sentetik veri üretilecek mi?
