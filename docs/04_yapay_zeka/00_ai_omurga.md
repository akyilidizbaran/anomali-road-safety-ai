# Yapay Zeka Omurgası

## Temel Karar

Proje tek bir modelle değil, görev bazlı uzman modellerle ilerlemelidir. Çünkü araç tespiti, plaka OCR, şerit, hız, hava/görüş ve cabin risk birbirinden farklı veri, model ve metrik ister.

Runtime hattın detaylı uçtan uca açıklaması için `docs/04_yapay_zeka/10_runtime_ai_pipeline_mimarisi.md` ana referans kabul edilir.

## Model Geliştirme Önceliği

İlk model geliştirme odağı araç tespitidir. Araç tespiti tamamlandıktan sonra araç takibi, hedef araç seçimi, plaka/OCR, evidence, sahne/görüş, şerit, hız ve cabin risk modülleri sırayla eklenecektir.

Eğitim ve deney ortamı Google Colab olacak. Başlangıç model ailesi araştırma sonrası seçilecek. Başarı, tek bir metrikle değil doğruluk, hız, latency, model boyutu ve sistem entegrasyonunu birlikte değerlendiren dengeli metrik paketiyle ölçülecektir.

Eğitimin ana yükü sıfırdan model eğitmek değildir. İnternet üzerinden elde edilen public/pretrained modeller kullanılacak; gerektiğinde fine-tune, veri işleme, post-processing ve proje hedeflerine göre output uyarlaması yapılacaktır.

## Pipeline

1. Context-gated scene/visibility/road analysis.
2. Vehicle detection.
3. Multi-vehicle lightweight tracking.
4. Target/risky vehicle selection.
5. Risk pre-score.
6. QoD candidate/request decision.
7. Expert model selection.
8. Expert inference on target vehicle ROI.
9. Event fusion.
10. Evidence package.

Detaylı routing politikası için `docs/04_yapay_zeka/11_context_gated_model_routing.md` kullanılmalıdır.

Model output contractları için `architecture/contracts/model_output_contract.md` kullanılmalıdır.

## Neden Rule-Based Başlangıç Kabul Edilebilir?

Risk skoru ve uzman model seçimi başlangıçta rule-based olabilir. Bunun avantajları:

* Açıklanabilir.
* Debug etmesi kolaydır.
* Rapor anlatısı nettir.
* Yanlış alarm kaynakları daha kolay bulunur.

Daha sonra öğrenilebilir risk modeli geliştirilebilir.

## Uzman Model Frekansları

| Modül | Frekans |
|---|---|
| Kamera preview | 30 FPS hedef |
| Vehicle detection | 15-30 FPS |
| Tracking | Her frame veya yüksek frekans |
| Context/scene routing | 1-2 Hz veya olay penceresi |
| OCR | Her 5-10 frame veya plaka netleşince |
| Scene analysis | 1-2 Hz |
| Lane | 10-15 FPS veya risk penceresi |
| Cabin risk | Kritik ROI varsa |
| Evidence | Olay bazlı |
