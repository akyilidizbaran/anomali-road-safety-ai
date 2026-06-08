# Araç Tespiti Modülü İçin Derin Araştırma Raporu

> Not: Bu dosya araç tespiti için derin araştırma arka planıdır. Uygulanacak kararlar ve şablonlar üst klasördeki aksiyon dosyalarına ayrılmıştır. Kaynak URL listesi `sources.md` içinde tutulur.

## Üst Düzey Sonuç ve Başlangıç Kararı

GitHub deposundaki mevcut mimari tanımı, araç tespitini açık biçimde ilk odak modül, yani tüm algı hattının kök bileşeni olarak konumlandırıyor; repo README’sinde “ilk odak araç tespiti olacak” ifadesi yer alıyor ve MVP sırası araç tespiti → hedef araç takibi → plaka tespiti/OCR → evidence card generation şeklinde tanımlanıyor. Aynı doküman, sistemin telefon kamerasından gelen canlı görüntüyü edge destekli yapay zekâ hattında analiz ederek risk skoru ve evidence package üreten bir karar destek sistemi olduğunu da belirtiyor. Bu nedenle araç tespiti modülü yalnızca “bir dedektör” değil, downstream modüllerin tamamının veri kalitesini belirleyen temel katmandır.

Pratik başlangıç önerim şudur: **ilk deney modeli olarak YOLO11n ile başlayın**. Bunun nedeni yalnızca güncel doğruluk değil; aynı zamanda Ultralytics ekosisteminde hazır ön-eğitimli ağırlık, eğitim/doğrulama/tahmin/export desteği, Android ve edge açısından zengin export hedefleri, Colab üzerinde hızlı deneme kolaylığı ve küçük parametre/FLOPs profiliyle çok daha hızlı iterasyon imkânı sunmasıdır. YOLO11 dokümantasyonunda yolo11n için COCO üzerinde 39.5 mAP, 2.6M parametre ve 6.5B FLOPs; yolo11s için 47.0 mAP, 9.4M parametre ve 21.5B FLOPs raporlanmaktadır. Aynı sayfa, YOLO11’in edge cihazlara ve farklı dağıtım ortamlarına uygunluğunu özellikle vurgular.

İlk karşılaştırma paketi olarak **YOLO11s**, **YOLOv10n/s**, **YOLOv8n/s**, **RT-DETR**, ve gelecekte olası telefonda-çalıştırma zorunluluğuna karşı **NanoDet-Plus** veya **YOLOv6Lite** ailesinden en az bir mobil aday birlikte benchmark edilmelidir. YOLOv10 dokümantasyonunda YOLOv10n için 39.5 AP ve 1.84 ms, YOLOv10s için 46.8 AP ve 2.49 ms raporlanırken; YOLOv8 dokümantasyonunda YOLOv8n için 37.3 mAP ve 3.2M parametre, YOLOv8s için 44.9 mAP ve 11.2M parametre raporlanır. RT-DETR dokümantasyonunda RT-DETR-L için 53.0 AP ve T4 üzerinde 114 FPS verilir; ancak bu avantaj daha büyük model maliyeti ve transformer tabanlı dağıtım riskiyle gelir. NanoDet-Plus repo sayfası ise mobil ARM CPU üzerinde 97 FPS, 980 KB INT8 / 1.8 MB FP16 model boyutu ve Android demo desteği bildirir.

Bugünkü bilgi durumuyla **en iyi MVP başlangıç noktası YOLO11n**, **en olası dengeli final adayı YOLO11s**, **en güçlü düşük-gecikme rakibi YOLOv10s**, **en güvenli geri dönüş tabanı YOLOv8n/s**, **mobil odaklı yedek aday ise NanoDet-Plus-m veya YOLOv6Lite-M/S** görünmektedir. Fakat bu sonuç yalnızca kamuya açık benchmarklardan çıkarılmış ön seçimdir; nihai model kararı mutlaka sizin kendi telefon kamera verinizde, kendi edge makinenizde ve kendi JSON/evidence/tracking hattınız içinde ölçülmelidir. Repo’nun kendi geliştirme yaklaşımı da zaten model seçiminin doğruluk, hız, latency, model boyutu ve export kolaylığına göre yapılacağını söylüyor.

Bir kritik not daha var: **lisans riski**. Ultralytics YOLOv8, YOLO10 ve YOLO11 sayfaları AGPL-3.0/enterprise lisans modelini belirtir; YOLOv6 ve YOLOv7 repoları GPL-3.0 lisanslıdır; YOLO-NAS dokümanı ise kütüphanenin Apache-2.0 olduğunu, fakat ön-eğitimli ağırlıkların non-commercial kullanım şartı taşıdığını söyler. Bu, yarışma prototipi ile gelecekte kapalı kaynak ticari ürün yolunun aynı şey olmadığını gösterir. Teknik olarak en iyi model ile lisans açısından en rahat model mutlaka aynı model olmayabilir.

## Araç Tespitinin Projedeki Rolü ve Çıktı Sözleşmesi

Depodaki açıklamaya göre sistem; araç, plaka, hız, şerit, sahne/görüş, yol durumu, araç dışı kullanıcı ve koşullu kabin risk sinyallerini analiz eden modüler bir karar destek sistemi olarak tasarlanmıştır. Aynı doküman, ilk odak alanın araç tespiti olduğunu ve sonraki modüllerin bunun üzerine ekleneceğini net biçimde söyler. Bunun anlamı şudur: **araç tespiti modülünün kaçırdığı her hedef**, takip, hedef araç seçimi, plaka OCR, hız kestirimi, evidence üretimi ve risk füzyonu zincirinde eksik veya yanlış bilgiye dönüşür; benzer biçimde **sahte pozitifler** de gereksiz takip başlatır, yanlış plaka alanı kırpar ve gerekirse kritik mod veya uzman model orkestrasyonunu boş yere tetikleyebilir.

Bu proje için araç tespiti modülünün girdisi, canlı video akışından gelen kare, kare numarası ve zaman damgasıdır. Çıkışı ise downstream modüllerin hemen tüketebileceği, olay uyumlu bir tespit listesi olmalıdır. Repo README’de sistemin evidence package ürettiği ve evidence kartları oluşturduğu açıkça yazılıdır; dolayısıyla tespit çıktısı yalnızca ekrana bbox çizmek için değil, sonradan açıklanabilir kanıt zinciri üretmek için de saklanabilir ve yeniden oynatılabilir olmalıdır.

Araç tespiti için beklenen minimum sözleşmeyi aşağıdaki gibi sabitlemek doğru olur:

```json
{
  "frame_id": 1520,
  "timestamp_utc": "2026-06-08T12:34:56.789Z",
  "source": {
    "camera_id": "android_back_cam_01",
    "resolution": [1280, 720]
  },
  "detections": [
    {
      "detection_id": "det_001",
      "class_name": "car",
      "class_id": 0,
      "bbox_xyxy": [320, 180, 760, 540],
      "bbox_xywh": [540, 360, 440, 360],
      "area_px": 158400,
      "confidence": 0.93,
      "detection_quality_score": 0.90,
      "model_version": "vehicle_detector_yolo11n_v1"
    }
  ]
}
```

Burada hem `bbox_xyxy` hem `bbox_xywh` saklamak anlamlıdır. `xyxy`, kırpma ve evidence görüntüsü üretimi için daha doğrudan; `xywh` ise tracking, merkez noktası hesabı, hız ve hedef araç seçimi gibi modüllerde daha pratiktir. `confidence` tek başına karar vermemeli, eşikler sınıfa ve sahne koşuluna göre kalibre edilmelidir. Hiç araç bulunamadığında `detections: []` dönülmeli; bu durum pipeline’da “hata” değil, geçerli bir algılama sonucu olarak işlenmelidir. Bu yapı ayrıca tracker başlatma, seçili hedefin idame ettirilmesi ve evidence ekranında son 10 yakalamanın düzgün sunulması için teknik olarak en temiz temeli sağlar. Bu yaklaşım, repo’nun evidence akışı ve modüler AI hattı yaklaşımıyla doğrudan uyumludur.

## Aday Model Aileleri ve Kısa Liste

### Ailelerin Pratik Değerlendirmesi

**YOLO11 ve YOLOv8 ailesi**, bu proje için en güvenli mühendislik başlangıcıdır. Resmî Ultralytics dokümantasyonu bu ailelerin detection için train/val/predict/export modlarını desteklediğini; export tarafında ONNX, OpenVINO, TensorRT, CoreML, TFLite, NCNN, QNN, ExecuTorch gibi birçok hedefi sunduğunu gösteriyor. YOLO11n ve YOLO11s, mAP/parametre dengesi açısından özellikle dikkat çekicidir; YOLOv8 ise biraz daha eski olmasına rağmen çok olgun araç zinciri sunduğu için “stabil fallback” rolüne çok uygundur. Dezavantaj: YOLOv8 ve YOLO11 için resmî akademik makale yok; performans verileri üretici dokümantasyonundan geliyor.

**YOLOv10**, gecikme öncelikli düşünülmesi gereken ailedir. Dokümantasyonunda NMS-free uçtan uca yaklaşım, one-to-one inference head ve düşük latency odağı açıkça anlatılır. Bu tasarım downstream tracking ve hedef araç seçimi açısından teorik olarak avantajlıdır; çünkü duplicate bbox, NMS davranışı ve post-processing gecikmesi üzerindeki yükü azaltabilir. Ancak burada en doğru cümle şudur: YOLOv10’un bu avantajı, sizin kendi export/inference zincirinizde ölçülmeden kabul edilmemelidir. Kamu benchmarklarında hızlı olması, sizin Mac edge makinenizde, sizin çözünürlüğünüzde, sizin kendi pipeline post-process’inizde aynı farkı vereceği anlamına gelmez.

**YOLOv6**, mühendislik tarafında ciddiye alınması gereken ama ana başlangıç hattı olması gerekmeyen bir ailedir. Çünkü repo sayfası bu modeli “industrial applications” için tasarlanmış olarak sunuyor; ayrıca ONNX, OpenVINO, TensorRT, NCNN ve Android başlıklarını doğrudan listeliyor. Üstelik YOLOv6Lite için mobil benchmark da verilmiş durumda. Eğer Ultralytics dışındaki bir yol da aynı anda araştırılacaksa, YOLOv6/YOLOv6Lite ikinci kulvardaki güçlü adaydır. Dezavantajı, ekipte tek bir standart eğitim/export API’si etrafında ilerlemeyi zorlaştırabilmesi ve lisans yükünün GPL tarafına kaymasıdır.

**YOLOv7 ve YOLOv9**, araştırma değeri taşıyan güçlü referanslardır; ancak ilk MVP için en iyi başlangıç değillerdir. YOLOv7, kendi döneminde gerçek zamanlı algılamada çok güçlü sonuçlar üretmiştir ve repo’su ONNX/TensorRT/CoreML export yolları da içerir; fakat artık daha eski bir kod tabanıdır. YOLOv9 ise PGI ve GELAN ile iyi fikirler getirmiş, fakat Ultralytics dokümantasyonu eğitim kaynak ihtiyacının YOLOv8 muadillerine göre daha uzun olabileceğini açıkça belirtir. Bu nedenle kısa iterasyon gereken MVP aşamasında ana rota yapılmaları gereksiz risk yaratır.

**RT-DETR**, projedeki en anlamlı transformer rakibidir. RT-DETR sayfası efektif hibrit encoder, IoU-aware query selection, NMS-free yapı ve decoder katman sayısını değiştirerek yeniden eğitmeden hız doğruluk ayarı yapabilme özelliğini vurgular. Bu, edge/backend odaklı bir ilk sürüm için teknik olarak çekicidir. Fakat mobil yola geçiş, quantization, export sorunsuzluğu ve inference stack olgunluğu CNN tabanlı YOLO ailesi kadar rahat değildir. Bu nedenle RT-DETR, “hemen ilk deney” değil, **YOLO kısa listesine karşı test edilmesi gereken transformer challenger** rolündedir.

**NanoDet, SSD MobileNet, MobileDet, EfficientDet-D0/D1** gibi hafif aileler, “telefon üzerinde inference zorunlu olursa” senaryosunda değerlidir. NanoDet repo’su Android demo, ncnn/MNN/OpenVINO backend’leri, çok küçük dosya boyutu ve mobil ARM CPU hızı bildiriyor. TensorFlow Model Zoo ise SSD MobileNet V2 FPNLite 640 ve EfficientDet-D0/D1 için hazır COCO ağırlıkları ve bazı hız/başarım rakamları listeliyor. Ancak bu ailelerin çoğu, araç tespitinin bu projedeki “root module” rolü düşünüldüğünde genellikle ana edge modeli değil, **mobil fallback** olarak daha mantıklıdır. Bunun nedeni, kök modülün downstream hatalara çok güçlü etki etmesidir; küçük model kazanımı bazen yanlış tetiklenmiş onlarca sonraki hataya dönüşebilir.

### Yoğunlaştırılmış aday tablo

Aşağıdaki tablo, kamuya açık ve resmî/yarı-resmî kaynaklardan toplanan **başlangıç karşılaştırma setini** özetler. Farklı kaynaklarda hız ölçümleri farklı donanım ve runtime ile verildiği için yalnızca tek başına doğrudan kıyas kabul edilmemelidir; asıl kararı sizin kendi benchmark’ınız verecektir.

| Model | Temsilî varyant | Kaynakta raporlanan metrik | Deploy durumu | Lisans durumu | Bu proje için rol |
|---|---|---|---|---|---|
| YOLO11 | n / s | n: 39.5 mAP, 2.6M params, 6.5B FLOPs; s: 47.0 mAP, 9.4M params, 21.5B FLOPs; detection için export destekli. | Ultralytics export ile ONNX, TensorRT, OpenVINO, CoreML, TFLite, NCNN, QNN vb. yol açık. | AGPL-3.0 / enterprise. | **MVP ana aday** ve büyük olasılıkla **final ana aday** |
| YOLOv10 | n / s | n: 39.5 AP, 2.3M params; s: 46.8 AP, 7.2M params; NMS-free yapı ve T4 FP16 düşük latency. | Ultralytics export destekli. | AGPL-3.0. | **Düşük-latency rakibi**, özellikle final için challenger |
| YOLOv8 | n / s | n: 37.3 mAP, 3.2M params; s: 44.9 mAP, 11.2M params; olgun eğitim/export hattı. | Ultralytics export destekli. | AGPL-3.0 / enterprise. | **Stabil fallback baseline** |
| YOLOv6 | S / Lite-M | YOLOv6-S: 45.0 mAP; YOLOv6Lite-M: 25.1 mAP, mobil benchmark verilmiş. ONNX/OpenVINO/TensorRT/NCNN/Android listeleniyor. | Güçlü deploy odağı; Android/NCNN yolunda iyi. | GPL-3.0. | **Mobil-kenarlı mühendislik adayı**, fakat ana rota değil |
| YOLOv7 | base | COCO test: 51.4 AP, batch1 161 FPS; ONNX/TensorRT/CoreML export örnekleri repo’da var. | Legacy ama zengin repo. | GPL-3.0. | **Araştırma referansı**, ilk MVP için fazla legacy |
| YOLOv9 | s / c | YOLOv9s 46.8 AP, YOLOv9c 53.0 AP; eğitim kaynak ihtiyacının YOLOv8’e göre artabileceği notu mevcut. | Ultralytics tarafında destek var ama ana akışta daha az pratik. | Kaynakta açık lisans bilgisi ayrıca doğrulanmalı; proje içinde ölçülmeli. | **Araştırma-only / secondary baseline** |
| YOLO-NAS | S | YOLO-NAS S: 47.5 mAP, 3.21 ms; INT8 varyant da raporlanıyor. | ONNX/TensorRT/OpenVINO üretim uyumluluğu vurgulanıyor. | Kütüphane Apache-2.0; pretrained weights non-commercial. | **Güçlü challenger**, ama lisans nedeniyle dikkatli |
| RT-DETR | L | 53.0 AP, 114 FPS; decoder katmanı azaltılarak 8.0 ms / 52.7 mAP → 7.4 ms / 52.5 mAP trade-off’u veriliyor. | Train/val/predict/export destekli. | Lisans proje entegrasyonuna göre ayrıca kontrol edilmeli. | **Transformer challenger**, ilk MVP ana rota değil |
| NanoDet-Plus | m / 1.5x | 34.1 mAP, 2.44M params, 4.7MB FP16; mobil ARM CPU üzerinde 25.49 ms; Android demo mevcut. | ncnn/MNN/OpenVINO/Android güçlü. | Apache-2.0. | **Mobil fallback**, edge-root model için doğruluk limiti olabilir |
| SSD MobileNet / EfficientDet | V2 FPNLite 640 / D0-D1 | SSD MobileNet V2 FPNLite 640: 28.2 COCO mAP; EfficientDet-D0: 33.6, D1: 38.4. | TF ekosisteminde taşınabilir. | Apache 2.0 tabanlı TensorFlow Model Garden. | **Mobil-uyumlu klasik baseline**, fakat ana kalite adayı değil |
| Faster R-CNN / Cascade / DINO / Deformable DETR | R50 vb. | Faster R-CNN R50 640: 29.3 mAP / 53 ms; DINO R50: 49.4 AP in 12 epochs, 51.3 AP in 24 epochs; Deformable DETR 10x daha hızlı convergence bildiriyor. | Daha ağır eğitim/inference maliyeti. | Çeşitli; proje başına ayrıca doğrulanmalı. | **Research only**, ilk MVP için önerilmez |

Pratik kısa listeyi ben şu şekilde sabitlerim: **YOLO11n**, **YOLO11s**, **YOLOv10n**, **YOLOv10s**, **YOLOv8n**, **RT-DETR-L**, ve “telefon içi fallback” için **NanoDet-Plus-m** veya **YOLOv6Lite-M**. Bu listede YOLO11n hızlı iterasyon için, YOLO11s kalite artışı için, YOLOv10s gecikme rakibi için, YOLOv8n/s güvenlik ağı için, RT-DETR-L transformer referansı için, NanoDet/YOLOv6Lite ise gelecekte gerçek on-device inference gerekirse koruma amacıyla bulunur.

## Veri Seti Stratejisi ve Alan Uyumu

### Veri seti ailelerinin projeye uygunluğu

Bu projede araç tespiti kararı yalnızca “en büyük veri seti hangisi” sorusuyla verilmemelidir. Çünkü sizin kamera geometriniz klasik internet görüntüsü değil; canlı yol videosu, muhtemelen sabit yol kenarı telefonu veya trafik kamerası benzeri senaryo, bazen de telefon kamerasından demoda canlı akış üretilecek. Bu yüzden genel nesne verisi ile yol alanı verisi arasında bilinçli katmanlama gerekir. COCO, Microsoft’un genel nesne veri setidir; 328 bin görüntüde 2.5 milyon etiketli örnek içerir ve 91 nesne tipiyle geniş ön-eğitim avantajı sunar. Ancak alan olarak genel sahne verisidir; bu yüzden road-domain fine-tune için tek başına yeterli değildir.

BDD100K bu proje için en önemli veri kaynaklarından biridir. Makalesi, 100 bin sürüş videosu ve coğrafi/çevresel/hava koşulu çeşitliliğini özellikle vurgular. Bu, gündüz-gece, yağmur, görüş değişimi ve gerçek sürüş bağlamında öğrenme için çok değerlidir. Özellikle telefon-dashcam benzeri bakış açısı açısından BDD100K, COCO’dan çok daha yakındır. Bu nedenle “yol alanına ilk gerçek adaptasyon” için benim birinci önerim BDD100K’dır.

UA-DETRAC, sabit trafik sahnesi ihtiyacınız için çok önemlidir. Makalesi 100 zorlu trafik videosu, 140 binden fazla kare ve hava durumu, perdeleme, truncation ve araç kategorisi gibi zengin anotasyonlar içerdiğini söyler. Eğer yarışma demosunda kamera zaman zaman yol kenarından sabit bakacaksa, UA-DETRAC araç tespiti ve özellikle tracking-readiness açısından BDD100K’yı çok iyi tamamlar. BDD100K daha çok sürüş videosu çeşitliliği sunarken, UA-DETRAC daha çok trafik-video ve gözetim benzeri dinamikleri getirir.

KITTI, daha eski ama hâlâ faydalı bir dış test setidir. Resmî site; verinin şehir içi, kırsal ve otoyol sürüşlerinden toplandığını, yüksek çözünürlüklü stereo video kameralar ve ek sensörlerle gerçek dünya benchmark’ı sunmayı amaçladığını belirtir. Bu veri, özellikle “dashcam benzeri açıya genelleme” kontrolü için uygundur. Ancak günümüz trafik yoğunluğu ve çeşitliliği açısından BDD100K veya Waymo kadar büyük ve çeşitli değildir; yani ana eğitim seti değil, daha çok **haricî doğrulama / sanity check** öneririm.

Cityscapes, nuScenes ve Waymo açık veri dünyasında çok güçlü referanslardır ama bunları projeye “hepsini yükleyelim” mantığıyla almak doğru değildir. Cityscapes 50 şehirden stereo urban sekanslar, 5000 ince ve 20 bin kaba anotasyon sunar; nuScenes 1000 adet 20 saniyelik sahne ve 6 kamera ile 360 derece görünüm sağlar; Waymo Open Dataset ise 1150 sahne, 20 saniyelik sekanslar ve kuvvetli çeşitlilik sunar. Bunlar özellikle dış test ve robustness analizi için güçlüdür; fakat ilk Colab fine-tune hattı için veri hazırlama ve annotation uyarlama maliyeti ciddi olabilir.

AI City / CityFlow ve VisDrone ise özel amaçlı önemli tamamlayıcılardır. CityFlow makalesi 40 kamera, 10 kavşak, 3 saatten fazla senkron HD video ve 200 binden fazla bbox ile trafik kamerası dünyasına çok yakın bir alan sunar; bu nedenle sabit kamera senaryosu ve ileride multi-vehicle testleri için değerlidir. VisDrone ise drone bakışı nedeniyle ana eğitim kaynağı olmamalıdır; ama uzak/küçük araç problemi için robustness test seti olarak faydalıdır.

### Önerilen veri seti kullanımı

| Veri seti | Tür | Güçlü tarafı | Alan boşluğu | Önerilen kullanım |
|---|---|---|---|---|
| COCO | Görüntü | Çok güçlü genel ön-eğitim, hedef sınıflar mevcut. | Yol videosu özgüllüğü zayıf | **Yalnızca pretrained başlangıç** |
| BDD100K | Video tabanlı sürüş | 100K video, coğrafi/çevresel/hava çeşitliliği. | Sabit trafik kamera geometrisi sınırlı | **Ana road-domain fine-tune** |
| UA-DETRAC | Trafik videosu | 100 video, >140K frame, weather/occlusion/category etiketleri. | Coğrafi çeşitlilik BDD kadar geniş değil | **Sabit kamera fine-tune + test** |
| KITTI | Sürüş benchmark’ı | Şehir/kırsal/otoyol, gerçek dünya benchmark. | Görece eski ve daha küçük | **External test** |
| CityFlow | Trafik kamerası | >3 saat HD, 40 kamera, >200K bbox. | Daha çok tracking odaklı kurulum | **Fixed-camera robustness test** |
| Cityscapes | Urban sekans | 50 şehir, güçlü urban bağlam. | Detection yerine segmentation ağırlığı | **İkincil yardımcı veri** |
| nuScenes | Multimodal sürüş | 1000 scene, 6 kamera, 23 class. | Veri hazırlama daha ağır | **Haricî robustness / ileri aşama** |
| Waymo Open | Büyük ölçekli sürüş | 1150 sahne, 2D/3D kutular, güçlü çeşitlilik. | Hazırlama maliyeti yüksek | **Final external generalization test** |
| VisDrone | Drone | Küçük/uzak nesne zorluğu. | Bakı açısı yüksek domain gap | **Sadece small-object robustness** |
| Kendi telefon videolarınız | Video | Hedef domainin tam karşılığı | Veri miktarı sınırlı | **Final acceptance test ve son adaptasyon** |

Benim pratik veri stratejim şu olur. **Aşama sıfır**: COCO-pretrained modeli hiçbir fine-tune yapmadan küçük bir dahili örnek video setinde koşturup alan farkını görün. **Aşama bir**: BDD100K üzerinde dört sınıfa indirgenmiş ilk road-domain fine-tune. **Aşama iki**: UA-DETRAC ve gerekiyorsa CityFlow’dan seçilmiş örneklerle sabit kamera geometrisine ikinci uyarlama. **Aşama üç**: kendi telefon kamerası videolarınızdan her 0.5 saniyede bir frame çıkarıp, video-level split ile 70/15/15 ayrılmış bir kurum içi veri seti oluşturun; bu seti hem tuning’in son safhasında küçük miktarda kullanın hem de son acceptance test için ayrı bir kilit test bölümü saklayın. BDD100K ve UA-DETRAC’in zengin hava/perdeleme çeşitliliği ile sizin gerçek kamera açınız birleşmeden final demo güvenli olmaz.

Sınıf haritalaması için önerim nettir. `bus -> bus`, `truck -> truck`, `motorcycle/motorbike -> motorcycle`, `car -> car`. Eğer veri setinde `van`, `pickup`, `other vehicle` gibi ara sınıflar varsa, **bu MVP’de ayrı sınıf açmayın**; ya `car` altında toplayın ya da veri temizliğini bozuyorsa dışarıda bırakın. `person` ve `rider` sınıflarını araç tespiti modülüne karıştırmayın; bunlar ileride araç dışı kullanıcı modülüne gitmeli. Özellikle `motorcycle` ile `bicycle/person` karışımı, bu modülün ayrı risklerinden biridir ve test planında özel alt küme olarak ölçülmelidir. Bu öneri, veri seti literatüründeki sınıf çeşitliliği ile sizin modüler proje kararınız arasındaki uyum için en temiz noktadır.

## Fine-Tune, Test ve Benchmark Planı

### Kısa vadeli eğitim planı

İlk fine-tune turunu karmaşıklaştırmamak gerekir. Başlangıç ağırlıkları olarak resmi COCO pretrained checkpoint’ler kullanılmalı; repo’nun model geliştirme yaklaşımı da sıfırdan büyük model eğitmek yerine public/pretrained modelleri araştırıp fine-tune etmeyi hedeflediğini açıkça söylüyor. Bu da doğrudan sizin bu modüle yaklaşımınızla uyumlu.

Pratik ilk eğitim planı şu şekilde kurulabilir:

| Model | Başlangıç ağırlığı | İlk eğitim veri seti | Görüntü boyutu | İlk tur önerisi | Colab uygunluğu | Beklenen risk |
|---|---|---|---|---|---|---|
| YOLO11n | `yolo11n.pt` | BDD100K 4-sınıf haritası | 640 | 50–100 epoch, erken durdurma | Çok uygun | Düşük boyut küçük araçlarda limit yapabilir |
| YOLO11s | `yolo11s.pt` | BDD100K + seçili UA-DETRAC | 640 | 50–100 epoch | Uygun | n’e göre daha yavaş ama daha dengeli |
| YOLOv10n | `yolov10n.pt` | BDD100K | 640 | 50–100 epoch | Uygun | Export ve gerçek stack davranışı ayrıca ölçülmeli |
| YOLOv10s | `yolov10s.pt` | BDD100K + UA-DETRAC | 640 | 50–100 epoch | Orta-iyi | NMS-free avantajı teorik, sahada ölçülmeli |
| YOLOv8n | `yolov8n.pt` | BDD100K | 640 | 50–100 epoch | Çok uygun | YOLO11’e göre daha düşük ceiling |
| RT-DETR-L | `rtdetr-l.pt` | BDD100K küçük pilot | 640 | Daha kısa pilot + dikkatli stop | Orta | Eğitim/inference maliyeti daha yüksek |
| NanoDet-Plus-m | resmi weights | Kendi mobil pilot veri | 320/416 | Kısa mobil pilot | Uygun | Root modül için doğruluk ceiling’i |

Buradaki epoch ve batch tavsiyeleri kamu benchmarkı değil, **ilk deneme konfigürasyonu** olarak anlaşılmalıdır. Colab GPU türüne göre batch boyutu değişir; önemli olan aynı veri kırılımı, aynı augment şablonu ve aynı değerlendirme protokolüyle adil kıyas yapmaktır.

Augment tarafında önerim şudur: parlaklık/kontrast, hafif motion blur, Gaussian blur, JPEG sıkıştırma bozunumu, random scale, sınırlı perspective, seçici yağmur/sis/gece simülasyonu kullanılabilir. Ancak bu proje plaka/OCR ve küçük/uzak araç downstream’ine gideceği için augmentasyonu “ne kadar agresif o kadar iyi” mantığıyla kurmamak gerekir. Özellikle güçlü random crop, aşırı mosaic ve çok sert atmosferik augmentasyon küçük araçların ve sonra kırpılacak plaka bölgelerinin istatistiğini bozabilir. Bu nedenle iki validasyon yapılmalıdır: genel detection validasyonu ve “target vehicle continuity” validasyonu.

### Test stratejisi

Bu modül için en kritik hata, yalnızca public benchmark mAP’ine bakıp model seçmektir. Sizin gerçek sorunuz “COCO’da kaç AP aldı” değil, “telefon kamerasından gelen canlı akışta hedef aracı downstream modüllere ne kadar kararlı besliyor” sorusudur. Bu nedenle test planı en az şu bölümlere ayrılmalıdır:

1. **İç validasyon seti**: eğitimde kullanılan ana veri setinin video-level ayrılmış validation bölümü.
2. **Held-out test set**: aynı veri ailesinden ama hiç görülmemiş video bazlı test.
3. **Haricî dashcam testi**: KITTI veya benzeri.
4. **Haricî fixed-camera testi**: UA-DETRAC ve/veya CityFlow.
5. **Kendi telefon kamera testiniz**: final karar için en kritik küme.
6. **Gece / düşük ışık alt kümesi**: BDD100K ve kendi verinizden.
7. **Yağmur / blur / visibility alt kümesi**: BDD100K, UA-DETRAC ve kendi videolarınızdan.
8. **Küçük/uzak araç alt kümesi**: gerekirse VisDrone veya kendi etiketlerinizle.
9. **Single-target senaryosu**: hedef tek araç ve downstream tracking kolaylığı için.
10. **Multi-vehicle senaryosu**: daha sonra hedef araç seçiminin kararlılığı için.

### Ölçülmesi gereken metrikler

Bu modül için benchmark planı mutlaka üç katmanlı olmalıdır:

**Algılama kalitesi metrikleri**: mAP@0.5, mAP@0.5:0.95, precision, recall, F1, sınıf başına AP, confusion matrix, false positive, false negative.
**Gerçek zamanlılık metrikleri**: FPS, ortalama latency, p95 latency, model yükleme süresi, CPU/GPU kullanımı, RAM kullanımı, model dosya boyutu, çözünürlük etkisi.
**Pipeline metrikleri**: kareler arası detection stability, tracking başlatma başarısı, target vehicle selection’e uygunluk, JSON contract uyumu, evidence crop kullanılabilirliği, export sonrası tutarlılık, INT8/FP16 düşüşü. Repo belgelerinde de model seçiminin yalnızca doğrulukla değil hız, latency, model boyutu ve export kolaylığıyla yapılacağı zaten yazılıdır.

Ben karar skoru için kullanıcı prompt’undaki ağırlıkları korurum; çünkü bu proje için mantıklı:
**Detection quality %35 + Real-time performance %25 + Deployment/export %15 + Robustness/domain generalization %15 + Fine-tune/maintenance practicality %10**.
Bu dağılım, “sadece mAP yüksek olsun” tuzağını kırar ama yine de kök modülün doğruluğunu en önemli eksen olarak bırakır.

Aşağıdaki karar matrisi ilk günden repo’ya boş şablon olarak konmalıdır:

| Model | Detection score | Latency/FPS score | Deploy score | Robustness score | Fine-tune practicality | Toplam | Karar |
|---|---:|---:|---:|---:|---:|---:|---|
| YOLO11n | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| YOLO11s | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| YOLOv10n | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| YOLOv10s | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| YOLOv8n | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| RT-DETR-L | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| NanoDet-Plus-m | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Bu tablonun bugün sayı ile doldurulmaması gerekir; çünkü promptunuzun doğru vurguladığı gibi **nihai karar kamu benchmark’ından değil, kendi proje benchmark’ınızdan çıkmalıdır**. RT-DETR için decoder katmanı azaltma ve query sayısı düşürme trade-off’unun kaynakta açıkça verilmesi, bazı modellerde hız/başarım optimizasyonunun “tek çekirdek sayıya” indirgenemeyeceğini de gösteriyor.

## Repo Çıktıları, Risk Analizi ve Nihai Öneri

### Repoda oluşturulması gereken dosyalar

Bu araştırmanın depo içinde kalıcı, yeniden üretilebilir ve ekipçe takip edilebilir hâle gelmesi için şu dosya yapısını öneririm. Repo zaten `research/`, `models/`, `docs/`, `testing/` gibi klasörleri bu tür çıktılar için ayırmış durumda.

`research/02_vehicle_detection/model_candidates.md` dosyası; model ailelerinin özeti, lisans notları, deploy yolları, resmi benchmark link/citation notları ve “neden shortlist’e girdi / neden çıkmadı” kararlarını içermelidir.
`research/02_vehicle_detection/dataset_candidates.md` dosyası; COCO, BDD100K, KITTI, UA-DETRAC, CityFlow, Cityscapes, nuScenes, Waymo, VisDrone, kendi veri stratejiniz ve sınıf haritalama notlarını içermelidir.
`research/02_vehicle_detection/benchmark_plan.md` dosyası; FPS, p95 latency, RAM, export success, quantization drop, evidence usability, tracking readiness metriklerini tek tek tanımlamalıdır.
`research/02_vehicle_detection/finetune_plan.md` dosyası; kısa listedeki her model için eğitim veri akışı, augment, early stopping, split politikası, sürümleme ve Colab komut şablonlarını içermelidir.
`research/02_vehicle_detection/decision_vehicle_detector_v1.md` dosyası; ilk model seçimi karar notu, nedenler, lisans riskleri ve “yeniden karar verme koşulları”nı tutmalıdır.
`models/experiments/vehicle_detection_experiment_template.md` dosyası; her deneye ait veri kırılımı, config, runtime, commit SHA, sonuç tabloları ve export artefact notlarını standartlaştırmalıdır.
`models/benchmarks/vehicle_detection_benchmark_template.csv` dosyası; tüm modellerin aynı sütunlarla kaydedildiği makine-okunur karşılaştırma dosyası olmalıdır.
`docs/04_yapay_zeka/01_arac_tespiti_takip.md` veya eşleniği; araç tespiti çıktısının tracking, target selection, plate OCR ve evidence modüllerine nasıl aktığını açıklayan teknik anlatımı içermelidir. Repo README’sindeki modül sırası ile birebir uyumlu olmalıdır.

### Başlıca riskler

Bu modül için en kritik teknik riskler; küçük/uzak araçlar, hareket bulanıklığı, gece/düşük ışık, yağmur/sis, perdeleme, sınıf karışması, alan farkı, export başarısızlığı, quantization kaybı ve video-level leakage’dır. UA-DETRAC açık biçimde weather, occlusion ve truncation zorluğunu; BDD100K çevresel ve hava çeşitliliğini; VisDrone küçük/uzak nesne zorluğunu; DETR/Deformable DETR literatürü de küçük obje ve verimli işlem maliyeti sorunlarını net biçimde gösterir. Bu riskler MVP’yi doğrudan etkiler, çünkü kök modül hatası downstream zincirde katlanır.

Bu risklerin etkisi ve önlemi aşağıdaki gibi özetlenebilir:

| Risk | Etki | Olasılık | Mitigasyon | MVP’ye etkisi |
|---|---|---|---|---|
| Küçük/uzak araç kaçırma | Tracking ve hedef araç seçimi bozulur | Yüksek | 640 çözünürlükten başlayıp gerekirse 960/1280 pilot; small-object alt testi; VisDrone/uzak araç alt kümesi | Evet |
| Gece/düşük ışık | Recall düşer | Yüksek | Night subset, parlaklık augment, kendi gece videoları | Evet |
| Yağmur/sis/blur | Precision ve recall aynı anda bozulur | Orta-yüksek | Weather subset, kontrollü augment, QA ile sahne bazlı eşik | Evet |
| Occlusion | Track kopması ve false negative | Yüksek | UA-DETRAC/CityFlow testleri, tracker-ready stability metriği | Evet |
| Motorcycle-bicycle-person karışması | Yanlış risk tetikleme | Orta | Person/rider’ı bu modül dışında tutma, confusion alt seti | Evet |
| Bus-truck karışması | Hedef araç sınıfı yanlışlaşır | Orta | Per-class AP ve confusion matrix takibi | Evet |
| Domain gap | Public set iyi, gerçek demoda kötü | Çok yüksek | Mutlaka kendi telefon videosu ile son test | Evet |
| Model fazla büyük | <1 s uçtan uca bütçe bozulur | Orta-yüksek | Nano/small varyantlar, pipeline asenkronluğu | Evet |
| Export/quantization sorunu | Android/edge geçişi durur | Orta | ONNX/TFLite/NCNN/QNN denemelerini erken başlatma | Evet |
| Video leak | Yanlış yüksek başarı | Orta | Video-level split ve izolasyon | Evet |

### Nihai öneri

Bu araştırmanın mevcut kanıtlarıyla nihai önerim şudur:

**İlk deney modeli olarak YOLO11n ile başlayın.** Çünkü bugün için en iyi “iterasyon hızı + kalite + export geleceği + ekosistem” dengesini veriyor. YOLO11n’nin ardından aynı veri ve aynı test protokolüyle **YOLO11s**, **YOLOv10n**, **YOLOv10s**, **YOLOv8n**, ardından zaman kalırsa **RT-DETR-L** benchmark edilmelidir. Eğer mobilde doğrudan inference fikri tekrar masaya güçlü gelirse, bu pakete **NanoDet-Plus-m** veya **YOLOv6Lite-M** de eklenmelidir.

**İlk fine-tune veri seti olarak BDD100K**, **ikinci aşama domain adaptasyonu için UA-DETRAC**, **final public test için KITTI + UA-DETRAC/CityFlow**, **nihai kabul testi için ise kendi telefon kamera videolarınız** kullanılmalıdır. Bu kombinasyon, genel road-domain, fixed-camera davranışı ve gerçek hedef cihaz açısından en dengeli veri planını verir.

**MVP için minimum kabul kriteri** olarak benim önerim: kendi edge makinenizde seçili giriş çözünürlüğünde detection stage p95 latency’nin canlı pipeline bütçesini bozmayacak düzeye inmesi; event JSON üretiminin hatasız çalışması; evidence crop’ların kullanılabilir olması; ve single-target senaryoda tracker’ın seçili aracı pratik olarak sürdürebilmesi. Sayısal eşikler ilk benchmark turundan sonra sabitlenmeli, fakat “sadece mAP yüksek” kabulü yapılmamalıdır.
**Final demo için minimum kriter** ise buna ek olarak düşük ışık ve çoklu araç sahnelerinde kabul edilebilir kararlılık, export başarısı ve gerekiyorsa hafif quantization sonrası anlamlı başarı kaybı olmamasıdır. Bu eşikler proje kabul kriteridir; literatür değil, sizin saha gereksiniminiz belirlemelidir.

Araç tespitinden sonra gelmesi gereken bir sonraki AI modülü, repo yol haritasıyla da uyumlu biçimde **araç takibi ve hedef araç seçimi** olmalıdır. Çünkü plaka OCR, hız, şerit/ilişkilendirme ve evidence paketinin tamamı “her karede yeniden sıfırdan bul” mantığıyla değil, “aynı aracı zamansal olarak koru ve seç” mantığıyla güvenilir hâle gelir. Repo’nun modül sırası da bunu aynen söylüyor.

### Raporlarda kullanılabilecek Türkçe metinler

Aşağıdaki paragraflar, TEKNOFEST raporunuza doğrudan uyarlanabilir niteliktedir:

**Araç tespitinin ilk AI modülü olma gerekçesi**
Projemizde araç tespiti modülü, tüm algı zincirinin başlangıç katmanını oluşturmaktadır. Telefon kamerasından veya sabit yol kamerasından alınan canlı görüntü akışında önce araçların konum ve sınıflarının güvenilir biçimde belirlenmesi gerekmektedir. Çünkü hedef araç takibi, plaka tespiti/OCR, hız kestirimi, şerit ilişkisi, evidence üretimi ve risk füzyonu gibi bütün sonraki modüller doğrudan araç tespiti çıktısına bağımlıdır. Kök modüldeki hatalar, zincirin aşağısında yanlış hedef seçimi, eksik plaka kırpımı, hatalı risk tetikleme ve zayıf kanıt üretimi gibi daha büyük hatalara dönüşmektedir. Bu nedenle araç tespiti, sistem başarımını belirleyen temel AI bileşeni olarak ele alınmıştır.

**Seçilen model ailesinin uygunluğu**
Yapılan araştırmada YOLO tabanlı güncel tek-aşamalı dedektörlerin, doğruluk, hız, model boyutu, export seçenekleri ve ince ayar yapılabilirlik bakımından proje için en dengeli yaklaşımı sunduğu görülmüştür. Özellikle YOLO11 ailesi, Ultralytics ekosistemi içinde eğitim, doğrulama, çıkarım ve export süreçlerini tek çatı altında sağlayarak hızlı prototipleme ve tekrar üretilebilir deney avantajı sunmaktadır. Aynı zamanda ONNX, TensorRT, OpenVINO, TF Lite ve benzeri export seçenekleri sayesinde edge ve gelecekte mobil dağıtım açısından güçlü bir teknik zemin oluşturmaktadır.

**Fine-tune stratejisi**
Model geliştirme yaklaşımımız sıfırdan büyük ölçekli bir dedektör eğitmek yerine, kamuya açık ön-eğitimli modellerin proje alanına özgü veriyle uyarlanmasına dayanmaktadır. Bu kapsamda öncelikle COCO ön-eğitimli ağırlıklarla başlangıç yapılacak, ardından BDD100K ile genel yol alanına adaptasyon sağlanacak, daha sonra UA-DETRAC ve kontrollü olarak toplanmış kendi kamera videolarımız ile sabit trafik kamerası ve hedef demo geometrisine uyum artırılacaktır. Veri ayrımı video seviyesinde yapılacak, böylece aynı videodan türetilen karelerin farklı veri bölümlerine sızarak gerçek dışı yüksek başarı üretmesi önlenecektir.

**Doğruluk-gecikme dengesinin ölçülmesi**
Model seçimi yalnızca doğruluk metriğine göre yapılmayacaktır. Bunun yerine mAP, precision, recall ve sınıf bazlı başarıların yanında FPS, ortalama gecikme, p95 gecikme, bellek kullanımı, model boyutu, export başarısı ve quantization sonrası performans korunumu birlikte değerlendirilecektir. Böylece yarışma demosunda gerçek zamanlı canlı akış bozulmadan, uçtan uca gecikme bütçesi korunarak ve sonraki AI modüllere yeterli kaliteyle çıktı üreterek çalışan dengeli bir araç tespiti modülü seçilecektir.

**Araç tespiti çıktısının diğer modüllere akışı**
Araç tespiti modülü her kare için araçların sınıfını, güven skorunu ve bounding box bilgisini olay uyumlu JSON biçiminde üretecektir. Bu yapı, takip modülünün araç kimliğini kareler arasında korumasını, hedef araç seçim modülünün tekil odak aracı belirlemesini, plaka tespiti/OCR modülünün doğru bölgeyi kırpmasını ve evidence bileşeninin açıklanabilir kanıt kartları üretmesini sağlayacaktır. Böylece sistem, yalnızca noktasal tespit yapan bir yapı olmaktan çıkıp, zamansal olarak tutarlı ve kullanıcıya açıklanabilir bir karar destek mimarisine dönüşecektir.

### Açık sorular ve sınırlılıklar

Bu rapordaki kamu benchmark’ları **aynı donanım ve aynı runtime üzerinde ölçülmemiştir**; dolayısıyla hız karşılaştırmaları tek başına nihai karar verdirmez. Özellikle YOLO11 ve YOLOv8 için resmî akademik makale yerine üretici dokümantasyonu kullanılmıştır; bu yüzden bu ailelerde kendi ölçümünüz daha da önemlidir. Ayrıca YOLO-NAS ve bazı GPL/AGPL tabanlı ailelerde lisans ve gelecekteki kapalı kaynak ürünleşme etkisi teknik başarıdan bağımsız biçimde ayrıca değerlendirilmelidir.

## Kaynaklar

Ultralytics YOLO11 dokümantasyonu — model varyantları, COCO metrikleri, export desteği, lisans bilgisi.

Ultralytics YOLOv8 dokümantasyonu — YOLOv8 varyantları, performans ve kullanım/benchmark akışı.

Ultralytics YOLOv10 dokümantasyonu — NMS-free tasarım, varyant performansları ve RT-DETR/YOLOv9 karşılaştırmaları.

Ultralytics export dokümantasyonu — ONNX, TensorRT, OpenVINO, CoreML, TFLite, NCNN, QNN, ExecuTorch vb. export hedefleri ve INT8/FP16 notları.

Ultralytics RT-DETR dokümantasyonu — RT-DETR-L/X performansı, export desteği ve decoder trade-off ayarları.

YOLOv6 resmî GitHub deposu — industrial applications odağı, benchmark tablosu, deploy başlıkları, Android/NCNN/OpenVINO/TensorRT desteği, mobil benchmark, lisans.

YOLOv7 resmî GitHub deposu ve makalesi — performans, export örnekleri ve lisans.

YOLOv9 makalesi ve Ultralytics sayfası — PGI/GELAN yaklaşımı ve model varyantları.

YOLO-NAS / SuperGradients dökümanları — performans, deploy uyumluluğu, non-commercial weights notu.

NanoDet resmî deposu — mobil ARM CPU hızı, Android demo, model boyutu ve Apache-2.0 lisansı.

TensorFlow Model Garden ve TF2 Detection Zoo — SSD MobileNet, EfficientDet, Faster R-CNN gibi klasik/mobile baseline’ların resmi benchmark listesi ve lisans.

Faster R-CNN, RetinaNet, Cascade R-CNN, DETR, Deformable DETR ve DINO makaleleri — iki aşamalı dedektörler, focal loss, end-to-end transformer dedektörler ve eğitim/inference karmaşıklığına ilişkin birincil bilimsel kaynaklar.

COCO, BDD100K, KITTI, UA-DETRAC, Cityscapes, nuScenes, Waymo Open Dataset, CityFlow ve VisDrone kaynakları — veri boyutu, ortam çeşitliliği, video/görüntü yapısı ve test/fine-tune uygunluğu için temel veri seti referansları.

Projenin GitHub deposu — mimari bağlam, modül sırası, MVP kapsamı, evidence akışı, model seçim yaklaşımı ve kök modül olarak araç tespiti vurgusu.
