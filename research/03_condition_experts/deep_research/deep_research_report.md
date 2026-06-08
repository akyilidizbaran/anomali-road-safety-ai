# Anomali Road Safety AI için Koşul Uzmanları Yaklaşımı

## Yönetici özeti

Bu proje için “condition-specific vehicle detector” yaklaşımı teknik olarak **mantıklıdır**, ancak **doğrudan her koşul için ayrı detector eğiterek başlamak** en doğru yol değildir. En uygulanabilir yaklaşım, önce güçlü bir **genel araç dedektörü** kurmak, onu gerçek proje veri akışına göre benchmark etmek, sonra yalnızca **ölçülebilir biçimde anlamlı fayda sağlayan** koşullar için uzman dedektör açmaktır. Bu nedenle üç strateji arasında bu proje için en uygun seçenek **Strateji 1**’dir: önce genel vehicle detector fine-tune, sonra condition-specific specialist fine-tune. Bu seçim, sizin mevcut mimarinizde zaten tarif edilmiş olan seçici çalışan uzman alt modüller, normal/kritik mod ayrımı, QoD/evidence yaklaşımı ve canlı edge çalışma hedefiyle en uyumlu seçenektir. citeturn53view0turn55view0turn51view0turn50view0 fileciteturn0file3 fileciteturn0file2

Literatür açısından bakıldığında, kötü hava ve düşük ışık altında algı bozulmasının gerçek bir sorun olduğu çok nettir; BDD100K ortam ve zaman çeşitliliğini, UA-DETRAC hava/koşul anotasyonlarını, ACDC ise gece, yağmur, kar ve sis gibi adverse condition alanlarını açıkça ortaya koyar. Son yıllardaki çalışmalar da “tek model her şeyi çözsün” varsayımının zorlandığını; bunun yerine domain adaptation, weather-aware routing, condition-aware fusion ve detector-guided enhancement çizgilerinin öne çıktığını gösterir. Bununla birlikte, 2D kamera tabanlı araç tespitinde “deploy edilen çok sayıda ayrı hava-koşulu uzman detector” henüz baskın standart değildir; bu yüzden fikir yenilikçidir ama ancak **sıkı benchmark, güçlü fallback ve kontrollü routing** ile güvenli hâle gelir. citeturn31view0turn32view0turn39academia0turn54view0turn54view1turn53view0

Bu proje için başlangıç önerim şudur:
Genel model olarak **YOLO11n** ile başlayın; çünkü sizde zaten baseline olarak düşünülmüş durumda, Ultralytics ekosistemi içinde eğitim/validation/export desteği güçlü ve küçük boyut/fena olmayan doğruluk dengesi sunuyor. Onunla birlikte mutlaka **YOLOv10n** ve **YOLO11s** benchmark edilmelidir. Eğer MacBook edge benchmark’ında YOLOv10n açık biçimde daha iyi latency-verim dengesi verirse aile seçimi YOLOv10’a çevrilebilir; aksi durumda operasyonel sadelik için tüm uzmanlarda aynı ailede kalmak daha doğrudur. Transformer tabanlı **RT-DETR-R18** ise araştırma/challenger modeli olarak benchmark edilmeli; fakat ilk MVP’de ana uzman ailesi olması gerekmiyor. citeturn56view1turn37view3turn58view3

MVP için tavsiye edilen ilk uzman listesi de geniş tutulmamalıdır. İlk sürümde ayrı expert olarak yalnızca şu üçlü açılmalıdır:
`vehicle_detector_general`, `vehicle_detector_night_low_light`, `vehicle_detector_rain`, `vehicle_detector_fog_low_visibility`.
Buna karşılık `glare`, `low_contrast`, `tunnel_or_parking_dark` ve `dark` gibi varyantlar başlangıçta ayrı detector olarak değil, önce condition profile katmanında etiketlenmeli; veri ve benchmark birikirse sonradan uzmanlaştırılmalıdır. Bunun nedeni, public veri tarafında gece/yağmur/sis kümelerinin görece net olması; buna karşılık glare/tunnel/parking-dark gibi alt koşulların çok daha az standartlaşmış olmasıdır. citeturn38view0turn38view1turn39academia0turn47view0

## Neden mantıklı, neden riskli

Koşul uzmanı yaklaşımının temel mantığı şudur: bazı çevresel koşullar yalnızca “görüntü kalitesini biraz düşürmez”; veri dağılımını kökten değiştirir. Düşük ışıkta sinyal-gürültü oranı bozulur, yağmurda yansımalar ve damla artefaktları oluşur, siste kontrast ve kenar ayrımı zayıflar. Bu da tek genel dedektörün tüm koşullarda aynı temsil gücüyle çalışmasını zorlaştırır. NOD çalışması düşük ışığın makine algısı için “özel dikkat gerektiren” ayrı bir problem olduğunu açıkça gösterirken, ACDC ve Foggy Cityscapes çizgisi adverse condition’ların standart perception performansını ciddi biçimde zorladığını gösterir. citeturn51view0turn39academia0turn50view0

Daha da önemlisi, çok yeni AW-MoE çalışması doğrudan şu tezi savunur: farklı hava koşullarını tek havuzda eğitmek, hava koşulları arası dağılım farkları nedeniyle “performance conflicts” oluşturabilir; weather-aware routing ile top-K weather-specific experts seçilmesi adverse condition performansını iyileştirebilir. Her ne kadar bu çalışma 3D multimodal bağlamda olsa da, Anomali Road Safety AI’de önerdiğiniz B-tipindeki “koşula özel araç detector” fikrini destekleyen en güçlü kavramsal paralelliklerden biridir. citeturn53view0

Ancak bunun ters tarafı da var. 2D adverse-weather detection literatürünün büyük kısmı ayrı deploy edilen specialist detector filolarından çok, şu yönelimlere ağırlık veriyor: deraining/dehazing gibi preprocessing, domain adaptation, image translation, detector-guided enhancement ve all-weather robust training. Yağmur altındaki object detection inceleme makalesi de ana hatların bunlar olduğunu özetliyor. Yani sizin fikriniz literatüre aykırı değil; ama “varsayılan endüstri standardı” da değil. Bu nedenle bu yaklaşımın başarısı model sayısından değil, **routing politikasının doğruluğundan** ve **uzman modelin gerçekten genel modelden daha iyi olduğunun kanıtlanmasından** gelecektir. citeturn55view0turn54view0turn54view1turn51view0

Üç strateji proje açısından şöyle okunmalıdır:

| Strateji | Ne yapar | Avantaj | Dezavantaj | Bu proje için karar |
|---|---|---|---|---|
| Strateji 1 | Önce genel detector, sonra seçili specialist’ler | En güvenli mühendislik sırası; routing’i benchmark’la açar; veri parçalanmasını azaltır | İkinci aşama benchmark disiplini ister | **Önerilen seçenek** |
| Strateji 2 | Doğrudan her koşul için ayrı detector | Teorik olarak condition-optimal olabilir | Veri çok bölünür; yanlış routing riski erken aşamada büyür; bakım yükü katlanır | **MVP için önerilmez** |
| Strateji 3 | Tek all-weather detector + preprocessing/augmentation | Operasyonel olarak en sade yaklaşım | Zor gece/sis senaryolarında condition-specific kazanç kaçabilir | İyi baseline/challenger, ama tek başına nihai tercih değil |

Strateji 1’in seçilmesinin nedeni yalnızca “daha temkinli” olması değildir. NOD düşük ışıkta detector-guided enhancement’ın faydalı olabileceğini, FeatEnHancer düşük ışık görevlerinde belirgin kazanımlar sağlayabildiğini, Foggy Cityscapes çizgisi ise sentetik sis verisinin gerçek sis testinde iyileştirme sağlayabildiğini gösterir. Buna karşılık 2026 tarihli robustness çalışması, adverse-condition odaklı sentetik eğitimlerin fayda sağlasa da **diminishing returns** ve **forgetting** doğurabildiğini gösterir. Yani erken aşamada çok sayıda specialist açmak yerine, önce genel temeli kurup sonra gerçekten kazandıran uzmanları aktifleştirmek daha rasyoneldir. citeturn51view0turn51view1turn50view0turn52view0

## Veri setleri ve önerilen uzman listesi

Koşul uzmanı yaklaşımının başarısı, tek tek model mimarisinden daha fazla şekilde **condition split kalitesine** bağlıdır. Bu proje için en kritik nokta, public veri setlerini “aynı 4 sınıfı öğreten ama farklı koşulları taşıyan alt kümeler” şeklinde yapılandırmaktır. Sizin elinizdeki 3 dark/low-light video bu iş için eğitim verisi olmamalı; overfit ve sahte başarı riski doğurur. Bunlar yalnızca smoke test ve acceptance test materyali olarak kullanılmalıdır. Bu, özellikle TEKNOFEST raporunda veri toplama, veri seti oluşturma ve test metodolojisi açık istenen bir başlık olduğu için önemlidir. fileciteturn0file2

Aşağıdaki tablo, bu proje için en faydalı public veri setlerini “koşul uzmanı” bağlamında özetler:

| Veri seti | Ne sağlar | Koşul etiketi | Araç bbox | YOLO dönüşümü | Lisans / kullanım riski | Tavsiye edilen rol |
|---|---|---|---|---|---|---|
| **BDD100K** | 100K sürüş videosu, 10 görev; hava, sahne ve günün saati çeşitliliği; 6 hava, 6 sahne tipi ve 3 zaman etiketi; car/truck/bus/motorcycle sınıfları mevcut. citeturn31view0turn45view0 | Evet | Evet | Pratik | İndirme portalı şartları **doğrulanmalı** | **Genel modelin ana omurgası**, ayrıca night/rain split |
| **UA-DETRAC** | 100 trafik videosu, 140K+ kare; hava, occlusion, truncation ve vehicle bbox anotasyonları; fixed traffic camera bakışı açısından çok değerli. citeturn32view0 | Evet | Evet | Pratik | Lisans/şartlar **doğrulanmalı** | **Traffic-camera domain fine-tune**, night/rain alt kümeleri |
| **ACDC** | 8012 görüntü; adverse yarı küme fog/night/rain/snow; object detection destekli adverse benchmark. citeturn39academia0 | Evet | Evet | Mümkün, ama paket formatı **kontrol edilmeli** | Şartlar **doğrulanmalı** | **Night/rain/fog specialist** ve external adverse test |
| **Foggy Cityscapes + Foggy Driving** | 20,550 sentetik sisli görüntü; 101 gerçek sisli görüntüde object detection ground truth; sentetik sis eğitiminin gerçek sis testine faydasını gösteren klasik benchmark. citeturn50view0 | Sis odaklı | Evet | Mümkün | Cityscapes türevi kullanım şartları **doğrulanmalı** | **Fog specialist** + gerçek fog external test |
| **ExDark** | 7,363 low-light görüntü, 10 koşul, 12 obje sınıfı, bbox; düşük ışık görünüm öğrenmek için çok yararlı. citeturn46view0 | Düşük ışık koşul kümeleri | Evet | Pratik | BSD-3, ancak ticari kullanım için yazarla iletişim notu var. citeturn46view0 | **Night/low-light specialist** için yardımcı veri |
| **NOD** | Sokakta gece çekilmiş büyük ölçekli night object detection verisi; düşük ışığın ayrı problem olduğunu ve detector-guided enhancement faydasını gösterir. citeturn51view0 | Gece | Evet | Erişim biçimine göre | Lisans/erişim **doğrulanmalı** | **Night specialist test/yardımcı fine-tune** |
| **DAWN** | 1000 gerçek adverse-weather görüntüsü; fog/snow/rain/sandstorm; araç bbox. citeturn47view0turn36academia2 | Evet | Evet | Pratik | Lisans **doğrulanmalı** | **External adverse benchmark**, özellikle rain/fog |
| **SHIFT** | Cloudiness, rain, fog intensity ve time-of-day shift’leri olan büyük sentetik driving dataset. citeturn33academia3 | Evet | 2D detection görevleri var | Mümkün | Lisans **doğrulanmalı** | **Sentetik destek** ve controlled condition split |
| **WEDGE** | 16 ekstrem hava koşulunda 3360 görüntü, 16513 bbox; gerçek adverse benchmark’ta fine-tune kazancı göstermiştir. citeturn47view0 | Evet | Evet | Pratik | **CC BY-NC-SA 4.0**, ticari/ürünleştirme açısından riskli. citeturn47view0 | **Sentetik destek**, research-only augment/fine-tune |
| **Waymo Open Dataset** | Çeşitli sürüş koşullarında yüksek kaliteli 2D/3D anotasyon; büyük genel detector testi için değerli olabilir. citeturn13academia2turn44view1 | Hava etiketi odaklı değil | Evet | Mümkün | **Non-commercial** lisans açıkça belirtiliyor. citeturn44view1 | Genel external test, ama demo/ürünleştirme için dikkat |

Bu veri seti matrisinden çıkan pratik sonuç şudur:
**Genel model** için en mantıklı omurga **BDD100K + UA-DETRAC**’tır. BDD100K görünüm ve koşul çeşitliliğini, UA-DETRAC ise fixed traffic camera benzeri bakışı güçlendirir. **Night specialist** için BDD100K night + UA-DETRAC night + ACDC night + ExDark/NOD; **Rain specialist** için BDD100K rain + UA-DETRAC rainy + ACDC rain + WEDGE rain supplement; **Fog specialist** için ACDC fog + Foggy Cityscapes + WEDGE fog ve değerlendirmede Foggy Driving/DAWN fog önerilir. citeturn31view0turn32view0turn39academia0turn46view0turn51view0turn50view0turn47view0

MVP için tavsiye edilen uzman listesi bu nedenle şöyledir:

- `vehicle_detector_general`
- `vehicle_detector_night_low_light`
- `vehicle_detector_rain`
- `vehicle_detector_fog_low_visibility`

Aşağıdaki uzmanlar ise ilk turda **ayrı model olmamalıdır**:

- `vehicle_detector_dark`
- `vehicle_detector_glare`
- `vehicle_detector_low_contrast`
- `vehicle_detector_tunnel_or_parking_dark`

Sebep, public veri tarafında bu gruplar için standart, yeterli ve lisansça net bbox veri akışının zayıf olmasıdır. İlk sürümde `dark`, `tunnel_or_parking_dark` ve benzeri sınıflar **night_low_light** uzmanına route edilebilir; `glare` ve `low_contrast` ise önce condition profile katmanında belirlenip, ileride yeterli veri birikirse ayrı uzmanlaştırılmalıdır. Bu, model patlamasını önler. citeturn38view0turn38view1turn39academia0turn47view0

## Model adayları ve geliştirme sırası

Bu projede uzman detector’lar için doğru seçim “en yüksek COCO mAP” modeli değildir. MacBook local edge/runtime, 720p canlı akış, bir saniye altı uçtan uca gecikme, ileride mobile/export ihtiyacı ve çoklu expert yönetimi birlikte düşünüldüğünde, **küçük ve orta küçük** modeller daha gerçekçidir. Bu yüzden ilk shortlist’te `n` ve `s` varyantları öne çıkmalıdır. citeturn56view1turn37view3turn58view3turn57view1

| Model | Resmi kaynak | Yaygınlaştırılmış ölçü | Güçlü yön | Kritik sınırlama | Bu proje için rol |
|---|---|---|---|---|---|
| **YOLO11n** | Ultralytics docs | COCO mAP 39.5, 2.6M param, CPU ONNX 56.1 ms. citeturn56view1 | Küçük, hızlı, export dostu, eğitim/val/export akışı çok olgun | Resmî makale yok; lisans AGPL/Enterprise. citeturn56view1turn56view2 | **İlk general baseline** |
| **YOLO11s** | Ultralytics docs | COCO mAP 47.0, 9.4M param, CPU ONNX 90.0 ms. citeturn56view1 | `n`’e göre daha güçlü doğruluk; specialist için kabul edilebilir büyüklük | `n`’e göre daha ağır | **Accuracy-oriented specialist adayı** |
| **YOLOv10n** | Ultralytics docs | COCO mAP 39.5, 2.3M param; düşük latency çizgisi, NMS-free. citeturn37view2turn37view3 | Çok iyi hız/verim dengesi; end-to-end/NMS-free yaklaşım | Export format desteği model-spesifik; tüm formatlar tam sorunsuz değil. citeturn37view3 | **Ana challenger** |
| **YOLOv10s** | Ultralytics docs | COCO mAP 46.8, 7.2M param. citeturn37view2 | Specialist için iyi hız-doğruluk dengesi | YOLO11s ile gerçek edge ölçümü şart | **Specialist challenger** |
| **RT-DETR-R18** | Resmî repo | COCO AP 46.5, 20M param, T4 TensorRT 217 FPS; Apache-2.0. citeturn58view3 | Transformer temelli güçlü global bağlam; resmî repo/weights; lisansı daha rahat | YOLO küçük varyantlarına göre daha ağır entegrasyon/ops yükü | **Araştırma / benchmark challenger** |
| **YOLOv8n/s** | Ultralytics docs | YOLOv8n 37.3 mAP, 3.2M; YOLOv8s 44.9 mAP, 11.2M. citeturn24view0 | Çok stabil, çok olgun ekosistem | YOLO11/YOLOv10’a göre artık daha çok fallback | **Güvenli fallback benchmark** |

Bu tablonun pratik okuması şudur: eğer bugün Colab’da ve MacBook edge tarafında hemen deneye başlanacaksa, **ilk deney sırası** şöyle olmalıdır:

1. `YOLO11n` — mevcut baseline ile uyumlu ilk genel model
2. `YOLOv10n` — latency challenger
3. `YOLO11s` — doğruluk artışı gerçekten değer mi testi
4. `YOLOv10s` — specialist için ikinci güçlü aday
5. `RT-DETR-R18` — araştırma/challenger, ilk hat model değil
6. `YOLOv8n/s` — geriye dönük sağlam karşılaştırma tabanı

Neden böyle? Çünkü condition-expert yaklaşımında en önemli operasyonel kazançlardan biri, tüm uzmanların aynı aileden gelmesi hâlinde eğitim scriptleri, export davranışı, inference wrapper’ı ve JSON çıktısının daha kolay yönetilmesidir. Bu nedenle ben aileyi ilk etapta **YOLO11** etrafında kurmanızı, **YOLOv10**’u ise ciddi challenger olarak benchmark etmenizi öneriyorum. Eğer sizin gerçek MacBook benchmark’ınızda YOLOv10n genel modelde ve specialist varyantlarında bariz üstünlük gösterirse, o zaman aileyi YOLOv10’a çevirmek mantıklıdır. Bu karar kamu benchmark’ına göre değil, **sizin edge benchmark’ınıza göre** verilmelidir. citeturn56view1turn37view3turn58view3

Burada küçük model mi biraz büyük model mi sorusunun cevabı da nettir:
**General modelde küçük**, **specialist’te gerekiyorsa bir kademe büyük**.
Yani `general = n`, `night/fog specialist = n veya s`, `critical-mode evaluator = s` yaklaşımı daha mantıklıdır. Çünkü uzman model her framede sürekli koşmayacağı için biraz daha büyük olmasına tolerans doğabilir; ama gene de `m/l/x` seviyeleri bu proje için gereksiz olur. citeturn56view1turn37view2turn58view3

## Benchmark protokolü ve runtime routing politikası

Koşul uzmanı yaklaşımında en büyük hata, “condition classifier dark dedi, dark modeli çağıralım” mantığını doğrudan canlıya taşımaktır. Doğru yaklaşım, routing’i **yalnızca iki şart birlikte sağlanıyorsa** açmaktır:
birincisi condition profile güveni yeterli olacak; ikincisi o condition için specialist modelin gerçekten general modelden daha iyi olduğu önceden benchmark’la kanıtlanmış olacak. AW-MoE’nin weather-aware routing fikri bunu destekler; sizin PDR’nizde tarif edilen normal/kritik mod ve QoD mantığı da aynı seçici çalışma mantığıyla uyumludur. citeturn53view0 fileciteturn0file3

Önerdiğim runtime akışı şöyledir:

```text
Camera Frame
   -> Condition Profile Model
   -> Temporal smoothing / hysteresis
   -> Routing Policy
      -> if confidence low: vehicle_detector_general
      -> if confidence high AND expert_proven_better: specialist detector
      -> if critical/risky and uncertainty high: general + specialist double-run
   -> Vehicle Detections JSON
   -> Tracking
   -> Risk Scoring
   -> Evidence / QoD candidate
```

Bu akışta **general model her zaman fallback** olmalıdır. Specialist model hiçbir zaman “tek güvenlik ağı” olmamalıdır. Condition confidence düşükse, son birkaç framede koşul kararsızsa, specialist health check başarısızsa, model warm değilse veya p95 latency bütçeyi aşıyorsa otomatik fallback general’e dönülmelidir. Ayrıca condition değişiminde ani model zıplamasını engellemek için **hysteresis** kullanılmalıdır; örneğin `night_low_light`’a geçmek için 5–10 ardışık frame veya 300–500 ms tutarlı koşul sinyali istenmeli, geri dönüş için daha düşük eşik kullanılmalıdır. Bu tür top-K expert ve confidence-controlled routing mantığı adverse-condition routing literatürüyle uyumludur. citeturn53view0turn38view1

Aynı frame’de hem general hem specialist çalıştırma kararında ise önerim nettir:
**normal modda tek detector**, **kritik modda veya routing belirsizliğinde çift detector**.
Bunun üç kullanım alanı vardır. Birincisi riskli araç/QoD adayı durumda kanıt kalitesini yükseltmek. İkincisi condition confidence sınır bölgesindeyken yanlış routing riskini azaltmak. Üçüncüsü de shadow-mode benchmark toplamak. Her framede iki model çalıştırmak, specialist sayısı arttıkça latency ve memory yükünü gereksiz büyütür. Sizin mimarinizdeki kontrollü QoD tetikleme fikri de bu kararı destekliyor. fileciteturn0file3

Uzman modelin “general’den anlamlı şekilde daha iyi” sayılması için proje içi bir promotion kuralı belirlemek gerekir. Benim önerim şudur:

- Condition-specific held-out sette **en az +2.0 mAP@0.5:0.95** **veya** **+3 AP@0.5** kazanç
- Ya da özellikle önemliyse **recall’da +4 puan** ve missed detection sayısında belirgin düşüş
- `FP/min` artışı %10’dan fazla olmamalı
- Specialist swap-in sonrası `p95 latency` toplam bütçeyi aşmamalı
- Yanlış route olabilecek “mixed misroute set” üzerinde specialist, general’e göre dramatik bozulma göstermemeli

Bu eşikler literatürden birebir alınmış zorunlu kurallar değil; proje operasyonu için benim önerdiğim kabul kriterleridir. Çünkü koşul uzmanı yaklaşımında asıl maliyet yanlış pozitif birkaç AP kaybı değil, **yanlış expert çağrısı yüzünden downstream tracking/plate/evidence zincirinin bozulmasıdır**.

Salt mAP yetmez. Özellikle düşük ışık bench’inde şu ek metrikleri de tutmanızı öneririm:

| Metrik | Neden gerekli |
|---|---|
| **FP/min** | Gece parlamaları ve yansımaların yanlış araç üretme eğilimini görünür kılar |
| **Missed detection rate** | Downstream plate, speed ve target selection’in asıl kırılgan noktası kaçırılan araçtır |
| **BBox adequacy** | Algı var gibi görünse de crop downstream OCR için işe yarıyor mu sorusunu cevaplar |
| **Confidence stability** | Aynı araç track’i boyunca skorların zıplaması tracking ve event confidence’ı bozar |
| **Track continuity / fragmentation** | ByteTrack çizgisinin de gösterdiği gibi düşük skor kutuları atılırsa track parçalanır. citeturn43academia1 |
| **Time-to-first-stable-detection** | Kadraja giren aracı kaç frame sonra güvenilir biçimde yakalıyor? |
| **Evidence usability** | Son ekran görüntüsü gerçekten kanıt olarak okunabilir mi? |

Ayrıca bir **robustness stress test** katmanı eklemek çok değerlidir. 2026 tarihli çalışma, adverse condition şiddetini kademeli sentetik operatörlerle artırıp modelin ilk başarısızlık noktasını “Average First Failure Coefficient” ile ölçmenin yararlı olduğunu gösteriyor. Bu metrik doğrudan lider karar kriteriniz olmayabilir; ama hangi specialist’in hangi şiddet seviyesinde kırıldığını görmek için çok faydalıdır. Aynı çalışma sentetik adverse-condition eğitiminin fayda sağlarken aşırı yapıldığında forgetting doğurabileceğini de gösteriyor. citeturn52view0

Preprocessing konusunda nihai önerim şudur:
**default çözüm specialist detector olsun; preprocessing ise condition-specific, ikincil deney hattı olarak kalsın.**
Bunun sebebi şu: NOD ve FeatEnHancer detector-guided low-light enhancement’ın faydalı olabileceğini gösteriyor; fakat Foggy Cityscapes çalışması image dehazing’in sisli semantic perception için yalnızca marjinal katkı verdiğini bildiriyor. Yani preprocessing her yerde “bedava kazanç” değildir. Bu yüzden tek başına “all-weather detector + universal preprocessing” stratejisi yerine, önce detector’ı condition-specific fine-tune edin; preprocessing’i ise night/fog branch’inde opsiyonel ablation olarak deneyin. citeturn51view0turn51view1turn50view0

## Uygulama planı, repo önerisi ve nihai karar

Tavsiye ettiğim geliştirme sırası şöyledir:

İlk fazda, dört sınıfa indirgenmiş ortak şema ile **genel veri seti** hazırlanmalıdır. BDD100K temel omurga, UA-DETRAC fixed-camera destek veri kaynağı olmalıdır. Video-level leakage önlemek için split’ler video bazında yapılmalı, aynı sahneden çıkan kareler train/val/test arasında dağılmamalıdır. Sonra `YOLO11n`, `YOLOv10n`, `YOLO11s` üçlüsüyle general benchmark alınmalıdır. Bu fazın sonunda “best_general.ckpt” seçilmeden hiçbir specialist açılmamalıdır. citeturn31view0turn32view0turn56view1turn37view3

İkinci fazda ilk specialist olarak **night_low_light** açılmalıdır. Bu hem sizin mevcut elinizde smoke test videosu olan tek koşul olması nedeniyle, hem de low-light sorununun literatürde ayrı zorluk olarak tekrar tekrar gösterilmiş olması nedeniyle en mantıklı ilk uzmandır. Night specialist’i doğrudan COCO’dan değil, **best_general checkpoint’inden** başlatın. Bu, araç şekli/ölçeği/genel yol sahnesi bilgisini korurken yalnızca düşük ışık domainine doğru ince ayar yapmanızı sağlar. citeturn51view0turn51view1

Üçüncü fazda yalnızca night specialist gerçekten anlamlı uplift üretirse **rain**, ardından **fog_low_visibility** açılmalıdır. Eğer night specialist bile benchmark’ta general’i anlamlı biçimde geçemiyorsa, erken specialist çoğaltmanın faydası düşüktür; o durumda Strateji 3 yönünde “tek general + daha iyi augmentation/preprocessing” ekseni güçlendirilmelidir. WEDGE ve Foggy Cityscapes sonuçları sentetik adverse data’nın destekleyici olarak işe yarayabileceğini, fakat aşırı bağımlılığın riskli olduğunu düşündürüyor. citeturn47view0turn50view0turn52view0

Colab deney planı da buna göre sade tutulmalıdır:

- **Deney ailesi A:** `general_yolo11n`, `general_yolov10n`, `general_yolo11s`
- **Deney ailesi B:** `night_yolo11n_from_general`, `night_yolo11s_from_general`
- **Deney ailesi C:** `rain_yolo11n_from_general`, `fog_yolo11n_from_general`
- **Deney ailesi D:** `night_preproc_plus_general` ve `fog_preproc_plus_general` ablation’ları
- **Deney ailesi E:** `rtdetr_r18_general` araştırma benchmark’ı

Repo tarafında ise condition experts için şu dosya/klasör yapısı yeterli ve temiz olur:

- `research/03_condition_experts/summary.md`
- `research/03_condition_experts/strategy_comparison.md`
- `research/03_condition_experts/dataset_matrix.md`
- `research/03_condition_experts/benchmark_protocol.md`
- `research/03_condition_experts/runtime_routing_policy.md`
- `research/03_condition_experts/colab_plan.md`
- `models/registry/vehicle_detector_registry.yaml`
- `configs/condition_profiles.yaml`
- `configs/condition_routing.yaml`
- `experiments/condition_experts/benchmark_results.csv`
- `experiments/condition_experts/manual_review_dark.csv`

`vehicle_detector_registry.yaml` içinde her model için şu alanlar tutulmalıdır:
`model_version`, `family`, `condition_tag`, `weights_path`, `input_size`, `benchmark_condition_set`, `uplift_vs_general`, `p95_latency_ms`, `memory_mb`, `export_format`, `enabled`, `proven_better`.
Böylece routing katmanı “hangi model var?” değil, “hangi model aktif ve benchmark’ta kanıtlı?” sorusunu cevaplar.

Event/evidence paketinde de hangi specialist’in kullanıldığı mutlaka loglanmalıdır. Örnek alanlar:

- `condition_profile`
- `condition_confidence`
- `detector_selected`
- `detector_family`
- `detector_version`
- `routing_reason`
- `fallback_used`
- `double_run_used`
- `evidence_frame_path`

Bu sayede final raporda ve mobil kanıt ekranında “neden bu model seçildi?” sorusuna açıklanabilir yanıt verilebilir; bu da sizin evidence/QoD anlatınızla doğrudan uyumludur. fileciteturn0file3

Bu araştırmanın nihai kararı şudur:

1. **Seçilecek strateji: Strateji 1**
   Önce genel vehicle detector fine-tune, sonra yalnızca benchmark’ta gerçekten daha iyi olduğu kanıtlanan specialist detector’lar.

2. **İlk başlanacak model:** `YOLO11n`
   Çünkü sizde baseline olarak zaten planlı, operasyonel olarak en hızlı ayağa kalkacak seçenek o. citeturn56view1

3. **İlk benchmark challengers:** `YOLOv10n`, `YOLO11s`, sonra `YOLOv10s`, ardından `RT-DETR-R18`. citeturn37view3turn58view3

4. **İlk açılacak specialist:** `vehicle_detector_night_low_light`
   Çünkü hem proje test materyaliniz orada, hem low-light literatürde ayrı problem olarak güçlü biçimde doğrulanmış durumda. citeturn51view0turn51view1

5. **MVP uzman listesi:**
   `general`, `night_low_light`, `rain`, `fog_low_visibility`

6. **İlk etapta açılmaması gereken uzmanlar:**
   `glare`, `low_contrast`, `tunnel_or_parking_dark`, `dark`
   Bunlar önce condition profile tarafında label olarak izlenmeli, sonra veri birikirse uzmanlaştırılmalı.

7. **Preprocessing politikası:**
   Detector’ı ikame eden ana çözüm değil; specialist detector’a destek olan ikincil ablation hattı.

8. **General fallback politikası:**
   Her zaman açık, her zaman güvenli çıkış yolu.

## Açık sorular ve sınırlamalar

BDD100K, UA-DETRAC, ACDC, DAWN ve SHIFT tarafında indirme portalı bazlı kullanım şartları burada web’den tam doğrulanamamayan noktalar içeriyor; bu yüzden bu veri setleri için **release/submission öncesi lisans doğrulaması yapılmalı**. Waymo’nun non-commercial şartı, WEDGE’in CC BY-NC-SA 4.0 yapısı ve ExDark’ın ticari kullanım notu ise daha nettir. citeturn44view1turn47view0turn46view0

İkinci sınırlama, MacBook local runtime için gerçek latency/FPS verisinin henüz ölçülmemiş olmasıdır. Kamu benchmark’ları T4 TensorRT, CPU ONNX veya üretici ortamları üzerindedir; son karar mutlaka sizin gerçek edge stack’inizde verilmelidir. Özellikle condition expert sayısı arttıkça memory/warm-up davranışı da ölçülmelidir. citeturn56view1turn37view3turn58view3

Üçüncü sınırlama, `glare`, `tunnel_or_parking_dark` ve `low_contrast` için public bbox verisinin dağınık olmasıdır. Bu yüzden bu uzmanlar araştırma olarak değerlidir; fakat MVP’de ayrı deploy modeli olmaları için yeterli zeminin henüz daha zayıf olduğu görülüyor. Bu boşluk, kontrollü kendi veri toplamanızla ileride kapatılabilir.