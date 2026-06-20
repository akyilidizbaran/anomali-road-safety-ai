# Sürücü, Yolcu ve Araç İçi Risk Analizi

## Gerçekçilik İlkesi

Dışarıdan bakan telefon kamerası sürücüyü her zaman göremez. Cam yansıması, mesafe, açı, gece ve araç içi karanlık bu görevi zorlaştırır. Bu nedenle sistem koşullu çalışmalıdır.

## Akış

1. Hedef araç tespit edilir.
2. Araç ROI alınır.
3. Ön cam veya yan cam bölgesi çıkarılır.
4. Görünürlük skoru hesaplanır.
5. Görünürlük yeterliyse cabin risk modeli çalışır.
6. Görünürlük yetersizse “analiz güvenilir değil” çıktısı verilir.

## 2026-06-20 Runtime Foundation Durumu

Cabin/driver hattı `CABIN-EXP-012-runtime-foundation` ile ilk kez repo içinde çalışır hale
getirildi. Bu deney ihlal kararı üretmez; yalnız sonraki specialist modeller için şu girdileri
üretir:

* araç ROI,
* cabin/cam ROI,
* visibility status,
* face/occupant candidate,
* driver candidate,
* torso/upper-body ROI candidate,
* enriched event skeleton.

Çalıştırma:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_cabin_driver_runtime_foundation.py
```

Üretilen küçük artifactler:

```text
models/benchmarks/artifacts/CABIN-EXP-012-runtime-foundation-summary.json
models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-cabin012.json
testing/reports/cabin_exp_012_runtime_foundation.md
```

İlk koşuda üç video da işlendi. Ancak YuNet checkpoint repo içinde bulunmadığı için face/occupant
tespitinde OpenCV Haar fallback kullanıldı ve face rate düşük kaldı. Bu nedenle bu sonuç phone,
smoking veya seatbelt kararının hazır olduğu anlamına gelmez. Foundation, öncelikle ROI ve
visibility gate doğrulaması olarak kullanılmalıdır.

| Video | View profile | Analysis-ready rate | Face frame rate | Karar |
|---|---|---:|---:|---|
| `video_1.mp4` | `side_driver_window` | `0.25` | `0.15` | ROI kullanılabilir; face fallback sınırlı. |
| `video_2.mp4` | `side_driver_window` | `0.2632` | `0.0` | ROI kullanılabilir; face yok. |
| `video_3.mp4` | `front_lhd` | `0.1176` | `0.0` | Görünürlük düşük; risk kapalı kalmalı. |

Kilit politika:

* `poor` veya `not_visible` karelerden risk kararı üretilmez.
* Telefon, sigara veya kemer kararı face/torso çıktısından türetilmez; ayrı specialist gerekir.
* Seatbelt bilinmiyorsa `unknown` kalır.
* Phone bu aşamada `null` kalır ve `PHONE-EXP-003/004` specialist çalışmasıyla açılır.

## Olası Riskler

* Telefon kullanımı.
* Sigara.
* Emniyet kemeri belirsizliği.
* Dikkat dağınıklığı.
* Yolcu sayısı.
* Görüş engelleyici nesne.

## Metrikler

* Precision.
* Recall.
* F1.
* False positive rate.
* Visibility gating doğruluğu.

## Sorulacak Noktalar

* Kontrollü cabin risk videosu çekilecek mi?
* Bu modül final demo için zorunlu mu?
