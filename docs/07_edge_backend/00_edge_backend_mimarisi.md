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

## Çalışma Ortamı Kararı

İlk demo ve model çıkarım ortamı **MacBook tabanlı local edge runtime** olacaktır. Android telefon kamera ve UI istemcisi olarak canlı frame veya stream gönderir; ağır model çıkarımı MacBook üzerinde çalışan backend/inference server tarafında yapılır.

Bu ayrım şu nedenle önemlidir:

* Eğitim/fine-tune işi Google Colab GPU üzerinde yürütülür.
* Demo sırasında model ağırlıkları ve inference runtime MacBook üzerinde çalışır.
* Android cihazın ilk aşamada ağır inference yükü taşıması beklenmez.
* Gerçek 5G/QoD entegrasyonu geldiğinde backend adapter katmanı değişebilir; model pipeline sözleşmesi aynı kalır.

## Frame Boyutu

Canlı input hedefi 720p frame seviyesidir. Backend preprocessing katmanı bu frame'i seçilen modelin input boyutuna resize eder. Model karşılaştırmalarında benchmark çözünürlüğü ve resize politikası ayrıca kaydedilmelidir.

## Sorulacak Noktalar

* MacBook ile telefon aynı local ağda mı, doğrudan kablolu/tethered bağlantıda mı çalışacak?
