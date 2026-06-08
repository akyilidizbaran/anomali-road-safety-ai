# Veri Seti Stratejisi

## Ana Karar

Her görev için ayrı veri seti, ayrı etiket yapısı, ayrı model ve ayrı metrik kullanılmalıdır. Tek veri seti bütün görevleri karşılamaz.

## Mevcut Veri Kararı

* Kullanılacak veri setleri araştırma ve uygulanmış çalışmalar incelenerek saptanacak.
* Test ve model karşılaştırmaları öncelikle internet üzerindeki açık veri setleri, makale ekleri, benchmark çalışmaları ve açık kaynak proje verileriyle yapılacak.
* Veri seti lisansları ilgili makale, proje sayfası, dataset card veya açık kaynak lisans metni üzerinden doğrulanacak.
* Yerel veri mümkünse toplanmayacak.
* Maskeleme yapılmayacak.
* Bu karar nedeniyle veri seti lisansı, kullanım izni, kişisel veri riski ve raporda etik açıklama daha önemli hale gelir.
* Test verisinin gerçekleştirildiği ortam izole olacak.

## Görev Bazlı Kaynaklar

* Araç tespiti: BDD100K, COCO, KITTI, UA-DETRAC.
* Plaka: CCPD, UFPR-ALPR, AOLP, varsa yerel Türk plaka verisi.
* OCR: Plaka crop verileri, sentetik Türk plaka üretimi.
* Şerit: TuSimple, CULane, BDD100K lane.
* Hava/görüş: ACDC, BDD100K weather, DAWN.
* Sürücü davranışı: State Farm, AUC Distracted Driver, Drive&Act.
* Hız: BrnoCompSpeed, AI City Challenge, kontrollü kalibrasyon videoları.

## Split

* %70 train.
* %15 validation.
* %15 test.
* Video-level split zorunlu.

## Veri Toplama

Yerel veri ana kaynak olarak planlanmaz. Zorunlu demo veya kontrollü doğrulama görüntüsü alınırsa bu veri repo dışında, erişimi sınırlı ortamda tutulmalıdır.

* Normal sahnelerde 0.5 saniyede bir frame.
* Kritik olaylarda 0.1-0.2 saniyede bir frame.
* Benzer kareleri elemek için duplicate kontrolü.

## Sorulacak Noktalar

* Maskeleme yapılmayacaksa kullanılacak açık veri setlerinin plaka/yüz paylaşım koşulları tek tek nasıl doğrulanacak?
* Final demo için canlı görüntü kaydı tutulacak mı, yoksa yalnız anlık inference mı yapılacak?
