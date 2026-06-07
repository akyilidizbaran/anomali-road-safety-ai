# Risk Takibi

## Ana Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| 5G API key geç gelmesi | QoD/Number Verification gerçek entegrasyonu gecikir | Mock/stub adapter |
| Hız kalibrasyonu yapılamaması | Mutlak km/s iddiası zayıflar | Göreli hız/risk skoru |
| Cabin risk görünürlüğü düşük | Yanlış pozitif riski | Visibility gating |
| OCR düşük ışıkta zayıf | Evidence kalitesi düşer | Temporal voting + QoD adaylığı |
| Tüm modellerin ağır çalışması | FPS/latency düşer | Normal/kritik mod + frame skipping |

## Ayrıntılı Risk Dosyaları

* `00_speed_calibration.md`
* `01_cabin_visibility.md`
* `02_public_repo_privacy.md`
* `03_30fps_latency.md`
* `04_qod_api_delay.md`
