# Driver Detection Module

Bu modül, hedef araç içinde sürücü adayı görülebiliyor mu sorusunu cevaplar.
Telefon, sigara, emniyet kemeri, esneme veya başka bir sürücü eylemi kararı
üretmez.

## Aktif Baseline

`DRIVER-EXP-001 = yunet_view_policy_driver_presence_v1`

Kaynak zincir:

```text
target vehicle track
-> cabin ROI
-> visibility gate
-> YuNet face / occupant detection
-> camera view profile role policy
-> driver_detection event field
```

## Neden Ayrı Modül?

FTR sürücü eylemlerine geçmeden önce sistemin sürücüyü görebildiğini ve rol
atamasının hangi varsayımla yapıldığını ayrı tutmak gerekir. Aksi halde telefon,
sigara veya kemer modelleri başarısız olduğunda bunun sebebi sürücü görünürlüğü mü
yoksa action modeli mi ayırt edilemez.

## Üretilen Alanlar

Event içinde yeni alan:

```json
{
  "driver_detection": {
    "status": "detected",
    "driver_present": true,
    "confidence": 0.8,
    "view_profile": "side_driver_window",
    "cabin_visibility": "limited",
    "occupant_count_estimate": 2,
    "passenger_count": 1,
    "risk_enabled": false,
    "action_enabled": false
  }
}
```

Durumlar:

* `detected`: sürücü adayı temporal gate ve view-profile policy ile atanabildi.
* `not_detected`: cabin görünür ama sürücü temporal gate geçmedi.
* `ambiguous`: yüz/occupant var ama sürücü rolü güvenilir atanamadı.
* `not_visible`: cabin görünür değil.
* `not_evaluable`: cabin kalitesi driver kararı için yetersiz.
* `not_run`: kaynak cabin summary yok.

## Aktif Karar

`DRIVER-EXP-001`, sonraki action specialist modülleri için gate/evidence sinyali
olarak kabul edilir. Risk üretmez ve FTR `sofor_eylemi` alanını tek başına
doldurmaz.
