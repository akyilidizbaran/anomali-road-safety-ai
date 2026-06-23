# Driver Skeleton Freeze Karari

Tarih: 2026-06-17

## Sabitlenen Baseline

`POSE-EXP-009 = vitpose_b_final_torso_baseline_v1` nihai driver skeleton
baseline olarak sabitlenmistir.

Kapsam:

* YuNet driver-face ile kimlik baglantisi,
* cabin-clamped upper-body ROI,
* omuz ve torso geometrisi,
* gorunurluk zayif karelerde evidence-only devam,
* seatbelt ve diger specialist modeller icin driver torso ROI.

Uc-video full-rate sonucunda pose rate `1.0`, torso anchor oranlari
`0.9305 / 1.0000 / 1.0000`, en uzun karar-kapsami kopmalari
`0.12 / 0.00 / 0.00 sn` olmustur.

## Kapatilan Kapsam

Asagidaki semantik arm-state siniflari artik baseline kabul kapisi degildir:

* bilek veya on kol direksiyonda,
* kol havada,
* off-wheel / wheel-candidate,
* dirsek-bilek geometrisinden telefon veya sigara karari.

`POSE-EXP-010 -> ARM-EXP-001`, `video_3`te `0.9851` available-state ve
`0.04 sn` longest miss gosteren en guclu arm-state candidate olarak reference
kalir. Ancak uc-video kabul ve anatomik dogruluk kaniti olmadigi icin secilmis
baseline degildir ve risk uretmez.

## Sonraki Kullanım

Telefon ve sigara object-first specialist detector ile aranir. Pose/hand bilgisi
yalniz nesne adayi bulunduktan sonra surucuyle iliskilendirme metadata'si olarak
cagrilabilir. Iskelet modeli tekrar acilmayacak; yeni bir specialist model icin
acik ve olculebilir hata kaniti olmadikca pose modeli arastirmasi yapilmayacaktir.
