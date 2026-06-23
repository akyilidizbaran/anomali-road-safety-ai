# Seatbelt Baseline Kararı v1

Tarih: 2026-06-14

## Karar

`SEATBELT-EXP-001 / opencv_diagonal_belt_evidence_v1` seçilmemiştir.

## Gerekçe

Üç-video smoke benchmark'ı pipeline'ın çalıştığını doğrulamıştır. Bununla
birlikte manuel incelemede diyagonal araç yüzeyi ve yansıma çizgilerinin kemer
kanıtı olarak işaretlenebildiği görülmüştür. Çizgi yokluğu da kemersizliği
kanıtlamaz.

| Video | Evaluable | Evidence-only | Positive evidence rate | Karar |
|---|---:|---:|---:|---|
| video_1 | 174 | 38 | 0.0402 | unknown |
| video_2 | 209 | 43 | 0.0096 | unknown |
| video_3 | 121 | 88 | 0.0000 | unknown |

Ortalama inference latency yaklaşık `1.715 ms`; en yüksek video P95 değeri
`4.716 ms` olmuştur. Düşük latency doğruluk eksikliğini telafi etmez.

## Contract Politikası

* `seatbelt_status=unknown` korunur.
* Candidate metadata `seatbelt_analysis_status=candidate` olarak tutulabilir.
* Çizgi yokluğundan `unbelted` çıkarılmaz.
* `incorrect` inference kapalıdır.
* Risk skoru değiştirilmez.

## Sonraki Karar Noktası

Kontrollü pozitif-negatif veri toplanıp öğrenilebilir classifier/detector
challenger ölçülmeden seatbelt baseline seçilmeyecektir.
