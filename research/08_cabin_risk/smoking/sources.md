# Smoking Research Sources

Tarih: 2026-06-23

## 1. Region extraction based cigarette usage classification

Kaynak:

* Paper: <https://arxiv.org/abs/2103.12523>
* Code link from paper: <https://github.com/MIntelligence-Group/CigDetect>
* Dataset: <https://data.mendeley.com/datasets/7b52hhzs3r/1>

İlgili bulgu:

* Cigarette küçük nesne olduğu için paper tüm frame yerine face/hand ROI yaklaşımı
  öneriyor.
* Mendeley smoker dataset 2400 image içeriyor: 1200 smoker, 1200 non-smoker.
* Dataset lisansı CC BY 4.0.
* Non-smoker sınıfı özellikle benzer gesture içeriyor: phone, water drinking,
  inhaler, nail biting gibi hard-negative benzeri örnekler.

Projeye etkisi:

* Bizim pipeline'da YuNet face + ViTPose/LK hand-mouth ROI ile uyumlu.
* Doğrudan sürücü windshield domain'i olmadığı için final baseline değil, dataset
  ve mimari referans.

## 2. Application-driven hierarchical hand-held action detection

Kaynak:

* Paper: <https://arxiv.org/abs/2210.06682>

İlgili bulgu:

* Sadece cigarette object veya sadece smoking pose tespiti düşük doğruluk riski
  taşıyor.
* Coarse-to-fine/hierarchical yaklaşım öneriliyor:
  * önce whole hand + cigarette + head ilişkisi,
  * sonra fingers + mouth area + cigarette fine detection.

Projeye etkisi:

* Telefon için kullandığımız object + pose-temporal fusion yaklaşımının sigarada da
  doğru yön olduğunu destekliyor.
* Tek branch yerine object branch + hand-mouth behavior branch kullanılmalı.

## 3. Synthetic Distracted Driving / driver action datasets

Kaynak:

* SynDD2 paper: <https://arxiv.org/abs/2204.08096>
* Drive&Act/noisy-label implementation reference:
  <https://github.com/ilonafan/DAR-noisy-labels>

İlgili bulgu:

* Driver action recognition için kamera açısı ve participant/session ayrımı kritik.
* Public driver action datasets çoğunlukla iç-kabin kamera açısına göre tasarlanmış.

Projeye etkisi:

* Mevcut dış/windshield kamera açısı farklı olduğu için bu kaynaklar doğrudan model
  baseline değil; action-head/backbone/challenger referansı.

## 4. State Farm / generic distracted-driver classifiers

Not:

* State Farm tarzı distracted-driver modelleri telefon, içecek, saç/makyaj,
  yolcuyla konuşma gibi sınıflarda güçlü olabilir; ancak standart sınıf seti
  sigarayı doğrudan hedeflemeyebilir.
* Bu nedenle hazır distracted-driver classifier sigara için ancak hard-negative
  veya generic behavior challenger olarak denenebilir.

## Araştırma Sonucu

Sigara için hazır model aramak mantıklı ama ana yol şu olmalı:

1. cigarette object specialist,
2. hand-mouth temporal behavior,
3. hard-negative ağırlıklı evaluation,
4. final risk üretmeden önce session-disjoint kabul seti.
