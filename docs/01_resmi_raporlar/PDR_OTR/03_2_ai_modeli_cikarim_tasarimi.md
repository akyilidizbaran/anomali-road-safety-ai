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
| Yol/araç dışı kullanıcı | Public detector + rule-based proximity | Normal/Kritik | Yaya/bisikletli/motosikletli ve riskli araca yakınlık bağlamı |
| Cabin risk | ROI detector/classifier | Kritik/koşullu | Görünürlük yeterliyse araç içi risk |

## Çıkarım İş Hattı

1. Frame preprocessing.
2. Ortam/sahne, hava, ışık ve görüş bağlamı.
3. Araç tespiti.
4. Araç takibi ve track ID.
5. Hedef araç skoru.
6. Genel yol durumu ve araç dışı kullanıcı/yaya sinyali.
7. Risk ön skoru.
8. Riskli araç için QoD aday/request kararı.
9. Kritik mod kararı.
10. Uzman model çağrıları.
11. Event fusion.
12. Evidence package.

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
