# Dataset Source and License Checklist

## Amaç

Condition-specific detector stratejisinde kullanılacak veri setleri için kaynak, koşul etiketi, bbox uygunluğu ve lisans riskini tek yerde izlemek.

Bu dosya final lisans onayı değildir. Her veri seti indirilmeden ve raporda kullanılmadan önce resmi download/terms sayfası ayrıca kaydedilmelidir.

## Kaynak Kontrol Tablosu

| Dataset | Kaynak | Koşul Etiketi | Araç Bbox | Lisans / Kullanım Durumu | Projedeki Rol |
|---|---|---|---|---|---|
| BDD100K | https://github.com/ucbdrive/bdd100k | `weather`, `scene`, `timeofday` alanları var | `box2d` road object sınıfları var | GitHub repo lisansı BSD-3; download portal şartları ayrıca saklanmalı | General road-domain + night/rain/fog split |
| UA-DETRAC | https://arxiv.org/abs/1511.04136 | Weather/occlusion/truncation annotation var | Vehicle bbox var | Lisans resmi download kaynağından doğrulanmalı | Fixed-camera adaptation ve tracking-readiness |
| ACDC | https://acdc.vision.ee.ethz.ch/ | Fog, nighttime, rain, snow adverse setleri | Object detection benchmark desteği var | Site non-commercial kullanım şartı bildiriyor; terms dosyası saklanmalı | Night/rain/fog external adverse benchmark |
| Foggy Cityscapes / Foggy Driving | https://arxiv.org/abs/1708.07819 | Fog odaklı | Foggy Driving object detection annotation içerir | Cityscapes türevi; Cityscapes terms non-commercial ve redistribution kısıtlı | Fog specialist test ve sentetik fog desteği |
| ExDark | https://github.com/cs-chan/Exclusively-Dark-Image-Dataset | 10 low-light condition | Object bbox var | BSD-3; ticari kullanım için yazarla iletişim notu var | Night/low-light auxiliary data |
| NOD | https://arxiv.org/abs/2110.10364 | Night / extreme low-light | Instance-level object annotation subset | Resmi veri erişimi ve lisans doğrulanmalı | Night specialist değerlendirme ve low-light analiz |
| DAWN | https://arxiv.org/abs/2008.05402 | Fog, rain, snow, sandstorm | Vehicle detection için tasarlanmış | IEEE DataPort / resmi erişim lisansı doğrulanmalı | Rain/fog/snow external test |
| SHIFT | https://arxiv.org/abs/2206.08367 | Cloudiness, rain, fog intensity, time of day | 2D detection görevleri var | Resmi download ve lisans doğrulanmalı | Sentetik controlled condition split |
| WEDGE | https://arxiv.org/abs/2305.07528 | 16 extreme weather condition | 2D bbox var | CC BY-NC-SA 4.0; ticari kullanım için riskli | Research-only synthetic supplement |
| Waymo Open Dataset | https://waymo.com/open/terms/ | Çeşitli koşullar; condition split doğrudan ana hedef değil | Camera/lidar labels var | Non-commercial; production/deploy kısıtları var | External research benchmark, MVP training için dikkat |

## Öncelik Kararı

İlk turda veri seti önceliği:

1. **BDD100K**: Ana road-domain general detector.
2. **UA-DETRAC**: Sabit kamera / trafik sahnesi domain desteği.
3. **ACDC**: Night/rain/fog adverse validation.
4. **ExDark veya NOD**: Night/low-light specialist için yardımcı kaynak.
5. **Foggy Cityscapes / DAWN**: Fog/rain external benchmark.

Waymo ve WEDGE bu aşamada ana eğitim datası olmamalıdır. Waymo non-commercial terms nedeniyle, WEDGE ise CC BY-NC-SA 4.0 nedeniyle final ürünleşme iddiasında dikkatli kullanılmalıdır.

## Doğrulama Checklist'i

Her veri seti için indirme öncesi şu alanlar doldurulmalı:

* [ ] Resmi download URL
* [ ] Terms/license URL
* [ ] Lisans adı
* [ ] Commercial / non-commercial durumu
* [ ] Redistribution izni
* [ ] Model weights paylaşım kısıtı
* [ ] Kişisel veri/plaka/yüz riski
* [ ] Citation BibTeX
* [ ] İndirilen subset
* [ ] Download tarihi
* [ ] YOLO/COCO dönüşüm script ihtiyacı
* [ ] Train/val/test split stratejisi

## Kaynaklardan Çıkan Kritik Notlar

* BDD100K format dokümanı `weather`, `scene`, `timeofday` alanlarını ve road object `box2d` etiketlerini listeler.
* UA-DETRAC makalesi 100 video, 140K+ frame, weather/occlusion/truncation/vehicle bbox annotation bilgisini verir.
* ExDark resmi GitHub sayfası 7,363 low-light image, 10 condition ve bbox bilgisini verir; ticari kullanım için iletişim notu içerir.
* Ultralytics YOLO11 ve YOLOv10 kullanımı lisans açısından ayrıca değerlendirilmeli; Ultralytics tarafında AGPL/Enterprise riski vardır.
* Cityscapes türevi fog veri setlerinde redistribution ve commercial use kısıtları final rapor/demo materyali açısından dikkat ister.
