# Kaynaklar

Doğrulama tarihi: 2026-06-14

* OpenCV Optical Flow tutorial:
  https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html
  * Sparse Lucas-Kanade için `cv.calcOpticalFlowPyrLK`.
  * Pyramid yaklaşımı büyük hareketleri daha sağlam izlemek için kullanılır.
* ViTPose-B model kaynağı:
  https://huggingface.co/usyd-community/vitpose-base-simple

OpenCV sayfası 2026-06-14 tarihinde tarayıcı ile doğrulandı. ViTPose model
referansı mevcut pose araştırma hattıyla aynıdır; checkpoint çalışma anında
Hugging Face cache'ine indirilir.
