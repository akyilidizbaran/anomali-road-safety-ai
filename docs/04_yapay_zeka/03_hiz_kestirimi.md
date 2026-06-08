# Hız Kestirimi

## Kritik İlke

Gerçek km/s tahmini yalnız kamera sabitlenirse ve referans mesafe biliniyorsa savunulabilir. Kalibrasyon yoksa sistem mutlak hız iddiası üretmemelidir.

## Mevcut Karar

Demo gerçek yol kenarında ve sabit kamera ile yapılacak. Projenin hedefi mutlak km/s tahmini üretmektir. Eğer kalibrasyon veya görüntü koşulları yeterli olmazsa sistem göreli hız/risk sınıflandırmasına düşecektir.

Ground truth hız yaklaşımı, yerel sahada zorunlu doğrudan ölçüm yapmak yerine literatürdeki/internette yayımlanmış hız kestirimi çalışmalarından yöntem ve değerlendirme fikri türetmek olarak belirlenmiştir. Final raporda bu yaklaşım kaynaklandırılmalıdır.

Kalibrasyon denemesi **final scope** olarak tutulacaktır. MVP aşamasında hız modülü mutlak km/s iddiası kurmak yerine track tabanlı göreli hareket, ani hızlanma/yavaşlama ve motion anomaly sinyali üretebilir.

## Referans Mesafe Otomatik Ölçülebilir mi?

Tek kameradan, sahnede hiçbir bilinen ölçek yokken güvenilir gerçek mesafe otomatik çıkarılamaz. Monoküler görüntüde ölçek belirsizliği vardır; yani sistem piksel hareketini görür ama bu hareketin kaç metreye karşılık geldiğini bilmek için bir referansa ihtiyaç duyar.

Pratik seçenekler:

1. **Yarı otomatik kalibrasyon:** Kullanıcı görüntü üzerinde yol üzerindeki 4 noktayı seçer ve bilinen mesafeyi girer. Homografi bu bilgiyle kurulur.
2. **Sahaya referans marker koyma:** Yol kenarına veya güvenli alana iki görünür marker konur; aralarındaki mesafe bilinir.
3. **Bilinen şerit genişliği varsayımı:** Şerit genişliği yaklaşık ölçek olarak kullanılır. Daha az güvenilirdir, çünkü yol tipine ve kamera açısına bağlı hata üretir.
4. **Harita/GPS/IMU desteği:** Kamera konumu ve yol geometrisi biliniyorsa destekleyici ölçek sağlanabilir; MVP için karmaşıktır.
5. **Fallback:** Referans güvenilir değilse mutlak km/s yerine göreli hız sınıflandırması yapılır.

Final scope için önerilen tasarım: Kullanıcıya demo başlangıcında kısa bir kalibrasyon adımı sunmak. Kullanıcı iki veya dört referans noktası seçer; sistem homografi matrisini hesaplar ve hız kestirimini confidence ile birlikte verir.

MVP için önerilen tasarım: Kalibrasyon UI veya marker zorunlu tutulmaz. Track history üzerinden göreli hareket skoru ve risk etiketi üretilir; raporda bunun km/s tahmini olmadığı açıkça yazılır.

## Kalibre Edilmiş Mod

1. Kamera sabitlenir.
2. Yol üzerinde gerçek mesafesi bilinen noktalar seçilir.
3. Piksel koordinatları dünya düzlemine homografiyle dönüştürülür.
4. Hedef araç alt merkez noktası takip edilir.
5. Yer değiştirme / zaman farkı ile hız hesaplanır.
6. Temporal smoothing uygulanır.

## Kalibrasyonsuz Mod

* Göreli hız.
* Ani hızlanma/yavaşlama.
* Takip tabanlı hareket aykırılığı.
* Risk sınıfı.

## Rapor Cümlesi

> Kalibre edilmiş sabit kamera senaryosunda sistem gerçek km/s tahmini üretir. Kalibrasyonun yetersiz olduğu mobil veya serbest kamera senaryolarında ise mutlak hız iddiası üretmek yerine göreli hız ve hareket aykırılığı skoruyla risk değerlendirmesi yapar.

## Metrikler

MVP:

* Relative motion consistency.
* Motion anomaly event accuracy.
* Track continuity.
* Risk sınıfı doğruluğu.

Final scope:

* MAE.
* RMSE.
* km/s hata aralığı.
* Calibration confidence.
