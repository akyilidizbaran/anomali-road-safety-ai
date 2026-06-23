# TORSO-EXP-001 Deterministic Driver Torso Baseline

Tarih: 2026-06-13T11:15:52Z

Karar: `rejected_full_video_user_review`

## Zincir

`YuNet driver face -> view-profile torso geometry -> quality gate -> temporal torso metadata`

## Sonuç

| Video | Profil | Evaluable | Usable Rate | Available Rate | Ready | Longest Miss | Mean Quality |
|---|---|---:|---:|---:|---|---:|---:|
| video_1.mp4 | side_driver_window | 187 | 1.0 | 1.0 | True | 0 | 0.9633 |
| video_2.mp4 | side_driver_window | 209 | 1.0 | 1.0 | True | 0 | 0.9688 |
| video_3.mp4 | front_lhd | 134 | 0.4254 | 0.4254 | True | 69 | 0.8039 |

## Sınırlar

* Bu deney insan pozu, seatbelt veya phone sınıflandırması yapmaz.
* Yeşil torso kutusu yalnız specialist model için candidate crop'tur.
* Geometrik ROI doğruluğu tam overlay manuel review ile onaylanmalıdır.
* Kemerli/kemersiz ayrımı kontrollü veri ve ayrı specialist benchmark ister.

## Manuel Review

* Şablon: `testing/templates/manual_driver_torso_review.csv`
* Crop ve overlay: `runs/driver_torso/` altında Git dışındadır.

## Full Video Review

Sampled kareler yanıltıcı biçimde makul görünse de kullanıcı üç tam overlay videosunda
kesintiler, yanlış torso yerleşimleri ve videolar arasında tutarsız davranış gördü.
Bu nedenle deterministic torso yöntemi reddedildi ve baseline olarak kullanılmayacak.
