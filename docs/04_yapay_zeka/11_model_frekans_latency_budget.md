# Model Frekans ve Latency Budget

## Amaç

Bu doküman runtime AI pipeline için gerçekçi çalışma frekansı ve latency beklentilerini tanımlar.

En önemli kural:

> 30 FPS, tüm ağır uzman modellerin 30 FPS çalışacağı anlamına gelmez.

30 FPS yalnız kamera preview veya frame input hedefi olarak kullanılabilir. Gerçek zamanlı davranış, hafif normal mod ve seçici uzman model aktivasyonu ile korunur.

## Frekans Planı

| Modül | Hedef Frekans | Çalışma Şekli | MVP Durumu |
|---|---:|---|---|
| Camera preview | 30 FPS hedef | Mobil UI preview | MVP |
| Frame input contract | 15-30 FPS hedef | Stream/frame metadata | MVP |
| Frame preprocessing | 15-30 FPS hedef | Her işlenen frame | MVP |
| Frame quality analysis | 5-15 FPS veya sampled | Hafif kalite sinyali | Final |
| Vehicle detection | 15-30 FPS, modele bağlı | Normal mod kök model | MVP |
| Vehicle tracking | Her frame veya yüksek frekans | Detection + tracker | MVP |
| Target vehicle selection | 5-15 FPS veya track update | Hafif scoring | MVP |
| Scene/weather/visibility | 1-2 Hz | Düşük frekans bağlam | Final |
| External road user | 5-15 FPS veya sampled | Hafif context / critical window | Final |
| Plate detection/OCR | Event-based veya 5-10 frame | Target ROI | MVP |
| Lane/road marking | 10-15 FPS veya event-based | Target/lane ROI | Final |
| Speed estimation | Sliding window based | Track history gerekir | Final |
| Cabin risk | Event-based + visibility gated | Target ROI | Future/extended |
| QoD decision | Event-based | Risk/evidence quality gate | Final |
| Evidence generation | Event-based | Risk threshold veya meaningful event | MVP |
| LLM explanation | Event-based / async | Structured output explanation | Final |

## Latency Budget Mantığı

Sabit bir latency değeri final benchmark olmadan iddia edilmemelidir. Bu aşamada budget, hedef davranışı tanımlar.

Önerilen budget sınıfları:

| Katman | Hedef | Not |
|---|---:|---|
| Mobile capture + encode | düşük | Cihaz ve çözünürlüğe bağlı |
| Network/uplink | düşük/orta | 5G, Wi-Fi veya local ağ durumuna bağlı |
| Preprocess | düşük | Basit görüntü dönüşümleri |
| Detection | ana latency yükü | İlk model seçimi burada kritik |
| Tracking | düşük | Detection output üzerine çalışır |
| Scene/weather | düşük frekanslı | Her frame çalışmaz |
| Expert models | olay bazlı | Normal mod latency’sini sürekli etkilememeli |
| Evidence package | event-based | UI overlay’den ayrı tutulabilir |
| LLM explanation | async olabilir | Karar verici olmadığı için geç gelebilir |

## Runtime Profil Önerileri

### Profile A - MVP Local Edge

* Mobile camera frame input.
* Local computer edge/backend.
* Vehicle detection + tracking.
* Target vehicle selection.
* Plate detection/OCR event window.
* Event JSON + evidence metadata.

### Profile B - Final Demo

* MVP profile.
* Scene/weather/visibility context.
* Lane/road marking expert.
* Speed fallback mode.
* QoD candidate/request status.
* Expanded evidence view.

### Profile C - Research/Future

* Multi-target mode.
* Robust cabin risk.
* Learned risk model.
* Real QoD optimization experiments.

## Real-Time Behavior Nasıl Korunur?

* Heavy expert modeller normal modda sürekli çalışmaz.
* Detection/tracking hattı ayrı tutulur.
* Scene/weather düşük frekanslı çalışır.
* OCR, lane, speed ve cabin yalnız target ROI veya event window içinde çalışır.
* Evidence generation event-based çalışır.
* LLM explanation async veya fallback template olabilir.

## Rapor Dili

Doğru ifade:

> Kamera preview 30 FPS hedefleyebilir; yapay zeka hattı gerçek zamanlı davranışı normal modda hafif detection/tracking, kritik modda ise seçici uzman model çağrılarıyla korur.

Kaçınılacak ifade:

> Tüm yapay zeka modelleri 30 FPS çalışır.

## Ölçülmesi Gereken Metrikler

* Detection FPS.
* Pipeline FPS.
* Median latency.
* P95 latency.
* Frame drop rate.
* Expert model latency.
* Event generation latency.
* Evidence save latency.
* QoD requested-to-active time, gerçek API sağlanırsa.

## Açık Noktalar

* İlk detection modeli seçilmeden gerçek latency değeri yazılmamalı.
* Edge cihaz donanımı netleşmeden final FPS hedefi kesinleştirilmemeli.
* 5G/QoD gerçek API davranışı ölçülmeden QoD latency iddiası kurulmameli.
