# Decision: Selective QoD Policy

## Date

2026-06-07

## Decision

QoD her riskli olayda otomatik aktif olmaz. Riskli araçta candidate/request akışı tetiklenir; yalnız karar güveni veya kanıt kalitesi artacaksa kısa süreli aktif olur.

## Rationale

QoD ağ kaynağıdır ve proje değerini seçici kalite artışıyla göstermelidir.

## Impact

* QoD status enum contract olarak tutulur.
* System ve Evidence ekranları QoD durumunu açık gösterir.
* Demo dili “QoD her zaman açık” iddiasından kaçınır.
