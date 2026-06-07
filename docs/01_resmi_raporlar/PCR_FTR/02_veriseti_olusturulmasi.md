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

## Sorulacak Noktalar

* Hangi veri setleri kesin kullanılacak?
* Yerel video çekimi yapılacak mı?
* Türk plaka için sentetik veri üretilecek mi?
