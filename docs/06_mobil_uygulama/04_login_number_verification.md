# Login ve Number Verification Akışı

## Ana Amaç

Kullanıcı sisteme kendi kullanıcı adı ve şifresiyle giriş yapar. Giriş denemesi başarılı olduğunda mobil uygulama Number Verification API’ye doğrulama isteği gönderir. Kullanıcı/cihaz/oturum eşleşmesi doğrulanırsa kullanıcı sisteme alınır.

## Akış

1. Kullanıcı login ekranında kullanıcı adı ve şifre girer.
2. Mobil uygulama backend auth endpoint’ine giriş isteği gönderir.
3. Backend kullanıcı adı/şifre doğrulamasını yapar.
4. Başarılı doğrulama sonrası Number Verification API’ye request gönderilir.
5. Number Verification kullanıcı/cihaz/oturum eşleşmesini doğrular.
6. Eşleşme başarılıysa session token üretilir.
7. Kullanıcı Camera/System/Evidence ekranlarına erişir.
8. Eşleşme başarısızsa kullanıcı sisteme alınmaz ve güvenli hata mesajı gösterilir.

## Durumlar

| Durum | Açıklama | Kullanıcı Sonucu |
|---|---|---|
| `credentials_invalid` | Kullanıcı adı/şifre hatalı | Giriş reddedilir |
| `number_verification_pending` | API yanıtı bekleniyor | Bekleme göstergesi |
| `number_verified` | Kullanıcı/cihaz eşleşti | Sisteme giriş |
| `number_mismatch` | Eşleşme başarısız | Giriş reddedilir |
| `verification_unavailable` | API geçici erişilemez | Fallback politika uygulanır |

## Fallback

API geliştirme aşamasında yoksa mock/stub doğrulama kullanılabilir. Ancak raporda bu durum açıkça belirtilmelidir. Gerçek API key sağlandığında aynı adapter arayüzü korunarak mock yerine gerçek Number Verification client bağlanır.

## Güvenlik Notları

* Şifreler loglanmamalıdır.
* API key repoya eklenmemelidir.
* Repo private olsa bile gerçek credential tutulmamalıdır.
* Token/session yönetimi backend tarafında yapılmalıdır.
* Başarısız doğrulama mesajları kullanıcı veya sistem bilgisini sızdırmamalıdır.

## Rapor Cümlesi

> Mobil uygulamada kullanıcı adı ve şifre doğrulamasından sonra Number Verification API üzerinden kullanıcı/cihaz/oturum eşleşmesi kontrol edilir. Eşleşme başarılıysa kullanıcı canlı analiz sistemine alınır; aksi durumda sistem erişimi reddeder.
