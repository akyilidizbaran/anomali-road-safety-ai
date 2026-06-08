# QoD Status Enum

QoD durumu backend, mobil UI, event JSON ve evidence ekranında aynı terimlerle kullanılmalıdır.

| Status | Anlam |
|---|---|
| `not_available` | QoD servisi veya API key yok |
| `mock_ready` | Geliştirme/mock QoD client hazır |
| `not_needed` | Olay için QoD katkısı beklenmiyor |
| `candidate` | Riskli olay QoD açısından aday |
| `requested` | QoD talebi gönderildi |
| `active` | QoD kısa süreli aktif |
| `expired` | QoD oturumu süresi doldu |
| `failed` | QoD isteği başarısız |

## Policy

QoD, riskli araç tespit edildiğinde aday/request akışına girebilir. Bu, QoD’nin her olayda otomatik aktif olacağı anlamına gelmez.
