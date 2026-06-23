# Tiny / Low-Light Driver Phone Detector Research

Tarih: 2026-06-17

## Problem

Mevcut `PHONE-EXP-001` COCO `cell phone` modeli, `video_2` icindeki koyu,
cam arkasinda ve kismen el/yuz ile ortulen telefonu kacirdi. Sorun yalniz model
confidence esigi degildir:

* telefon full frame'de cok az piksel kapliyor,
* cam yansimasi ve dusuk kontrast nesne kenarini siliyor,
* COCO telefonu cabin/window domain'inde yeterince temsil etmiyor,
* mevcut seed dataset tek videodan gelen 21 benzer pozitif crop'tan olusuyor,
* kontrollu negatif ve hard-negative ornekleri henuz yok.

Bu nedenle sifir-shot COCO model degistirmek tek basina yeterli degildir. Ana
kaldiraclar driver-face-near crop, P2 small-object head, yuksek cozum ve domain
etiketli fine-tune'dur.

Hazir modeller kabul kapisini gecmezse ekip kendi specialist modelini egitecektir.
Bu, sifirdan rastgele agirliklarla baslamak zorunda degildir: once uygun pretrained
backbone domain verisiyle fine-tune edilir; gerekiyorsa P2 head veya phone-specific
architecture egitilir. Smoking/cigarette gibi COCO'da guclu sinifi olmayan gorevler
icin custom specialist egitimi beklenen ana yoldur.

## Resmi Kaynak Bulgulari

### YOLO26

Ultralytics YOLO26, STAL egitim mekanizmasiyla small-object positive label
coverage'ini korumayi hedefler. Resmi aile `n/s/m/l/x` detection modellerini,
train/val/predict/export akislarini destekler.

Resmi `yolo26-p2.yaml`, standart P3/8 basligina ek olarak P2/4 detection head
uretir. Bu, face-near crop'taki kucuk telefon icin dogrudan ilgili mimari
degisikliktir. P2 icin hazir scale-specific checkpoint yayinlanmamistir; YAML
mimarisi egitilmeli ve gerekirse standart YOLO26 checkpoint'inden uyumlu
katmanlar yuklenmelidir.

Yerel `ultralytics 8.4.66` ortaminda `yolo26s-p2.yaml` basariyla kuruldu:
`9,765,856` parametre, P2/P3/P4/P5 detection head.

### YOLO11 ve Acik-Sozcuklu Modeller

YOLO11n COCO sonucu bu domain'de false-negative verdigi icin tekrar ana aday
olmayacaktir. YOLOE/open-vocabulary veya VLM modelleri dataset kesfi ve label
audit icin kullanilabilir; ancak cok kucuk, koyu ve kismi telefon bbox'i icin
deterministic runtime baseline yerine gecmez.

### Tiling / SAHI

Full vehicle veya cabin frame'de tiling kucuk nesne pikselini koruyabilir, ancak
bu projede YuNet ile driver face-near ROI zaten daha kontrollu bir zoom saglar.
Ilk deneyde SAHI eklenmeyecek. P2 + face-near ROI basarisiz kalirsa full cabin
tiling ayri challenger olarak acilabilir.

## Secilen Deney Sirasi

| Deney | Model | Input | Rol |
|---|---|---|---|
| `PHONE-EXP-002` | YOLO11n seed fine-tune | face-near | mevcut kontrol |
| `PHONE-EXP-003` | YOLO26s-P2 | face-near, 960 px | ana small-object challenger |
| `PHONE-EXP-004` | YOLO26s standard | face-near, 960 px | P2 katkisini izole eden kontrol |
| `PHONE-EXP-005` | YOLO26m-P2 | face-near, 960/1280 px | veri buyurse accuracy challenger |

Ilk secim `PHONE-EXP-003`tur. `m-P2` hemen kullanilmaz; 21 korelasyonlu pozitif
crop'ta daha buyuk model genellemeyi duzeltmez ve overfit riskini artirir.

## Veri Plani

Baseline seciminden once en az su gruplar ayri video/session bazinda toplanmalidir:

* aydinlik ve karanlikta telefon kulakta,
* telefon elde ancak yuzden uzakta,
* telefon yok,
* el yanakta / yuzde ancak telefon yok,
* yolcu telefonu,
* cam ve parlak trim yansimasi,
* siyah/beyaz telefon ve farkli kiliflar,
* kismi gorunen telefon.

Train/val split frame bazinda degil video/session bazinda yapilmalidir. Ayni
videonun komsu kareleri iki split'e dagitilmayacaktir. Ilk hedef en az 200-500
pozitif ve pozitif sayisinin 2-3 kati negatif/hard-negative crop'tur.

## Egitim Politikasi

* Tek sinif: `phone`.
* Primary input: YuNet driver `face_near` crop.
* Baslangic cozum: `imgsz=960`; telefon kutusu resize sonrasinda en az yaklasik
  12-16 piksel olmali.
* Raw goruntu korunur; brightness/gamma/contrast varyasyonlari augmentation olarak
  eklenir, split'ler arasinda ayni kaynak frame kullanilmaz.
* Dusuk detection threshold candidate recall icin kullanilabilir; risk karari
  temporal persistence ve driver association olmadan uretilmez.
* `phone_risk=null` baseline kabul edilene kadar korunur.

## Kabul Kapisi

* Ayrik held-out videolarda precision, recall ve AP50 raporu.
* Karanlik/aydinlik ve uzak/yakin breakdown.
* Telefon kulakta longest miss ve temporal detection rate.
* El-yuz, yansima ve yolcu telefonu false-positive testleri.
* Full overlay manuel review.
* Mean/P95 latency ve MacBook runtime uygunlugu.

Tek `video_2` uzerinde yuksek skor model secimi icin yeterli degildir.

## Kaynaklar

* Ultralytics YOLO26: https://docs.ultralytics.com/models/yolo26/
* Resmi YOLO26-P2 config: https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/models/26/yolo26-p2.yaml
* Ultralytics train mode: https://docs.ultralytics.com/modes/train/
* YOLO26 paper: https://arxiv.org/abs/2606.03748
* Ultralytics repository/license: https://github.com/ultralytics/ultralytics

Kaynaklar 17 Haziran 2026 tarihinde Playwright ile dogrulandi. Ultralytics docs,
GitHub repository ve yerel package config'i ayni P2 small-object mimarisini
gosterdi. Puppeteer baglantisi zaman asimina ugradi; ekran goruntusu alinmadi.
