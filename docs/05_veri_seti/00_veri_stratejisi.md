# Veri Seti Stratejisi

## Ana Karar

Her görev için ayrı veri seti, ayrı etiket yapısı, ayrı model ve ayrı metrik kullanılmalıdır. Tek veri seti bütün görevleri karşılamaz.

## Mevcut Veri Kararı

* Kullanılacak veri setleri araştırma ve uygulanmış çalışmalar incelenerek saptanacak.
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

* Normal sahnelerde 0.5 saniyede bir frame.
* Kritik olaylarda 0.1-0.2 saniyede bir frame.
* Benzer kareleri elemek için duplicate kontrolü.

## Sorulacak Noktalar

* Maskeleme yapılmayacaksa kullanılacak açık veri setlerinin plaka/yüz paylaşım koşulları tek tek nasıl doğrulanacak?
* Final demo için canlı görüntü kaydı tutulacak mı, yoksa yalnız anlık inference mı yapılacak?
