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

## Sorulacak Noktalar

* Hangi veri setleri kesin kullanılacak?
* Yerel video çekimi yapılacak mı?
* Türk plaka için sentetik veri üretilecek mi?
