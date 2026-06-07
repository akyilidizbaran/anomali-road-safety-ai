# Edge/Backend Mimarisi

## Amaç

Mobil cihazdan gelen frame veya stream’i alıp AI çıkarımını çalıştırmak, event üretmek ve sonuçları mobil uygulamaya döndürmek.

## Katmanlar

1. Video input.
2. Preprocess.
3. Normal mode inference.
4. Risk pre-decision.
5. Critical expert selector.
6. Expert inference.
7. Event fusion.
8. Evidence storage.
9. Mobile response.

## Teknoloji

* Python.
* FastAPI.
* WebSocket.
* PyTorch/ONNX Runtime.
* JSON metadata.
* Local file evidence store.

## Sorulacak Noktalar

* İlk backend local ağda mı çalışacak?
* Deployment için cloud mı edge laptop mı?
