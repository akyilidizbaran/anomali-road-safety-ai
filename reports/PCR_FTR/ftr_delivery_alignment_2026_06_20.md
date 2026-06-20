# FTR Teslim Dokumani Uyum Matrisi - 2026-06-20

Kaynak PDF: `reports/_official_templates/teknofest_2026_ftr_teslim_dokumani.pdf`

Bu dosya FTR asamasinda otomatik degerlendirme icin zorunlu olan teslim sozlesmesini
repo kapsamiyla eslestirir. Bundan sonraki ana hedef, genis proje mimarisini korurken
degerlendirme paketinin burada belirtilen JSON semasina birebir uymasidir.

## 1. Ana Sonuc

FTR dokumani proje kapsamimizi daraltmaz; ancak otomatik degerlendirme hedefini netlestirir:

```text
/app/data/input/video.mp4
        -> model pipeline
        -> /app/data/output/results.json
```

`results.json` icinde iki zorunlu ana blok bulunmalidir:

1. `arac_bilgisi`: tek ana aracin tip, plaka, renk ve ortak confidence skoru.
2. `tespitler`: zaman bazli surucu eylemi, nesne ve yolcu tespitleri.

QoD, edge dashboard, evidence package, speed, lane ve LLM aciklama katmani proje degeri
olarak korunabilir; fakat FTR otomatik puanlama ciktisinin icinde dogrudan beklenen alanlar
degildir. Bu nedenle submission icin ayrica bir `ftr_output_adapter` katmani kurulmalidir.

## 2. Zorunlu Etiketler

### 2.1 `arac_bilgisi`

| Alan | Zorunlu degerler / format | Repo durumu | Aksiyon |
|---|---|---|---|
| `tip` | `sedan`, `suv`, `hatchback`, `pickup`, `minibus`, `panelvan`, `kamyon` | Kismi | VATTR/BoxCars siniflari FTR tiplerine map edilmeli; eksik siniflar icin ek dataset veya fallback policy gerekli. |
| `plaka` | Turkiye plaka regex uyumlu, ASCII, bosluksuz veya normalize | Kismi | Plate detector + CCT-XS OCR var; final regex normalization ve low-confidence fallback `tespit edilemedi` policy gerekiyor. |
| `renk` | `beyaz`, `siyah`, `gri`, `kirmizi`, `mavi`, `sari`, `yesil`, `turuncu`, `kahverengi` | Eksik | Arac rengi classifier veya ROI tabanli color heuristic/model eklenmeli. |
| `confidence_score` | 0.0-1.0 float | Kismi | Tip+plaka+renk ortak confidence aggregation kuralı tanimlanmali. |

### 2.2 `tespitler`

| Kategori | Zorunlu etiketler | Repo durumu | Aksiyon |
|---|---|---|---|
| `sofor_eylemi` | `arkaya_bakma`, `esneme`, `sigara_icme`, `su_icme`, `telefonla_konusma`, `slalom`, `etrafa_bakinma`, `emniyet_kemeri_ihlali` | Buyuk olcude eksik | Cabin/driver action pipeline ana oncelige alinmali. `slalom` tracking/lateral motion sinyaliyle uretilebilir. |
| `nesneler` | `teknocan`, `bilgisayar` | Eksik | Nesne detector/ classifier eklenmeli. `teknocan` ozel sinif oldugu icin veri stratejisi netlestirilmeli. |
| `yolcular` | `arka_koltuk_1`, `arka_koltuk_2`, `on_koltuk` | Eksik | Cabin passenger occupancy/localization modeli veya keypoint/seat ROI yaklasimi kurulmalı. |

Her `tespitler[]` elemani sunlari icermelidir:

```json
{
  "zaman_saniye": 14.5,
  "kategori": "sofor_eylemi",
  "etiket": "telefonla_konusma",
  "confidence_score": 0.89
}
```

## 3. Submission Ortami

| Kalem | FTR zorunlulugu | Repo durumu | Aksiyon |
|---|---|---|---|
| Dockerfile root seviyesinde | Zorunlu | Eksik | Root `Dockerfile` eklenmeli. |
| Base image | `nvidia/cuda:12.1.0-base-ubuntu22.04` | Eksik | Dockerfile bu imajdan baslamali. |
| Girdi yolu | `/app/data/input/video.mp4` | Eksik | `main.py` bu path'i okumali. |
| Cikti yolu | `/app/data/output/results.json` | Eksik | `main.py` bu path'e yazmali. |
| Model yolu | `/app/models/` veya dokumandaki ornek `/app/weights/` | Eksik | Tek standart secilmeli; FTR metnindeki tablo `/app/models/` dedigi icin ana yol `/app/models/` olmali. |
| GPU | NVIDIA Tesla T4 | Eksik | Runtime CUDA/T4 icin test edilmeli; MacBook MPS sadece lokal dev. |
| Kaynak limitleri | 4 vCPU, 16 GB RAM, 2 GB SHM, 8 GB image, 10 dk runtime | Eksik | Hafif modeller, frame sampling ve model lazy-load stratejisi uygulanmali. |
| Internet | Build sonrasi runtime'da kapali varsayilmali | Eksik | Tum agirliklar image icinde veya `/app/models/` icinde bulunmali. |

## 4. Mevcut Repo ile Uyum

### Uyumlu Olanlar

* Tek ana arac varsayimi zaten hedef arac secimi ve ByteTrack hattiyla uyumlu.
* Arac detection + tracking temel omurgasi mevcut.
* Plate detection + CCT-XS OCR baseline mevcut ve FTR `plaka` alanina aday.
* Vehicle attribute classifier denendi; FTR `tip` alanina uyarlanabilir fakat etiket map'i gerekli.
* Confidence skorlarini JSON'a tasima aliskanligi mevcut.
* Open-source dataset ve Colab fine-tune yaklasimi FTR veri seti serbestligiyle uyumlu.

### Uyumlu Olmayan / Eksik Olanlar

* Mevcut event/evidence JSON semasi FTR `results.json` semasi degil.
* `renk` tahmini icin aktif model veya heuristic yok.
* Cabin action, object ve passenger tespitleri aktif degil.
* Docker submission paketi yok.
* T4 runtime ve 10 dakika time budget olcumu yok.
* Tum kategori/etiket degerleri icin ASCII-safe normalize validator yok.
* Hata yonetimi ve bozuk/eksik video durumunda standard fallback `results.json` yok.

## 5. Hizin Konumu

FTR dokumani `hiz`, `speed_kmh` veya `estimated_kmh` alanini otomatik cikti semasinda istemiyor.
Bu nedenle mevcut speed pipeline ana FTR tesliminin dogrudan puanlanan parcasi degildir.

Speed modulu iki sekilde korunur:

1. `slalom` etiketi icin track/lateral motion sinyali destekleyici olabilir.
2. Proje raporunda risk/evidence zenginlestirme olarak anlatilabilir.

Mevcut `SPEED-EXP-005A` grafiklerinde raw ve moving-average hiz sinyalleri bbox geometry
ve kadraj cikisi nedeniyle gurultuludur. Bu, "model her seyi yanlis anliyor" demek degildir;
ancak bu yaklasimin tek basina final mutlak km/s olarak kullanilamayacagini gosterir.
FTR icin speed calismasi ikincil tutulmali, asıl oncelik `arac_bilgisi` ve `tespitler`
JSON dogruluguna verilmelidir.

## 6. Yeni Oncelik Sirasi

1. FTR `results.json` schema/validator/adapter.
2. Root Dockerfile + `main.py` + `/app/data/input/video.mp4` -> `/app/data/output/results.json` smoke run.
3. `arac_bilgisi` pipeline:
   * vehicle type mapping,
   * plate OCR normalization,
   * color classifier/heuristic,
   * aggregate confidence.
4. `tespitler` pipeline:
   * driver action labels,
   * `slalom` tracking rule,
   * `teknocan`/`bilgisayar` object detection,
   * passenger seat occupancy.
5. T4/10 dakika runtime budget ve image size kontrolu.
6. FTR rapor metinleri ve final teslim checklist.

## 7. Degerlendirme Icin Kirmizi Cizgiler

* JSON key'leri birebir korunmali: `video_id`, `arac_bilgisi`, `tespitler`, `zaman_saniye`,
  `kategori`, `etiket`, `confidence_score`.
* Etiketler Turkce karakter icermemeli ve kucuk harf olmali.
* Evaluation ortaminda olup olmadigini anlamaya calisan hileli path/hostname/IP/file-existence
  branch'leri yazilmamali.
* Kod input video yoksa veya bozuksa kontrollu hata yonetimi yapmali; mumkunse schema-valid
  dusuk guvenli fallback JSON uretmeli.
* Runtime internet baglantisina guvenmemeli.
