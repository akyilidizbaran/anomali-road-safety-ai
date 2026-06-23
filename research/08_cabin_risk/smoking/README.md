# Smoking / Cigarette Detection Research

Tarih: 2026-06-23

## Kısa Karar

Sigara için hazır bir modeli doğrudan baseline yapmak şu aşamada savunulabilir
görünmüyor.

En doğru başlangıç mimarisi:

`YuNet driver face -> ViTPose-B torso/arm observation -> mouth/hand ROI -> cigarette object specialist -> hand-mouth temporal fusion -> guarded smoking_status`

Telefon tarafında öğrendiğimiz ana ders burada da geçerli:

* küçük nesne tek başına zor,
* object yokluğu negatif karar değildir,
* pose/hand tek başına risk değildir,
* hard-negative olmadan risk baseline seçilmez.

## Neden Hazır Model Yetmeyebilir?

Sigara, telefondan daha küçük ve daha az pikselli bir nesne. Mevcut kamera açısında
sürücü cam arkasında, düşük ışıkta ve yüz/elle kısmi kapanma altında görülüyor. Bu
yüzden genel web görüntüleriyle eğitilmiş cigarette/smoker modelleri muhtemelen
domain transferde zorlanacak.

Araştırmada öne çıkan iki teknik desen:

1. **ROI-first classification/detection**
   Tüm frame yerine yüz, ağız ve el çevresi ROI'lerinden karar üretmek.

2. **Hierarchical/coarse-to-fine detection**
   Önce hand/head/cigarette ilişkisini kaba seviyede bulup sonra ağız, parmak ve
   cigarette çevresinde ince detector çalıştırmak.

Bu desenler mevcut pipeline'ımızla uyumlu.

## Önerilen İlk Baseline Adayı

`SMOKING-EXP-001 = cigarette_object_yolo26s_face_hand_roi_v1`

Amaç:

* ağız/çene çevresi,
* el-yüz yakın bölgesi,
* parmak/eldeki ince beyaz obje,
* opsiyonel duman/parlak uç evidence'i

üzerinden cigarette object candidate üretmek.

Bu model final risk üretmez. Sadece:

* `smoking_object_detected`
* `smoking_object_confidence`
* `smoking_object_roi`
* `smoking_evidence_source`

gibi metadata üretir.

## Önerilen Davranış Baseline Adayı

`SMOKING-EXP-002 = cigarette_object_hand_mouth_temporal_fusion_v1`

Kanıtlar:

* cigarette object branch,
* hand-mouth / wrist-mouth proximity,
* same-side temporal consistency,
* mouth-zone dwell time,
* pose reliability guardrail,
* optional smoke/glow visual cue.

Çıktı statüleri:

* `smoking_likely`
* `candidate`
* `not_detected`
* `not_evaluable`

`smoking_risk` veya event risk artışı final kabul seti geçene kadar kapalı kalır.

## Hard-Negative Listesi

Sigara için hard-negative seti telefon kadar kritik. Minimum alt tipler:

* telefonla konuşma,
* el ağızda/yüzde,
* tırnak yeme,
* su içme,
* yiyecek yeme,
* kalem/çubuk/şeker tutma,
* maske/sakal/bıyık veya yüz çevresi parlaklık,
* yolcu sigarası,
* cam yansıması,
* düşük ışıkta beyaz trim/parlama.

## Final Baseline Kabul Kapısı

İlk savunulabilir baseline için session bazlı minimum:

* `positive_smoking_sessions >= 3`
* `negative_sessions >= 5`
* `hard_negative_sessions >= 3`
* `occluded_or_tiny_cigarette_positive_sessions >= 1`
* event recall `>= 0.80`
* event specificity `>= 0.90`
* hard-negative specificity `>= 0.90`

Ek güvenlik kuralı:

* Object yoksa `not_detected` değil, pose/visibility'e göre `candidate` veya
  `not_evaluable` bırakılabilir.
* Pose reliability düşükse negatif karar üretilmez.
* Tek kare cigarette benzeri obje risk üretmez; temporal süreklilik gerekir.

## Veri Toplama Planı

İlk veri paketi:

| Grup | Minimum | Not |
|---|---:|---|
| Pozitif smoking | 3 session | farklı kişi/açı/ışık |
| Negatif neutral | 5 session | el ağızdan uzak |
| Hard-negative | 3 session | el-ağız var ama sigara yok |
| Occluded positive | 1 session | sigara küçük/kısmi görünür |

Frame-level box yerine ilk aşamada segment-level label yeterli:

* `smoking`
* `neutral`
* `face_touch_hard_negative`
* `drink_eat_hard_negative`
* `phone_call_hard_negative`
* `unknown`

Object detector eğitimi için sonradan ağız/el ROI crop'larında cigarette box
etiketi gerekir.

## Mevcut Pipeline ile Bağlantı

Kullanılacak hazır altyapı:

* YuNet cabin face anchor,
* ViTPose-B torso/shoulder baseline,
* phone-call temporal-head yaklaşımı,
* event skeleton enrichment contract,
* `smoking_status` / `smoking_confidence` alanları.

Yeni yazılacak scriptler telefon scriptlerinin sibling'i olmalı:

* `scripts/benchmarks/run_smoking_baseline.py`
* `scripts/benchmarks/prepare_smoking_finetune_samples.py`
* `scripts/benchmarks/prepare_smoking_segment_review.py`
* `scripts/benchmarks/train_smoking_temporal_head.py`
* `scripts/benchmarks/enrich_event_skeleton_with_smoking.py`

## İlk Teknik Yol Haritası

1. Mevcut `Test/video_1-3.mp4` içinde sigara pozitif var mı manuel taranır.
2. Eğer yoksa ekipten pozitif sigara örneği istenir.
3. İlk review pack hazırlanır:
   * mouth/hand ROI contact sheet,
   * kısa candidate segmentler,
   * neutral/hard-negative segmentler.
4. Hazır cigarette/smoker modelleri yalnız challenger olarak denenir.
5. Eğer hazır model domain transferde zayıfsa YOLO26s-P2 cigarette specialist
   fine-tune edilir.
6. Object branch, hand-mouth temporal fusion ile birleştirilir.
7. Kabul kapısı geçilene kadar `smoking_risk=null` kalır.

## İlk Uygulama Durumu

`SMOKING-EXP-000 = smoking_segment_review_pack_v1` eklendi ve çalıştırıldı.

Komut:

```bash
.venv-yolo/bin/python scripts/benchmarks/prepare_smoking_segment_review.py
```

Çıktılar:

* `runs/smoking_review/segment_review_v1/manual_smoking_segments_review.csv`
* `runs/smoking_review/segment_review_v1/clips/`
* `runs/smoking_review/segment_review_v1/contact_sheets/`
* `models/benchmarks/artifacts/smoking/SMOKING-EXP-000-segment_review_pack.json`
* `testing/reports/smoking_exp_000_segment_review.md`

Sonuç: 3 videodan toplam 6 mouth/hand review segmenti çıkarıldı. Bu segmentler
henüz etiketlenmediği için baseline veya training verisi değildir.

Visual review sonrası durum:

* `smoking=0`
* `phone_call_hard_negative=1`
* `unknown=2`
* `not_evaluable=3`

Mevcut üç videoda sigara pozitif yok. Bu nedenle sigara modeli eğitimi için yeni
pozitif session gereklidir. Hazır cigarette detector denemesi yapılırsa mevcut veri
yalnız false-positive / hard-negative smoke testi sayılmalıdır.
