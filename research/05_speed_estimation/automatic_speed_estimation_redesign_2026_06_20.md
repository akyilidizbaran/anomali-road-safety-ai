# Automatic Monocular Speed Estimation Redesign — 2026-06-20

## Yönetici Özeti

Bu doküman, Anomali Road Safety AI projesindeki hız modülünü manuel yol ölçümü gerektiren
homografi odağından çıkarıp **otomatik/yaklaşık km/s adayları** üreten bir yaklaşıma yeniden
tasarlar.

Yeni hedef:

* Kullanıcıdan yol üzerinde ölçülmüş referans noktası beklememek.
* Tek kamera, sabit veya yarı sabit yol kenarı görüntüsünden otomatik hız adayları üretmek.
* Her adayı `confidence`, `failure_reason`, `warning_flags` ve `speed_mode` ile event/evidence
  JSON'a taşımak.
* Hiçbir çıktıyı hukuki/cezai hız ölçümü olarak sunmamak.

Bu tasarımda `SPEED-EXP-004C` manuel homografi ana yol olmaktan çıkarılır. Bunun yerine otomatik
aday üretim sırası aşağıdaki gibi olacaktır:

1. `SPEED-EXP-005A`: Naver/Revaud tarzı bbox-track + araç boyutu prior otomatik sahne geometri adayı.
2. `SPEED-EXP-005B`: FARSEC-lite depth + track + average vehicle length otomatik hız adayı.
3. `SPEED-EXP-005C`: Mevcut plate-scale v2 adayı; fallback/sanity-check olarak korunur.
4. `SPEED-EXP-005D`: Speed candidate fusion ve if-not-then-do routing.

2026-06-20 kapanış notu: `SPEED-EXP-005D` uygulanarak mevcut hız fazı FTR ana yolunu
bloklamayacak şekilde kapatıldı. FARSEC-lite/depth çalışması artık zorunlu sonraki adım değil,
FTR `arac_bilgisi` ve `tespitler` modüllerinden sonra opsiyonel future/support adımıdır.

`SPEED-EXP-004A` relative speed ve `SPEED-EXP-004B` plate/VATTR sanity-check korunur. `SPEED-EXP-004C`
semi-manual homography yalnız opsiyonel saha doğrulama/fallback olarak kalır.

## Neden Plan Değişti?

Önceki `004C` yaklaşımı en az dört yol düzlemi noktasının metre cinsinden ölçülmesini bekliyordu.
Bu akademik olarak temizdir ancak proje hedefiyle uyumsuzdur:

* Demo veya gerçek saha ortamında ölçülü referans nokta her zaman sağlanamaz.
* Kullanıcı deneyimi açısından otomatik çalışan bir karar destek hattı gerekir.
* Projenin AI tarafındaki değeri, manuel ölçüm istemeden yaklaşık ve açıklanabilir hız adayları
  üretebilmesidir.

Bu yüzden yeni hız modülü, kesin homografi yerine **çok adaylı otomatik hız kestirimi** olarak
tasarlanacaktır.

## Değişmeyen Kırmızı Çizgiler

* Sistem ceza/hukuki hız ölçüm sistemi değildir.
* `estimated_kmh` ancak güvenilir candidate olarak yazılır; final/doğru hız iddiası kurulmaz.
* Her aday için kaynak, güven, fallback ve uyarılar saklanır.
* Ground-truth hız yoksa sonuçlar qualitative/manual review ve consistency check olarak raporlanır.
* Düşük ışık, uzak plaka, track jitter, ID switch ve model belirsizliği hız güvenini düşürür.

## Kaynak Araştırma Özeti

### 1. Naver/Revaud ICCV 2021

Kaynaklar:

* Paper: https://openaccess.thecvf.com/content/ICCV2021/html/Revaud_Robust_Automatic_Monocular_Vehicle_Speed_Estimation_for_Traffic_Surveillance_ICCV_2021_paper.html
* Code: https://github.com/naver/cctv

Özet:

Revaud ve Humenberger, trafik gözetleme videolarında kalibrasyonun ana zorluk olduğunu belirtir
ve yalnız off-the-shelf object detector çıktılarından yararlanan iki otomatik kalibrasyon yöntemi
önerir. Yöntem, birden fazla tracked bbox'ı birlikte kullanır ve araçların benzer/bilinen 3D
boyutlara sahip olduğu varsayımından yararlanır.

Projeye uygunluk:

* Bizde zaten `YOLO11n`, `ByteTrack`, bbox history ve `VATTR` vehicle dimension prior var.
* Bu yaklaşım bizim mevcut speed fusion omurgasına en doğal şekilde bağlanır.
* Lisans `CC BY-NC-SA 3.0`; ticari amaç olmayacağı ve atıf verileceği için araştırma/prototip
  kapsamında kullanılabilir.

Risk:

* Repo doğrudan bizim veriye tak-çalıştır olmayabilir.
* BrnoCompSpeed odaklı örnekler ve bağımlılıklar adaptasyon gerektirebilir.
* Düşük ışık ve göğüs yüksekliği kamera açısında sonuçlar ayrıca test edilmelidir.

### 2. FARSEC / Depth-Based Automatic Speed Estimation

Kaynaklar:

* Paper: https://arxiv.org/html/2309.14468
* Abs: https://arxiv.org/abs/2309.14468

Özet:

FARSEC, traffic camera videolarında otomatik real-time hız kestirimi için depth mapping, tracked
vehicle center points ve average vehicle length varsayımı kullanır. Makale; kamera hareketi, farklı
video formatları, FPS yönetimi ve sliding-window hız üretimini kapsayan daha end-to-end bir sistem
tasarlar.

Projeye uygunluk:

* Bizim sistemde tracking ve FPS zaten var.
* DepthAnything/MiDaS gibi pretrained monocular depth modelleriyle `FARSEC-lite` uygulanabilir.
* Average car length veya VATTR body prior ile ölçek tahmini yapılabilir.

Risk:

* Monocular depth metrik ölçek vermez; ölçeği araç boyutu/track istatistiği ile yaklaşıklamak gerekir.
* Düşük ışık depth modelini bozabilir.
* GitHub kaynağı her ortamda doğrudan erişilebilir/aktif olmayabilir; fikir kendimiz modüler
  uygulanmalıdır.

### 3. Plate-Scale Candidate

Kaynak / mevcut repo çıktıları:

* `research/05_speed_estimation/plate_scale_monocular_speed_baseline_2026_06_17.md`
* `testing/reports/speed_exp_001_plate_scale_baseline.md`
* `testing/reports/speed_exp_002_plate_bbox_xyz_baseline.md`

Özet:

Türkiye uzun plaka boyutu (`0.52m x 0.11m`) bilinen fiziksel referans olarak kullanılır. Plaka bbox
genişliği/yüksekliği ve full-frame center hareketi üzerinden yaklaşık derinlik ve hız adayı üretilir.

Projeye uygunluk:

* Plaka detector ve OCR hattımız hazır.
* Plaka görünür front/rear araçlarda hızlı ve açıklanabilir bir adaydır.
* Mevcut sonuçlar fallback/sanity-check olarak kalmalıdır.

Risk:

* Bbox tek başına plaka köşesi/pose bilgisi sağlamaz.
* Mevcut plate aspect ratio standart orandan saptığı için adaylar düşük güvenlidir.
* Yan profil, uzak/karanlık plaka ve motion blur durumunda düşer.

## Yeni Deney Sırası

### SPEED-EXP-005A — Naver/Revaud BBox Geometry Candidate

Amaç:

Tracked vehicle bbox history ve araç dimension prior kullanarak manuel nokta istemeden sahne
geometrisi/ölçek adayı üretmek.

Girdiler:

* `TRK-EXP-001` ByteTrack track history
* `VD-EXP-002` vehicle detector output
* `VATTR-EXP-001` body/dimension prior
* FPS
* bbox bottom-center / width / height / area history

Teknik yaklaşım:

1. Naver/cctv repo ve paper algoritmasını incele.
2. Minimum adaptasyonla bizim event skeleton formatımıza wrapper yaz.
3. Eğer doğrudan çalışmazsa paper fikrini basitleştir:
   * çoklu bbox trajectory,
   * normalleştirilmiş araç boyutu prior,
   * bbox scale ve bottom-center motion,
   * camera geometry/scale parametre optimizasyonu.
4. Çıktıyı `speed_candidate.source = "bbox_geometry_auto"` olarak yaz.

Başarı kriteri:

* 3 demo video için crash etmeden aday üretmesi.
* `video_3`ün `video_1/video_2`ye göre daha hızlı olduğuna dair tutarlı sinyal üretmesi.
* Candidate confidence ve failure flags üretmesi.

Beklenen çıktı:

```json
{
  "source": "bbox_geometry_auto",
  "speed_kmh": 18.4,
  "speed_range_kmh": [12.2, 26.7],
  "confidence": 0.42,
  "quality_flags": ["track_long", "bbox_history_available"],
  "warning_flags": ["auto_scale_approximation", "not_for_legal_enforcement"]
}
```

### SPEED-EXP-005B — FARSEC-Lite Depth Candidate

Amaç:

Pretrained monocular depth modeli ile frame/track boyunca göreli derinlik değişimini çıkarıp araç
boyutu prior ile yaklaşık metrik ölçeğe bağlamak.

Girdiler:

* Target track frame listesi
* Vehicle bbox / bottom-center points
* Depth model output
* VATTR veya default vehicle length prior
* FPS

Önerilen modeller:

* İlk pratik aday: MiDaS small veya DepthAnything small/base.
* MacBook local yavaş kalırsa Colab inference notebook seçeneği açılabilir.

Teknik yaklaşım:

1. Track boyunca sample frame seç.
2. Depth map çıkar.
3. Vehicle ROI içinde robust depth statistic hesapla:
   * median depth,
   * bottom-center çevresi depth,
   * bbox içi percentile.
4. Depth değişimini bbox scale ve araç uzunluk prior ile normalize et.
5. Sliding-window hız adayı üret.

Başarı kriteri:

* Plaka görünmezse bile aday üretebilmesi.
* `relative_speed_label` ile çelişkiyi raporlayabilmesi.
* Düşük güvenli durumda `speed_mode=relative` fallback'e düşebilmesi.

### SPEED-EXP-005C — Plate-Scale V2 Candidate

Amaç:

Mevcut plate-scale denemesini daha iyi kalite kontrolleriyle fallback/sanity-check olarak korumak.

Geliştirme:

* Plate bbox temporal smoothing.
* Aspect ratio quality score.
* Plate bbox jitter score.
* Full-frame plate center trajectory.
* OCR/plate visibility confidence gate.
* Türkiye plaka oranı ve bbox boşluk toleransı.

Karar:

Bu yöntem tek başına ana hız kaynağı olmayacak. Ancak plaka netse fusion içinde güçlü destekleyici
aday olabilir.

### SPEED-EXP-005D — If-Not-Then-Do Speed Fusion

Amaç:

Hız adaylarını tek bir karar ağacıyla birleştirmek. Weighted average yerine açıklanabilir fallback
mantığı kullanılacak.

Routing:

```text
IF bbox_geometry_auto usable:
    use as primary absolute_candidate
ELIF farsec_lite_depth usable:
    use as primary approximate_candidate
ELIF plate_scale_v2 usable:
    use as low-confidence approximate_candidate
ELIF relative_track usable:
    use relative speed only
ELSE:
    speed_mode = unavailable
```

Candidate agreement:

* Naver/Revaud ve FARSEC-lite aynı yönde ise confidence artar.
* Plate-scale, ana adayla uyumluysa evidence support olur.
* Plate-scale veya depth ana adayla aşırı çelişirse `candidate_disagreement_high` yazılır.
* VATTR düşük güvenliyse dimension prior fusion'a katılmaz.

## Event/Evidence JSON Alanları

Yeni speed block:

```json
{
  "speed": {
    "mode": "absolute_candidate",
    "estimated_kmh": 24.6,
    "speed_range_kmh": [17.8, 32.9],
    "primary_speed_source": "bbox_geometry_auto",
    "candidate_speeds": [
      {
        "source": "bbox_geometry_auto",
        "speed_kmh": 24.6,
        "confidence": 0.51
      },
      {
        "source": "farsec_lite_depth",
        "speed_kmh": 21.2,
        "confidence": 0.38
      },
      {
        "source": "plate_scale_v2",
        "speed_kmh": 12.8,
        "confidence": 0.22
      }
    ],
    "fusion_confidence": 0.49,
    "fallback_reason": null,
    "warning_flags": [
      "approximate_monocular_speed",
      "not_for_legal_enforcement"
    ]
  }
}
```

`estimated_kmh` yalnız `mode` şu değerlerden biriyse dolabilir:

* `absolute_candidate`
* `approximate_candidate`

`relative` modda `estimated_kmh = null` kalır.

## Uygulama Planı

### Adım 1 — Doküman ve Contract Güncellemesi

* Bu planı repo içinde kaynak plan olarak kaydet.
* `speed_fusion_layer_implementation_plan.md` içine bu redesign'a referans ver.
* `PROJECT_MEMORY.md` decision log'a otomatik hız adayı kararını işle.

### Adım 2 — SPEED-EXP-005A Araştırma/Adaptasyon

* `naver/cctv` repo lisans ve bağımlılıklarını incele.
* Kodu lokal ayrı vendor/cache olarak indirme ya da paper fikrinden minimal kendi implementasyonumuzu yazma kararı ver.
* Bizim `speed004b` event JSON'undan track/bbox input adapter yaz.

### Adım 3 — SPEED-EXP-005A Smoke Run

* 3 demo video üzerinde bbox geometry candidate üret.
* Summary JSON/CSV/MD rapor üret.
* Adaylar sadece `candidate` olarak işaretlensin.

### Adım 4 — SPEED-EXP-005B FARSEC-Lite

* Pretrained depth model seç.
* 3 video target track sample frame'lerinde depth çıkar.
* Depth + bbox + vehicle length prior ile hız adayı üret.

### Adım 5 — SPEED-EXP-005C Plate-Scale V2

* Mevcut plate-scale hesaplarını smoothing ve quality gate ile yeniden üret.
* V2 çıktılarını 005A/005B ile aynı contract'a taşı.

### Adım 6 — SPEED-EXP-005D Fusion

* If-not-then-do routing script'i yaz.
* Event/evidence JSON'u yeni `candidate_speeds` alanıyla zenginleştir.
* Manuel review için overlay ve CSV üret.

## Başarı Kriterleri

Minimum başarı:

* 3 demo videoda en az bir otomatik approximate km/s candidate üretmek.
* `video_3` için `video_1/video_2`ye göre daha yüksek speed candidate veya riskli motion etiketi üretmek.
* Aday confidence düşükse bunu açıkça işaretlemek.
* Sistem hata durumunda `relative` veya `unavailable` fallback'e düşmek.

Güçlü başarı:

* 005A ve 005B adayları aynı yönde sonuç verirse fusion confidence artmalı.
* Plate-scale V2 yalnız plaka net olduğunda destekleyici sinyal olmalı.
* Her çıktı FTR raporuna aktarılabilecek açıklanabilir event/evidence alanları üretmeli.

## Riskler

* Mutlak hız ground-truth olmadan doğrulanamaz; yalnız aday üretildiği söylenebilir.
* Monocular depth gerçek metrik derinlik vermez; ölçek tahmini gerekir.
* Araç dimension prior yanlışsa hız adayı sapar.
* Düşük ışık ve motion blur tüm otomatik yöntemleri etkiler.
* Naver/Revaud kodu lisans ve adaptasyon nedeniyle doğrudan repo içine kopyalanmamalı; gerekiyorsa
  kullanım/atıf net yazılmalıdır.

## Nihai Karar

Aktif hız yol haritası artık şu şekilde ilerler:

1. `SPEED-EXP-005A` Naver/Revaud tarzı bbox geometry auto candidate.
2. `SPEED-EXP-005B` FARSEC-lite depth candidate.
3. `SPEED-EXP-005C` plate-scale v2 fallback/sanity-check.
4. `SPEED-EXP-005D` if-not-then-do speed fusion.

Eğer 005A ve 005B beklenen şekilde işimize yaramazsa sonraki adaylar açılır:

* wheelbase/cross-ratio wheel-center yöntemi,
* vanishing point / lane-marking auto calibration,
* keypoint/3D bbox based vehicle pose yöntemi,
* kontrollü sürücü/video ground-truth kalibrasyon deneyi.
