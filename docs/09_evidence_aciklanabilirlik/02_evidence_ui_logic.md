# Evidence UI Logic

## Amaç

Evidence UI, yapay zeka sisteminin ürettiği kritik olayları mobil kullanıcıya anlaşılır şekilde gösterirken teknik kanıtı da denetlenebilir biçimde erişilebilir tutar.

Bu tasarım üç seviyeyi ayırır:

1. User-level explanation.
2. Technical evidence.
3. Raw model metadata.

## Mobile Evidence Representation

Mobil uygulamada her evidence card öncelikle tek bir screenshot/image gösterir.

Kartın ana görseli:

* Overlay screenshot olabilir.
* Overlay yoksa original frame screenshot olabilir.
* Görsel private/backend storage URI üzerinden temsil edilir.
* Gerçek görseller Git reposuna commit edilmez.

Kartta kısa bilgiler:

* Event ID.
* UTC timestamp.
* Risk level.
* Risk type/reasons.
* Target track ID.
* QoD status.
* Evidence status.

## Short LLM-Supported Explanation

Screenshot altında kısa bir açıklama bulunur.

Kurallar:

* Açıklama yalnız structured AI outputs üzerinden üretilir.
* LLM bağımsız karar vermez.
* LLM risk skorunu değiştirmez.
* LLM yeni ihlal/hukuki hüküm üretmez.
* LLM yoksa template fallback kullanılır.

Örnek doğru dil:

> Sistem, hedef aracın kısa zaman penceresinde ani yanal hareket gösterdiğini ve düşük görüş koşulu nedeniyle kanıt kalitesinin sınırlı olabileceğini işaretlemiştir.

Yasak dil:

> Sürücü kesin suçludur.

## Collapsible Explanation Area

Mobil evidence kartındaki açıklama hamburger/accordion benzeri katlanabilir bir alan olarak tasarlanır.

Collapsed view:

* Kısa risk açıklaması.
* Risk level.
* Confidence.

Expanded view:

* Risk reasons.
* Called expert models.
* QoD reason.
* Scene/visibility context.
* LLM/template explanation source.

## “Kanıtları Gör” Action

`Kanıtları Gör` aksiyonu comprehensive technical evidence view açar.

Bu view kullanıcı seviyesi açıklamadan daha tekniktir ve rapor/demo savunmasında denetlenebilirlik sağlar.

## Technical Evidence View

Technical evidence view şu alanları içermelidir:

* Original frame reference.
* Overlay screenshot reference.
* Target vehicle crop reference.
* Plate crop reference if available.
* Model outputs.
* Confidence scores.
* Risk score.
* Risk reasons.
* Model versions.
* Latency/FPS info.
* Which expert models were called.
* Routing decision reasons.
* QoD status.
* Event JSON.

## Raw Model Metadata

Raw model metadata, doğrudan son kullanıcıya gösterilmek zorunda değildir. Teknik view veya debug mode içinde gösterilebilir.

Örnek raw metadata:

* Raw bbox arrays.
* Per-character OCR confidence.
* NMS threshold.
* Model input size.
* Track history length.
* Calibration profile ID.
* Inference latency per expert.

## Evidence Card Data Mapping

| UI Alanı | Event JSON Kaynağı |
|---|---|
| Screenshot | `evidence.overlay_image_uri` |
| Event ID | `event_id` |
| Timestamp | `timestamp_utc` |
| Risk level | `risk.risk_level` |
| Risk score | `risk.risk_score` |
| Track ID | `target_vehicle.track_id` |
| QoD | `system.qod_status` |
| Expert models | `routing_decision.experts_called` |
| User explanation | `explanation.user_level_summary` |
| Technical explanation | `explanation.technical_summary` |

## Explanation Source Rules

| Source | Kullanım |
|---|---|
| `structured_outputs` | Backend rule/template output |
| `template` | LLM yoksa deterministic fallback |
| `local_llm` | Local LLM structured JSON’u açıklar |
| `api_llm` | API LLM structured JSON’u açıklar |
| `not_generated` | Açıklama üretilemedi |

## Evidence Generation Conditions

Evidence şu durumlarda üretilebilir:

* Risk score threshold aşılır.
* Plate/OCR anlamlı event üretir.
* Lane/speed/cabin/external user expert meaningful output üretir.
* QoD candidate/request event kaydı oluşur.
* Demo veya test sırasında manuel evidence capture istenir.

## Security and Privacy

* Evidence medyası Git reposuna commit edilmez.
* Plaka/yüz/cabin görselleri private storage sınırında tutulur.
* Teknik evidence view erişimi oturum doğrulamasına bağlı olmalıdır.
* Rapor görselleri ayrıca izin ve güvenlik kontrolünden geçmelidir.

## MVP vs Final

MVP evidence:

* Screenshot/reference.
* Target vehicle crop.
* Plate crop if available.
* Event JSON.
* Risk reasons.
* Basic model versions.

Final evidence:

* QoD status and reason.
* Per-expert outputs.
* Latency/FPS.
* Routing decision.
* Collapsible LLM-supported explanation.

Future evidence:

* Multi-target evidence comparison.
* Learned risk model attribution.
* Rich interactive timeline.
