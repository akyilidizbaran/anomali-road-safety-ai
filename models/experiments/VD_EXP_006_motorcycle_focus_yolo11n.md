# VD-EXP-006 - Motorcycle-Focused Vehicle Detector Improvement

## Final Durum

Durum: **Başarısız / runtime'a terfi ettirilmedi / local artefactleri temizlendi**

Kullanıcı manuel kontrolüne göre `Test/video_1.mp4`, `Test/video_2.mp4` ve
`Test/video_3.mp4` içinde motosiklet görünmesi beklenirken, VD-EXP-006 modeli bu
davranışı güvenilir şekilde sağlayamadı. Model `video_3` içinde sınırlı sayıda
`motorcycle` sinyali üretse de `car` baskınlığı ve yeni `bus` flicker hataları
oluşturdu. Bu nedenle son eğitilen motorcycle-focused model proje kapsamında
geri çekildi.

Karar:

* `VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N` aktif/best detector değildir.
* Son local checkpoint ve local smoke-test çıktıları silindi.
* Google Drive / Colab run klasörü silinmedi; gerektiğinde geriye dönük inceleme
  için korunur.
* Aktif `best.pt`, önceki `VD-EXP-002-GENERAL-YOLO11N` checkpoint'i olarak kalır.
* Bundan sonraki model geliştirme odağı tekrar `car` / genel araç tespiti
  kalitesine döner; motorcycle özel fine-tune şimdilik ertelenir.

Aktif kalan model:

```text
models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

Korunan Colab checkpoint kaydı:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/VD-EXP-006-MOTORCYCLE-FOCUS/train/VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N/weights/best.pt
```

## Amaç

`VD-EXP-002` fine-tuned general YOLO11n modelinde gözlenen motorcycle/car confusion problemini genel veri dağılımında azaltmak.

Bu deney yalnız `Test/video_1-3.mp4` örneklerine uyum sağlamak için tasarlanmaz. Bu üç video sadece qualitative smoke/failure-case materyalidir. Asıl hedef, BDD100K ve gerekiyorsa lisansı doğrulanmış ek public veriler üzerinde genel motorcycle ayrımını iyileştirmektir.

## Tetikleyen Gözlem

Manual review sonucu:

* `Test/video_1.mp4` ve `Test/video_2.mp4`: Ana araç her frame'de doğru tespit ediliyor.
* `Test/video_3.mp4`: Ana araç her frame'de doğru tespit ediliyor.
* `Test/video_3.mp4`: Arka plandaki çok karanlık motosiklet görünür olduğu karelerde sistematik biçimde `car` olarak sınıflandırılıyor.

İlgili kayıtlar:

* `testing/manual_reviews/vd_exp_002_dark_video_manual_review.json`
* `testing/reports/vd_exp_002_motorcycle_class_confusion_action.md`
* `testing/reports/vd_exp_002_dark_video_smoke_test_summary.md`

## Neden Post-Processing Yetmez?

Track-level class voting kısa süreli flicker hatalarını düzeltebilir. Bu vakada hata tutarlı aynı yönde gözlendiği için voting çoğunluğu yine `car` olarak sabitler. Bu yüzden model tarafında motorcycle-focused validation/fine-tune gerekir.

Kısa vadede downstream evidence politikası:

```json
{
  "class_review_required": false,
  "recommended_event_label": "car",
  "raw_detector_class_counts_are_final": true
}
```

Bu politika modeli düzeltmez; detector ne üretiyorsa event/evidence tarafına onu taşır. Hata gözlemi yalnız model geliştirme failure-case'i olarak kullanılır.

## Deney Stratejisi

Başlangıç checkpoint'i:

```text
models/checkpoints/vehicle_detection/VD-EXP-002-GENERAL-YOLO11N-best.pt
```

Colab Drive kaynak checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/VD-EXP-002/train/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/VD-EXP-002/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt
```

Not: VD-EXP-002 summary/registry kayıtlarında `train/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt` yolu görünüyor; Drive araması bazı durumlarda aynı klasörü ara `train/` olmadan da gösterebiliyor. VD-EXP-006 notebook her iki yolu ve lokal checkpoint fallback'ini dener.

Veri:

* BDD100K 4-class vehicle subset.
* `motorcycle` içeren image'lar ayrı indekslenecek.
* `night_low_light` + `motorcycle` kesişimi ayrı validation slice olacak.
* `day_clear` motorcycle örnekleri de korunacak; amaç yalnız dark videoya overfit etmek değildir.
* Mümkünse ek public low-light motorcycle kaynakları araştırılacak; lisans doğrulanmadan training'e eklenmeyecek.

Eğitim yaklaşımı:

1. `VD-EXP-002` general checkpoint'ten devam et.
2. Training sampler içinde `motorcycle` içeren image'ları oversample et.
3. `night_low_light` + `motorcycle` örneklerine kontrollü brightness/contrast/blur augmentation uygula.
4. Validation setini değiştirme; motorcycle-focused slice ayrıca raporla.
5. Same split / same metric protocol kullan.
6. `Test/video_1-3.mp4` yalnız local sanity check olarak çalıştırılır; training/validation seti sayılmaz.

## Colab Veri Hazırlama Notu

VD-EXP-006 veri kaynağı Drive mount içindeki `datasets/bdd100k_vehicle_yolo/images/all` değildir. Google Drive kontrolünde bu klasör ve `labels/all` klasörü boş göründü. Önceki VD-EXP-002 yaklaşımına uygun olarak ağır image/label okuması Colab local diskinde yapılmalıdır.

Beklenen local kaynak:

```text
/content/anomali-road-safety-ai-work/datasets/bdd100k_vehicle_yolo/profiles/general/data.yaml
```

Güncel VD-EXP-006 notebook artık bu hazırlık aşamasını kendi içinde taşır. Notebook başında gömülü `VD-EXP-002 Local Dataset Bootstrap` bölümü bulunur:

* Drive mount ve BDD100K arşiv/cache kontrolü yapılır.
* Arşivler gerekirse Colab local diske kopyalanır.
* BDD100K -> YOLO conversion local `/content/anomali-road-safety-ai-work` altında yapılır.
* `profiles/general/data.yaml` üretilir.
* Eğitim başlatılmaz; eğitim yalnız VD-EXP-006 bölümünde başlar.

Bu yüzden yeni Colab runtime açıldığında ayrı VD-EXP-002 notebook'u manuel çalıştırmak zorunlu değildir; VD-EXP-006 `Run All` ile önce local profile dataset'i hazırlar. Drive'daki boş image/label klasörlerini taramaz.

Local `bdd100k_vehicle_metadata.csv` bulunmazsa notebook mevcut local profile listeleri ve YOLO label dosyalarından sınırlı bir metadata tablosu üretir:

```text
/content/anomali-road-safety-ai-vd-exp-006/metadata/bdd100k_vehicle_metadata_rebuilt_from_profile_lists.csv
```

Bu fallback eğitim için yeterlidir; `car`, `bus`, `truck`, `motorcycle` sayımlarını local YOLO label dosyalarından çıkarır ve train/val/test split bilgisini profile listelerinden üretir.

Sınırlama: Orijinal BDD100K attribute metadata'sı yoksa `condition_profile` alanı `unknown` olur. Bu durumda `night_low_light + motorcycle` validation slice boş olabilir ve notebook bu slice'ı hata vermeden `skipped_empty_slice` olarak raporlar. Bu, motorcycle-focused genel fine-tune'u engellemez; yalnız düşük ışık kırılımı için resmi/önceki metadata yeniden üretildiğinde daha güçlü rapor kanıtı sağlar.

## Metrikler

Zorunlu:

* overall mAP50
* overall mAP50-95
* class AP: `car`, `bus`, `truck`, `motorcycle`
* `motorcycle` precision / recall
* `car -> motorcycle` ve `motorcycle -> car` confusion proxy
* `night_low_light + motorcycle` slice metriği
* MacBook local smoke test FPS / latency

Manual smoke:

* `Test/video_3.mp4` background motorcycle class behavior.
* Ana aracın car detection stabilitesi bozuldu mu?
* False motorcycle üretimi arttı mı?

## Kabul Kriterleri

Deney başarılı sayılmak için:

* `motorcycle` AP/recall artmalı.
* `video_3` background motorcycle her görünür karede `car` olarak kalmamalı.
* Ana araç `car` tespiti bozulmamalı.
* Overall mAP50-95 ciddi düşmemeli.
* Runtime smoke test kabul edilebilir FPS seviyesinde kalmalı.

Başarısız sayılacak durumlar:

* Motorcycle recall artsa bile car false positive/false motorcycle artışı evidence kalitesini bozarsa.
* Ana araç tespiti zayıflarsa.
* İyileşme yalnız 3 örnek videoya overfit görünürse.

## Colab Run Sonucu - 2026-06-15

Kullanıcı tarafından `notebooks/VD_EXP_006_MOTORCYCLE_FOCUS_YOLO11n_Colab_outpassed.ipynb`
olarak kaydedilen output notebook incelendi.

Run durumu:

* Notebook hatasız tamamlandı; `ERRORS []`.
* BDD100K local bootstrap başarılı:
  * Train image: `70000`
  * Val image: `10000`
  * YOLO conversion metadata: `32904` image, `17` kolon
  * General profile: train `23055`, val `4918`, test `4931`
* Eğitim `VD-EXP-002-GENERAL-YOLO11N` checkpoint'inden devam etti.
* Eğitim erken durdu: en iyi sonuç epoch 1'de kaydedildi, patience 8 sonrası early stop.

Colab checkpoint:

```text
/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/VD-EXP-006-MOTORCYCLE-FOCUS/train/VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N/weights/best.pt
```

Google Drive dosya ID:

```text
1ijjO0qs3Rr5ploqtbQ4FDkCbqwMkmZ09
```

Lokal test checkpoint'i artık korunmuyor. Kullanıcı kararı sonrası local VD-EXP-006
checkpoint silindi:

```text
models/checkpoints/vehicle_detection/VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N-best.pt
```

### Validation Metrikleri

| Slice | Images | Instances | mAP50 | mAP50-95 | Precision mean | Recall mean | Motorcycle AP50 | Motorcycle AP50-95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| overall_val | 4918 | 54124 | 0.483 | 0.315 | 0.600 | 0.454 | 0.215 | 0.101 |
| motorcycle_val | 151 | 1826 | 0.545 | 0.363 | 0.653 | 0.490 | 0.366 | 0.162 |
| night_motorcycle_val | 27 | 276 | 0.587 | 0.355 | 0.855 | 0.531 | 0.366 | 0.116 |

Yorum:

* Motorcycle-focused slice üzerinde `motorcycle` AP50, overall slice'a göre daha iyi görünmektedir.
* Ancak overall validation'da motorcycle sınıfı hâlâ düşük kalmaktadır: precision `0.404`, recall `0.267`, AP50 `0.215`.
* Bu sonuç, motorcycle ayrımı için bir sinyal verdiğini ancak modelin final/promoted detector olarak kabul edilmesi için yeterli olmadığını gösterir.
* Early stopping'in epoch 1'de en iyi modeli seçmesi, oversampling/fine-tune ayarlarının daha dengeli tekrar ele alınması gerektiğine işaret eder.

## Local Dark Video Smoke Test - 2026-06-15

VD-EXP-006 checkpoint'i local MacBook ortamına indirildi ve `Test/video_1-3.mp4` üzerinde
tam video smoke test çalıştırıldı.

Bu local çıktıların kalıcı tutulmasına karar verilmedi. Kullanıcı kararı sonrası
local checkpoint, annotated video çıktıları, JSON summary ve smoke-test Markdown
raporu temizlendi. Colab/Drive tarafı silinmedi.

Silinen local artefactler:

```text
models/checkpoints/vehicle_detection/VD-EXP-006-MOTORCYCLE-FOCUS-YOLO11N-best.pt
runs/vehicle_detection/VD-EXP-006-motorcycle-focus-dark-smoke/
runs/detect/runs/vehicle_detection/VD-EXP-006-motorcycle-focus-dark-smoke/
models/benchmarks/artifacts/VD-EXP-006-motorcycle-focus-yolo11n-dark-smoke-summary.json
testing/reports/vd_exp_006_motorcycle_focus_dark_video_smoke_test_summary.md
```

VD-EXP-002 -> VD-EXP-006 karşılaştırması:

| Video | VD-EXP-002 class counts | VD-EXP-006 class counts | Yorum |
|---|---|---|---|
| `video_1` | `car:598` | `car:641` | Ana araç detection korunuyor; motorcycle yok. |
| `video_2` | `car:645` | `car:587` | Ana araç detection korunuyor; toplam car sayısı azaldı. |
| `video_3` | `car:611`, `motorcycle:6` | `car:659`, `motorcycle:12`, `bus:7` | Motorcycle sinyali arttı; ancak car/bus flicker hâlâ var. |

Manuel değerlendirme:

* VD-EXP-006, `video_3` içinde soldaki karanlık objeyi bazı karelerde `motorcycle`
  olarak işaretledi.
* Ancak kullanıcı değerlendirmesine göre `video_1`, `video_2` ve `video_3` içinde
  motosiklet görünmesi beklenirken model bu ihtiyacı karşılamadı.
* `car` baskınlığı devam etti ve ek olarak `bus` flicker oluştu.
* Bu sonuç BDD100K tabanlı motorcycle-focused denemenin bu amaç için yeterli
  olmadığını gösterdi.
* Bu nedenle model promoted edilmedi; aktif best checkpoint `VD-EXP-002` olarak
  bırakıldı.

Runtime:

* MacBook MPS ile yaklaşık `27-30 FPS` aralığında smoke test tamamlandı.
* Bu hız, lokal demo için umut verici smoke-test sinyalidir; ancak final runtime iddiası değildir.

## Rapor Dili

Kullanılacak ifade:

> Düşük ışıkta motosiklet sınıf ayrımı için ayrı bir failure-case iyileştirme deneyi tasarlanmıştır.

Kaçınılacak ifade:

> Motorcycle/car problemi tamamen çözüldü.

Bu deney tamamlanana kadar `VD-EXP-002` raporlarında motorcycle/car confusion, model geliştirme failure-case'i olarak korunur; runtime event/evidence ise raw detector sınıfını taşımaya devam eder.

2026-06-15 nihai değerlendirme:

> Motorcycle-focused fine-tune denemesi, beklenen motosiklet görünürlüğünü güvenilir
> şekilde sağlayamadığı ve class stability'yi bozduğu için başarısız kabul edilmiştir.
> Model runtime'a terfi ettirilmez; aktif best detector `VD-EXP-002-GENERAL-YOLO11N`
> olarak kalır.
