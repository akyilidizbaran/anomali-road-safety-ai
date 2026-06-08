# Local Manual Test Videos

Bu klasör geçici manuel benchmark ve smoke-test videoları içindir.

## Current Local Set

* `video_1.mp4`
* `video_2.mp4`
* `video_3.mp4`

Bu videolar dark/low-light koşulundaki ilk manuel test materyalidir. Git'e eklenmez.

## Kullanım Kuralı

1. Her benchmark denemesinde model çıktısı bu videolar üzerinde izlenir.
2. Video çıktıları manuel kontrol edilir.
3. Accuracy / hata notları model ve deney kaydıyla birlikte `testing/templates/manual_video_benchmark_review.csv` formatında yazılır.
4. Video dosyaları memory/disk yükü oluşturmaması için benchmark turu tamamlandıktan sonra silinebilir.

## Manual Review Notu

Bu videolarda şimdilik resmi ground truth annotation yoktur. Bu nedenle ilk sonuçlar mAP olarak değil, manuel review score olarak raporlanmalıdır.

## Git Kuralı

Bu klasördeki video, frame, crop ve evidence görselleri repoya commit edilmez. Yalnız bu README takip edilir.
