# Dengeli Başarı Metrikleri

## Mevcut Karar

Model geliştirmede başarı tek bir metrikle ölçülmeyecek. Doğruluk, hız, gecikme, model boyutu ve sistem/evidence katkısı birlikte değerlendirilecek.

## Neden Dengeli Metrik?

Bu proje canlı mobil-edge yol güvenliği sistemi olduğu için yalnız yüksek accuracy yeterli değildir. Model yüksek doğruluk verse bile çok yavaşsa canlı sistem için uygun değildir. Çok hızlı ama yanlış alarm oranı yüksekse evidence kalitesi düşer.

## Araç Tespiti İçin İlk Metrik Paketi

| Metrik | Amaç |
|---|---|
| mAP@0.5 | Araç bbox başarımı |
| Precision | Yanlış alarm kontrolü |
| Recall | Araç kaçırma riskini ölçme |
| F1 | Precision/recall dengesi |
| Inference latency | Canlı sistem gecikmesi |
| FPS | Gerçek zamanlılık |
| Model size | Edge/mobile uyumu |
| Export success | ONNX/TFLite dönüşebilirlik |
| Overlay compatibility | Mobil UI’ye aktarılabilir JSON üretimi |

## Sistem Seviyesi Metrikler

* Uçtan uca latency.
* Pipeline FPS.
* Frame drop oranı.
* CPU/GPU kullanımı.
* Bellek kullanımı.
* Event JSON üretim süresi.

## Event/Evidence Katkısı

Araç tespiti modeli yalnız bbox üretmez; sonraki modüllerin temel girdisidir. Bu yüzden şu sorular da ölçülmelidir:

* Hedef araç seçimi için yeterli bbox kararlılığı var mı?
* Tracking için yeterli detection sürekliliği var mı?
* Plaka ROI çıkarımı için araç bbox yeterince doğru mu?
* Evidence görselinde bbox anlaşılır mı?

## Raporlama

Final raporda tek bir “başarı oranı” yerine küçük bir metrik tablosu kullanılmalıdır. Bu tablo jüriye sistemin canlı kullanım için dengeli tasarlandığını gösterir.
