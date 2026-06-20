# Cabin / Driver Baseline Decision v1

Tarih: 2026-06-20

Bu karar dosyası `CABIN_DRIVER_FINETUNE_HANDOFF.md` içindeki handoff bilgilerini repo
aksiyonlarına çevirir. Handoff dosyası tek başına çalıştırılabilir repo durumu değildir;
referans verdiği script/checkpoint/artifactlerin önemli kısmı bu repoda bulunmadığı için
kararlar yeniden üretilebilir `CABIN-EXP-012` foundation deneyiyle sabitlenmiştir.

## Amaç

Cabin/driver hattının ilk amacı doğrudan ihlal üretmek değildir. Önce hedef araç üzerinde
aşağıdaki runtime foundation çıktıları güvenilir şekilde üretilmelidir:

1. Araç ROI.
2. Cabin/cam ROI.
3. Cabin visibility status.
4. Face / occupant candidate.
5. Driver candidate.
6. Torso / upper-body ROI candidate.
7. Specialist modeller için phone/smoking/seatbelt ROI girdisi.

Bu foundation olmadan phone, smoking, seatbelt veya yolcu konumu fine-tune çalışması adil
değerlendirilemez.

## Kilit Kararlar

| Alan | Karar | Gerekçe |
|---|---|---|
| Cabin visibility | Zorunlu gate | Görünürlük yetersizse risk kararı üretilmez. |
| Face / occupant | YuNet handoff kararı korunur, repo koşusunda Haar fallback kullanılabilir | YuNet checkpoint repo içinde yok; fallback yalnız foundation smoke içindir. |
| Driver skeleton | Omuz/torso anchor ile sınırlı | Pose/torso tek başına telefon/sigara/kemer kararı üretmez. |
| Lower-arm state | Kapalı | Wheel/raised/off-wheel semantiği handoff tarafından kapatılmıştır. |
| Seatbelt | `unknown` | Kemer çizgisi yokluğu `unbelted` sayılmaz. |
| Phone | `null`, aktif specialist hedefi | Hazır COCO phone baseline yetersiz görülmüş; custom specialist gerekir. |
| Smoking | not started | Phone sonrası ayrı small-object specialist olarak açılmalıdır. |

## CABIN-EXP-012 Runtime Foundation

İlk somut repo deneyi:

```text
scripts/benchmarks/run_cabin_driver_runtime_foundation.py
```

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

Ağır overlay çıktıları Git dışındadır:

```text
runs/cabin/CABIN-EXP-012-runtime-foundation/
```

## İlk Koşu Sonucu

| Video | View profile | Sampled frame | Analysis-ready rate | Face frame rate | Max occupant candidate | Yorum |
|---|---|---:|---:|---:|---:|---|
| `video_1.mp4` | `side_driver_window` | 20 | 0.25 | 0.15 | 2 | ROI doğru; visibility çoğunlukla poor/not_visible. |
| `video_2.mp4` | `side_driver_window` | 19 | 0.2632 | 0.0 | 0 | ROI doğru; face fallback tespit üretmedi. |
| `video_3.mp4` | `front_lhd` | 17 | 0.1176 | 0.0 | 0 | Ön görüşte cabin visibility düşük. |

Aggregate:

```text
event_count = 3
ok_event_count = 3
total_sampled_frames = 56
mean_analysis_ready_frame_rate = 0.2103
mean_face_frame_rate = 0.05
```

## Yorum

`CABIN-EXP-012`, cabin runtime foundation için başarılıdır çünkü 3 hedef event üzerinde
araç ROI, cabin ROI, visibility, torso ROI ve enriched event skeleton üretmiştir. Ancak face
tespiti mevcut Haar fallback ile yeterli değildir. Bu sonuç phone/smoking/seatbelt modelinin
başarısız olduğu anlamına gelmez; önce YuNet checkpoint aktarımı veya daha güçlü face/occupant
baseline bağlantısı gerektirebilir.

## FTR Etkisi

FTR `results.json` için cabin/driver tarafı şu kategorilere bağlanacaktır:

| FTR kategori | Etiketler | Mevcut durum |
|---|---|---|
| `sofor_eylemi` | `telefonla_konusma`, `sigara_icme`, `emniyet_kemeri_ihlali`, `etrafa_bakinma`, `arkaya_bakma`, `esneme`, `su_icme` | Foundation hazır; specialist kararları eksik. |
| `yolcular` | `on_koltuk`, `arka_koltuk_1`, `arka_koltuk_2` | Face/occupant candidate var ama koltuk konumu yok. |
| `nesneler` | `teknocan`, `bilgisayar` | Ayrı object specialist gerekir. |

## Değiştirilmemesi Gerekenler

* `poor` veya `not_visible` karelerden risk kararı üretilmez.
* Telefon görülmesi tek başına `phone_risk=true` yapmaz; temporal persistence ve driver association gerekir.
* Seatbelt bilinmiyorsa `unknown` kalır.
* Lower-arm wheel/raised/off-wheel çalışması bu fazda açılmaz.
* Pozitif-only küçük smoke veri baseline olarak raporlanmaz.

## Sonraki Karar

Bir sonraki aktif teknik iş `PHONE-EXP-003/004` için phone specialist baseline/fine-tune planıdır.
Ancak phone çalışmasına başlamadan önce `CABIN-EXP-012` overlayleri manuel kontrol edilmeli ve
gerekirse YuNet checkpoint repo dışı materyal olarak aktarılmalıdır.
