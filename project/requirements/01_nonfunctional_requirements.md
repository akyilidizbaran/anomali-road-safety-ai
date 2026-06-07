# Non-Functional Requirements

## NFR-001 Decision Support Boundary

Sistem otomatik ceza veya hukuki hüküm üretmez.

## NFR-002 Public Repo Safety

Repo içine secret, model ağırlığı, raw video, evidence image veya kişisel veri içeren medya commit edilmez.

## NFR-003 Performance

Camera preview 30 FPS hedefleyebilir; ağır uzman modeller olay bazlı ve seçici çağrılır.

## NFR-004 Traceability

Her kritik olay event ID, timestamp, track ID, model version ve decision reason ile izlenebilir olmalıdır.

## NFR-005 Extensibility

MVP single-target mode ile başlar; multi-target mode deneysel genişletme olarak tasarlanır.
