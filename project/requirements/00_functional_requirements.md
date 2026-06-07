# Functional Requirements

## FR-001 Login and Number Verification

Kullanıcı kullanıcı adı/şifre ile giriş yapar. Başarılı credential kontrolünden sonra Number Verification API kullanıcı/cihaz/oturum eşleşmesini doğrular.

## FR-002 Live Camera Stream

Mobil uygulama CameraX mantığında canlı kamera görüntüsü üretir ve edge/backend sistemine frame/stream gönderir.

## FR-003 Normal Mode Analysis

Normal modda ortam/sahne analizi, araç tespiti, takip, hedef araç seçimi, genel yol durumu ve araç dışı kullanıcı/yaya durumu izlenir.

## FR-004 Risky Vehicle Decision

Riskli araç sinyali oluştuğunda kritik mod adayı üretilir ve QoD candidate/request akışı tetiklenir.

## FR-005 Evidence Package

Kritik olay için event JSON, karar gerekçesi, model versiyonları, bbox, confidence ve QoD durumu kaydedilir.
