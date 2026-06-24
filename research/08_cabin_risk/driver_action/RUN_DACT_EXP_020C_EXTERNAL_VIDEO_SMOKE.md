# RUN - DACT-EXP-020C External Video Smoke Test

## Amaç

`DACT-EXP-020B`, State Farm iç-kabin sürücü görüntüleriyle eğitildi. Projenin
demo videoları ise yol kenarı / araç dışı kamera görüntüleridir. Bu nedenle
modeli doğrudan 3 demo video üzerinde test etmeden runtime'a bağlamak doğru
değildir.

`DACT-EXP-020C`, bu domain farkını ölçen smoke testtir:

* `full_frame`: tüm dış kamera karesi
* `target_vehicle`: hedef araç crop'u
* `cabin_candidate`: hedef araç içinden kabin/cam adayı crop

Bu üç giriş modunda `DACT-EXP-020B` skorları üretilir. Amaç final doğruluk
ölçmek değil, dış kamera verisinde modelin yanlış pozitif aksiyon üretme
eğilimini görmek ve temporal/görünürlük gate ihtiyacını kanıtlamaktır.

## Ön Koşul

Colab'da üretilen checkpoint lokal repoda şu konuma koyulmalıdır:

```text
models/checkpoints/cabin_driver/DACT-EXP-020B/DACT-EXP-020B-efficientnet_b0-best.pth
```

Colab Drive kaynak yolu:

```text
/content/drive/MyDrive/anomali-road-safety-ai/models/checkpoints/cabin_driver/DACT-EXP-020B/DACT-EXP-020B-efficientnet_b0-best.pth
```

Label map opsiyoneldir; yoksa checkpoint içindeki label bilgisi veya repo
fallback label sırası kullanılır. Varsa şu konuma koyulabilir:

```text
models/checkpoints/cabin_driver/DACT-EXP-020B/DACT-EXP-020B-label-map.json
```

## Çalıştırma

Video işleri için repo ortamında `.venv-yolo-run` kullanılmalıdır:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_dact_020b_external_video_smoke.py \
  --render-mode all
```

Daha hızlı debug için:

```bash
.venv-yolo-run/bin/python scripts/benchmarks/run_dact_020b_external_video_smoke.py \
  --sample-every 25 \
  --max-frames 120
```

Varsayılan script şu kaynakları kullanır:

```text
Test/video_1.mp4
Test/video_2.mp4
Test/video_3.mp4
models/benchmarks/artifacts/TRK-EXP-001-yolo11n-bytetrack-event-skeletons-paddle-driver-detection.json
```

## Çıktılar

Git'e eklenmeyecek görsel/video çıktıları:

```text
runs/driver_action/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/annotated/
```

`--render-mode all` ile her video için `full_frame`, `target_vehicle` ve
`cabin_candidate` olmak üzere 9 annotated MP4 üretilir.

Küçük takip artefactleri:

```text
models/benchmarks/artifacts/cabin_driver/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/dact_exp_020c_external_video_smoke_summary.json
models/benchmarks/artifacts/cabin_driver/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/dact_exp_020c_external_video_smoke_summary.csv
models/benchmarks/artifacts/cabin_driver/DACT-EXP-020C-external_video_domain_transfer_smoke_v1/dact_exp_020c_external_video_smoke_frames.csv
testing/reports/dact_exp_020c_external_video_smoke.md
```

## Karar Politikası

Bu smoke testte:

```json
"should_emit_driver_action": false
```

Bu bilinçli bir karardır. Çünkü:

* Eğitim domain'i iç-kabin görüntüdür.
* Test domain'i dış kamera / yol kenarıdır.
* Dış görünüşte telefon, su içme veya arkaya bakma doğrudan gözlenmeyebilir.
* Pozitif skor yalnız domain-transfer alarmı veya candidate sinyalidir.

Runtime'da final eylem yazmak için en az şu zincir gerekir:

```text
DRIVER-EXP-001 driver visible
-> cabin/driver crop yeterli görünürlük
-> DACT-EXP-020B frame-level score
-> temporal persistence
-> optional specialist support
-> event/evidence JSON
```

## Beklenen Yorum

3 örnek dış kamera videosunda modelin çok güvenli pozitif aksiyon üretmesi iyi
değil, uyarı sinyalidir. Sağlıklı sonuç şu olmalıdır:

* `telefonla_konusma` ve `su_icme` dış kamera üzerinde doğrudan final event
  üretmemeli.
* `arkaya_bakma_candidate` yalnız candidate kalmalı.
* Temporal gate pozitifleri bastırmalı veya “visibility insufficient” kararına
  düşürmelidir.

Bu testten sonra `DACT-EXP-020C` çıktısı incelenip gerekirse:

1. daha iyi cabin crop seçimi,
2. driver visibility threshold,
3. confidence threshold,
4. temporal voting window,
5. dış kamera için ayrı specialist yaklaşımı

kararları alınacaktır.
