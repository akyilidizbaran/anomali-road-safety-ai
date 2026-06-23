# Phone-Call Behavior Baseline V2 Kararı

Tarih: 2026-06-18

## Karar

`PHONE-CALL-EXP-002 = phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2`
teknik candidate olarak seçildi, ancak veri kapsama kapısını geçmediği için henüz
final baseline olarak sabitlenmedi.

20 Haziran 2026 itibarıyla `EXP-002 + EXP-007` stack'i
`PHONE-CALL-PROVISIONAL-BASELINE` adıyla entegrasyon/demo için donduruldu. Bu final
risk baseline'ı değildir; `phone_risk=null` kalır. Detay:
`research/08_cabin_risk/phone/phone_call_provisional_baseline.md`.

V2 farkları:

* yüzün tamamı yerine ayrı image-left/image-right kulak interaction bölgeleri,
* anatomik omuz-dirsek-bilek zinciri,
* aynı taraf sürekliliği,
* iki saniyelik geçmişe bakan causal pencere,
* ayrı giriş/çıkış eşiğiyle hysteresis,
* görünür telefon için standard YOLO26s object branch,
* object ve pose-temporal kanıtın ayrı contract alanları.

## Üç-Video Sonucu

| Video | Object | Call status | Ear rate | Side consistency | Longest |
|---|---|---|---:|---:|---:|
| `video_1` | not detected | candidate | 0.8556 | 0.5336 | 1.08 sn |
| `video_2` | detected | handheld_call_likely | 0.9474 | 0.7677 | 3.60 sn |
| `video_3` | not detected | candidate | 0.4552 | 0.8116 | 0.20 sn |

Kullanıcı tarafından pozitif olduğu doğrulanan `video_2` doğru yakalandı. Kulak
geometrisi, `video_1/3` kayıtlarını kesin çağrı yerine candidate seviyesinde tuttu.

## Object Challenger Karşılaştırması

`video_2`, seed eğitimin kaynağı olduğu için aşağıdaki sonuç genelleme metriği
değil, yalnız pipeline smoke karşılaştırmasıdır.

| Model | video_2 detection rate | Mean latency | Karar |
|---|---:|---:|---|
| YOLO26s-P2 | 0.4449 | 115.1 ms | seçilmedi |
| standard YOLO26s | 0.8163 | 81.4 ms | v2 object candidate |

## Kabul Kapısı

İlk savunulabilir baseline için en az (kapsama **session** bazında sayılır):

* 3 farklı pozitif session,
* 5 farklı negatif session,
* bunlardan >= 2 hard-negative session (boş olmayan `negative_subtype`),
* >= 1 occluded-positive session (`phone_visibility=not_visible|partially_occluded`),
* event recall >= 0.80,
* genel event specificity >= 0.90,
* hard-negative alt kümesinde specificity >= 0.90,
* yüz kaşıma, saç/gözlük düzeltme, yanağa dayanma, sigara ve yolcu telefonu
  örneklerinin manuel review'u.

20 Haziran 2026'da `evaluate_phone_call_behavior.py` sertleştirildi: kapsama satır
değil ayrı `session_id` üzerinden sayılır, hard-negative specificity ayrı raporlanır
ve kabul için ayrıca >= 0.90 olmalıdır. Böylece yalnız kolay negatiflerle alınan
yüksek genel specificity baseline'ı geçiremez. Harness her blocker'ı
`coverage_blockers` / `quality_blockers` alanlarında açıkça döner.

Mevcut confusion matrix yalnız doğrulanmış `video_2`yi içerir: `TP=1`; negatif ve
hard-negative session olmadığı için specificity hesaplanamaz. Harness şu blocker'ları
döndürür: `positive_sessions=1<3`, `negative_sessions=0<5`,
`hard_negative_sessions=0<2`, `specificity=None<0.9`,
`hard_negative_specificity=None<0.9`. Bu nedenle `baseline_accepted=false` ve
`phone_risk=null` korunur.

## Harici Davranış Modeli Araştırması

18 Haziran 2026'da iki bağımsız domain challenger yerelde üç videoda denendi.
İkisi de `PHONE-CALL-EXP-002` yerine geçirilecek kadar ayrıştırıcı değildi.

| Deney | Kaynak | Yerel sonuç | Karar |
|---|---|---|---|
| `PHONE-CALL-EXP-003` | State Farm üzerinde eğitilmiş YOLO26s, 4 sınıf | Pozitif `video_2` phone ortalaması 0.1293-0.1568; `video_3` 0.3396-0.3868 | domain transfer başarısız |
| `PHONE-CALL-EXP-004` | AI City 2024 Track 3 X3D rearview/right-view fold 0, 16 sınıf | Her iki view modelinde de `video_2` cabin kliplerinde yalnız 1/11 kez phone top-1; zamanları farklı, sürdürülebilir sinyal yok | domain transfer başarısız |

State Farm modeli yakın iç-kabin/gündüz görüntülerine; AI City modeli araç içine
yerleştirilmiş üç kamera görünümüne göre eğitilmiş. Mevcut ön-cam dış kamera
görüntüsünde sürücü az piksel kaplıyor ve cam/karanlık etkisi bulunuyor. Sonuçlar,
yalnız yeni pretrained checkpoint aramanın baseline kapısını çözmediğini gösteriyor.

Doğrulanan kaynaklar:

* State Farm challenger: <https://huggingface.co/maco018/in-car-distraction-yolo26>
* AI City veri ve görev tanımı: <https://www.aicitychallenge.org/2024-data-and-evaluation/>
* AI City resmi üst ekip kod listesi: <https://github.com/NVIDIAAICITYCHALLENGE/2024AICITY_Code_From_Top_Teams>
* SKKU X3D çözümü ve ağırlık bağlantıları: <https://github.com/SKKUAutoLab/aicity_2024_driving_action>

Tekrarlanabilir ölçüm ayrıntıları ve checksum değerleri:
`models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-003-004-external-action-challengers.json`.

## Sonraki Teknik Karar

Baseline'a giden yol, mevcut kamera domain'inde session-disjoint veri toplamaktır.
Toplanan kliplerle üç sınıflı bir temporal head eğitilecek:

1. `phone_call`,
2. `face_touch_hard_negative`,
3. `neutral`.

Object branch pozitif kanıt olarak kalacak; görünmeyen telefonlarda temporal action
head ve el-kulak geometrisi birlikte karar verecek. Dış modeller yalnız backbone
başlatma/challenger amaçlı kullanılacak; yerel kabul setini geçmeden risk üretmeyecek.

## Temporal Head Eğitim Durumu

19 Haziran 2026'da `PHONE-CALL-EXP-005 = phone_call_temporal_head_v1` eğitim
hattı eklendi. Bu model, görüntüden doğrudan büyük backbone fine-tune etmek yerine
mevcut kanıt katmanlarını pencere bazında kullanır:

* el-yüz ve el-kulak oranları,
* sol/sağ kulak taraf sürekliliği,
* en uzun sürdürülebilir el-kulak sekansı,
* pose confidence / optical-flow recovery sinyali,
* telefon object detection oranı ve face-near sinyali.

Gerçek modda script, reviewed segment label dosyasında en az iki sınıf yoksa eğitimi
durdurur. Mevcut eldeki reviewed etiketler yalnız `video_2=phone_call` içerdiği
için gerçek eğitim bilinçli olarak durmuştur. Pipeline doğrulaması için
`--smoke-pseudo-labels` ile kısa bir eğitim çalıştırıldı; bu koşuda `video_2`
pozitif, `video_1/3` pseudo negatif kabul edildiği için sonuç baseline kanıtı
değildir.

Smoke sonucu:

| Alan | Değer |
|---|---:|
| Window sayısı | 40 |
| Train window | 28 |
| Eval window | 12 |
| Train sınıfları | 14 neutral / 14 phone_call |
| Eval sınıfı | 12 neutral |
| Eval accuracy | 0.833333 |
| Baseline eligible | false |

Bu çıktı yalnız eğitim kodunun ve feature birleşiminin çalıştığını gösterir. Baseline
kararı için reviewed segment etiketleriyle yeniden koşulmalıdır:

```bash
.venv-yolo/bin/python scripts/benchmarks/train_phone_call_temporal_head.py
```

Smoke doğrulama komutu:

```bash
.venv-yolo/bin/python scripts/benchmarks/train_phone_call_temporal_head.py \
  --smoke-pseudo-labels \
  --epochs 80 \
  --artifact models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-005-temporal_head_smoke_training.json
```

20 Haziran 2026'da review CSV'nin boş `final_label` alanları nedeniyle gerçek
komutun neden durduğu netleştirildi. Script artık boş review CSV için açık hata
verir ve `split=review` satırlarını, label doldurulduktan sonra session bazında
otomatik train/val olarak ayırır.

Ek olarak orijinal review CSV'ye dokunmadan seed-label eğitim dosyası üretildi:

* Seed label CSV: `runs/phone_call_review/segment_review_v1/manual_phone_call_segments_seed_labels.csv`
* Seed eğitim artifact'i: `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-005-temporal_head_seed_training.json`
* Seed model: `models/checkpoints/cabin/phone_call_temporal_head_exp005_seed.pt`

Seed eğitimde yalnız güvenli satırlar trainable yapıldı: kullanıcı doğruluğu olan
`video_2_candidate_01=phone_call` ve üç neutral/context segmenti `neutral`. Şüpheli
`video_1_candidate_01` ve `video_3_candidate_01` `unknown` bırakıldı.

Seed sonuç:

| Alan | Değer |
|---|---:|
| Trainable label | 3 neutral / 1 phone_call |
| Window sayısı | 12 |
| Train window | 11 |
| Eval window | 1 |
| Positive session | 1 |
| Negative session | 3 |
| Eval accuracy | 1.0 |
| Baseline eligible | false |

Bu sonuç baseline kanıtı değildir; eval setinde yalnız 1 neutral window vardır.
Ama gerçek `final_label` formatı ve temporal-head eğitim hattı çalışmaktadır.

20 Haziran 2026 ikinci review geçişinde ana review CSV de dolduruldu:

* `video_1_candidate_01 = phone_call` (`phone_visibility=not_visible`),
* `video_2_candidate_01 = phone_call` (`phone_visibility=not_visible`),
* `video_1_neutral_01`, `video_2_neutral_01`, `video_3_neutral_01 = neutral`,
* `video_3_candidate_01 = unknown` ve eğitim dışında bırakıldı.

Bu review ile gerçek komut çalıştı:

```bash
.venv-yolo/bin/python scripts/benchmarks/train_phone_call_temporal_head.py \
  --segment-labels runs/phone_call_review/segment_review_v1/manual_phone_call_segments_review.csv
```

Sonuç:

| Alan | Değer |
|---|---:|
| Trainable label | 3 neutral / 2 phone_call |
| Window sayısı | 22 |
| Train window | 21 |
| Eval window | 1 |
| Positive session | 2 |
| Negative session | 3 |
| Eval accuracy | 1.0 |
| Baseline eligible | false |

Bu da baseline değildir; çünkü kabul kapısı hâlâ `positive_sessions>=3` ve
`negative_sessions>=5` ister. Ayrıca eval seti yalnız 1 neutral window içerdiği için
accuracy değeri karar metriği olarak kullanılmaz.

## Segment Review Paketi

20 Haziran 2026'da `PHONE-CALL-EXP-006 = phone_call_segment_review_pack_v1`
eklendi. Bu adım model eğitmez; `PHONE-CALL-EXP-002` içindeki el-kulak aday
kanıtlarını insan review'una uygun segmentlere dönüştürür.

Üretilen review seti:

| Video | Candidate segment | Neutral/context segment | Not |
|---|---:|---:|---|
| `video_1.mp4` | 1 | 1 | candidate `phone_call`, neutral context `neutral` |
| `video_2.mp4` | 1 | 1 | candidate `phone_call`, neutral context `neutral` |
| `video_3.mp4` | 1 | 1 | candidate `unknown`, neutral context `neutral` |

Çıktılar:

* Review CSV: `runs/phone_call_review/segment_review_v1/manual_phone_call_segments_review.csv`
* Segment klipleri: `runs/phone_call_review/segment_review_v1/clips/`
* Contact sheet görselleri: `runs/phone_call_review/segment_review_v1/contact_sheets/`
* Trace artifact: `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-006-segment_review_pack.json`

Review CSV'de `final_label` alanı doldurulunca aynı dosya doğrudan temporal-head
eğitimine verilebilir:

```bash
.venv-yolo/bin/python scripts/benchmarks/train_phone_call_temporal_head.py \
  --segment-labels runs/phone_call_review/segment_review_v1/manual_phone_call_segments_review.csv
```

## Pose Reliability Diagnostic

20 Haziran 2026'da `PHONE-CALL-EXP-007 = phone_call_pose_reliability_diagnostic_v1`
eklendi. Bu adım davranış kararı üretmez; EXP-002'nin dayandığı pose kanıtının
güvenilirliğini ölçer.

| Video | Reliability | Evaluable | Complete arm | Kritik not |
|---|---|---:|---:|---|
| `video_1.mp4` | usable_borderline | 0.5468 | 0.8770 | evaluable rate sınırda |
| `video_2.mp4` | decision_usable | 0.6129 | 0.9330 | en güvenilir pose kanıtı |
| `video_3.mp4` | usable_borderline | 0.4702 | 0.7985 | optical-flow wrist 0.3252, identity reset 8 |

Guardrail: `usable_borderline` durumda sistem daha güçlü temporal süreklilik istemeli;
pose yokluğundan negatif üretmemelidir. `pose_limited` durumda çıktı
`not_evaluable` veya düşük riskli `candidate` olmalıdır.

## Pose Reliability Guardrail Bağlandı

20 Haziran 2026'da EXP-007 çıktısı EXP-002 fusion kararına bağlandı:

* `decision_usable`: standart EXP-002 eşikleri kullanılır.
* `usable_borderline`: `min_sustained_seconds` en az `1.5s` yapılır.
* `pose_limited`: daha yüksek süre/oran eşiği ister; pozitifleşirse candidate'a
  düşürülür.

Yeniden üretilen EXP-002 sonucu:

| Video | Label | Status | Pose | Applied min sustained | Longest | Side rate | Outcome |
|---|---|---|---|---:|---:|---:|---|
| `video_1.mp4` | positive | candidate | usable_borderline | 1.5s | 1.08s | 0.5336 | FN |
| `video_2.mp4` | positive | handheld_call_likely | decision_usable | 0.8s | 3.60s | 0.7677 | TP |
| `video_3.mp4` | unknown | candidate | usable_borderline | 1.5s | 0.20s | 0.8116 | pending |

Bu guardrail baseline yapmadı. Güncel değerlendirme:

* `baseline_accepted=false`
* `recall=0.5`
* `positive_sessions=2<3`
* `negative_sessions=0<5`
* `hard_negative_sessions=0<2`
* `specificity=None`

Yorum: Guardrail genelleme açısından doğru yönde; borderline pose'da kısa/tutarsız
kanıtı yüksek güvenli pozitif yapmıyor. Ancak bu, `video_1` gibi occluded-positive
örnekte recall kaybı yaratıyor. Bu noktada video_1'i pozitif yapmak için eşiği
düşürmek test setine fit olur ve hard-negative olmadan savunulamaz.

## Artifactler

* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-002-phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2-summary.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-002-evaluation.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-PROVISIONAL-BASELINE.json`
* `testing/templates/manual_phone_call_review.csv`
* `testing/templates/manual_phone_call_segments.csv`
* `scripts/benchmarks/prepare_phone_call_segment_review.py`
* `scripts/benchmarks/analyze_phone_call_pose_reliability.py`
* `scripts/benchmarks/train_phone_call_temporal_head.py`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-005-temporal_head_smoke_training.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-005-temporal_head_training.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-005-temporal_head_seed_training.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-006-segment_review_pack.json`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-007-pose_reliability.json`
* `runs/phone_call_review/segment_review_v1/`
* `runs/phone_call_baseline_v2/phone_call_exp_002/annotated/`
* `models/benchmarks/artifacts/phone_call_baseline_v2/PHONE-CALL-EXP-003-004-external-action-challengers.json`
