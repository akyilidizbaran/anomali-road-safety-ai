# Context-Gated Model Routing

## Amaç

Bu doküman, ortam/sahne değişkenlerinin model çağırma, güven skoru yorumlama, QoD adaylığı ve uzman model seçimini nasıl etkileyeceğini açıklar.

Temel fikir:

```text
Ortam bağlamı -> hafif normal takip -> riskli hedef araç -> QoD kararı -> uzman model çağırma -> evidence package
```

Bu yaklaşım tek büyük model yerine bağlama duyarlı, seçici ve açıklanabilir bir model orkestrasyonu sağlar.

## Temel Tasarım Kararı

Ortam analizi **pipeline gate** gibi çalışır; ancak detection/tracking hattını bloklayan ağır bir ön koşul olmamalıdır.

Doğru çalışma biçimi:

1. İlk frame penceresinde hava, ışık, görüş ve yol bağlamı çıkarılır.
2. Araç detection ve tracking hattı normal modda başlar.
3. Ortam analizi düşük frekansta güncellenir.
4. Tracking ve araç detection daha yüksek frekansta devam eder.
5. Riskli araç sinyali oluşursa hedef araç üzerinde QoD aday/request akışı ve uzman model seçimi yapılır.

## Normal Mod Davranışı

Normal modda sistem tüm araçları hafif şekilde izlemelidir.

Normal mod çıktıları:

* Tüm araçlar için bbox.
* Araç sınıfı.
* Confidence.
* Track ID.
* Track stability.
* Temel risk ön sinyali.
* Ortam/sahne bağlamı.
* Genel yol ve araç dışı kullanıcı/yaya durumu.

Normal modda tüm araçlar için ağır analiz yapılmaz. Plaka OCR, hız, lane, cabin risk gibi uzman modeller yalnız riskli/hedef araçta veya risk penceresinde çağrılır.

## Kritik Mod Davranışı

Kritik mod, riskli araç veya riskli yol olayı sinyali oluştuğunda devreye girer.

Kritik modda:

* Hedef araç ROI önceliklendirilir.
* QoD candidate/request akışı tetiklenir.
* QoD aktifliği ayrıca politika kararına bağlıdır.
* İlgili uzman modeller çağrılır.
* Event JSON ve evidence package üretilir.

## QoD Kararı

Riskli araç tespit edilmesi QoD sürecini başlatabilir; ancak QoD’nin aktif olacağı anlamına gelmez.

QoD aktiflik sorusu:

> QoD bu olayda karar güvenini veya kanıt kalitesini anlamlı şekilde artırır mı?

Evetse kısa süreli kalite artırımı yapılır. Hayırsa uzman modeller mevcut görüntü kalitesiyle çalışır ve QoD status `NOT_NEEDED` veya `CANDIDATE` seviyesinde kalabilir.

## Routing Politika Tablosu

| Bağlam / Sinyal | Etkilediği Karar | Çağrılabilecek Uzman | QoD Etkisi | Evidence Notu |
|---|---|---|---|---|
| Düşük ışık | OCR ve detection güveni daha temkinli yorumlanır | Plate OCR, scene model | QoD adaylığı artar | Karar gerekçesine düşük ışık eklenir |
| Sis / düşük görüş | Model belirsizliği artar | Scene/visibility model | QoD adaylığı artar | Görüş kalitesi confidence ile kaydedilir |
| Yağmur / ıslak yol | Yol koşulu risk bağlamı güçlenir | Road context, lane | Koşullu | Yol yüzeyi event JSON’a eklenir |
| Şerit görünürlüğü düşük | Lane sonucu düşük güvenle raporlanır | Lane/road marking | Koşullu | Lane güveni ayrıca belirtilir |
| Plaka bulanık | OCR güveni düşük olabilir | Plate detector, OCR | QoD güçlü aday | Plate crop ve OCR confidence saklanır |
| Ani yanal hareket | Track penceresi kritikleşir | Tracking window, lane | Koşullu | Track continuity ve hareket gerekçesi saklanır |
| Hız şüphesi | Hız kestirimi çağrılır | Speed estimation | Koşullu | Kalibrasyon durumu ayrıca yazılır |
| Yaya/bisikletli/motosikletli yakınlığı | Risk skoru artar | External user risk analysis | Koşullu | Relative position ve risk relation saklanır |
| Cabin görünürlüğü yeterli | Cabin risk analizi aday olur | Cabin risk model | Genelde QoD değil, ROI kalitesiyle ilişkili | Görünürlük yeterliliği kaydedilir |

## Frekans ve Kaynak Kullanımı

| Modül | Normal Mod | Kritik Mod | Not |
|---|---|---|---|
| Camera preview | 30 FPS hedef | 30 FPS hedef | UI akıcılığıdır, tüm modellerin 30 FPS çalıştığı anlamına gelmez |
| Vehicle detection | 15-30 FPS hedef | Hedef araç ROI ile desteklenebilir | İlk model geliştirme odağıdır |
| Tracking | Yüksek frekans | Yüksek frekans | Riskli olay sürekliliği için önemlidir |
| Scene/weather/visibility | 1-2 Hz | Risk penceresinde tekrar kontrol edilebilir | Bağlam sinyalidir |
| Road/external user | Düşük/orta frekans | Hedef araç yakınlığı için önceliklenir | Yaya/bisikletli/motosikletli bağlamı |
| Plate OCR | Çalışmaz veya düşük frekanslı aday | Hedef araç ROI | Plaka görünürlüğü ve risk durumuna bağlı |
| Lane/road marking | Düşük/orta frekans | Hedef araç penceresinde | Şerit ihlali ve yanal hareket için |
| Speed estimation | Genelde çalışmaz | Kalibrasyon ve track yeterliyse | Mutlak km/s olmazsa göreli hız |
| Cabin risk | Çalışmaz | Görünürlük yeterliyse | Final genişletme |
| Evidence | Olay yoksa üretilmez | Olay bazlı | Event JSON + metadata |

## Rule-Based Başlangıç Politikası

Başlangıçta routing kararı rule-based olabilir. Bu proje için uygundur çünkü:

* Açıklanabilir.
* Rapor ve jüri savunması kolaydır.
* Hangi sinyalin hangi uzman modeli çağırdığı izlenebilir.
* Yanlış pozitif kaynakları daha kolay analiz edilir.

Daha sonra yeterli event verisi oluşursa öğrenilebilir bir risk/routing modeli geliştirilebilir.

## Örnek Routing JSON

```json
{
  "frame_id": "frame_000123",
  "scene_context": {
    "lighting": "low_light",
    "visibility": "limited",
    "weather": "rain",
    "confidence": 0.82
  },
  "normal_mode": {
    "tracked_vehicle_count": 5,
    "active_track_ids": ["TRK-12", "TRK-13", "TRK-17", "TRK-18", "TRK-21"]
  },
  "target_vehicle": {
    "track_id": "TRK-17",
    "pre_risk_score": 0.74,
    "risk_reasons": [
      "sudden_lateral_motion",
      "low_visibility",
      "plate_blur"
    ]
  },
  "routing_decision": {
    "mode": "critical",
    "qod_status": "CANDIDATE",
    "qod_reason": "low_visibility_and_plate_blur_may_reduce_evidence_quality",
    "experts_to_call": [
      "Plate OCR",
      "Lane/Road Marking",
      "Speed Estimation",
      "Evidence Quality Selector"
    ]
  }
}
```

## Kabul Kriteri

Bu yaklaşım uygulanmış sayılabilmesi için:

* Ortam analizi çıktısı event/overlay response içinde görünmelidir.
* Normal modda birden fazla araç track ID ile izlenebilmelidir.
* Kritik modda yalnız riskli/hedef araç için ağır uzman model çağrısı yapılmalıdır.
* QoD status, riskli araçta aday/request/active/not needed olarak ayrılmalıdır.
* Event JSON içinde routing gerekçesi ve çağrılan uzman modeller kaydedilmelidir.
