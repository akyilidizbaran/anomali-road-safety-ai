# Evidence ve Açıklanabilirlik Omurgası

## Ana Fikir

Sistem alarm üretmekle kalmaz. Her kritik olayı denetlenebilir kanıt paketine dönüştürür.

## Evidence Package İçeriği

* Event ID.
* Timestamp.
* Source frame ID.
* Track ID.
* Bounding boxes.
* Confidence scores.
* Risk score.
* Risk level.
* Called expert models.
* QoD status.
* Model versions.
* Decision reason.
* Image crop URI.
* Overlay screenshot URI.

## LLM Açıklama Katmanı

LLM karar vermez. Structured event JSON’u insan tarafından anlaşılır açıklamaya dönüştürür.

Mevcut karar:

* LLM API ile bağlanabilir.
* Alternatif olarak local LLM bilgisayar üzerinde çalıştırılıp bir domain/sunucu üzerinden servis edilebilir.
* Fallback durumunda sabit/template açıklama metinleri kullanılabilir.
* Her durumda LLM karar verici değil, açıklama üretici katmandır.

Yasak ifadeler:

* Bu sürücü suçludur.
* Kesin ihlal yapmıştır.
* Ceza uygulanmalıdır.

Doğru ifadeler:

* Sistem bu olayı yüksek riskli olarak işaretlemiştir.
* Model güveni şu seviyededir.
* Görüş koşulu nedeniyle belirsizlik artmıştır.

## Sorulacak Noktalar

* Local LLM kullanılacaksa model adı, donanım ve servis endpoint’i ne olacak?
* API kullanılacaksa hangi sağlayıcı ve hangi güvenlik sınırları kullanılacak?
