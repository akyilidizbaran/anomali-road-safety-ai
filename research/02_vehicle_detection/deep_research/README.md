# Vehicle Detection Deep Research

Bu klasör, araç tespiti modülü için derin araştırma raporlarını ve kaynak kayıtlarını tutar.

## Dosyalar

* `deep_research_report.md`: Araç tespiti için derin araştırma metni. Bu dosya karar arka planıdır; uygulama takibi için doğrudan tek kaynak değildir.
* `condition_experts_deep_research_report.md`: Condition-aware / specialist vehicle detector yaklaşımı için deep research çıktısı. Bu rapor, `general -> night_low_light -> rain -> fog_low_visibility` faz sırasını destekler.
* `sources.md`: Raporda ve aksiyon dosyalarında kullanılan gerçek kaynak URL listesi.

## Kullanım Kuralı

Yeni bir modül için derin araştırma üretildiğinde aynı yapı kullanılmalıdır:

```text
research/<module>/deep_research/
  README.md
  deep_research_report.md
  sources.md
```

Karar ve uygulama dosyaları, derin araştırma klasörünün yanında ayrı Markdown/CSV dosyaları olarak tutulmalıdır.
