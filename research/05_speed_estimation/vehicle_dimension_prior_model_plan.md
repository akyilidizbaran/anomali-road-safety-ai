# Vehicle Dimension Prior Model Plan

## Amaç

`Vehicle Dimension Prior` modülü, hız kestirimi için araç crop'larından ek ölçek sinyali üretir. Bu modül doğrudan hız ölçmez; `Speed Fusion Layer` içinde plaka ölçeği, homografi/track hareketi ve araç boyutu ön bilgisiyle birlikte kullanılır.

## Neden Ayrı Model?

Plaka tespiti, araç marka/model tanıma ve teker/keypoint çıkarımı farklı görevlerdir:

* Plaka modeli küçük nesne tespiti yapar.
* Araç attribute modeli araç gövde tipi veya fine-grained sınıf tahmini yapar.
* Keypoint modeli teker, far veya araç köşe noktası gibi geometrik referansları çıkarır.

Bu görevleri erken aşamada tek modelde birleştirmek mevcut çalışan plaka modelini bozabilir. Bu yüzden ilk tasarım modülerdir.

## Seçilen İlk Deney

* Deney adı: `VATTR-EXP-001`
* Notebook: `notebooks/VATTR_EXP_001_BoxCars_Vehicle_Attribute_Classifier_Colab.ipynb`
* Dataset adayı: BoxCars116k
* İlk backbone: `MobileNetV3-Large`
* Ağır run challenger: `EfficientNet-B0`
* Çıktı tipi: araç sınıfı/gövde tipi veya fine-grained etiket + yaklaşık dimension prior

BoxCars116k seçilme nedeni, trafik gözetleme kameralarından farklı açılarda araç görüntüleri içermesi ve bizim sabit yol kenarı kamera senaryomuza web fotoğrafı ağırlıklı datasetlerden daha yakın olmasıdır.

## Runtime Contract

Önerilen model çıktısı:

```json
{
  "track_id": "TRK-17",
  "vehicle_attribute": {
    "label": "sedan_or_fine_grained_class",
    "confidence": 0.82,
    "body_type_prior": "sedan",
    "wheelbase_m_mean": 2.75,
    "wheelbase_m_min": 2.55,
    "wheelbase_m_max": 3.0,
    "use_for_speed_fusion": true
  }
}
```

`use_for_speed_fusion=false` ise bu sinyal mutlak km/s hesabına doğrudan katılmaz; yalnız evidence notu olarak tutulur.

## Speed Fusion İçindeki Rol

`Vehicle Dimension Prior` şu durumlarda faydalıdır:

* Plaka görünür ama plate-scale hız hesabı düşük güvenliyse.
* Homografi yok ama araç tipi güvenilir tahmin ediliyorsa.
* Araç yan/rear-side açıdaysa ve wheel/keypoint tespiti mümkünse.
* Plaka görünmüyor ancak araç bbox/track hareketi stabilse.

Bu sinyal tek başına hukuki veya kesin hız ölçümü değildir.

## SKoPe3D ve ApolloCar3D Konumu

* `KPT-EXP-001`: OpenPifPaf ApolloCar3D pretrained keypoint smoke test yapılabilir. Sıfırdan eğitim gerektirmeden teker/keypoint görünür mü sorusunu hızlı yanıtlar.
* `KPT-EXP-002`: SKoPe3D ile roadside-view keypoint fine-tune değerlendirilebilir. SKoPe3D sentetik olduğu için domain gap riski vardır; ancak yol kenarı kamera açısına ApolloCar3D'den daha yakındır.

## Riskler

* Fine-grained marka/model tahmini domain kayması nedeniyle yanlış olabilir.
* Yanlış marka/model tahmini yanlış wheelbase prior üretir.
* Araç crop'u karanlık veya uzaktaysa attribute confidence düşer.
* Görünüm açısı bilinmeden wheelbase ölçüsü güvenilir kullanılmaz.
* 3 demo videosu eğitim için yeterli değildir; yalnız smoke/manual review amacıyla kullanılmalıdır.

## Kaynaklar

* BoxCars GitHub: https://github.com/JakubSochor/BoxCars
* BoxCars paper: https://arxiv.org/abs/1703.00686
* CompCars dataset: https://mmlab.ie.cuhk.edu.hk/datasets/comp_cars/
* SKoPe3D dataset: https://duolu.github.io/skope3d.html
* OpenPifPaf ApolloCar3D plugin: https://openpifpaf.github.io/plugins_apollocar3d.html
