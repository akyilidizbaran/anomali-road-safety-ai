# Etiketleme Standardı

## Araç Tespiti

Etiket:

* bbox
* sınıf
* occlusion durumu
* frame ID

Format:

* YOLO txt
* COCO JSON

## Plaka

Etiket:

* plate bbox
* OCR text
* okunabilirlik skoru
* blur/düşük ışık etiketi

## Şerit

Etiket:

* lane line
* mask
* road marking sınıfı

## Cabin Risk

Etiket:

* driver visible
* passenger count
* phone/smoking/seatbelt
* visibility sufficient / insufficient

## Kalite Kontrol

* Her etiket ikinci kişi tarafından gözden geçirilmeli.
* Belirsiz örnekler “uncertain” olarak işaretlenmeli.
* Test seti elle daha sıkı kontrol edilmeli.

## Sorulacak Noktalar

* Roboflow mu CVAT mı ana etiketleme aracı olacak?
