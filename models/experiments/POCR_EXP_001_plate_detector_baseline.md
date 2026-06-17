# POCR-EXP-001 - Existing Plate Detector Baseline

Tarih: 2026-06-15

## Durum

Repo içinde aktif olarak kullanılabilir bir lokal plate detector checkpoint'i vardır:

```text
models/checkpoints/plate/license_plate_detector.pt
```

Dosya boyutu yaklaşık `5.2 MB` ve PyTorch zip checkpoint formatındadır. Bu dosya Git tarafından takip edilmemelidir; model ağırlıkları lokal/Drive artifact olarak tutulur.

## Model Kaynağı

Bu checkpoint, `research/04_plate_ocr/RUN_POCR_EXP_001.md` talimatındaki akışa göre `morsetechlab/yolov11-license-plate-detection` ailesinden indirilebilir Ultralytics YOLO plate detector olarak kullanılmak üzere konumlandırılmıştır.

Kesin model variant ve lisans bilgisi, checkpoint yeniden indirildiğinde model card ile birlikte kaydedilmelidir. Mevcut checkpoint için repo içindeki kanıt, POCR-EXP-001 smoke test raporları ve JSON artifactleridir.

## Mevcut Baseline Sonucu

Kaynak:

```text
models/benchmarks/artifacts/POCR-EXP-001-plate-detection-yolo-summary.json
testing/reports/pocr_exp_001_plate_detection_summary_yolo.md
```

Test kapsamı:

* `Test/video_1.mp4`
* `Test/video_2.mp4`
* `Test/video_3.mp4`
* Target scope: ByteTrack ile seçilmiş hedef araç ROI
* OCR: yok
* Plate confidence: `0.25`

Özet metrikler:

| Video | Target frame | Plate frame | Detection rate | Max confidence | Mean latency |
|---|---:|---:|---:|---:|---:|
| `video_1.mp4` | 342 | 209 | 0.6111 | 0.7791 | 26.291 ms |
| `video_2.mp4` | 340 | 192 | 0.5647 | 0.7950 | 21.324 ms |
| `video_3.mp4` | 284 | 212 | 0.7465 | 0.7787 | 24.904 ms |

Toplam:

* Target frame: `966`
* Plate detected frame: `613`
* Plate detection rate: `0.6346`
* Total plate boxes: `616`
* Ortalama confidence: `0.740`
* Ortalama latency: `24.173 ms`
* Ortalama p95 latency: `39.022 ms`

## Baseline Olarak Kullanım Kararı

Bu model **mevcut pretrained/local plate detection baseline** olarak korunacaktır.

Ancak bu model final model değildir:

* Kendi verimizle fine-tune edilmedi.
* Türkiye plaka domain'i için kapsamlı benchmark yapılmadı.
* Manual plate bbox correctness sayımı henüz tamamlanmadı.
* Model card/lisans bilgisi final rapor öncesi yeniden doğrulanmalıdır.

## Geliştirme Yönü

Yeni kapsamlı çalışma bu baseline'a karşı ölçülecektir:

```text
POCR-EXP-005-YOLO11N-PLATE-DETECTOR
```

Plan:

1. Turkish Number Plates Roboflow dataset'i birincil training verisi olarak kullan.
2. Roboflow License Plate Recognition 10,125 dataset'ini hacim desteği olarak ekle.
3. Duplicate / near-duplicate temizliği ve source-grouped split üret.
4. YOLO11n single-class `license_plate` detector fine-tune et.
5. UFPR-ALPR üzerinde dış benchmark/generalization değerlendirmesi yap.
6. POCR-EXP-001 mevcut checkpoint'e karşı mAP, recall, usable crop rate ve latency farklarını raporla.

## OCR'a Geçiş Kriteri

OCR'a geçmeden önce plate detector tarafında şu minimumlar sağlanmalıdır:

* Target track başına en az bir usable plate crop.
* Manual review ile doğru plate bbox çoğunluğu.
* False positive plate bbox oranının kabul edilebilir seviyeye inmesi.
* `plate_not_visible`, `plate_low_confidence`, `plate_bbox_uncertain` failure reason alanlarının doğru yazılması.
