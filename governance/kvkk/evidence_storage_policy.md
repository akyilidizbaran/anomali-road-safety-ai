# Evidence Storage Policy

## Repository Boundary

Evidence package yapısı Git içinde dokümante edilebilir; gerçek evidence görüntüleri, crop dosyaları ve videolar Git içinde tutulmaz. Repo private olsa bile bu sınır korunur.

## Stored Metadata

* Event ID.
* Timestamp.
* Track ID.
* Bounding box.
* Confidence score.
* Risk level.
* Model versions.
* QoD status.
* Decision reason.

## Storage Note

Test sırasında evidence medyası private local/backend storage altında tutulmalıdır.
