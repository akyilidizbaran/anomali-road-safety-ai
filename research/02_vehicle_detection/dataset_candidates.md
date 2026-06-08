# Vehicle Detection Dataset Candidates

## Amaç

Araç tespiti modülünde kullanılacak veri setlerini görev rolüne göre ayırmak, sınıf haritalamasını netleştirmek ve lisans doğrulama zorunluluğunu kaydetmek.

## Veri Kullanım Kararı

Bu projede yerel veri ana eğitim kaynağı olmayacaktır. Ana plan:

1. Public/pretrained modellerle sıfır fine-tune baseline.
2. Açık veri setleriyle road-domain fine-tune.
3. Fixed-camera veri setleriyle domain uyarlama ve test.
4. Gerekirse izole ortamda sınırlı kendi telefon videosu ile final acceptance test.

Ham veri, frame crop, plaka görüntüsü ve evidence görselleri Git'e eklenmez.

## Veri Seti Rolleri

| Dataset | Rol | Neden | Kullanım Aşaması | Kaynak |
|---|---|---|---|---|
| COCO | Pretrained başlangıç | Genel nesne ön-eğitimi ve hazır ağırlıklar | Baseline | https://cocodataset.org/ |
| BDD100K | Ana road-domain fine-tune | Driving videos, farklı hava/ışık/çevre koşulları | İlk fine-tune | https://github.com/bdd100k/bdd100k |
| UA-DETRAC | Fixed-camera adaptation + test | Trafik videosu, occlusion/weather/truncation notları | İkinci aşama ve tracking-readiness | https://arxiv.org/abs/1511.04136 |
| KITTI | External sanity test | Dashcam-style dış doğrulama | Final public test | https://www.cvlibs.net/datasets/kitti/ |
| CityFlow | Fixed-camera robustness | Çok kamera trafik görüntüsü, trafik akışı ve bbox | Sabit kamera robustness | https://arxiv.org/abs/1903.09254 |
| VisDrone | Small-object robustness | Uzak/küçük araç zorluğu | Opsiyonel alt test | Kaynak/lisans ayrıca doğrulanmalı |
| Kendi telefon videosu | Final acceptance / demo check | Hedef kamera geometrisinin gerçek karşılığı | Sınırlı, izole, repo dışı | Lokal kısıtlı veri |

## Sınıf Haritalaması

MVP sınıfları:

* `car`
* `bus`
* `truck`
* `motorcycle`

Önerilen mapping:

| Kaynak Sınıf | MVP Sınıfı | Not |
|---|---|---|
| `car` | `car` | Doğrudan |
| `bus` | `bus` | Doğrudan |
| `truck` | `truck` | Doğrudan |
| `motorcycle`, `motorbike` | `motorcycle` | Veri setine göre isim normalize edilmeli |
| `van`, `pickup` | `car` veya ignore | Dataset kararında tutarlı seçilmeli |
| `person`, `rider`, `bicycle` | vehicle detection dışında | Araç dışı kullanıcı modülüne ayrılmalı |
| `other vehicle` | ignore veya mapped | Veri kalitesi bozuluyorsa ignore |

## Split Politikası

* Split image-level değil video-level yapılmalıdır.
* Aynı videodan gelen frame'ler train/val/test arasında bölünmemelidir.
* Varsayılan oran: 70/15/15.
* Final acceptance test kilit tutulmalı; model seçiminde tekrar tekrar kullanılmamalıdır.

## Lisans Kontrolü

Her veri seti için aşağıdaki alanlar `data/README_assets/dataset_inventory_template.csv` veya görev bazlı dataset card içinde doldurulmalıdır:

* Kaynak URL
* Lisans
* Kullanım amacı
* Redistribution izni
* Kişisel veri riski
* Citation
* Download tarihi
* Kullanılan subset

## Önemli Kısıt

Maskeleme yapılmayacağı için plaka/yüz içeren görüntüler raporda veya repoda açıkça paylaşılmamalıdır. Görsel kanıt gerekirse kontrollü, izinli ve kişisel veri riski azaltılmış örnekler seçilmelidir.
