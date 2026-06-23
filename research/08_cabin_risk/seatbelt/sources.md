# Seatbelt Specialist Kaynak Notları

## Repo İçi Kanıtlar

* Seçili torso girdisi:
  `POSE-EXP-009-vitpose_b_final_torso_baseline_v1-summary.json`
* Seatbelt smoke sonucu:
  `SEATBELT-EXP-001-opencv_diagonal_belt_evidence_v1-summary.json`
* Manuel review şablonu:
  `testing/templates/manual_seatbelt_review.csv`

## Dış Kaynak Kararı

Doğrulama tarihi: 2026-06-14.

* Robust Seatbelt Detection and Usage Recognition for Driver Monitoring Systems:
  https://arxiv.org/abs/2203.00810
  * Düşük kontrast, el/saç örtülmesi, blur, IR ve geniş açı distorsiyonunu temel
    problem olarak tanımlar.
  * Local predictor + global assembler + shape modeling yaklaşımı kullanır.
  * CC BY-NC-SA 4.0 makale lisansı; yeniden kullanılabilir checkpoint
    doğrulanmadı.
* NADS-Net:
  https://arxiv.org/abs/1910.03695
  * Driver/passenger pose ve seatbelt detection için özel FPN/multi-head mimari.
  * 100 sürücü ve 50 oturumda farklı illumination koşullarını ölçer.
  * Açık checkpoint/veri indirme bağlantısı doğrulanmadı.
* FeatEnHancer:
  https://arxiv.org/abs/2308.03594
  * Düşük ışıkta yalnız görsel iyileştirme yerine downstream task loss ile
    feature enhancement yaklaşımını destekler.
* RISEF YOLO11s seatbelt classifier:
  https://huggingface.co/RISEF/yolov11s-seatbelt
  * Binary classifier, AGPL-3.0.
  * Eğitim kaynağı Kaggle windshield-view verisidir.
  * Model kartı yaklaşık 15 kat sınıf dengesizliği ile gece, tinted glass ve
    yoğun glare eksikliğini açıkça belirtir.
  * Pretrained smoke challenger olarak kullanılabilir; final baseline değildir.
* Safe-Drive-TN Seat-Belt-Classification:
  https://huggingface.co/Safe-Drive-TN/Seat-Belt-Classification
  * MIT etiketi vardır ancak model kartı yoktur.
  * Depoda şüpheli/unsafe pickle uyarıları bulunduğu için challenger olarak
    seçilmedi.

Genel pose modellerinin kemer durumunu güvenilir biçimde çözdüğü
varsayılmamıştır. Model seçimi kontrollü veri, lisans kaydı ve ölçülebilir
classifier/detector benchmark'ından sonra yapılacaktır.

Sonraki telefon/el fazları için planlanan resmi kaynaklar:

* MediaPipe Hand Landmarker:
  https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python
* MMPose RTMPose projeleri:
  https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose
* Ultralytics COCO:
  https://docs.ultralytics.com/datasets/detect/coco
