# Seatbelt Specialist Araştırması

## Kapsam

Seatbelt specialist, seçilmiş `POSE-EXP-009` sürücü torso ROI üzerinde çalışır.
Dirsek, bilek veya sürekli kol iskeleti kullanmaz. Telefon, el ve sigara
specialist'leri bu teslimatın parçası değildir.

## Mevcut Sonuç

`SEATBELT-EXP-001`, OpenCV çizgi segmentleriyle torso üzerinde diyagonal kemer
kanıtı arayan muhafazakar bir referans deneyidir. Üç mevcut videoda çalıştırılmış,
ancak manuel incelemede araç yüzeyi ve yansımaların kemer benzeri çizgi
üretebildiği görülmüştür.

Bu nedenle deney **seçilmiş seatbelt baseline değildir**:

* çizgi yokluğu `unbelted` olarak yorumlanmaz;
* `incorrect` sınıfı açılmaz;
* event contract içinde `seatbelt_status=unknown` korunur;
* çıktı yalnız benchmark, veri toplama ve candidate evidence amacıyla kullanılır.

## 2026-06-14 Düşük Işık Teşhisi

`video_2` yaklaşık 4.4-5.6 saniye aralığı kare bazında incelendi:

* `SEATBELT-EXP-001` video genelinde sıfır sonuç üretmemiştir; 241-242.
  karelerde iki evaluable `belted` adayı vardır. Ancak oran `0.0096` olduğu için
  temporal sonuç doğru biçimde `unknown` kalmıştır.
* Ekran görüntüsündeki 250. kare civarında `POSE-EXP-009` torso ROI tamamen
  kaybolmaktadır.
* Mevcut torso crop'ları bazı karelerde sürücü gövdesinden çok kapı, cam ve araç
  dış yüzey çizgilerini içermektedir.
* Global sahne condition etiketi tek başına yeterli değildir. Seatbelt specialist
  kendi lokal driver-context ROI kalite profilini hesaplamalıdır.

Bu nedenle `POSE-EXP-009` sürücü/torso evidence anchor olarak kalır; seatbelt
classifier girdisi ise YuNet yüz, cabin bbox ve kısa süreli cabin-motion takibiyle
üretilen daha geniş driver-context ROI olacaktır.

## SEATBELT-EXP-002

Condition-aware classifier challenger hattı eklendi:

1. YuNet yüzü view-profile ile sürücü adayı olarak alınır.
2. Ani yüz sıçramaları reddedilir.
3. Yüz kısa süre kaybolursa ROI cabin hareketiyle en fazla 25 kare taşınır.
4. Lokal brightness/contrast/dark ratio ölçülür.
5. `raw` ve condition-routed (`CLAHE` veya `gamma+CLAHE`) crop birlikte ölçülür.
6. Candidate kararlar manuel review tamamlanmadan event/risk'e yazılmaz.

İlk checkpoint challenger:

* `RISEF/yolov11s-seatbelt`
* YOLO11s binary image classifier
* AGPL-3.0
* Model kartına göre gece, renkli cam ve yoğun parlama verisi yetersizdir.
* Eğitim verisi ciddi sınıf dengesizliği taşır.

Bu model yalnız karşılaştırmalı pretrained challenger'dır; baseline değildir.

## 2026-06-14 Erteleme Kararı

Kullanıcı full-video manuel incelemesinde `SEATBELT-EXP-002` çıktısında da
güvenilir ve görünür bir kemer kararı göremedi. Bu nedenle seatbelt modeli
seçilmeden ertelenmiştir:

* `SEATBELT-EXP-001` reference heuristic olarak kalır.
* `SEATBELT-EXP-002` condition-aware challenger olarak kalır.
* İki deney de baseline değildir.
* Event çıktısında `seatbelt_status=unknown` korunur.
* Risk skoru seatbelt nedeniyle değiştirilmez.

Aktif faz sürekli driver arm-state baseline'dır. Seatbelt, kontrollü ve etiketli
`belted/unbelted/incorrect/not_evaluable` verisi veya daha uygun cabin görüntüsü
sağlandığında kaldığı yerden yeniden açılacaktır.

Dosyalar:

* `benchmark_plan.md`
* `decision_seatbelt_baseline_v1.md`
* `RUN_SEATBELT_BASELINE.md`
* `sources.md`
