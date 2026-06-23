# Driver Pose Sources

Doğrulama tarihi: 2026-06-13

## Resmi Kaynaklar

* Ultralytics Pose Estimation:
  https://docs.ultralytics.com/tasks/pose/
  * Pose modellerinin `-pose` suffix kullandığı, COCO pretrained modellerin 17
    keypoint ürettiği ve `result.boxes` ile `result.keypoints` API'leri doğrulandı.
* MediaPipe Pose Landmarker overview:
  https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker
  * Lite/Full/Heavy bundle, 33 landmark, normalized/world coordinates ve
    `num_poses` seçenekleri doğrulandı.
* MediaPipe Pose Landmarker Python:
  https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python
  * Python Tasks API, VIDEO mode, timestamp gereksinimi ve tracking davranışı
    doğrulandı.
* MediaPipe license:
  https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE
* Ultralytics license:
  https://github.com/ultralytics/ultralytics/blob/main/LICENSE
* RTMPose official project:
  https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose
  * RTMPose-L Body7 384x288 için COCO AP `78.3`, Body8 PCK@0.1 `95.56`,
    AUC `74.38`, ONNX model paketi ve top-down inference seçenekleri doğrulandı.
  * Body7'nin yedi veri kümesinden oluştuğu, Body8'in OCHuman'ı değerlendirmeye
    eklediği doğrulandı; OCHuman eğitim verisi olarak kaydedilmedi.
  * RTMW-L 384x288 Cocktail14 modelinin 133 COCO-WholeBody keypoint, Whole AP
    `70.1`, Whole AR `78.0` ürettiği doğrulandı.
  * Cocktail14 eğitim kapsamının UBody ve InterHand dahil 14 veri kümesi olduğu
    doğrulandı.
* DWPose official repository:
  https://github.com/IDEA-Research/DWPose
  * Whole-body distillation yaklaşımı, COCO+UBody eğitimi ve 384x288 modelin
    body/hand/whole-body sonuçları doğrulandı.
* RTMPose official ONNXRuntime example:
  https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose/examples/onnxruntime
  * Saf Python/OpenCV/ONNXRuntime preprocess, SimCC decode ve rescale akışı
    doğrulandı.
* MMPose installation:
  https://mmpose.readthedocs.io/en/latest/installation.html
  * MMPose 1.x/MMCV 2.x eşleşmesi ve CPU/macOS desteği doğrulandı.
* RTMO official project:
  https://github.com/open-mmlab/mmpose/tree/main/projects/rtmo
  * Tek-aşamalı, dedektörsüz ve özellikle dört kişiden fazla sahnelerde top-down
    yaklaşıma göre hız avantajı sunduğu doğrulandı.
* ViTPose official repository:
  https://github.com/ViTAE-Transformer/ViTPose
  * ViTPose-B COCO AP `75.8`, OCHuman AP `88.0`, Apache-2.0 lisans ve eski
    PyTorch 1.9/MMCV 1.3.9 kurulum gereksinimi doğrulandı.
* MMPose license:
  https://github.com/open-mmlab/mmpose/blob/main/LICENSE

## Web Doğrulama Kaydı

* Playwright ile RTMPose, RTMO ve MMPose installation sayfaları; model tabloları,
  dataset kapsamı ve deployment seçenekleri doğrulandı.
* Puppeteer ile ViTPose sonuç/kurulum tablosu, MMPose Apache-2.0 lisansı ve resmi
  RTMPose ONNXRuntime örnek kodu doğrulandı. DWPose resmi README'si Puppeteer ile
  ham GitHub içeriği üzerinden doğrulandı.
* Doğrulama zamanı: 13 Haziran 2026, Europe/Istanbul.
* Ekran görüntüsü alınmadı; metin ve URL doğrulaması kullanıldı.
