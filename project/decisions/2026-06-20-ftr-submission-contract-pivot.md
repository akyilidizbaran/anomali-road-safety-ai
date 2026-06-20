# Decision: FTR Submission Contract Pivot

Date: 2026-06-20

## Decision

FTR asamasi icin ana teslim hedefi, genis mobil/edge/evidence mimarisinden once resmi
degerlendirme contract'ina uygun Docker tabanli inference paketi olacak.

Hakem tarafindan beklenen ana contract:

```text
/app/data/input/video.mp4 -> /app/data/output/results.json
```

`results.json` icinde `arac_bilgisi` ve `tespitler` bloklari bulunacak.

## Rationale

Yeni FTR teslim dokumani otomatik degerlendirme scriptlerinin bekledigi JSON anahtarlarini,
etiket degerlerini, Docker base image'ini, runtime path'lerini ve donanim limitlerini net
olarak tanimliyor. Bu sozlesmeye uymayan genis event/evidence JSON'u teknik olarak faydali
olsa bile otomatik degerlendirmede kabul edilmeyebilir.

## Impact

* `architecture/contracts/ftr_results_output_contract.md` ana submission contract'i oldu.
* `project/requirements/03_ftr_submission_requirements.md` eklendi.
* Roadmap once FTR output adapter, Docker packaging, vehicle info ve cabin/action tespitlerine
  odaklanacak.
* Speed/QoD/evidence katmanlari proje ici destek ve rapor degeri olarak korunacak, fakat FTR
  `results.json` icin zorunlu alan sayilmayacak.

## Alternatives Considered

* Eski zengin event/evidence JSON'u hakem ciktisi yapmak: Reddedildi, resmi schema ile uyumsuz.
* Speed/homography calismasini ana hedef yapmak: Reddedildi, FTR output schema hiz alani istemiyor.
* Docker packaging'i sona birakmak: Reddedildi, runtime path ve 10 dakika limiti model secimini etkiliyor.
