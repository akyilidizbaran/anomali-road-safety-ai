# Risk: 30 FPS and Latency

## Risk

30 FPS hedefi tüm uzman modellerin her karede çalışacağı şeklinde yanlış anlaşılabilir.

## Impact

Gerçek zamanlılık iddiası teknik olarak savunulamaz hale gelebilir.

## Mitigation

* Camera preview ile inference FPS ayrılır.
* Normal mod hafif tutulur.
* Uzman modeller olay bazlı çağrılır.
* FPS/latency metrikleri ayrı raporlanır.

## Status

Open.
