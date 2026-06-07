# Araç Tespiti ve Takip

## Amaç

Canlı görüntüde araçları tespit etmek, sınıflandırmak, takip ID’si vermek ve hedef araç seçimi için kararlı çıktı üretmek.

## Araç Tespiti

Aday modeller:

* YOLOv8/v9/v10/v11 nano/small.
* RT-DETR edge uygunluğu araştırılabilir.

Sınıflar:

* car
* bus
* truck
* motorcycle

## Takip

Aday tracker:

* ByteTrack.
* BoT-SORT.
* DeepSORT.
* OC-SORT.

## Metrikler

Araç tespiti:

* mAP@0.5
* mAP@0.5:0.95
* Precision
* Recall
* F1

Takip:

* IDF1
* MOTA
* ID switch
* Track stability

## Açık Sorular

* Başlangıç modeli hangi YOLO sürümü olacak?
* Takip için ByteTrack mi BoT-SORT mu seçilecek?
