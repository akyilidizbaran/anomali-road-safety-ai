# Genel Yol ve Araç Dışı Kullanıcı Durumu

## Amaç

Proje yalnız riskli aracı analiz etmekle sınırlı kalmamalıdır. Normal modda genel yol durumu ve araç dışı kullanıcı/yaya durumu da izlenmelidir. Bu bilgiler kritik olay kararına bağlamsal destek verir.

## Genel Yol Durumu

Analiz edilecek sinyaller:

* Yol yüzeyi görünür mü?
* Şerit/road marking görünür mü?
* Yol ıslak mı, kuru mu, düşük görüş altında mı?
* Işık durumu detection ve OCR için yeterli mi?
* Sis, yağmur, karanlık veya far parlaması var mı?
* Yol çizgisi veya sınır algısı güvenilir mi?

Bu sinyaller özellikle QoD adaylığı, OCR güveni, lane analizi ve hız kestirimi için bağlam sağlar.

## Araç Dışı Kullanıcı Durumu

Araç dışı kullanıcılar şu sınıfları kapsayabilir:

* Yaya.
* Bisikletli.
* Motosikletli.
* Yol kenarındaki insan.
* Trafik görevlisi veya demo personeli.

İlk aşamada bu modül, public/pretrained object detection modellerindeki `person`, `bicycle`, `motorcycle` gibi sınıflardan yararlanabilir. Sıfırdan eğitim ana hedef değildir; model seçimi ve fine-tune ihtiyacı araştırma sonrası belirlenecektir.

## Risk Skoruna Katkı

Araç dışı kullanıcı durumu şu durumlarda risk skoruna katkı sağlar:

* Riskli araç yayaya yakınsa.
* Yol kenarında insan varsa ve araç şerit/yol dışına yakınsa.
* Görüş düşükken araç dışı kullanıcı tespit edilmişse.
* Araç ani manevra yaparken çevrede yaya/bisikletli varsa.

## Event JSON Alanları

Önerilen alan:

```json
{
  "road_context": {
    "surface_condition": "wet",
    "lane_marking_visibility": "low",
    "lighting": "low_light",
    "visibility": "limited",
    "confidence": 0.78
  },
  "external_users": [
    {
      "type": "pedestrian",
      "bbox": [120, 240, 180, 410],
      "confidence": 0.84,
      "relative_position": "roadside",
      "risk_relation": "near_target_vehicle"
    }
  ]
}
```

## Model Yaklaşımı

Başlangıç:

* Public/pretrained object detection modeli.
* Person/bicycle/motorcycle sınıflarının kullanımı.
* Road context için sahne/görüş sınıflandırıcı.

Geliştirme:

* Gerekiyorsa yol kenarı/yaya senaryolarıyla fine-tune.
* Distance/proximity rule-based risk relation.
* Event explanation içinde “araç dışı kullanıcı yakınlığı” gerekçesi.

## Metrikler

* Person/bicycle/motorcycle detection precision/recall.
* Road context classification accuracy/macro F1.
* Risk relation false positive oranı.
* Event-level katkı: kritik olay açıklamasına doğru bağlam ekleniyor mu?
