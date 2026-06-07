# Decision: LLM Explanation Only

## Date

2026-06-07

## Decision

LLM karar verici değil, structured event JSON’dan insan okunur açıklama üreten katmandır.

## Rationale

Risk kararı deterministik model çıktıları, kurallar ve event fusion üzerinden izlenebilir kalmalıdır. LLM çıktısı kararın kaynağı yapılırsa denetlenebilirlik zayıflar.

## Impact

* LLM API, local LLM veya template fallback kullanılabilir.
* Evidence package içinde asıl karar gerekçesi structured field olarak saklanır.
