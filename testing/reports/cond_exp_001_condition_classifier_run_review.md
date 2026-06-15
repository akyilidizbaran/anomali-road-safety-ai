# COND-EXP-001 Condition Classifier Run Review

## Amaç

Bu rapor, `COND_EXP_001_BDD100K_MobileNetV3_Condition_Classifier_Colab_outputsaved.ipynb` çıktısının FTR rapor şablonundaki veri seti, model eğitimi, çözüm detayları ve sınama beklentilerini ne ölçüde karşıladığını değerlendirir.

Bu koşu araç tespiti modeli değildir. Yalnız canlı frame için `condition_profile` üretmeyi hedefleyen classifier/router baseline koşusudur.

## Drive Doğrulaması

Google Drive üzerinde doğrulanan ana çıktı dizini:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/condition_profile/COND-EXP-001/
```

Doğrulanan çıktılar:

| Çıktı | Durum | Drive yolu |
|---|---:|---|
| MobileNetV3-Small checkpoint | Var | `runs/condition_profile/COND-EXP-001/train/COND-EXP-001-mobilenet_v3_small/best.pt` |
| Eğitim geçmişi | Var | `runs/condition_profile/COND-EXP-001/train/COND-EXP-001-mobilenet_v3_small/history.csv` |
| Deney özeti | Var | `runs/condition_profile/COND-EXP-001/train/COND-EXP-001-mobilenet_v3_small/summary.json` |
| Backbone karşılaştırması | Var | `runs/condition_profile/COND-EXP-001/summaries/backbone_comparison.csv` |
| Markdown özet | Var | `runs/condition_profile/COND-EXP-001/reports/cond_exp_001_condition_classifier_summary.md` |
| Dark video smoke test | Boş çıktı | `runs/condition_profile/COND-EXP-001/summaries/dark_video_condition_smoke.json` |

Drive proje kökü ayrıca kontrol edildi. Kök dizinde yalnız `runs` ve `datasets` klasörleri görünüyor; `Test/` klasörü ve `video_1` araması sonuç döndürmedi. Bu nedenle dark-video smoke test'in boş kalması model hatasından önce veri yerleşimi eksikliğidir.

## Çalışma Özeti

| Alan | Değer |
|---|---|
| Deney ID | `COND-EXP-001` |
| Model | `MobileNetV3-Small` |
| Başlangıç ağırlığı | ImageNet pretrained TorchVision |
| Veri kaynağı | BDD100K image attributes |
| Sınıflar | `day_clear`, `night_low_light`, `low_light_transition`, `rain`, `fog_low_visibility`, `adverse_other`, `unknown` |
| Runtime hedefi | MacBook local edge/backend için hafif router modeli |
| Eğitim ortamı | Google Colab GPU |
| Checkpoint | `best.pt` |

## Ana Metrikler

| Metrik | Değer |
|---|---:|
| Best epoch | 1 |
| Best validation macro-F1 | 0.6578 |
| Test accuracy | 0.7455 |
| Test macro-F1 | 0.6582 |
| Test weighted-F1 | 0.7444 |
| Mean confidence | 0.7540 |

## Sınıf Bazlı Bulgular

| Sınıf | Precision | Recall | F1 | Test support | Yorum |
|---|---:|---:|---:|---:|---|
| `day_clear` | 0.774 | 0.617 | 0.686 | 412 | Kullanılabilir baseline, transition ile karışıyor. |
| `night_low_light` | 0.836 | 0.855 | 0.845 | 358 | En güçlü sınıflardan biri; demo dark videolar için umut verici. |
| `low_light_transition` | 0.693 | 0.731 | 0.712 | 402 | Gündüz/gece geçişlerinde makul ayrım sağlıyor. |
| `rain` | 0.781 | 0.760 | 0.770 | 366 | İlk baseline için yeterli seviyede. |
| `fog_low_visibility` | 0.200 | 0.200 | 0.200 | 10 | Yetersiz; FTR'de güçlü iddia kurulamaz. |
| `adverse_other` | 0.678 | 0.803 | 0.735 | 346 | Geniş/karma sınıf olduğu için açıklama dikkatli yapılmalı. |

## FTR Şablonu Kapsam Değerlendirmesi

| FTR başlığı | Karşılama durumu | Not |
|---|---|---|
| 2. Veriseti oluşturulması | Kısmen yeterli | BDD100K kaynağı, metadata tabanlı etiket mantığı, sınıf dengelenmesi ve split üretimi var. Metadata duplicate riski için notebook patch'lendi ve tekrar koşu önerilir. |
| 3.1 Problemin analizi | Yeterli | Işık, hava ve görüş koşulunun detection/router üzerindeki etkisi açıklanabilir. |
| 3.2 Çözüm mimarisi | Yeterli | Classifier, detector router'a bağlam sinyali veren ayrı modül olarak konumlandırılabilir. |
| 3.3 Çözüm detayları | Kısmen yeterli | MobileNetV3-Small, preprocessing, sınıf mapping, fallback router anlatılabilir. ONNX/export ve latency ölçümü henüz yok. |
| 4. Çözümün sınanması | Kısmen yeterli | Accuracy, macro-F1, weighted-F1, per-class rapor var. Demo video smoke test boş kaldığı için saha/demo kanıtı eksik. |

## Teknik Uyarılar

1. Notebook çıktısında BDD100K metadata satır sayısı `160000` görünüyor; BDD100K 100K image + label yapısına göre bu, aynı görüntünün image-level ve frame-level kayıt olarak iki kez yazılmış olabileceğini gösterir. Aktif notebook'a dedup guard eklendi.
2. `fog_low_visibility` test support değeri yalnız `10`; bu sınıf için sonuçlar istatistiksel olarak güvenilir değildir.
3. Dark video smoke test boş çıktı. Drive altında `/content/drive/MyDrive/anomali-road-safety-ai/Test/video_1.mp4` - `video_3.mp4` bulunmadan FTR'de demo koşulu kanıtı olarak kullanılamaz.
4. Eğitim sırasında Colab DataLoader multiprocessing cleanup uyarıları görüldü. Aktif notebook default `NUM_WORKERS=0` olacak şekilde güncellendi.

## Karar

Bu koşu, `condition_profile` classifier/router fikrinin çalıştığını ve checkpoint üretilebildiğini gösteren geçerli bir ilk baseline'dır.

Ancak FTR için final kanıt sayılmadan önce aynı notebook güncel patch ile tekrar koşulmalıdır. Ağır bir run açmadan önce öncelik:

1. metadata dedup sonrası split ve metrikleri yeniden üretmek,
2. Drive `Test/` klasörüne 3 demo videoyu koyup dark video smoke test'i çalıştırmak,
3. fog sınıfını güçlü iddia dışında tutmak veya ACDC/DAWN gibi ek veriyle desteklemektir.

## Sonraki Aksiyon

Önerilen sıradaki adım ağır ResNet18 run değildir. Önce patch'lenmiş MobileNetV3-Small run tekrar edilmeli ve dark video smoke test çıktısı alınmalıdır. Bu tekrar koşuda macro-F1 belirgin düşerse veya dark videolarda `night_low_light` baskınlığı görülmezse `RUN_RESNET18=True` challenger koşusu açılmalıdır.
