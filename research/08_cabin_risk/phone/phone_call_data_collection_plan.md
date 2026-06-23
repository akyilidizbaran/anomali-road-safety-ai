# Phone-Call Baseline Veri Toplama Plani

Tarih: 2026-06-18

## Minimum Kabul Seti

Her video farkli bir kayit/session olmali; ayni videonun komsu kareleri ayri test
ornekleri sayilmaz.

### Pozitif - en az 3 video

1. Telefon sag kulakta, normal aydinlik.
2. Telefon sol kulakta, dusuk aydinlik/cam yansimasi.
3. Telefon el/kafa tarafindan kismen veya tamamen kapanmis.

### Negatif / Hard Negative - en az 5 video

1. Yuz veya burun kasima.
2. Sac/gozluk/maske duzeltme.
3. Yanaga dayanma veya eli cene altinda tutma.
4. Sigara/yeme/icme nedeniyle elin agiz bolgesine gelmesi.
5. Yolcunun telefon kullanmasi veya surucunun telefonu kulaktan uzakta tutmasi.

Mumkunse ek negatifler: emniyet kemerine uzanma, el sallama, kulaklik duzeltme ve
direksiyonda iki el.

Bu minimum set yalnız event-level kabul testi içindir. Temporal action head eğitimi
için hedef en az 30 ayrı session'dır:

* 10 `phone_call`,
* 10 `face_touch_hard_negative`,
* 10 `neutral`.

Train/validation/test ayrımı kare bazında değil session ve mümkünse kişi bazında
yapılmalıdır. Aynı videodan üretilen komşu klipler iki farklı split'e giremez.

## Mevcut Videolar İçin Segment Review Akışı

Mevcut `video_1/2/3` kayıtlarından hızlı etiket üretmek için review paketi:

```bash
.venv-yolo/bin/python scripts/benchmarks/prepare_phone_call_segment_review.py
```

Bu komut:

* el-kulak aday segmentlerini çıkarır,
* her video için ek neutral/context segmenti önerir,
* kısa review kliplerini `runs/phone_call_review/segment_review_v1/clips/` altına,
* contact sheet görsellerini `runs/phone_call_review/segment_review_v1/contact_sheets/` altına,
* doldurulacak CSV'yi `runs/phone_call_review/segment_review_v1/manual_phone_call_segments_review.csv`
  altına yazar.

Reviewer, CSV'deki `final_label` alanını şu değerlerden biriyle doldurmalıdır:

* `phone_call`
* `face_touch_hard_negative`
* `neutral`
* `unknown`

Pozitiflerde `phone_visibility` için `visible`, `partially_occluded` veya
`not_visible`; negatiflerde `negative_subtype` için ör. `face_scratch`,
`hair_glasses_adjust`, `cheek_rest`, `smoke_eat_drink`, `passenger_phone`
yazılmalıdır.

Review tamamlanınca temporal head gerçek modda şöyle eğitilir:

```bash
.venv-yolo/bin/python scripts/benchmarks/train_phone_call_temporal_head.py \
  --segment-labels runs/phone_call_review/segment_review_v1/manual_phone_call_segments_review.csv
```

## Kayit Protokolu

* Her klip 5-10 saniye.
* Kamera acisi mevcut test videolarina benzer, arac ve yuz ayni anda gorunur.
* Pozitif davranis en az 2 saniye surer.
* Klip etiketi `positive`, `negative` veya `unknown` olarak
  `testing/templates/manual_phone_call_review.csv` dosyasina yazilir.
* Ayni kisi/aydinlikla sinirli kalmamak icin en az iki kisi veya iki farkli session
  tercih edilir.
* Ham videolar Git'e eklenmez.
* Her session için davranış başlangıç/bitiş saniyesi işaretlenir; tüm videoya tek
  etiket verilmez.
* Pozitiflerde sağ/sol kulak ve telefonun `visible`, `partially_occluded`,
  `not_visible` durumu ayrıca kaydedilir.
* Negatiflerde `face_scratch`, `hair_glasses_adjust`, `cheek_rest`, `smoke_eat_drink`,
  `passenger_phone` alt tipi tutulur.

## Kabul Komutu

```bash
.venv-yolo/bin/python scripts/benchmarks/evaluate_phone_call_behavior.py
```

Kabul icin `coverage_gate_passed=true`, `quality_gate_passed=true` ve
`baseline_accepted=true` birlikte gerekli.

Harness 20 Haziran 2026'da sertlestirildi. Kapsama artik satir degil **ayri
`session_id`** uzerinden sayilir; ayni kayittan komsu klipler kapsamayi sismez.

Coverage kapisi (varsayilan):

* `>=3` pozitif session,
* `>=5` negatif session,
* `>=2` hard-negative session (bos olmayan `negative_subtype`),
* `>=1` occluded-positive session (`phone_visibility=not_visible|partially_occluded`).

Quality kapisi (varsayilan):

* recall `>=0.80`,
* genel specificity `>=0.90`,
* **hard-negative specificity `>=0.90`** (sadece bos olmayan `negative_subtype`
  satirlari uzerinde). Kolay negatiflerle alinan yuksek specificity tek basina
  yetmez.

Bu nedenle `testing/templates/manual_phone_call_review.csv` su kolonlari icermeli:
`session_id`, `negative_subtype`, `phone_visibility`. Bunlar bos kalirsa harness
acik blocker doner ve baseline kabul edilmez.
