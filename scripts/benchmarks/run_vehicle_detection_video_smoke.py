#!/usr/bin/env python3
"""Run a local vehicle detection smoke test on the three dark videos.

Large annotated videos stay under ignored `runs/` paths. Small JSON/Markdown
summaries are written to tracked benchmark/report locations.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import torch
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS = (
    ROOT
    / "models"
    / "checkpoints"
    / "vehicle_detection"
    / "VD-EXP-002-GENERAL-YOLO11N-best.pt"
)
DEFAULT_VIDEOS = [ROOT / "Test" / f"video_{idx}.mp4" for idx in range(1, 4)]
DEFAULT_RUNS_DIR = ROOT / "runs" / "vehicle_detection" / "VD-EXP-002-dark-smoke"
DEFAULT_ARTIFACT = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "VD-EXP-002-general-yolo11n-dark-smoke-summary.json"
)
DEFAULT_REPORT = ROOT / "testing" / "reports" / "vd_exp_002_dark_video_smoke_test_summary.md"


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * 0.95))
    return round(float(ordered[idx]), 3)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(statistics.fmean(values)), 3)


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def video_metadata(video_path: Path) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    try:
        return {
            "frame_count_reported": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0),
            "fps": round(float(cap.get(cv2.CAP_PROP_FPS) or 0.0), 3),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
        }
    finally:
        cap.release()


def find_annotated_video(output_dir: Path, video_stem: str) -> str | None:
    candidates: list[Path] = []
    for suffix in ("*.mp4", "*.avi", "*.mov", "*.mkv"):
        candidates.extend(output_dir.rglob(suffix))
    if not candidates:
        return None
    candidates.sort(key=lambda path: (video_stem not in path.stem, len(path.parts), path.name))
    return str(candidates[0].relative_to(ROOT))


def summarize_boxes(result: Any, class_counts: Counter[str], confs: list[float]) -> int:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return 0
    names = getattr(result, "names", {}) or {}
    count = 0
    cls_values = boxes.cls.detach().cpu().tolist() if boxes.cls is not None else []
    conf_values = boxes.conf.detach().cpu().tolist() if boxes.conf is not None else []
    for cls_id, conf in zip(cls_values, conf_values):
        class_name = str(names.get(int(cls_id), int(cls_id)))
        class_counts[class_name] += 1
        confs.append(float(conf))
        count += 1
    return count


def run_video(
    model: YOLO,
    video_path: Path,
    runs_dir: Path,
    device: str,
    imgsz: int,
    conf: float,
    classes: list[int] | None,
    save_annotated: bool,
    max_frames: int | None,
) -> dict[str, Any]:
    meta = video_metadata(video_path)
    output_name = video_path.stem
    video_output_dir = runs_dir / output_name
    video_output_dir.mkdir(parents=True, exist_ok=True)

    class_counts: Counter[str] = Counter()
    confs: list[float] = []
    pipeline_ms: list[float] = []
    inference_ms: list[float] = []
    frames_processed = 0
    frames_with_detections = 0
    total_detections = 0
    start = time.perf_counter()

    predictions = model.predict(
        source=str(video_path),
        stream=True,
        save=save_annotated,
        project=str(runs_dir),
        name=output_name,
        exist_ok=True,
        imgsz=imgsz,
        conf=conf,
        classes=classes,
        device=device,
        verbose=False,
    )

    for result in predictions:
        frames_processed += 1
        speed = getattr(result, "speed", {}) or {}
        frame_ms = sum(float(speed.get(key, 0.0)) for key in ("preprocess", "inference", "postprocess"))
        if frame_ms > 0:
            pipeline_ms.append(frame_ms)
        if "inference" in speed:
            inference_ms.append(float(speed["inference"]))

        detected = summarize_boxes(result, class_counts, confs)
        total_detections += detected
        if detected:
            frames_with_detections += 1
        if max_frames is not None and frames_processed >= max_frames:
            break

    wall_seconds = time.perf_counter() - start
    return {
        "video": str(video_path.relative_to(ROOT)),
        **meta,
        "frames_processed": frames_processed,
        "frames_with_detections": frames_with_detections,
        "total_detections": total_detections,
        "detections_by_class": dict(sorted(class_counts.items())),
        "mean_confidence": mean(confs),
        "mean_pipeline_ms": mean(pipeline_ms),
        "p95_pipeline_ms": p95(pipeline_ms),
        "mean_inference_ms": mean(inference_ms),
        "p95_inference_ms": p95(inference_ms),
        "wall_seconds": round(wall_seconds, 3),
        "effective_fps": round(frames_processed / wall_seconds, 3) if wall_seconds else None,
        "annotated_video_uri": find_annotated_video(video_output_dir, output_name)
        if save_annotated
        else None,
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# VD-EXP-002 Dark Video Smoke Test Summary",
        "",
        "## Kapsam",
        "",
        "Bu rapor, fine-tuned `vehicle_detector_general` checkpoint'i ile lokal dark video",
        "smoke test sonucunu kaydetmek icindir. Bu test final model dogrulugu iddiasi",
        "degildir; FTR raporunda `manual qualitative review` ve pipeline kullanilabilirligi",
        "kaniti olarak kullanilmalidir.",
        "",
        "## Kosu Bilgisi",
        "",
        f"* Weights: `{summary['weights']}`",
        f"* Device: `{summary['device']}`",
        f"* Image size: `{summary['imgsz']}`",
        f"* Confidence threshold: `{summary['conf']}`",
        f"* Classes: `{summary['classes']}`",
        f"* Annotated output root: `{summary['runs_dir']}`",
        "",
        "## Video Sonuclari",
        "",
        "| Video | Frames | Detected Frames | Detections | Classes | Mean Conf | Mean ms | p95 ms | FPS | Annotated |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in summary["videos"]:
        classes = ", ".join(f"{key}:{value}" for key, value in row["detections_by_class"].items()) or "-"
        lines.append(
            "| {video} | {frames_processed} | {frames_with_detections} | {total_detections} | "
            "{classes} | {mean_confidence} | {mean_pipeline_ms} | {p95_pipeline_ms} | "
            "{effective_fps} | {annotated} |".format(
                video=row["video"],
                frames_processed=row["frames_processed"],
                frames_with_detections=row["frames_with_detections"],
                total_detections=row["total_detections"],
                classes=classes,
                mean_confidence=row["mean_confidence"],
                mean_pipeline_ms=row["mean_pipeline_ms"],
                p95_pipeline_ms=row["p95_pipeline_ms"],
                effective_fps=row["effective_fps"],
                annotated=f"`{row['annotated_video_uri']}`" if row["annotated_video_uri"] else "-",
            )
        )
    lines.extend(
        [
            "",
            "## Rapor Notu",
            "",
            "* Bu smoke test 3 lokal dark video uzerinde gorsel kontrol icin uretilir.",
            "* Annotated videolar `runs/` altindadir ve Git'e eklenmez.",
            "* Manuel review tamamlanmadan accuracy, recall veya hukuki kanit iddiasi kurulmaz.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--videos", type=Path, nargs="*", default=DEFAULT_VIDEOS)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--classes", type=int, nargs="*", default=[0, 1, 2, 3])
    parser.add_argument("--max-frames", type=int, default=0, help="0 means process full video.")
    parser.add_argument("--no-save-annotated", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    weights = args.weights.resolve()
    if not weights.exists():
        raise FileNotFoundError(
            f"Fine-tuned weights not found: {weights}\n"
            "Copy the Drive checkpoint to this path or pass --weights.\n"
            "Expected Drive source: "
            "/content/drive/MyDrive/anomali-road-safety-ai/runs/vehicle_detection/"
            "VD-EXP-002/train/VD-EXP-002-GENERAL-YOLO11N/weights/best.pt"
        )
    missing_videos = [str(path) for path in args.videos if not path.exists()]
    if missing_videos:
        raise FileNotFoundError("Missing video files:\n" + "\n".join(missing_videos))

    device = resolve_device(args.device)
    model = YOLO(str(weights))
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.artifact.parent.mkdir(parents=True, exist_ok=True)

    videos = [
        run_video(
            model=model,
            video_path=video.resolve(),
            runs_dir=args.runs_dir,
            device=device,
            imgsz=args.imgsz,
            conf=args.conf,
            classes=args.classes or None,
            save_annotated=not args.no_save_annotated,
            max_frames=args.max_frames or None,
        )
        for video in args.videos
    ]
    summary = {
        "experiment_id": "VD-EXP-002-dark-video-smoke",
        "weights": str(weights.relative_to(ROOT)) if weights.is_relative_to(ROOT) else str(weights),
        "device": device,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "classes": args.classes,
        "runs_dir": str(args.runs_dir.relative_to(ROOT)) if args.runs_dir.is_relative_to(ROOT) else str(args.runs_dir),
        "videos": videos,
    }
    args.artifact.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary, args.report)
    print(f"Wrote JSON summary: {args.artifact}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()
