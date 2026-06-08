# Vehicle Detection Deep Research Sources

Bu dosya araç tespiti derin araştırmasında kullanılan kaynakları gerçek URL'lerle listeler. Kaynaklar final model kararı vermeden önce yeniden kontrol edilmelidir.

## Model Families

| Source | URL | Kullanım |
|---|---|---|
| Ultralytics YOLO11 documentation | https://docs.ultralytics.com/models/yolo11/ | YOLO11n/s başlangıç adayları, COCO metrikleri, kullanım örnekleri, lisans notu |
| Ultralytics YOLOv10 documentation | https://docs.ultralytics.com/models/yolov10/ | YOLOv10n/s düşük latency challenger, NMS-free yaklaşım, lisans notu |
| Ultralytics YOLOv8 documentation | https://docs.ultralytics.com/models/yolov8/ | Stabil fallback baseline |
| Ultralytics RT-DETR documentation | https://docs.ultralytics.com/models/rtdetr/ | Transformer challenger ve export desteği |
| Ultralytics export documentation | https://docs.ultralytics.com/modes/export/ | ONNX, OpenVINO, TensorRT, CoreML, TFLite, NCNN, QNN, ExecuTorch export hedefleri |
| YOLOv6 GitHub repository | https://github.com/meituan/YOLOv6 | YOLOv6/YOLOv6Lite adayları, deploy notları, GPL-3.0 lisansı |
| YOLOv6 paper | https://arxiv.org/abs/2301.05586 | YOLOv6 teknik referansı |
| NanoDet GitHub repository | https://github.com/RangiLyu/nanodet | Mobil fallback adayı, Android/ncnn/MNN/OpenVINO notları |
| YOLOv10 paper | https://arxiv.org/abs/2405.14458 | NMS-free YOLOv10 teknik referansı |

## Dataset Sources

| Source | URL | Kullanım |
|---|---|---|
| BDD100K GitHub repository | https://github.com/bdd100k/bdd100k | Road-domain fine-tune, 100K video ve çok görevli driving dataset kaynağı |
| BDD100K CVPR 2020 paper | https://openaccess.thecvf.com/content_CVPR_2020/papers/Yu_BDD100K_A_Diverse_Driving_Dataset_for_Heterogeneous_Multitask_Learning_CVPR_2020_paper.pdf | BDD100K akademik referans |
| BDD100K arXiv | https://arxiv.org/abs/1805.04687 | BDD100K alternatif akademik referans |
| UA-DETRAC arXiv | https://arxiv.org/abs/1511.04136 | Fixed-camera detection/tracking, 100 video, 140K+ frame, occlusion/weather annotations |
| UA-DETRAC ScienceDirect | https://www.sciencedirect.com/science/article/pii/S1077314220300035 | UA-DETRAC journal reference |
| KITTI official benchmark | https://www.cvlibs.net/datasets/kitti/ | External dashcam-style sanity test |
| CityFlow CVPR 2019 paper | https://openaccess.thecvf.com/content_CVPR_2019/html/Tang_CityFlow_A_City-Scale_Benchmark_for_Multi-Target_Multi-Camera_Vehicle_Tracking_and_CVPR_2019_paper.html | Fixed-camera / traffic camera robustness test |
| CityFlow arXiv | https://arxiv.org/abs/1903.09254 | CityFlow alternative academic reference |

## License Notes

* Ultralytics YOLO11/YOLOv10/YOLOv8: AGPL-3.0 / Enterprise licensing should be treated as a project risk before productization.
* YOLOv6: GPL-3.0 according to the official repository.
* NanoDet: license must be verified from the official repository before use.
* Dataset license and redistribution terms must be verified separately before downloading, training, or publishing derived artifacts.

## Repo Rule

Do not commit downloaded datasets, raw frames, evidence images, model checkpoints, or exported model binaries to this repository.
