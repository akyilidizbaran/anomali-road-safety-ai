# Project Yönetim Alanı

Bu klasör teknik kod veya rapor metni değil, proje yönetimi ve karar takibi için ayrılmıştır.

## Alt Klasörler

* `requirements`: Yarışma isterleri, proje gereksinimleri ve kapsam maddeleri.
* `decisions`: Mimari ve teknik karar kayıtları.
* `risks`: Riskler, teknik borçlar ve azaltma planları.

## Kullanım

Her büyük karar için `decisions/` altında tarihli bir Markdown dosyası açılmalıdır. Her risk için `risks/` altında risk, etki, olasılık ve azaltma planı yazılmalıdır.

## Başlangıç Dosyaları

Gereksinimler:

* `requirements/00_functional_requirements.md`
* `requirements/01_nonfunctional_requirements.md`
* `requirements/02_acceptance_criteria.md`

Riskler:

* `risks/00_speed_calibration.md`
* `risks/01_cabin_visibility.md`
* `risks/02_public_repo_privacy.md`
* `risks/03_30fps_latency.md`
* `risks/04_qod_api_delay.md`

Kararlar:

* `decisions/2026-06-07-single-target-first.md`
* `decisions/2026-06-07-edge-first-balanced-mobile.md`
* `decisions/2026-06-07-llm-explanation-only.md`
* `decisions/2026-06-07-qod-selective-policy.md`
