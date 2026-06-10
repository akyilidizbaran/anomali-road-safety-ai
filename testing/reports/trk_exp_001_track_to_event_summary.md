# TRK-EXP-001 Track-to-Event Summary

Tarih: 2026-06-11

## Amaç

ByteTrack çıktısını sistemin target vehicle selection ve event/evidence skeleton hattına bağlamak.

Bu rapor gerçek risk tespiti iddiası kurmaz. Üretilen eventler `target_vehicle_selected` seviyesinde ara kayıt/skeleton niteliğindedir.

## Kaynak

* Experiment: `TRK-EXP-001`
* Tracker: `ByteTrack` / `bytetrack.yaml`
* Detector: `yolo11n.pt`
* Condition profile: `dark`

## Üretilen Artifactler

* Track post-process JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-track-postprocess.json`
* Event skeleton JSON: `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json`

## Seçilen Hedefler

| Video | Track Count | Selected Target | Stable Class | Track Stability | Selection Score |
|---|---:|---|---|---:|---:|
| video_1.mp4 | 3 | TRK-001 | car | 0.964 | 0.905 |
| video_2.mp4 | 4 | TRK-001 | car | 0.949 | 0.898 |
| video_3.mp4 | 8 | TRK-002 | car | 0.949 | 0.916 |

## Uygulanan Heuristikler

* `track_stability`: track yaşı, missing frame oranı, confidence, class vote purity ve class switch sinyalinin birleşimi.
* `stable_class`: benchmark summary içindeki confidence ağırlıklı class vote sonucudur.
* `target_selection_score`: track stability, confidence, bbox görünürlüğü, frame merkezine yakınlık, track yaşı ve sınıf önceliğinin birleşimi.
* `qod_status`: bu aşamada gerçek QoD isteği değildir; skeleton event içinde evidence kalitesi düşükse `candidate`, aksi halde `not_needed` olarak işaretlenir.

## Sınırlamalar

* Bu aşamada speed, plate OCR, lane ve cabin modülleri çalıştırılmadı.
* Eventler karar destek skeleton'ıdır; kritik olay veya hukuki sonuç üretmez.
* History sample alanları yalnız güncel tracking benchmark script'iyle üretilmiş summary dosyalarında dolar.

## Sonraki Adım

Seçilen `target_track_id` üzerinden relative speed baseline kurulmalı. Ardından aynı track penceresi üstünde plate detection/OCR temporal voting eklenmelidir.
