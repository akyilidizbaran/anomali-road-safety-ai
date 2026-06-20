# CABIN-EXP-012 Runtime Foundation

Bu rapor cabin/driver hattinin ilk calisir foundation smoke test sonucudur. Bu asama telefon, sigara, kemer veya ihlal karari uretmez; yalniz sonraki specialist modeller icin cabin ROI, visibility, face/occupant ve torso ROI adaylarini uretir.

## Kapsam

* Input: mevcut ByteTrack target vehicle event skeleton.
* Videolar: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`.
* Agir overlay ciktilari: `runs/cabin/CABIN-EXP-012-runtime-foundation/`.
* JSON summary: `models/benchmarks/artifacts/CABIN-EXP-012-runtime-foundation-summary.json`.
* Enriched event skeleton: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-cabin012.json`.

## Sonuc Tablosu

| Event | Video | View | Sampled frame | Analysis-ready rate | Face frame rate | Max occupant candidate | Status |
|---|---|---|---:|---:|---:|---:|---|
| EVT-TRK-EXP-001-video_1-TRK-001 | `video_1.mp4` | `side_driver_window` | 20 | 0.25 | 0.15 | 2 | `ok` |
| EVT-TRK-EXP-001-video_2-TRK-001 | `video_2.mp4` | `side_driver_window` | 19 | 0.2632 | 0.0 | 0 | `ok` |
| EVT-TRK-EXP-001-video_3-TRK-002 | `video_3.mp4` | `front_lhd` | 17 | 0.1176 | 0.0 | 0 | `ok` |

## Karar

* `CABIN-EXP-012` arac/cabin ROI, visibility ve torso ROI uretimi icin calisir runtime foundation olarak kabul edilir.
* Mevcut kosuda face/occupant tespiti zayiftir; YuNet checkpoint repo icinde olmadigi icin Haar fallback kullanilmistir.
* `poor` veya `not_visible` kareler risk kararina katilmaz.
* Face/occupant ve torso ROI ciktisi ihlal karari degildir; yalniz specialist ROI ve evidence metadata girdisidir.
* Seatbelt bu asamada `unknown`, phone ise `null` kalir.

## Sinirlar

* YuNet checkpoint repo icinde bulunmadigi icin bu kosuda OpenCV Haar fallback kullanilabilir; YuNet checkpoint eklendiginde ayni script `--yunet-model` ile tekrar kosulmalidir.
* Static event bbox, full per-frame target bbox yerine foundation smoke icin kullanilir. Phone/smoking fine-tune oncesi gerekirse per-frame track bbox baglantisi guclendirilmelidir.
* Lokal 3 video benchmark degil; manuel review ve runtime input dogrulama materyalidir.

## Sonraki Adim

1. Overlay'ler manuel kontrol edilir.
2. Cabin/torso ROI yeterliyse phone ROI export adimina gecilir.
3. Face/occupant bilgisi phone kararinda zorunlu olacaksa once YuNet checkpoint aktarimi tamamlanir.
4. `PHONE-EXP-003/004` phone specialist baseline/fine-tune planina bu foundation uzerinden gecilir.
