# FTR Submission Requirements

Bu gereksinimler FTR asamasi resmi teslim dokumanina gore eklenmistir ve bundan sonraki
uygulama onceliginde eski genis demo/dashboard hedeflerinin onune gecer.

## FTR-SUB-001 Docker Entry

Repo root seviyesinde `Dockerfile` bulunmali ve `docker run` ile ekstra manuel adim olmadan
otomatik inference baslamalidir.

## FTR-SUB-002 Runtime Paths

Program su path'leri kullanmalidir:

* Input: `/app/data/input/video.mp4`
* Output: `/app/data/output/results.json`
* Model directory: `/app/models/`

## FTR-SUB-003 Base Image and Limits

Docker imaji `nvidia/cuda:12.1.0-base-ubuntu22.04` tabanli olmali ve Tesla T4 GPU,
4 vCPU, 16 GB RAM, 2 GB SHM, 8 GB image ve 10 dakika runtime limitleri dikkate alinmalidir.

## FTR-SUB-004 Results JSON

`results.json` dosyasi `architecture/contracts/ftr_results_output_contract.md` ile uyumlu
olmalidir.

## FTR-SUB-005 Vehicle Information

Her video icin tek ana araca ait asagidaki bilgiler uretilecektir:

* `tip`
* `plaka`
* `renk`
* ortak `confidence_score`

## FTR-SUB-006 Timed Detections

`tespitler` listesi surucu eylemi, nesne ve yolcu etiketlerini saniye bazli uretmelidir.
Etiketler FTR izinli listesi disina cikmamalidir.

## FTR-SUB-007 ASCII and Exact Match

Tum kategori ve etiket degerleri ASCII-safe, kucuk harfli ve resmi dokumandaki degerlerle
birebir ayni olmalidir.

## FTR-SUB-008 Error Handling

Video bulunamazsa, bozuksa veya model cikti uretemezse kod kontrolsuz crash etmemelidir.
Degerlendirme manipülasyonu sayilabilecek ortam tespiti branch'leri yazilmamalidir.

## FTR-SUB-009 Runtime Internet Independence

Model agirliklari ve gerekli kaynaklar image/model klasoru icinde bulunmali; runtime
internet baglantisina guvenilmemelidir.

## FTR-SUB-010 Internal vs Submission Output

Proje ici event/evidence JSON'u korunabilir; ancak hakeme giden cikti yalniz FTR
`results.json` adapter'i tarafindan uretilmelidir.
