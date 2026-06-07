# 3.2 Yapay Zeka Modeli ve Çıkarım Tasarımı

## Resmi Beklenti

Canlı video akışı üzerinden çıkarım yapacak yapay zeka mimarisi açıklanmalıdır. Seçilen modelin probleme uygunluğu, fine-tuning yaklaşımı, doğruluk-gecikme dengesi ve quantization gibi optimizasyonlar anlatılmalıdır.

## Ana Yaklaşım

Tek büyük model yerine **modüler ve seçici uzman model mimarisi** kullanılmalıdır. Normal modda hafif analiz sürekli çalışır. Kritik modda yalnız gerekli uzman modeller çağrılır.

## AI Bileşen Tablosu

| Görev | Aday Yöntem | Çalışma Modu | Rapor Gerekçesi |
|---|---|---|---|
| Araç tespiti | YOLO nano/small | Normal | Gerçek zamanlılık ve doğruluk dengesi |
| Araç takibi | ByteTrack / BoT-SORT | Normal | Track ID ve olay sürekliliği |
| Hedef araç seçimi | Rule-based score | Normal | Kaynakları tek araca odaklama |
| Plaka tespiti | YOLO plate detector | Kritik | Araç ROI içinde küçük nesne tespiti |
| OCR | PaddleOCR / CRNN | Kritik | Plaka metni ve karakter güveni |
| Hız | Homography + tracking | Kritik/koşullu | Kalibrasyon varsa km/s, yoksa göreli risk |
| Şerit | YOLOP / lane-specific | Normal/Kritik | Şerit yakınlığı ve ihlal sinyali |
| Sahne/hava | ResNet18 / MobileNetV3 | Düşük frekans | Görüş koşulu ve QoD adaylığı |
| Cabin risk | ROI detector/classifier | Kritik/koşullu | Görünürlük yeterliyse araç içi risk |

## Çıkarım İş Hattı

1. Frame preprocessing.
2. Araç tespiti.
3. Araç takibi ve track ID.
4. Hedef araç skoru.
5. Sahne/görüş kalitesi.
6. Risk ön skoru.
7. Kritik mod kararı.
8. Uzman model çağrıları.
9. Event fusion.
10. Evidence package.

## Optimizasyon Yaklaşımı

* ROI tabanlı çıkarım.
* Frame skipping.
* Asenkron inference queue.
* ONNX export.
* FP16/INT8 quantization.
* Model boyutu ve latency benchmark.

## Sorulacak Noktalar

* Başlangıç YOLO sürümü ne olacak?
* OCR için PaddleOCR mı özel CRNN mi?
* Cabin risk MVP’ye dahil mi final genişletme mi?
