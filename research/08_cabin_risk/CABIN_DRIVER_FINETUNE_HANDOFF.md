# Cabin / Driver Baseline ve Fine-Tune Handoff

Tarih: 2026-06-17

Bu dosya Cabin/Driver fazinda yapilan model deneylerini, secim kararlarini,
reddedilen yaklasimlari ve fine-tune calismasinin baslangic noktalarini tek yerde
toplar. Otomatik metrikler manuel full-video review ile birlikte yorumlanmistir.

## 1. Son Durum

Evet, Cabin/Driver face ve scoped pose baseline'lari sabitlenmistir.

| Modül | Secilen baseline | Durum | Kullanım sınırı |
|---|---|---|---|
| Cabin visibility | OpenCV kalite metrikleri + policy gate | selected policy | `good/limited/poor/not_visible`; poor kare risk uretmez |
| Face / occupant | `CABIN-EXP-004` OpenCV YuNet 2026may | selected | driver-face anchor ve occupant metadata |
| Driver skeleton | `POSE-EXP-009` ViTPose-B final torso v1 | selected/frozen | yalnız omuz/torso ve specialist ROI |
| Lower-arm state | yok | closed | wheel/raised/off-wheel sınıflandırması yapılmaz |
| Seatbelt | yok | deferred | `seatbelt_status=unknown` |
| Phone | yok | active challenger | `phone_risk=null` |
| Smoking | yok | not started | custom specialist veri/model bekleniyor |

Aktif zincir:

`target track -> cabin ROI/visibility -> YuNet face/occupant -> ViTPose-B shoulder/torso -> object detector + conditional arm-focus behavior fusion`

Telefon nesnesi, sigara nesnesi veya kemer varligi pose iskeletinden turetilmez.
Ancak telefon kapali/gorunmezken zamansal ve anatomik el-kulak durusu ayri bir
`phone_call_status` davranis sinyali uretebilir; bu sinyal `phone_detected` yerine
gecmez.

## 2. Veri ve Degerlendirme Protokolu

* Lokal videolar: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`.
* Toplam hedef frame: `968` (`342 / 341 / 285`).
* View profiles: `video_1/2=side_driver_window`, `video_3=front_lhd`.
* Modeller ayni YuNet cabin artifact'i ve face-anchored ROI uzerinde karsilastirildi.
* Tek kare veya aggregate oran tek basina kabul nedeni sayilmadi.
* Full-rate overlay manuel incelemesi secim icin zorunlu tutuldu.
* `poor/not_visible` kareler evidence olarak saklanabilir ancak risk kararina katilmaz.

`Test/`, `runs/` ve binary checkpoint'ler Git disindadir. Fine-tune yapacak ekip
uyesine bu klasorler ayrica aktarilmalidir.

## 3. Cabin Face / Occupant Deneyleri

| Deney | Model | Video/frame | Face rate | Latency mean/P95 | Karar | Neden |
|---|---|---:|---:|---:|---|---|
| `CABIN-EXP-001` | BlazeFace full-range | 3 / 968 | `0.6136` | `2.635 / 2.902 ms` | rejected | Full-rate kosuda kesintiler, `video_2`de 39-frame eligible miss, arka occupant recall yetersiz |
| `CABIN-EXP-002` | BlazeFace short-range | 3 / 195 | `0.2462` | `1.242 / 2.045 ms` | rejected | Sampled recall full-range'den cok dusuk; full-rate tekrar anlamsiz |
| `CABIN-EXP-004` | OpenCV YuNet 2026may | 3 / 968 | `0.9101` | `25.802 / 62.056 ms` | **selected** | En iyi temporal face continuity, gercek ikinci occupant recall, uc-video manuel review pass |

YuNet temporal occupant sonucu:

| Video | View profile | Occupant estimate | Driver candidate | Mean/P95 face latency |
|---|---|---:|---|---:|
| `video_1` | side driver window | 2 | true | `36.486 / 65.038 ms` |
| `video_2` | side driver window | 2 | true | `39.283 / 67.490 ms` |
| `video_3` | front LHD | 1 | true | `10.751 / 29.855 ms` |

YuNet; BlazeFace'e gore daha yuksek recall, ikinci occupant tespiti, OpenCV runtime
uyumu ve uc full-overlay manuel kabul nedeniyle secildi. Yan gorunumde coklu yuz
varsa driver rolu zorla atanmaz.

Checkpoint: `models/checkpoints/cabin/face_detection_yunet_2026may.onnx`

## 4. Upper-Body / Pose / Torso Deneyleri

| Deney | Model/yöntem | Kapsam | Sonuc | Karar nedeni |
|---|---|---|---|---|
| `POSE-EXP-001` | YOLO11n-pose COCO-17 | generic pose | rejected | `0.9698` pose rate anatomik kaliteyi yansitmadi; uzak/yakin kol ve torso yanlis |
| `POSE-EXP-002` | MediaPipe Pose Full | generic pose | rejected | `video_3` pose `0.7388`, seatbelt anchor `0.2687`, phone anchor `0.2015`, 91-frame miss |
| `TORSO-EXP-001` | YuNet deterministic torso | geometric fallback | rejected | Full videoda kopma, yanlis yerlesim ve video tutarsizligi |
| `POSE-EXP-003` | RTMPose-L Body7 384x288 | upper-body | rejected action-grade | Pose `0.9981`; phone arm-chain `0.1070/0.8134/0.2015` |
| `POSE-EXP-004` | RTMW-L Cocktail14 WholeBody | body+hand | rejected action-grade | Pose `1.0`; `video_3` hand anchor `0.2388`, hand-near-face `0.0746` |
| `POSE-EXP-005` | ViTPose-B raw | upper-body | reference | Omuz/torso en guclu ham aday; dirsek/bilek confidence kesintili |
| `POSE-EXP-006` | ViTPose-B + 200 ms smoothing | stabilized pose | superseded | Kisa dropout azaldi; manuel review kol kopmalarini reddetti |
| `POSE-EXP-007` | ViTPose-B + hysteresis | arm continuity | superseded | `video_3` arm-chain `0.7015 -> 0.9254`; tek-video sonuc |
| `POSE-EXP-008` | visibility-decoupled ViTPose-B | evidence continuity | superseded | Poor karelerde evidence devam etti; risk gate kapali kaldi |
| `POSE-EXP-009` | ViTPose-B final torso v1 | shoulder/torso | **selected/frozen** | Uc videoda en kararlı torso; action-grade kol iddiasi kaldirildi |
| `POSE-EXP-010` | ViTPose-B arm-focus | arm observation | reference-only | `video_3` available `0.9851`, miss `0.04 sn`; uc-video/anatomik kabul yok |
| `POSE-EXP-011` | YOLO11n-pose arm-focus | arm observation | rejected | available `0.3209`, longest miss `0.94 sn` |
| `ARM-EXP-001` | bounded LK arm tracker | arm-state metadata | closed/reference | wheel/raised/off-wheel semantigi kapatildi |
| `VLM-ARM-EXP-001` | `LLAMA_MODEL_ADI` placeholder | VLM audit | invalid/not run | Ollama baglantisi yok; 3/3 call failure |

### Secilen Pose Baseline

`POSE-EXP-009 = vitpose_b_final_torso_baseline_v1`

| Video | Torso anchor | Longest miss | P95 shoulder jitter | Evidence-only frame |
|---|---:|---:|---:|---:|
| `video_1` | `0.9305` | `0.12 sn` | `0.1459` | 38 |
| `video_2` | `1.0000` | `0.00 sn` | `0.0827` | 43 |
| `video_3` | `1.0000` | `0.00 sn` | `0.0954` | 88 |

Aggregate pose rate `1.0`, analysis-ready rate `0.9755`, mean/P95 latency
`53.942 / 67.260 ms`.

Kabul edilen kullanim: YuNet driver identity, cabin-clamped ROI, omuz/torso,
specialist ROI ve poor karelerde evidence-only devam.

Kabul edilmeyen kullanim: dirsek/bilekten telefon-sigara karari, kol
direksiyonda/havada/off-wheel karari, pose keypoint'ini hand landmark yerine
kullanma veya dusuk gorunurlukten risk artirma.

Fine-tune baslangic ailesi: Hugging Face `usyd-community/vitpose-base-simple`.
Hedef omuz/torso continuity olmali; phone/smoking object recall pose loss'una
yuklenmemelidir.

## 5. Seatbelt Deneyleri

| Deney | Model | Sonuc | Karar |
|---|---|---|---|
| `SEATBELT-EXP-001` | OpenCV diagonal belt evidence | Evidence `0.0402/0.0096/0.0000`, mean `1.715 ms` | not selected |
| `SEATBELT-EXP-002` | RISEF YOLO11s seatbelt classifier | Manuel review'da guvenilir kemer sonucu yok | deferred/not selected |

Yansima, govde kenari ve trim cizgileri false-positive uretti. Cizgi yoklugu
`unbelted` sayilmadi. `seatbelt_status=unknown`, `incorrect` kapali ve risk skoru
degismemis durumdadir. Fine-tune icin kontrollu
`belted/unbelted/incorrect/not_evaluable` verisi gerekir.

## 6. Phone Deneyleri ve Aktif Fine-Tune Yonu

| Deney | Model | Input | Durum | Not |
|---|---|---|---|---|
| `PHONE-EXP-001` | YOLO11n COCO `cell phone` | driver-phone ROI | rejected false-negative | Telefon pozitif `video_2`de 0/245 detection |
| `PHONE-EXP-002` | YOLO11n custom seed | face-near | prepared/not trained | 21 manuel pozitif crop; kontrol |
| `PHONE-EXP-003` | YOLO26s-P2 | face-near 960 | primary challenger | Resmi P2/4 small-object head |
| `PHONE-EXP-004` | standard YOLO26s | face-near 960 | control planned | P2 katkisini izole eder |
| `PHONE-EXP-005` | YOLO26m-P2 | face-near 960/1280 | deferred | Veri buyurse accuracy challenger |
| `PHONE-CALL-EXP-001` | phone object + ViTPose/LK temporal fusion | object + hand-to-ear | candidate passed on video_2 | Object false-negative iken call likely `0.9649`; hard-negative gate bekliyor |
| `PHONE-CALL-EXP-002` | standard YOLO26s + ViTPose/LK ear-zone fusion | object + causal ear behavior | selected candidate, not accepted baseline | video_2 likely; video_1/3 candidate; labeled coverage yetersiz |

Mevcut seed dataset:

* Manifest: `runs/phone/finetune_samples/video_2_phone_manual_labels.csv`
* YOLO data: `runs/phone/specialist_datasets/phone_windshield_seed_v1/data.yaml`
* 21 pozitif: 17 train / 4 val; negatif yok.
* Ayni videonun komsu kareleri train/val'e dagitildi.
* Yalnız overfit/smoke icindir; baseline metrigi uretmez.

Hazir model yetersizse custom specialist egitimi onayli ana secenektir. Telefon ve
ozellikle sigara icin pretrained backbone + domain fine-tune beklenen yoldur.

Fine-tune veri kapisi:

* Farkli session/video bazli train/val/test split.
* En az 200-500 pozitif phone crop.
* Pozitif sayisinin 2-3 kati negatif/hard-negative.
* Aydinlik/karanlik, telefon kulakta/elde/yuzden uzakta.
* Telefon yok ama el yanakta, yolcu telefonu, cam/trim yansimasi.
* Farkli telefon renk/kilifi ve kismi gorunen telefon.

Ilk adil karsilastirma ayni data, seed, augmentasyon ve `imgsz=960` ile
YOLO26s-P2 versus standard YOLO26s olmalidir.

```bash
source .venv-yolo/bin/activate
python scripts/benchmarks/train_phone_specialist_challengers.py \
  --allow-positive-only-smoke
```

Inference training crop dagilimiyla ayni olmalidir:

```bash
python scripts/benchmarks/run_phone_baseline.py \
  --model <best.pt> --class-name phone --roi-mode face_near \
  --confidence 0.05 --imgsz 960
```

Baseline kabul edilene kadar `phone_risk=null` kalir.

## 7. Runtime Contract

* YuNet face, occupant count ve driver candidate metadata uretir.
* ViTPose-B secilmis surekli shoulder/torso baseline'idir; arm-focus profili
  yalniz conditional telefon-konuşma davranis kaniti icin calistirilabilir.
* Occupant varligi risk skorunu artirmaz.
* `poor/not_visible` frame specialist risk kararina katilmaz.
* Nesne tespiti tek basina ihlal degildir; temporal persistence ve driver
  association gerekir.
* Telefon nesnesi gorunmese bile ayni taraf el-kulak durusunun zamansal surekliligi
  `phone_call_status=handheld_call_likely` davranis metadata'si uretebilir.
* Tek kare hand/pose risk artiramaz; kontrollu negatif review tamamlanana kadar
  bu davranis sinyali de `phone_risk` artiramaz.

Event artifact:

* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin.json`
* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-phone.json`
* `models/benchmarks/artifacts/PHONE-CALL-EXP-001-phone_object_vitpose_lk_temporal_fusion_v1-summary.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-002-phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2-summary.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-002-evaluation.json`
* `models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-cabin-phone-call.json`

Her iki artifact'te 3 event vardir ve mevcut plate bilgisi korunur.

## 8. Kod ve Artifact Haritasi

Calistirma scriptleri:

* `scripts/benchmarks/run_cabin_visibility_baseline.py`
* `scripts/benchmarks/enrich_event_skeleton_with_cabin.py`
* `scripts/benchmarks/run_driver_pose_baseline.py`
* `scripts/benchmarks/run_driver_torso_baseline.py`
* `scripts/benchmarks/run_driver_arm_state_baseline.py`
* `scripts/benchmarks/run_seatbelt_baseline.py`
* `scripts/benchmarks/run_seatbelt_classifier_challenger.py`
* `scripts/benchmarks/run_phone_baseline.py`
* `scripts/benchmarks/prepare_phone_finetune_samples.py`
* `scripts/benchmarks/prepare_phone_specialist_yolo_dataset.py`
* `scripts/benchmarks/train_phone_specialist_challengers.py`

Karsilastirma tablolari:

* `models/benchmarks/cabin/cabin_baseline_comparison.csv`
* `models/benchmarks/cabin/driver_pose_baseline_comparison.csv`
* `models/benchmarks/cabin/driver_torso_baseline_comparison.csv`
* `models/benchmarks/cabin/driver_arm_state_comparison.csv`
* `models/benchmarks/cabin/seatbelt_baseline_comparison.csv`
* `models/benchmarks/cabin/phone_baseline_comparison.csv`

Nihai karar dosyalari:

* `research/08_cabin_risk/decision_cabin_baseline_v1.md`
* `research/08_cabin_risk/upper_body_pose/decision_driver_pose_baseline_v1.md`
* `research/08_cabin_risk/upper_body_pose/decision_driver_skeleton_freeze_v1.md`
* `research/08_cabin_risk/arm_state/decision_arm_state_baseline_v1.md`
* `research/08_cabin_risk/seatbelt/decision_seatbelt_baseline_v1.md`
* `research/08_cabin_risk/phone/deep_research_tiny_phone_detector.md`

Secilmis summary JSON:

* `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-009-vitpose_b_final_torso_baseline_v1-summary.json`
* `models/benchmarks/artifacts/PHONE-EXP-001-yolo11n_coco_cell_phone_driver_roi_v1-summary.json`

Tum Cabin/Driver benchmark summary artifact'leri:

* `models/benchmarks/artifacts/CABIN-EXP-001-blazeface_full_range-summary.json`
* `models/benchmarks/artifacts/CABIN-EXP-002-blazeface_short_range-summary.json`
* `models/benchmarks/artifacts/CABIN-EXP-004-opencv_yunet_2026may-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-001-yolo11n_pose_coco17-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-002-mediapipe_pose_landmarker_full-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-003-rtmpose_l_body7_384x288_onnx-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-004-rtmw_l_cocktail14_wholebody_384x288_onnx-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-005-vitpose_b_simple_coco17_hf-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-006-vitpose_b_temporal_stabilized_v1-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-007-vitpose_b_temporal_hysteresis_v2-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-008-vitpose_b_visibility_decoupled_v3-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-009-vitpose_b_final_torso_baseline_v1-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-010-vitpose_b_arm_focus_observations_v1-summary.json`
* `models/benchmarks/artifacts/POSE-EXP-011-yolo11n_pose_arm_focus_coco17-summary.json`
* `models/benchmarks/artifacts/TORSO-EXP-001-yunet_face_anchored_deterministic_torso_v1-summary.json`
* `models/benchmarks/artifacts/ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json`
* `models/benchmarks/artifacts/ARM-EXP-001-yolo11n_pose_arm_focus_coco17-lk_arm_tracker_v1-summary.json`
* `models/benchmarks/artifacts/VLM-ARM-EXP-001-LLAMA_MODEL_ADI-summary.json`
* `models/benchmarks/artifacts/SEATBELT-EXP-001-opencv_diagonal_belt_evidence_v1-summary.json`
* `models/benchmarks/artifacts/SEATBELT-EXP-002-condition_roi_extract-summary.json`
* `models/benchmarks/artifacts/SEATBELT-EXP-002-risef_yolo11s_seatbelt_cls-summary.json`
* `models/benchmarks/artifacts/PHONE-EXP-001-yolo11n_coco_cell_phone_driver_roi_v1-summary.json`

Overlay klasorleri:

* Face: `runs/cabin/cabin_exp_004/annotated/`
* Torso: `runs/cabin_pose/pose_exp_009/annotated/`
* Arm reference: `runs/driver_arm_state/arm_exp_001/annotated/`
* Phone rejected baseline: `runs/phone/phone_exp_001/annotated/`

Secilmis baseline'lari yeniden uretme:

```bash
source .venv-yolo/bin/activate

python scripts/benchmarks/run_cabin_visibility_baseline.py \
  --experiment CABIN-EXP-004

HF_HOME=.hf-cache MPLCONFIGDIR=.mplconfig python \
  scripts/benchmarks/run_driver_pose_baseline.py \
  --experiment POSE-EXP-009
```

Ortam bagimliliklari: `scripts/benchmarks/requirements.txt`.

## 9. Fine-Tune Ekibine Verilecek Paket

Repo ile birlikte su Git-disi materyaller ayrica verilmelidir:

1. `Test/video_1.mp4`, `video_2.mp4`, `video_3.mp4` ve veri kullanim izni.
2. `runs/cabin/cabin_exp_004/annotated/` manuel referans overlay'leri.
3. `runs/cabin_pose/pose_exp_009/annotated/` final torso overlay'leri.
4. `runs/phone/finetune_samples/` telefon crop ve annotation CSV'si.
5. `runs/phone/specialist_datasets/phone_windshield_seed_v1/` seed YOLO dataset.
6. Gerekliyse `models/checkpoints/cabin/` binary checkpoint'leri.

Mevcut test videolari train'e katilirsa eski baseline ile adil karsilastirma
yapilamaz. En az bir tamamen held-out video/session korunmalidir.

## 10. Degistirilmemesi Gereken Kararlar

* YuNet yeni challenger olcumle gecilmeden kaldirilmaz.
* `POSE-EXP-009` scoped shoulder/torso baseline olarak sabittir.
* Lower-arm wheel/raised/off-wheel calismasi yeniden acilmaz.
* Seatbelt bilinmiyorsa `unknown`; yokluk `unbelted` sayilmaz.
* Telefon gorulmesi tek basina `phone_risk=true` yapmaz.
* Pozitif-only 21-crop smoke sonucu baseline olarak raporlanmaz.
* Hazir model yetersizse custom phone/smoking specialist fine-tune yapilir.
