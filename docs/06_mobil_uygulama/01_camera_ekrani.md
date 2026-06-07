# Camera Ekranı

## Amaç

Canlı demo ekranıdır. Kullanıcı sistemin şu anda ne gördüğünü ve hangi kararları verdiğini izler.

## Gösterilecek Bilgiler

* Canlı kamera görüntüsü.
* Araç bounding box.
* Hedef araç vurgusu.
* Araç tipi.
* Track ID.
* Plaka kutusu.
* OCR sonucu.
* Risk seviyesi.
* Normal/kritik mod.
* QoD durumu.
* FPS.
* Latency.
* Hava/görüş etiketi.

## Overlay Kuralları

* Düşük risk: yeşil.
* Orta risk: sarı.
* Yüksek risk: turuncu.
* Kritik risk: kırmızı.
* Hedef araç diğerlerinden daha belirgin çizilmelidir.

## Sorulacak Noktalar

* Camera ekranında tüm metrikler aynı anda mı, yoksa debug modu açılınca mı görünecek?
