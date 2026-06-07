# Risk: QoD API Delay

## Risk

QoD veya Number Verification API keyleri geç gelebilir veya entegrasyon takvimi gecikebilir.

## Impact

Gerçek 5G/QoD entegrasyonu demo tarihine yetişmeyebilir.

## Mitigation

* Mock/stub adapter arayüzü korunur.
* Gerçek API geldiğinde adapter değişir, AI pipeline bozulmaz.
* Raporda mock/gerçek ayrımı açıkça belirtilir.

## Status

Open.
