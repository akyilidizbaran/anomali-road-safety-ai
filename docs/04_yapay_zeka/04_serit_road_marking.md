# Şerit / Road Marking Analizi

## Amaç

Yol çizgilerini veya şerit sınırlarını tespit ederek hedef aracın şerit içindeki konumunu ve ihlal şüphesini değerlendirmek.

## Aday Yaklaşımlar

1. Lane-specific modeller: Ultra-Fast Lane Detection, LaneATT, CLRNet.
2. Multi-task sürüş modelleri: YOLOP, YOLOPv2.
3. YOLO/segmentation ile road marking tespiti.

## MVP Yaklaşımı

Şerit/road marking modülü, araç tespiti + tracking + plaka/OCR + evidence hattından sonra ele alınacaktır.

MVP'de lane sonucu zorunlu event alanı değildir. İlk uçtan uca sistem event/evidence üretir hale geldikten sonra basit segmentation, YOLO tabanlı road marking gösterimi veya lane-specific modeller karşılaştırılabilir.

## Risk Sinyalleri

* Araç alt merkez noktası şerit sınırına yakın.
* Şerit çizgisi geçiliyor.
* Kısa zaman penceresinde ani yanal hareket var.
* Görüş koşulu düşük olduğu için belirsizlik yüksek.

## Metrikler

* Lane IoU.
* F1.
* Lane accuracy.
* Lane violation event accuracy.

## Sorulacak Noktalar

* Plate/evidence hattı tamamlandıktan sonra ilk lane yaklaşımı segmentation mı, lane-specific model mi olacak?
