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

## FR-006 FTR Results JSON

Sistem FTR submission modunda `/app/data/input/video.mp4` dosyasını okuyarak
`/app/data/output/results.json` dosyasını resmi FTR contract'a uygun üretir.

## FR-007 Vehicle Info Extraction

Her video için tek ana araç özelinde `tip`, `plaka`, `renk` ve ortak `confidence_score`
alanları üretilir.

## FR-008 Timed Driver/Object/Passenger Detections

Sürücü eylemi, nesne ve yolcu tespitleri zaman saniyesiyle birlikte `tespitler[]` listesine
resmi FTR etiketleriyle yazılır.
