# Driver Action Model ve Veri Araştırması

Tarih: 2026-06-23

Bu dosya, FTR kapsamındaki `sofor_eylemi` alanı için sürücü eylemi
modellerinin hangi veri ve model omurgasıyla ilerletileceğini belirler. Amaç tek
seferde bütün sınıfları final yapmak değildir; her etiketi çalışır bir baseline'a
bağlamak, güvenilir olmayan etiketleri `candidate` veya `not_evaluable` olarak
tutmak ve zaman kalırsa fine-tune ile iyileştirmektir.

## 1. Kısa Karar

`slalom` bu fazda cabin-view modeliyle değil, dış kamera target-track hareket
analiziyle kilitlenir. Sıradaki driver/cabin fazı şu sırayla açılmalıdır:

1. `DACT-EXP-020B` - State Farm + opsiyonel AUC tabanlı driver action
   classifier.
2. `DACT-EXP-021` - phone / bottle-cup / cigarette gibi küçük nesne specialist
   detector'ları.
3. `DACT-EXP-022` - yawning/esneme için face-landmark + yawn classifier.
4. `DACT-EXP-023` - seatbelt violation için ayrı belt detector/usage classifier.
5. `DACT-EXP-024` - gaze/head-pose ile `etrafa_bakinma` ve `arkaya_bakma`
   güçlendirme.

İlk notebook olarak `DACT-EXP-020B` hazırlanmalıdır. Bunun nedeni elimizde
State Farm zip akışı, Colab classifier altyapısı ve FTR ile birebir örtüşen iki
güçlü sınıfın bulunmasıdır: `telefonla_konusma` ve `su_icme`.

## 2. Mevcut Repo Durumu

| Modül | Durum | Bu fazdaki etkisi |
|---|---|---|
| `CABIN-EXP-020A` cabin-view gate | Kabul edildi | Dış yol videosu cabin-action hattına sokulmaz. |
| YuNet face / occupant | Seçilmiş baseline | Cabin görünürse driver face anchor olarak kullanılabilir. |
| ViTPose torso | Seçilmiş/frozen | Torso/shoulder ROI ve temporal evidence için kullanılır. |
| Phone branch | Candidate, final değil | `telefonla_konusma` kararını destekler ama tek başına final risk üretmez. |
| Smoking branch | Pozitif veri yok | Yeni veri/model gerektirir. |
| Seatbelt branch | Deferred | `emniyet_kemeri_ihlali` ayrı fazdır. |
| `DACT-EXP-001` slalom | Çalışır baseline | Dış kamera track residual sinyalidir; cabin-action modeli değildir. |

Önemli sınır: `Test/video_1.mp4`, `Test/video_2.mp4`, `Test/video_3.mp4`
dış-yol/dark test videolarıdır. Bunlar driver-action eğitimi veya action accuracy
iddiası için uygun değildir. Bu videolarda cabin-action hattının beklenen çıktısı
`not_cabin_view` / `not_evaluable` olmalıdır.

## 3. FTR Driver Label Haritası

| FTR etiketi | İlk önerilen çözüm | Veri desteği | Karar seviyesi |
|---|---|---|---|
| `slalom` | Track residual / lateral oscillation heuristic | Mevcut 3 video + tracking | Kilitli baseline, manuel overlay review sonrası FTR adapter'a bağlanabilir. |
| `telefonla_konusma` | Image classifier + phone/hand-ear temporal fusion | State Farm, AUC, DMD | İlk güçlü sınıf. Texting ile phone-call ayrımı korunmalı. |
| `su_icme` | Image classifier + bottle/cup object evidence | State Farm, AUC, DMD | İlk güçlü sınıf. Object branch ile desteklenmeli. |
| `arkaya_bakma` | Reaching-behind classifier + head/torso direction gate | State Farm/AUC weak, DMD daha iyi | `candidate` başlatılmalı; yalnız reaching'i bakma diye kesin yazmamak gerekir. |
| `etrafa_bakinma` | Head pose / gaze temporal classifier | DMD gaze/head-pose, MediaPipe landmarks | State Farm ile kapatılmaz; ayrı head-pose fazı gerekir. |
| `esneme` | Face landmark mouth aspect ratio + yawn classifier | YawDD, NTHU DDD, DMD fatigue | Ayrı face/yawn fazı gerekir. |
| `sigara_icme` | Cigarette object specialist + hand-mouth temporal fusion | Genel cigarette/smoking verileri + custom hard-negative | State Farm ile kapatılmaz; özel pozitif veri gerekir. |
| `emniyet_kemeri_ihlali` | Seatbelt detector / usage recognition | Seatbelt DMS literatürü, Roboflow/Kaggle adayları, custom | Ayrı belt fazı; yokluk tek başına ihlal değildir. |

## 4. Veri Seti Araştırması

| Veri seti | Kullanım | Güçlü taraf | Risk / sınırlama | Karar |
|---|---|---|---|---|
| State Farm Distracted Driver Detection | `telefonla_konusma`, `su_icme`, reaching-behind, hard-negative | 10 sınıflı sürücü davranışı; Kaggle erişimi ve repo akışımız hazır | Kaggle competition/rules erişimi gerekir; tek-kare dataset; texting phone-call ile karıştırılmamalı | `DACT-EXP-020B` için birincil başlangıç |
| AUC Distracted Driver Dataset | State Farm dışı validation / ikinci kaynak | 44 katılımcı, 14.478 frame; phone, text, drinking, reaching, passenger sınıfları var | Non-commercial, yeniden dağıtım yasak; erişim/izin dikkatli | İkinci kaynak / external validation |
| DMD Driver Monitoring Dataset | Daha kapsamlı driver monitoring ve fatigue/gaze/action | RGB face/body/hands view, distraction, fatigue, gaze, head pose etiketleri | Çok büyük; 2026 revizyonunda stream/subject kısıtları var; subset builder gerekir | Orta vadede en güçlü gerçek-car kaynak |
| Drive&Act | Fine-grained action/video-temporal benchmark | 12 saat, 29 sequence, 5 view, 83 hiyerarşik label | Research only; simulator/static görevler; büyük ve karmaşık | Video-temporal model ve future research |
| 3MDAD | Day/night, multiview/multimodal driver action | Gerçek araç, daytime/nighttime, frontal/side views | CC BY-NC-ND; derivative/model-release yorumu riskli olabilir | Sadece dikkatli research/eval adayı |
| YawDD | `esneme` / yawn | 342 driver yawn videosu, dash/mirror view | Parked-car; yalnız yawn odaklı | `DACT-EXP-022` için ana aday |
| NTHU Drowsy Driver Detection | Yawn/slow blink/head nod | Drowsiness davranışları | Simulated/acted; erişim ve format ayrıca doğrulanmalı | Yawn/fatigue destek kaynağı |
| Roboflow / HF synthetic driver monitoring | Phone, cigarette, drinking, seatbelt object detector destekleri | Hızlı YOLO export, CC kaynaklar bulunabilir | Veri kalitesi/lisans değişken; domain gap yüksek | Birincil değil, specialist destek/hard-negative |

## 5. Model Adayları

| Model ailesi | Nerede kullanılır | Artı | Eksi | Karar |
|---|---|---|---|---|
| MobileNetV3-Large | İlk action classifier | Hafif, Colab/MacBook uyumlu, önceki notebook desenleriyle aynı | Tek-kare; temporal action'ı doğrudan öğrenmez | `DACT-EXP-020B` ana aday |
| EfficientNet-B0 | İlk action classifier | Genelde MobileNet'ten daha güçlü, hâlâ hafif | Biraz daha yüksek latency | `DACT-EXP-020B` challenger |
| VideoMAE / TimeSformer / X3D | Clip-level action | Gerçek temporal davranışı daha iyi modelleyebilir | Veri ve compute maliyeti yüksek; MacBook runtime daha zor | İlk fazdan sonra |
| MediaPipe Face Landmarker / face mesh | Yawn, gaze/head movement, mouth metric | Tek kamera, gerçek zamanlı, landmark tabanlı açıklanabilir sinyal | Cam/düşük ışıkta face visibility gate ister | `esneme` ve `etrafa_bakinma` için güçlü |
| ViTPose + temporal geometry | Phone-call, hand-mouth, torso/head relation | Mevcut pipeline ile uyumlu, domain-agnostic geometri sağlar | Keypoint kalitesi düşükse karar üretilmez | Classifier'ı destekleyen evidence layer |
| YOLO11/YOLO26 small-object specialist | phone, bottle/cup, cigarette, seatbelt | Evidence JSON için bbox/crop üretir | Küçük nesne recall zor; hard-negative şart | `DACT-EXP-021+` |
| VLM/video-language model | Audit veya teacher | Fine-grained açıklama üretebilir | Runtime ağır, deterministik değil, FTR için fazla riskli | İlk fazda kullanılmamalı |

## 6. Önerilen İlk Deney: DACT-EXP-020B

Deney adı:

```text
DACT-EXP-020B-statefarm_auc_driver_action_classifier_v1
```

İlk hedef:

* `telefonla_konusma`
* `su_icme`
* `arkaya_bakma_candidate`
* `safe_or_no_event`
* `other_distraction_hard_negative`

State Farm sınıf mapping'i:

| Kaynak sınıf | İç label | FTR kullanımı |
|---|---|---|
| `c0 safe driving` | `safe_or_no_event` | Event üretmez |
| `c1 texting right`, `c3 texting left` | `phone_use_non_call` | Phone-use hard-negative/support; doğrudan `telefonla_konusma` değil |
| `c2 phone right`, `c4 phone left` | `telefonla_konusma` | FTR driver action candidate |
| `c5 operating radio` | `other_distraction_hard_negative` | Event üretmez veya internal candidate |
| `c6 drinking` | `su_icme` | FTR driver action candidate |
| `c7 reaching behind` | `arkaya_bakma_candidate` | Head/torso gate geçmeden final `arkaya_bakma` değil |
| `c8 hair/makeup` | `other_distraction_hard_negative` | Smoking/face-touch için hard-negative |
| `c9 talking passenger` | `passenger_interaction_candidate` | `etrafa_bakinma` için doğrudan yeterli değil |

Notebook çıktıları:

```text
notebooks/CABIN_EXP_020B_Driver_Action_Classifier_Colab.ipynb
models/checkpoints/cabin_driver/DACT-EXP-020B-driver-action-classifier-best.pth
models/benchmarks/artifacts/cabin_driver/DACT-EXP-020B-summary.json
testing/reports/dact_exp_020b_driver_action_classifier.md
```

Runtime contract:

1. `CABIN-EXP-020A` önce çalışır.
2. Eğer frame/crop `not_cabin_view` ise driver action classifier çalışmaz.
3. Cabin görünürse action classifier crop/clip üzerinde çalışır.
4. Tek frame kararı final olmaz; track/clip-level temporal voting uygulanır.
5. FTR etiketi yalnız confidence, temporal persistence ve support evidence gate
   geçtiğinde yazılır.

## 7. Temporal Voting ve Gate

İlk gate önerisi:

| Alan | Öneri |
|---|---|
| Sampling | 5-10 FPS cabin/action sampling |
| Clip window | 1.0-2.0 sn kayan pencere |
| Per-frame min confidence | `0.55` başlangıç, validation sonrası sweep |
| Clip-level persistence | Aynı action en az `3` frame / pencerenin `%40`ı |
| Conflict handling | Phone-call ile drinking aynı anda ise `ambiguous_multi_action` |
| Not evaluable | Cabin visibility poor, face missing veya action confidence düşük |

FTR adapter'a doğrudan yazılacak alanlar:

```json
{
  "sofor_eylemi": "telefonla_konusma",
  "confidence": 0.0,
  "source": "DACT-EXP-020B + temporal_gate",
  "status": "candidate|confirmed|not_evaluable",
  "evidence_refs": []
}
```

## 8. Kabul Kriterleri

`DACT-EXP-020B` final değil, ilk driver-action baseline kabulü için minimum:

* State Farm split driver/session leakage olmadan yapılmalı.
* `telefonla_konusma` ve `su_icme` per-class F1 raporlanmalı.
* `phone_use_non_call` ile `telefonla_konusma` ayrımı confusion matrix'te ayrıca
  gösterilmeli.
* AUC dataset erişilebilirse external validation yapılmalı; erişilemiyorsa raporda
  "external validation pending" yazılmalı.
* `Test/video_1-3.mp4` dış-yol videolarında action inference `not_cabin_view` gate
  ile kapanmalı.
* Checkpoint, label map, confusion matrix, class support ve inference latency
  kaydedilmeli.

## 9. Neden Sigara / Kemer / Esneme ile Başlamıyoruz?

* `sigara_icme`: State Farm/AUC içinde doğrudan yok. Cigarette çok küçük nesne;
  pozitif/hard-negative veri olmadan false positive riski yüksek.
* `emniyet_kemeri_ihlali`: Kemer çizgisi görünmemesi ihlal değildir. Kemer kullanımı
  ayrı usage-recognition problemidir.
* `esneme`: Action classifier değil, yüz/mouth landmark veya yawn-specific video
  dataset ister.
* `etrafa_bakinma`: Genel action classifier etiketi değil, head pose/gaze temporal
  problemidir.

Bu yüzden ilk deney en çok veri desteği olan ve raporda savunması en kolay iki
etiketi kapatır: `telefonla_konusma` ve `su_icme`.

## 10. Kaynaklar

* State Farm Distracted Driver Detection:
  https://www.kaggle.com/c/state-farm-distracted-driver-detection
* State Farm sınıf listesi için açık README referansı:
  https://github.com/Abhinav1004/Distracted-Driver-Detection
* AUC Distracted Driver Dataset:
  https://heshameraqi.github.io/distraction_detection
* Drive&Act dataset:
  https://driveandact.com/
* Drive&Act ICCV 2019 paper:
  https://openaccess.thecvf.com/content_ICCV_2019/papers/Martin_DriveAct_A_Multi-Modal_Dataset_for_Fine-Grained_Driver_Behavior_Recognition_in_ICCV_2019_paper.pdf
* DMD official site:
  https://dmd.vicomtech.org/
* DMD GitHub / 2026 revision notes:
  https://github.com/Vicomtech/DMD-Driver-Monitoring-Dataset
* 3MDAD dataset page:
  https://sites.google.com/view/ihsen-alouani/datasets
* YawDD dataset:
  https://qualinet.github.io/databases/video/yawdd_a_yawning_detection_dataset/
* MediaPipe Face Landmarker:
  https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker
* Hugging Face video classification task guide:
  https://huggingface.co/docs/transformers/en/tasks/video_classification
* VideoMAE model documentation:
  https://huggingface.co/docs/transformers/en/model_doc/videomae
