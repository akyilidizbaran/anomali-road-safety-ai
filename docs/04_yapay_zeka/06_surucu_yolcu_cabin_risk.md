# Sürücü, Yolcu ve Araç İçi Risk Analizi

## Gerçekçilik İlkesi

Dışarıdan bakan telefon kamerası sürücüyü her zaman göremez. Cam yansıması, mesafe, açı, gece ve araç içi karanlık bu görevi zorlaştırır. Bu nedenle sistem koşullu çalışmalıdır.

## Akış

1. Hedef araç tespit edilir.
2. Araç ROI alınır.
3. Ön cam veya yan cam bölgesi çıkarılır.
4. Görünürlük skoru hesaplanır.
5. Görünürlük yeterliyse cabin risk modeli çalışır.
6. Görünürlük yetersizse “analiz güvenilir değil” çıktısı verilir.

## 2026-06-21 Baseline Reset Kararı

`CABIN-EXP-012-runtime-foundation` heuristik ROI/visibility denemesi manuel kontrolde baseline
kalitesinde görülmediği için repodan kaldırıldı. Bu nedenle cabin/driver tarafında devam yönü
heuristik cabin ROI üretmek değil, doğrudan model tabanlı bir baseline seçip onun üzerinde
fine-tune etmektir.

Yeni baseline yaklaşımı:

1. **Driver action classifier baseline**
   * State Farm / AUC Distracted Driver tarzı sürücü eylemi veri setleriyle başlar.
   * İlk hedef FTR `sofor_eylemi` etiketleridir: `telefonla_konusma`, `sigara_icme`,
     `su_icme`, `etrafa_bakinma`, `arkaya_bakma`, `esneme`.
2. **Small-object specialist baseline**
   * Telefon, sigara, bilgisayar ve teknocan gibi küçük nesneler için YOLO tabanlı ayrı
     detector kullanılır.
   * Bu model action classifier çıktısını destekleyen veya çürüten evidence sinyali üretir.
3. **Passenger / seat-region baseline**
   * `on_koltuk`, `arka_koltuk_1`, `arka_koltuk_2` için ayrı yolcu/koltuk konumu çalışması
     gerekir.

Bu reset sonrası seatbelt hâlâ dikkatli ele alınmalıdır: kemer görünmüyorsa `unknown` kalır;
yokluk doğrudan `emniyet_kemeri_ihlali` sayılmaz.

Detaylı plan:

```text
research/08_cabin_risk/model_first_cabin_baseline_plan_v1.md
```

İlk somut notebook:

```text
notebooks/CABIN_EXP_020A_Cabin_Driver_View_Baseline_Colab.ipynb
```

Bu notebook doğrudan eylem sınıflandırmaz. Önce `driver_cabin_visible` / `not_cabin_view`
gate'ini öğrenir. Bu gate başarılı olmadan `telefonla_konusma`, `su_icme`, `arkaya_bakma` ve
`etrafa_bakinma` eylem sınıflandırmasına geçilmemelidir.

## Olası Riskler

* Telefon kullanımı.
* Sigara.
* Emniyet kemeri belirsizliği.
* Dikkat dağınıklığı.
* Yolcu sayısı.
* Görüş engelleyici nesne.

## Metrikler

* Precision.
* Recall.
* F1.
* False positive rate.
* Visibility gating doğruluğu.

## Sorulacak Noktalar

* Kontrollü cabin risk videosu çekilecek mi?
* Bu modül final demo için zorunlu mu?
