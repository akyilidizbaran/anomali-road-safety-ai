# Phone Benchmark Plan

Tarih: 2026-06-14

## `PHONE-EXP-001`

* Model: `yolo11n.pt`.
* Dataset/classes: COCO `cell phone`.
* Confidence: `0.25` varsayılan. İlk `0.10` smoke koşusu parlak A-pillar ve far
  yansımasını telefon sandığı için güvenli varsayılan sıkılaştırıldı.
* Input: CABIN-EXP-004 driver/cabin metadata.
* ROI: YuNet driver face ve cabin/vehicle bbox ile driver-focused search region.
* Output: `detected`, `not_detected`, `not_evaluable`.
* Risk: kapalı, `phone_risk=null`.

## Metrikler

* evaluable frame count,
* positive frame count,
* detection rate,
* object-near-face rate,
* mean/P95 phone latency,
* manual false-positive/false-negative review.

## `PHONE-EXP-001` Smoke Sonucu

Mevcut üç video koşulduktan sonra kullanıcı `video_2`nin telefonla konuşma pozitif
video olduğunu doğruladı. COCO `cell phone` modeli bu videoda telefonu karar
eşiğinde yakalayamadı; yüz çevresi diagnostik crop'larında bazı kutular ancak
`0.01-0.04` confidence aralığında çıktı ve yansıma false-positive'leriyle
karıştı.

Karar: `PHONE-EXP-001`, mevcut telefon pozitif video için false-negative verdiği
için seçilmiş baseline değildir.

## `PHONE-EXP-002`

* Amaç: küçük, koyu ve cam arkasında kalan telefon için specialist detector
  challenger hazırlamak.
* Veri: `video_2.mp4` 30-230 aralığından 21 adet `face_near` crop.
* Annotation: `runs/phone/finetune_samples/video_2_phone_manual_labels.csv`
  içinde seed manuel bbox.
* YOLO dataset: `runs/phone/specialist_datasets/phone_windshield_seed_v1/`.
* Split: 17 train / 4 val. Split aynı videodan geldiği için gerçek genelleme
  metriği sayılmaz.
* Model: başlangıç `yolo11n.pt` fine-tune; tek sınıf `phone`.
* Runner: `run_phone_baseline.py`, custom model için `--class-name phone`,
  `--experiment-id PHONE-EXP-002`, `--model-key yolo11n_phone_windshield_seed_v1`.

Karar sınırı: Bu deney sadece object recall'ı düzeltmek için challenger'dır.
Negatif/yansıma/yolcu telefonu örnekleri ve ayrı held-out pozitif video olmadan
baseline seçilmeyecek; `phone_risk=null` korunacak.

## `PHONE-EXP-003` - Ana Challenger

* Model: resmi `yolo26s-p2.yaml` small-object detection mimarisi.
* Transfer: uyumlu katmanlarda `yolo26s.pt`; P2 head egitimle ogrenilir.
* Input: YuNet driver `face_near` crop, `imgsz=960`.
* Sinif: `phone`.
* Gerekce: P2/4 head ve YOLO26 STAL small-object positive coverage.
* Durum: research_selected, dataset gate bekliyor.

## `PHONE-EXP-004` - Mimari Kontrol

* Model: standard `yolo26s.pt`.
* Ayni dataset, split, augmentasyon ve `imgsz=960` kullanilir.
* Amac: kazanimin YOLO26 ailesinden mi P2 head'den mi geldigini ayirmak.

`PHONE-EXP-003/004` frame bazinda degil video/session bazinda ayrilmis held-out
veri olmadan baseline karari alamaz.

## Kabul

Phone baseline ancak kontrollü telefon var/yok ve telefon yüze yakın/uzak videolarla
ölçüldükten sonra seçilebilir. Sıradaki deney küçük/cam-arkası telefon için
etiketli crop seti ve fine-tune/challenger hattıdır.

## `PHONE-CALL-EXP-001` - Occluded Phone Behavior Fusion

Amaç, telefon nesnesi el/kafa tarafından kapandığında sürücünün telefonla konuşma
davranışını ayrı bir temporal sinyal olarak yakalamaktır.

* Object branch: `PHONE-EXP-003/004`, görünür telefon kanıtı.
* Pose branch: anatomik olarak geçerli omuz-dirsek-bilek zinciri.
* Davranış kanıtı: aynı taraf bileğin kulak/yüz kenarında sürmesi.
* Object yokluğu davranış adayını veto etmez.
* İlk eşik: en az `0.8 sn` kesintisiz duruş, evaluable karelerin en az `%45`i ve
  dominant taraf tutarlılığı en az `%70`.
* Output: `phone_call_status`, `phone_call_confidence`, evidence source,
  hand-near-ear rate ve en uzun süre.
* Risk: kontrollü negatif review tamamlanana kadar kapalıdır.

Zorunlu negatifler: yüz kaşıma, gözlük/saç düzeltme, yanağa dayanma, esneme,
el sallama, kemere uzanma, yolcu telefonu ve sürücünün telefonu elde fakat
kulaktan uzakta tutması.

### `video_2` Sonucu - 17 Haziran 2026

* Object: `not_detected` (`PHONE-EXP-001`).
* Behavior: `handheld_call_likely`, confidence `0.9649`.
* Evaluable: `209` frame; hand-near-ear `202/209 = 0.9665`.
* Dominant side: `right`, consistency `0.7158`.
* Longest sustained interval: `180 frame = 3.6 sn`.
* Causal sliding-window activation: frame `49`, yaklaşık `0.98 sn`.
* Karar: positive-video behavior smoke passed; hard-negative gate pending.

## `PHONE-CALL-EXP-002` - Ear-Zone Hardened Candidate

18 Haziran 2026'da generic hand-near-face yerine explicit sol/sag kulak bantlari,
causal 2 saniye pencere ve hysteresis eklendi. Standard YOLO26s object sonucu ile
fuse edilen uc-video cikti:

* `video_1`: candidate, longest `1.08 sn`, side consistency `0.5336`.
* `video_2`: handheld-call likely, longest `3.60 sn`, side consistency `0.7677`.
* `video_3`: candidate, longest `0.20 sn`.

Karar: teknik candidate secildi; minimum `3` pozitif ve `5` negatif session ile
recall/specificity kapisi gecilmeden baseline sabitlenmeyecek.
