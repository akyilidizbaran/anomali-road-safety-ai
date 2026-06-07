# QoD Status Enum

QoD durumu backend, mobil UI, event JSON ve evidence ekranında aynı terimlerle kullanılmalıdır.

| Status | Anlam |
|---|---|
| `NOT_AVAILABLE` | QoD servisi veya API key yok |
| `MOCK_READY` | Geliştirme/mock QoD client hazır |
| `NOT_NEEDED` | Olay için QoD katkısı beklenmiyor |
| `CANDIDATE` | Riskli olay QoD açısından aday |
| `REQUESTED` | QoD talebi gönderildi |
| `ACTIVE` | QoD kısa süreli aktif |
| `EXPIRED` | QoD oturumu süresi doldu |
| `FAILED` | QoD isteği başarısız |

## Policy

QoD, riskli araç tespit edildiğinde aday/request akışına girebilir. Bu, QoD’nin her olayda otomatik aktif olacağı anlamına gelmez.
