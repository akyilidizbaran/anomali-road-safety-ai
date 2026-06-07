# Auth, Normal Mode and QoD Flow

Bu akış, `leD24n5kb...pdf` ve güncel proje kararlarına göre ana çalışma sırasını gösterir.

```mermaid
flowchart TD
  A["Kullanıcı adı + şifre"] --> B["Backend auth kontrolü"]
  B -->|Başarılı| C["Number Verification API request"]
  B -->|Başarısız| Z["Erişim reddi"]
  C -->|Eşleşti| D["Session açılır"]
  C -->|Eşleşmedi| Z
  D --> E["CameraX canlı kamera"]
  E --> F["5G / stream uplink"]
  F --> G["Edge preprocess"]
  G --> H["Ortam analizi: hava, ışık, görüş"]
  H --> I["Normal detection + tracking"]
  I --> J["Genel yol ve araç dışı kullanıcı durumu"]
  J --> K["Hedef araç ve risk ön skoru"]
  K -->|Düşük risk| L["Normal overlay"]
  K -->|Riskli araç| M["QoD candidate/request"]
  M --> N{"QoD fayda sağlar mı?"}
  N -->|Evet| O["Kısa süreli kalite artırımı"]
  N -->|Hayır| P["QoD gerekmiyor"]
  O --> Q["Kritik mod uzman modeller"]
  P --> Q
  Q --> R["Plate OCR / Speed / Lane / External User / Cabin"]
  R --> S["Event fusion JSON"]
  S --> T["Evidence package"]
  T --> U["Mobil Evidence ekranı"]
```

## Notlar

* QoD tetikleme, her riskte otomatik aktiflik anlamına gelmez.
* Ortam analizi detection kararını tek başına değiştirmez; risk skoruna ve model güven yorumuna bağlam sağlar.
* Araç dışı kullanıcı/yaya durumu ilk aşamada public/pretrained detection sınıflarıyla temsil edilebilir.
