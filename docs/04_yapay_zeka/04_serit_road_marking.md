# Şerit / Road Marking Analizi

## Amaç

Yol çizgilerini veya şerit sınırlarını tespit ederek hedef aracın şerit içindeki konumunu ve ihlal şüphesini değerlendirmek.

## Aday Yaklaşımlar

1. Lane-specific modeller: Ultra-Fast Lane Detection, LaneATT, CLRNet.
2. Multi-task sürüş modelleri: YOLOP, YOLOPv2.
3. YOLO/segmentation ile road marking tespiti.

## MVP Yaklaşımı

MVP için basit segmentation veya YOLO tabanlı road marking gösterimi yapılabilir. Daha sonra lane-specific modellere geçilebilir.

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

* MVP’de gerçek lane model mi, görsel road marking detector mı?
