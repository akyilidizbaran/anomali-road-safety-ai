# Deep Research Prompt — Speed Fusion Layer İçin Ek Bakış Açıları

Anomali Road Safety AI projesi için tek kamera tabanlı hız kestirimi kapsamında `Speed Fusion Layer` tasarımına yönelik çok kapsamlı bir derin araştırma yapmanı istiyorum.

## Proje Bağlamı

Proje, mobil veya sabit kamera görüntüsünden araç tespiti, takip, plaka/OCR, koşul profili, risk kararı ve evidence JSON üreten bir karar destek sistemidir. Mevcut hız çalışmasında üç farklı sinyal düşünülmektedir:

1. Plaka ölçeği tabanlı hız adayı:
   * Türkiye uzun plaka boyutu fiziksel referans olarak kullanılır.
   * Plaka bbox/center hareketiyle yaklaşık derinlik ve hız adayı çıkarılır.
2. Homografi / track tabanlı hız adayı:
   * Sabit kamera ve yol düzlemi kalibrasyonu varsa araç alt merkez noktası dünya düzlemine projekte edilir.
   * Track boyunca yer değiştirme / zaman farkı ile km/s adayı üretilir.
3. Araç boyutu / wheelbase prior tabanlı hız adayı:
   * Araç crop'undan araç tipi, mümkünse marka/model veya gövde sınıfı tahmin edilir.
   * Araç boyutu veya wheelbase prior hız hesabına yardımcı ölçek olarak kullanılır.

Sistem hukuki hız ölçüm sistemi değildir. Kalibrasyon veya güvenilir referans yoksa mutlak km/s iddiası yerine göreli hız / motion anomaly sinyali üretilmelidir.

## Araştırma Amacı

Bu üç sinyale ek olarak tek kamera hız kestiriminde kullanılabilecek başka güvenilir ve uygulanabilir bakış açılarını araştır. Özellikle bizim sabit yol kenarı kamera, 720p video, MacBook local inference ve Colab deney ortamı koşullarımızı dikkate al.

## Araştırılacak Başlıklar

1. Plate-scale, homography-track ve vehicle-dimension prior sinyallerinin güçlü/zayıf yanları.
2. Bu sinyaller nasıl ağırlıklı fusion ile birleştirilebilir?
3. Confidence-aware fusion nasıl tasarlanmalı?
4. Kalibrasyon yoksa relative speed nasıl normalize edilmeli?
5. Track history, bbox scale, optical flow, lane geometry, vanishing point, camera height, object bottom-center ve wheel/keypoint sinyalleri nasıl kullanılabilir?
6. Tek kamera hız kestiriminde yaygın akademik yaklaşımlar nelerdir?
7. BrnoCompSpeed erişimi yoksa hangi alternatif dataset veya kontrollü test planı kullanılabilir?
8. Ground truth hız verisi olmadan hangi smoke-test ve manual-review metrikleri raporlanabilir?
9. Hangi sinyaller evidence JSON içine yazılmalı?
10. Hangi durumlarda sistem `speed_mode=absolute_candidate`, `speed_mode=relative`, `speed_mode=unavailable` döndürmeli?

## Beklenen Çıktı Formatı

1. Yönetici özeti
2. Mevcut üç sinyalin değerlendirmesi
3. Eklenebilecek yeni hız sinyalleri
4. Önerilen Speed Fusion Layer mimarisi
5. Confidence ve fallback tasarımı
6. Dataset / benchmark alternatifi
7. Manuel test ve rapor metrikleri
8. Evidence JSON alanları
9. Riskler ve sınırlamalar
10. Nihai öneri
11. Kaynakça

## Net Karar İsteği

Sonuçta şu sorulara açık cevap ver:

* Bu projede ilk speed fusion sürümü hangi sinyalleri kullanmalı?
* Mutlak km/s adayı hangi koşullarda üretilebilir?
* Hangi koşullarda yalnız göreli hız üretilmelidir?
* Hangi ek sinyal en hızlı uygulanabilir?
* Hangi ek sinyal akademik olarak en güçlü ama uygulama maliyeti yüksek?
* BrnoCompSpeed yoksa en savunulabilir doğrulama planı nedir?

Kaynakları güvenilir bağlantılarla ver. Kesin doğruluk veya hukuki hız ölçümü iddiası kurma.
