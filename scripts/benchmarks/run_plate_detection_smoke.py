#!/usr/bin/env python3
"""POCR-EXP-001 - License plate DETECTION smoke test (detector only, no OCR).

Bu script plaka/OCR hattının ikinci denemesinin ilk adımıdır. Amaç: ByteTrack ile
seçilmiş hedef aracın *tespit edildiği her karede* araç ROI'sini alıp üzerinde plaka
TESPİTİ yapmak ve iki farklı plaka detector'ını karşılaştırmak. OCR (metin okuma) bu
aşamada YOKTUR; o POCR-EXP-002/003'te eklenecektir.

Akış:
  1) yolo11n + ByteTrack ile her videoyu kare kare çalıştır, tüm track kutularını topla.
  2) Event skeleton'daki best_frame + bbox ile IoU eşleşmesi yaparak hedef track'i seç
     (track ID numarasına güvenmeden, daha sağlam).
  3) Hedef track'in göründüğü her karede araç ROI'sini crop'la.
  4) Her crop üzerinde seçili plaka detector'larını çalıştır (Ultralytics YOLO plate,
     HuggingFace YOLOS). Plaka bbox + confidence + latency kaydet.
  5) Orijinal kare üzerine hedef araç + plaka kutularını çizip her video için tam
     annotated video (_plate_detection.mp4) yaz; plaka kırpıntılarını OCR için sakla;
     küçük özet JSON + Markdown raporu üret. Ham görseller/videolar ignore'lu runs/ altında.

Bu script offline/internet yok ortamda model indiremez. Plaka model ağırlıkları MacBook
tarafında bulunmalıdır (aşağıdaki README'ye bakın).

Çalıştırma (MacBook .venv-yolo):
  python scripts/benchmarks/run_plate_detection_smoke.py \
      --plate-yolo-weights models/checkpoints/plate/license_plate_detector.pt \
      --models yolo yolos

Ham görseller KVKK gereği Git'e eklenmez (runs/ ignore'lu). Yalnız özet JSON/MD tutulur.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_DETECTOR = ROOT / "yolo11n.pt"
DEFAULT_RUNS_DIR = ROOT / "runs" / "plate_ocr" / "POCR-EXP-001-plate-detection"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_SUMMARY_NAME = "POCR-EXP-001-plate-detection-summary.json"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "pocr_exp_001_plate_detection_summary.md"

# Vehicle detector config. COCO pretrained modellerde class id'ler 2/3/5/7 iken,
# fine-tune edilen proje modellerinde class id'ler 0..N olabilir. Runtime'da
# model.names üzerinden çözülür; bu değer yalnız fallback içindir.
DEFAULT_COCO_VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
TARGET_VEHICLE_CLASS_NAMES = {"car", "motorcycle", "bus", "truck"}

# Plate detector overlay renkleri (BGR).
MODEL_COLORS = {"yolo": (0, 220, 0), "yolos": (255, 120, 0)}


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value))


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[int(round((len(ordered) - 1) * 0.95))], 3)


def iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def padded_clamped_bbox(bbox: list[float], width: int, height: int, padding_ratio: float) -> list[int]:
    x1, y1, x2, y2 = [float(v) for v in bbox]
    pad_x = max(0.0, x2 - x1) * padding_ratio
    pad_y = max(0.0, y2 - y1) * padding_ratio
    return [
        max(0, min(width, int(round(x1 - pad_x)))),
        max(0, min(height, int(round(y1 - pad_y)))),
        max(0, min(width, int(round(x2 + pad_x)))),
        max(0, min(height, int(round(y2 + pad_y)))),
    ]


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def resolve_vehicle_classes(detector_model: Any) -> tuple[list[int], dict[int, str]]:
    names = getattr(detector_model, "names", {}) or {}
    resolved: dict[int, str] = {}
    for raw_idx, raw_name in names.items():
        idx = int(raw_idx)
        name = str(raw_name).strip().lower()
        if name in TARGET_VEHICLE_CLASS_NAMES:
            resolved[idx] = name
    if resolved:
        return sorted(resolved.keys()), resolved
    return sorted(DEFAULT_COCO_VEHICLE_CLASSES.keys()), DEFAULT_COCO_VEHICLE_CLASSES


# --------------------------------------------------------------------------------------
# Plate detector adapters
# --------------------------------------------------------------------------------------
class PlateDetector:
    key: str = "base"

    def detect(self, crop_bgr: Any) -> list[dict[str, Any]]:
        """Return list of {"bbox_xyxy": [x1,y1,x2,y2] (crop coords), "confidence": float}."""
        raise NotImplementedError


class UltralyticsPlateDetector(PlateDetector):
    key = "yolo"

    def __init__(self, weights: Path, device: str, conf: float, imgsz: int) -> None:
        from ultralytics import YOLO

        if not weights.exists():
            raise FileNotFoundError(
                f"Plate YOLO weights bulunamadı: {weights}. README'deki indirme adımına bakın."
            )
        self.model = YOLO(str(weights))
        self.device = device
        self.conf = conf
        self.imgsz = imgsz
        self.model_ref = str(weights)

    def detect(self, crop_bgr: Any) -> list[dict[str, Any]]:
        results = self.model.predict(
            crop_bgr, conf=self.conf, imgsz=self.imgsz, device=self.device, verbose=False
        )
        out: list[dict[str, Any]] = []
        r = results[0]
        if r.boxes is not None and r.boxes.xyxy is not None:
            for box, score in zip(r.boxes.xyxy.cpu().tolist(), r.boxes.conf.cpu().tolist()):
                out.append({"bbox_xyxy": [round(float(v), 2) for v in box], "confidence": round(float(score), 4)})
        return out


class YolosPlateDetector(PlateDetector):
    key = "yolos"

    def __init__(self, model_name: str, device: str, threshold: float) -> None:
        import torch
        from transformers import AutoImageProcessor, AutoModelForObjectDetection

        self.torch = torch
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModelForObjectDetection.from_pretrained(model_name)
        self.device = device
        self.model.to(device)
        self.model.eval()
        self.threshold = threshold
        self.model_ref = model_name

    def detect(self, crop_bgr: Any) -> list[dict[str, Any]]:
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        inputs = self.processor(images=rgb, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            outputs = self.model(**inputs)
        h, w = crop_bgr.shape[:2]
        target_sizes = self.torch.tensor([[h, w]]).to(self.device)
        processed = self.processor.post_process_object_detection(
            outputs, threshold=self.threshold, target_sizes=target_sizes
        )[0]
        out: list[dict[str, Any]] = []
        for score, box in zip(processed["scores"].cpu().tolist(), processed["boxes"].cpu().tolist()):
            out.append({"bbox_xyxy": [round(float(v), 2) for v in box], "confidence": round(float(score), 4)})
        return out


def build_detectors(args: argparse.Namespace, vehicle_device: str) -> list[PlateDetector]:
    detectors: list[PlateDetector] = []
    if "yolo" in args.models:
        try:
            detectors.append(
                UltralyticsPlateDetector(
                    weights=args.plate_yolo_weights,
                    device=vehicle_device,
                    conf=args.plate_conf,
                    imgsz=args.plate_imgsz,
                )
            )
            print(f"[ok] YOLO plate detector yüklendi: {args.plate_yolo_weights}")
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] YOLO plate detector yüklenemedi -> {exc}")
    if "yolos" in args.models:
        try:
            yolos_device = args.yolos_device if args.yolos_device != "auto" else "cpu"
            detectors.append(
                YolosPlateDetector(model_name=args.yolos_model, device=yolos_device, threshold=args.plate_conf)
            )
            print(f"[ok] YOLOS plate detector yüklendi: {args.yolos_model} ({yolos_device})")
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] YOLOS plate detector yüklenemedi -> {exc}")
    return detectors


# --------------------------------------------------------------------------------------
# Tracking + target selection
# --------------------------------------------------------------------------------------
def load_target_specs(events_path: Path) -> dict[str, dict[str, Any]]:
    """source_video -> {best_frame, bbox_xyxy, track_id_label}."""
    data = json.loads(events_path.read_text(encoding="utf-8"))
    specs: dict[str, dict[str, Any]] = {}
    for event in data.get("events", []):
        source = event.get("source") or {}
        target = event.get("target_vehicle") or {}
        video = source.get("source_video")
        if not video:
            continue
        fw = target.get("frame_window") or {}
        specs[video] = {
            "best_frame": int(fw.get("best_frame") or 1),
            "bbox_xyxy": target.get("bbox_xyxy") or target.get("bbox"),
            "track_id_label": target.get("track_id"),
        }
    return specs


def track_video(detector_model: Any, video_path: Path, tracker: str, classes: list[int],
                class_labels: dict[int, str],
                conf: float, imgsz: int, device: str) -> tuple[dict[int, dict[int, dict[str, Any]]], dict[str, Any]]:
    """Return (tracks, meta). tracks[track_id][frame] = {bbox_xyxy, conf, cls}."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Video açılamadı: {video_path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)

    tracks: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        results = detector_model.track(
            frame, persist=True, tracker=tracker, classes=classes,
            conf=conf, imgsz=imgsz, device=device, verbose=False,
        )
        r = results[0]
        if r.boxes is not None and getattr(r.boxes, "is_track", False) and r.boxes.id is not None:
            ids = r.boxes.id.int().cpu().tolist()
            cls = r.boxes.cls.int().cpu().tolist()
            confs = r.boxes.conf.cpu().tolist()
            xyxy = r.boxes.xyxy.cpu().tolist()
            for tid, cid, score, box in zip(ids, cls, confs, xyxy):
                tracks[int(tid)][frame_idx] = {
                    "bbox_xyxy": [float(v) for v in box],
                    "conf": float(score),
                    "cls": class_labels.get(int(cid), str(cid)),
                }
    cap.release()
    return tracks, {"width": width, "height": height, "fps": round(fps, 3), "frames": frame_idx}


def select_target_track(tracks: dict[int, dict[int, dict[str, Any]]], spec: dict[str, Any]) -> tuple[int | None, str]:
    best_frame = spec.get("best_frame")
    ref_bbox = spec.get("bbox_xyxy")
    # 1) IoU eşleşmesi: best_frame'de skeleton bbox'ına en çok örtüşen track.
    if ref_bbox and best_frame:
        best_tid, best_iou = None, 0.0
        for tid, frames in tracks.items():
            obs = frames.get(int(best_frame))
            if not obs:
                continue
            score = iou(obs["bbox_xyxy"], [float(v) for v in ref_bbox])
            if score > best_iou:
                best_tid, best_iou = tid, score
        if best_tid is not None and best_iou >= 0.3:
            return best_tid, f"iou_match_best_frame={best_iou:.2f}"
    # 2) Fallback: en uzun ömürlü track.
    if tracks:
        longest = max(tracks.items(), key=lambda kv: len(kv[1]))
        return longest[0], "fallback_longest_track"
    return None, "no_tracks"


# --------------------------------------------------------------------------------------
# Per-video plate detection over target track frames
# --------------------------------------------------------------------------------------
def process_video(video_path: Path, spec: dict[str, Any], detector_model: Any,
                  detectors: list[PlateDetector], args: argparse.Namespace,
                  device: str, vehicle_classes: list[int], vehicle_class_labels: dict[int, str]) -> dict[str, Any]:
    print(f"\n=== {video_path.name} : tracking ===")
    tracks, meta = track_video(
        detector_model, video_path, args.tracker, vehicle_classes, vehicle_class_labels,
        args.conf, args.imgsz, device,
    )
    target_tid, reason = select_target_track(tracks, spec)
    if target_tid is None:
        return {"video": video_path.name, "status": "failed", "failure_reason": "no_target_track",
                "frame_meta": meta, "models": {}}
    target_frames = sorted(tracks[target_tid].keys())
    if args.frame_stride > 1:
        target_frames = target_frames[:: args.frame_stride]
    print(f"hedef track id={target_tid} ({reason}), {len(target_frames)} kare "
          f"(stride={args.frame_stride}) - plaka tespiti başlıyor...")

    runs_dir = args.runs_dir
    target_all = sorted(tracks[target_tid].keys())
    run_set = set(target_all[:: args.frame_stride]) if args.frame_stride > 1 else set(target_all)
    target_set = set(target_all)

    per_model: dict[str, dict[str, Any]] = {
        d.key: {"frames_with_plate": 0, "total_plates": 0, "confidences": [], "latencies_ms": [],
                "model_ref": getattr(d, "model_ref", d.key), "plate_crop_dir": rel(runs_dir / "plates" / d.key / video_path.stem)}
        for d in detectors
    }
    per_frame_records: list[dict[str, Any]] = []

    # Tam çözünürlüklü annotated video writer (orijinal kare üzerine kutular çizilir).
    width, height = meta["width"], meta["height"]
    out_w, out_h = max(1, int(width * args.video_scale)), max(1, int(height * args.video_scale))
    annot_dir = runs_dir / "annotated"
    annot_dir.mkdir(parents=True, exist_ok=True)
    model_suffix = "-".join(d.key for d in detectors)
    annot_path = annot_dir / f"{video_path.stem}_plate_detection_{model_suffix}.mp4"
    writer = cv2.VideoWriter(str(annot_path), cv2.VideoWriter_fourcc(*"mp4v"),
                             float(meta["fps"]), (out_w, out_h))

    cap = cv2.VideoCapture(str(video_path))
    fnum = 0
    total_run = len(run_set)
    processed = 0
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        fnum += 1
        if fnum in target_set:
            vbox = tracks[target_tid][fnum]["bbox_xyxy"]
            vx1, vy1, vx2, vy2 = [int(round(v)) for v in vbox]
            cx1, cy1, cx2, cy2 = padded_clamped_bbox(vbox, width, height, args.padding_ratio)
            crop = frame[cy1:cy2, cx1:cx2].copy() if (fnum in run_set and cx2 > cx1 and cy2 > cy1) else None
            cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), (255, 255, 255), 2)
            cv2.putText(frame, f"target TRK-{target_tid:03d}", (vx1, max(0, vy1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            if crop is not None:
                processed += 1
                if processed % 25 == 0 or processed == total_run:
                    print(f"  {video_path.name}: {processed}/{total_run} kare işlendi")
                frame_rec: dict[str, Any] = {"frame": fnum, "models": {}}
                for d in detectors:
                    t0 = time.perf_counter()
                    try:
                        dets = d.detect(crop)
                    except Exception as exc:  # noqa: BLE001
                        frame_rec["models"][d.key] = {"error": str(exc)}
                        continue
                    latency = (time.perf_counter() - t0) * 1000.0
                    per_model[d.key]["latencies_ms"].append(latency)
                    color = MODEL_COLORS.get(d.key, (0, 0, 255))
                    best_conf = None
                    for i, det in enumerate(dets):
                        bx1, by1, bx2, by2 = [int(round(v)) for v in det["bbox_xyxy"]]
                        # crop koordinatlarını tam kare koordinatına taşı
                        fx1, fy1, fx2, fy2 = cx1 + bx1, cy1 + by1, cx1 + bx2, cy1 + by2
                        cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), color, 2)
                        cv2.putText(frame, f"{d.key} {det['confidence']:.2f}", (fx1, max(0, fy1 - 4)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
                        per_model[d.key]["confidences"].append(det["confidence"])
                        best_conf = det["confidence"] if best_conf is None else max(best_conf, det["confidence"])
                        px1, py1 = max(0, bx1), max(0, by1)
                        px2, py2 = min(crop.shape[1], bx2), min(crop.shape[0], by2)
                        if px2 > px1 and py2 > py1:
                            pdir = runs_dir / "plates" / d.key / video_path.stem
                            pdir.mkdir(parents=True, exist_ok=True)
                            cv2.imwrite(str(pdir / f"frame_{fnum:06d}_plate{i}.jpg"),
                                        crop[py1:py2, px1:px2], [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    if dets:
                        per_model[d.key]["frames_with_plate"] += 1
                        per_model[d.key]["total_plates"] += len(dets)
                    frame_rec["models"][d.key] = {
                        "plate_count": len(dets),
                        "best_confidence": best_conf,
                        "latency_ms": round(latency, 3),
                        "vehicle_bbox_xyxy_frame": [round(float(v), 2) for v in vbox],
                        "vehicle_roi_xyxy_frame": [cx1, cy1, cx2, cy2],
                        "vehicle_roi_origin_xy": [cx1, cy1],
                        "detections": [
                            {
                                "bbox_xyxy_crop": det["bbox_xyxy"],
                                "bbox_xyxy_frame": [
                                    round(float(cx1 + det["bbox_xyxy"][0]), 2),
                                    round(float(cy1 + det["bbox_xyxy"][1]), 2),
                                    round(float(cx1 + det["bbox_xyxy"][2]), 2),
                                    round(float(cy1 + det["bbox_xyxy"][3]), 2),
                                ],
                                "center_xy_frame": [
                                    round(float(cx1 + (det["bbox_xyxy"][0] + det["bbox_xyxy"][2]) / 2.0), 2),
                                    round(float(cy1 + (det["bbox_xyxy"][1] + det["bbox_xyxy"][3]) / 2.0), 2),
                                ],
                                "width_px": round(float(det["bbox_xyxy"][2] - det["bbox_xyxy"][0]), 2),
                                "height_px": round(float(det["bbox_xyxy"][3] - det["bbox_xyxy"][1]), 2),
                                "confidence": det["confidence"],
                            }
                            for det in dets
                        ],
                    }
                per_frame_records.append(frame_rec)
        out_frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_AREA) if args.video_scale != 1.0 else frame
        writer.write(out_frame)

    cap.release()
    writer.release()
    print(f"  annotated video: {rel(annot_path)}")

    models_summary = {}
    n = len(run_set)
    for key, agg in per_model.items():
        models_summary[key] = {
            "model_ref": agg["model_ref"],
            "run_frames": n,
            "target_track_frames": len(target_set),
            "frames_with_plate": agg["frames_with_plate"],
            "plate_detection_rate": round(agg["frames_with_plate"] / n, 4) if n else 0.0,
            "total_plates": agg["total_plates"],
            "mean_confidence": mean(agg["confidences"]),
            "max_confidence": round(max(agg["confidences"]), 4) if agg["confidences"] else None,
            "mean_latency_ms": mean(agg["latencies_ms"]),
            "p95_latency_ms": p95(agg["latencies_ms"]),
            "plate_crop_dir": agg["plate_crop_dir"],
        }

    return {
        "video": video_path.name,
        "status": "completed",
        "failure_reason": None,
        "target_track_id": target_tid,
        "target_track_selection_reason": reason,
        "target_frame_count": n,
        "frame_meta": meta,
        "annotated_video": rel(annot_path),
        "models": models_summary,
        "per_frame": per_frame_records if args.keep_per_frame else "omitted_use_--keep-per-frame",
    }


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {summary['experiment_id']} Plate Detection Smoke Test (detector-only)",
        "",
        f"Tarih: {summary['generated_at_utc']}",
        "",
        "## Amaç",
        "",
        "Hedef aracın tespit edildiği her karede araç ROI'si üzerinde plaka TESPİTİ yapmak ve "
        "seçili plaka model(ler)ini değerlendirmek. OCR (metin okuma) bu aşamada yoktur.",
        "",
        "## Konfigürasyon",
        "",
        f"* Araç detector: `{summary['vehicle_detector']}` / tracker `{summary['tracker']}`",
        f"* Plaka modelleri: `{', '.join(summary['models_requested'])}`",
        f"* ROI padding: `{summary['padding_ratio']}`  | plate conf: `{summary['plate_conf']}`",
        "",
        "## Sonuç (model × video)",
        "",
        "| Video | Model | Hedef Kare | Plakalı Kare | Tespit Oranı | Maks Conf | Ort. Latency (ms) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for v in summary["videos"]:
        if v["status"] != "completed":
            lines.append(f"| {v['video']} | - | - | - | FAILED: {v['failure_reason']} | - | - |")
            continue
        for key, m in v["models"].items():
            lines.append(
                f"| {v['video']} | {key} | {m['run_frames']} | {m['frames_with_plate']} | "
                f"{m['plate_detection_rate']} | {m['max_confidence']} | {m['mean_latency_ms']} |"
            )
    lines += [
        "",
        "## Manuel İnceleme",
        "",
        f"* Annotated videolar (orijinal kare üzerine kutular, ignore'lu): `{summary['runs_dir']}/annotated/<video>_plate_detection_<model>.mp4`",
        f"* Plaka kırpıntıları (ignore'lu): `{summary['runs_dir']}/plates/<model>/<video>/`",
        "* Manuel review şablonu: `testing/templates/manual_plate_ocr_review.csv`",
        "",
        "## Notlar",
        "",
        "* Bu çalışma final plaka okuma doğruluğu iddiası kurmaz; detector smoke test'tir.",
        "* Ham plaka görselleri kişisel veri sayılır ve Git'e eklenmez.",
        "* Tespit oranı yüksek/güveni yüksek + yan profilde false positive üretmeyen model tercih edilir; "
        "nihai karar kullanıcının manuel incelemesiyle verilecektir.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="POCR-EXP-001 plate detection smoke test (no OCR).")
    p.add_argument("--experiment-id", default="POCR-EXP-001")
    p.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    p.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    p.add_argument("--videos", type=Path, nargs="*", default=None, help="Belirli videolar (varsayılan: skeleton'daki tüm hedefler).")
    p.add_argument("--detector", type=Path, default=DEFAULT_DETECTOR, help="Araç detector ağırlığı (yolo11n.pt).")
    p.add_argument("--tracker", default="bytetrack.yaml")
    p.add_argument("--device", default="auto", help="Araç+YOLO plate cihazı (auto/mps/cuda/cpu).")
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--conf", type=float, default=0.25, help="Araç detector confidence.")
    # plate models
    p.add_argument("--models", nargs="+", default=["yolo", "yolos"], choices=["yolo", "yolos"])
    p.add_argument("--plate-yolo-weights", type=Path, default=ROOT / "models" / "checkpoints" / "plate" / "license_plate_detector.pt")
    p.add_argument("--yolos-model", default="nickmuchi/yolos-small-finetuned-license-plate-detection")
    p.add_argument("--yolos-device", default="cpu", help="YOLOS cihazı (transformers); mps'te sorun olabilir.")
    p.add_argument("--plate-conf", type=float, default=0.25)
    p.add_argument("--plate-imgsz", type=int, default=640)
    p.add_argument("--padding-ratio", type=float, default=0.10, help="Araç ROI etrafına eklenen pay.")
    p.add_argument("--frame-stride", type=int, default=1, help="Hedef track karelerinden her N'inciyi işle (YOLOS CPU'da yavaşsa 5 yap).")
    # outputs
    p.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    p.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    p.add_argument("--summary-name", default=None, help="Özet JSON dosya adı. Boşsa experiment-id + model suffix kullanılır.")
    p.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    p.add_argument("--video-scale", type=float, default=1.0, help="Annotated video çıktı ölçeği (1.0=orijinal çözünürlük, 0.5=yarı).")
    p.add_argument("--keep-per-frame", action="store_true", help="Per-frame kayıtları özet JSON'a göm (büyük).")
    return p.parse_args()


def main() -> None:
    from ultralytics import YOLO

    args = parse_args()
    args.runs_dir = args.runs_dir.resolve()
    device = resolve_device(args.device)
    print(f"Cihaz (araç+yolo plate): {device}")

    specs = load_target_specs(args.events.resolve())
    if args.videos:
        videos = [v.resolve() for v in args.videos]
    else:
        videos = [(args.videos_dir / name).resolve() for name in specs.keys()]

    detector_model = YOLO(str(args.detector.resolve()))
    vehicle_classes, vehicle_class_labels = resolve_vehicle_classes(detector_model)
    print(f"Vehicle classes: {vehicle_class_labels}")
    detectors = build_detectors(args, device)
    if not detectors:
        raise SystemExit("Hiç plaka detector yüklenemedi. README'deki kurulum/indirme adımlarına bakın.")

    video_results = []
    for video in videos:
        if not video.exists():
            video_results.append({"video": video.name, "status": "failed", "failure_reason": "video_not_found", "models": {}})
            continue
        spec = specs.get(video.name, {"best_frame": 1, "bbox_xyxy": None, "track_id_label": None})
        video_results.append(process_video(video, spec, detector_model, detectors, args, device,
                                           vehicle_classes, vehicle_class_labels))

    summary = {
        "experiment_id": args.experiment_id,
        "stage": "plate_detection_smoke_test",
        "ocr": "not_in_scope_this_stage",
        "generated_at_utc": now_utc(),
        "vehicle_detector": rel(args.detector.resolve()),
        "vehicle_classes": vehicle_class_labels,
        "tracker": args.tracker,
        "models_requested": args.models,
        "models_loaded": [d.key for d in detectors],
        "padding_ratio": args.padding_ratio,
        "plate_conf": args.plate_conf,
        "input_events": rel(args.events.resolve()),
        "videos_dir": rel(args.videos_dir.resolve()),
        "runs_dir": rel(args.runs_dir),
        "videos": video_results,
        "manual_review_template": "testing/templates/manual_plate_ocr_review.csv",
        "notes": [
            "Detector-only smoke test; OCR yok.",
            "Ham plaka/araç görselleri runs/ altında ignore'ludur, commit edilmez.",
            "Hedef track IoU eşleşmesiyle seçilir; track ID numarasına güvenilmez.",
        ],
    }

    suffix = "-".join(d.key for d in detectors)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    summary_name = args.summary_name or f"{args.experiment_id}-plate-detection-{suffix}-summary.json"
    summary_path = args.artifact_dir / summary_name
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path = args.report.with_name(f"{args.report.stem}_{suffix}{args.report.suffix}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(summary), encoding="utf-8")

    print("\n=== ÖZET ===")
    print(json.dumps({"summary": rel(summary_path), "report": rel(report_path),
                      "videos": [{"video": v["video"], "status": v["status"],
                                  "models": {k: m.get("plate_detection_rate") for k, m in v.get("models", {}).items()}}
                                 for v in video_results]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
