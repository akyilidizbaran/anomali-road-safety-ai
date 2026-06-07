# Kontrollü Video Toplama Protokolü

Ana tercih yerel veri toplamamak olsa da demo ve final genişletme için kontrollü video gerekebilir.

## Kapsam

* Gerçek yol kenarı demo canlı kamera ile tasarlanır.
* Kontrollü video yalnız risk azaltma, offline doğrulama veya cabin risk final genişletmesi için kullanılır.
* Ham video ve evidence görüntüleri public repoya commit edilmez.

## Minimum Kural

* Çekimde yer alacak kişilerden izin alınır.
* Plaka/yüz/sürücü-yolcu içeren görüntüler erişimi sınırlı lokal/backend storage içinde tutulur.
* Rapor için kullanılacak görseller ayrıca seçilir.
* Paylaşılacak görsellerde izin, kaynak ve saklama amacı net olmalıdır.

## Kayıt Alanları

| Alan | Açıklama |
|---|---|
| Video ID | Lokal benzersiz kayıt ID |
| Tarih | Çekim tarihi |
| Konum Türü | Gerçek yol kenarı / kontrollü alan |
| İzin Durumu | Alındı / gerekli değil / bekliyor |
| Kullanım Amacı | Demo / test / cabin risk / rapor |
| Public Repo | Hayır |
