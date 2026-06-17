#!/usr/bin/env python3
"""Run local condition-profile classifier smoke tests on video files."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKPOINT = ROOT / "models" / "checkpoints" / "condition_profile" / "COND-EXP-001-mobilenet_v3_small-best.pt"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_OUTPUT = ROOT / "models" / "benchmarks" / "artifacts" / "COND-EXP-001-local-dark-video-smoke-summary.json"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "cond_exp_001_local_dark_video_smoke_test.md"


DEFAULT_CONDITION_CLASSES = [
    "day_clear",
    "night_low_light",
    "low_light_transition",
    "rain",
    "fog_low_visibility",
    "adverse_other",
    "unknown",
]


def build_model(backbone: str, num_classes: int) -> nn.Module:
    if backbone == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    if backbone == "resnet18":
        model = models.resnet18(weights=None)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model
    raise ValueError(f"Unsupported backbone: {backbone}")


def load_checkpoint(path: Path, device: torch.device) -> tuple[nn.Module, list[str], dict]:
    checkpoint = torch.load(path, map_location=device)
    backbone = checkpoint.get("backbone", "mobilenet_v3_small")
    classes = checkpoint.get("condition_classes") or DEFAULT_CONDITION_CLASSES
    model = build_model(backbone, len(classes))
    state_dict = checkpoint.get("state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model, list(classes), checkpoint


def frame_transform(image_size: int) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def classify_frame(model: nn.Module, frame_bgr: np.ndarray, tfm, device: torch.device, classes: list[str]) -> tuple[str, float, dict[str, float]]:
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    tensor = tfm(Image.fromarray(frame_rgb)).unsqueeze(0).to(device)
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1).squeeze(0).cpu().numpy()
    idx = int(probs.argmax())
    score_map = {label: float(score) for label, score in zip(classes, probs)}
    return classes[idx], float(probs[idx]), score_map


def router_decision(profile: str, confidence: float, threshold: float) -> dict[str, object]:
    if confidence < threshold:
        return {
            "selected_detector_profile": "general",
            "fallback_used": True,
            "routing_reason": "condition confidence below threshold",
        }
    return {
        "selected_detector_profile": "general",
        "fallback_used": True,
        "routing_reason": f"{profile} specialist is not promoted; general detector remains active",
    }


def run_video(video: Path, model: nn.Module, tfm, device: torch.device, classes: list[str], sample_every: int, threshold: float) -> dict[str, object]:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        return {"video": str(video), "status": "failed", "failure_reason": "video_open_failed"}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    frame_idx = 0
    predictions: list[str] = []
    confidences: list[float] = []
    score_sums: dict[str, float] = defaultdict(float)
    sampled_preview = []
    start = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % sample_every != 0:
            continue
        label, confidence, score_map = classify_frame(model, frame, tfm, device, classes)
        predictions.append(label)
        confidences.append(confidence)
        for key, value in score_map.items():
            score_sums[key] += value
        if len(sampled_preview) < 12:
            sampled_preview.append(
                {
                    "frame_id": frame_idx,
                    "condition_profile": label,
                    "confidence": round(confidence, 4),
                }
            )

    cap.release()
    elapsed = time.perf_counter() - start
    counts = Counter(predictions)
    dominant = counts.most_common(1)[0][0] if counts else "unknown"
    dominant_confidence = float(np.mean([conf for pred, conf in zip(predictions, confidences) if pred == dominant])) if counts else 0.0
    mean_confidence = float(np.mean(confidences)) if confidences else 0.0
    sampled_frames = len(predictions)
    mean_scores = {key: (score_sums[key] / sampled_frames if sampled_frames else 0.0) for key in classes}
    top_mean_scores = sorted(mean_scores.items(), key=lambda item: item[1], reverse=True)[:3]

    return {
        "video": str(video),
        "status": "ok",
        "source_resolution": [width, height],
        "video_fps": fps,
        "total_frames": total_frames,
        "sample_every_n_frames": sample_every,
        "sampled_frames": sampled_frames,
        "profile_counts": dict(counts),
        "profile_ratios": {key: counts.get(key, 0) / max(sampled_frames, 1) for key in classes},
        "dominant_profile": dominant,
        "dominant_confidence_mean": dominant_confidence,
        "mean_confidence": mean_confidence,
        "top_mean_scores": [{"label": key, "score": value} for key, value in top_mean_scores],
        "sampled_preview": sampled_preview,
        "processing_seconds": elapsed,
        "sampled_fps": sampled_frames / elapsed if elapsed > 0 else 0.0,
        **router_decision(dominant, dominant_confidence, threshold),
    }


def write_report(path: Path, summary: dict[str, object]) -> None:
    rows = []
    for item in summary["videos"]:
        if item.get("status") != "ok":
            rows.append(f"| `{Path(item['video']).name}` | failed | - | - | - | `{item.get('failure_reason')}` |")
            continue
        rows.append(
            "| `{video}` | {samples} | `{dominant}` | {dom_conf:.3f} | {mean_conf:.3f} | {reason} |".format(
                video=Path(item["video"]).name,
                samples=item["sampled_frames"],
                dominant=item["dominant_profile"],
                dom_conf=item["dominant_confidence_mean"],
                mean_conf=item["mean_confidence"],
                reason=item["routing_reason"],
            )
        )

    text = "\n".join(
        [
            "# COND-EXP-001 Local Dark Video Smoke Test",
            "",
            "## Scope",
            "",
            "This is a local qualitative smoke test for the selected condition-profile classifier checkpoint. It is not ground-truth accuracy.",
            "",
            "## Model",
            "",
            f"* Checkpoint: `{summary['checkpoint']}`",
            f"* Backbone: `{summary['backbone']}`",
            f"* Selection source: `{summary['selection_source']}`",
            f"* Device: `{summary['device']}`",
            "",
            "## Results",
            "",
            "| Video | Sampled frames | Dominant profile | Dominant confidence | Mean confidence | Router decision |",
            "|---|---:|---|---:|---:|---|",
            *rows,
            "",
            "## Interpretation",
            "",
            "* Expected behavior for the current dark/low-light local videos is a dominant `night_low_light` or low-light-adjacent profile.",
            "* The router still falls back to the general detector because condition specialists are not promoted yet.",
            "* Manual review is still required; this smoke test only checks pipeline usability and qualitative profile consistency.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--sample-every", type=int, default=15)
    parser.add_argument("--confidence-threshold", type=float, default=0.65)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    return parser.parse_args()


def resolve_device(choice: str) -> torch.device:
    if choice == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    if choice in {"auto", "mps"} and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def main() -> None:
    args = parse_args()
    if not args.checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {args.checkpoint}")
    if not args.videos_dir.exists():
        raise FileNotFoundError(f"Videos directory not found: {args.videos_dir}")

    device = resolve_device(args.device)
    model, classes, checkpoint = load_checkpoint(args.checkpoint, device)
    image_size = int(checkpoint.get("image_size", 224))
    tfm = frame_transform(image_size)

    videos = sorted(args.videos_dir.glob("video_*.mp4"))
    if not videos:
        raise FileNotFoundError(f"No video_*.mp4 files found under: {args.videos_dir}")

    results = [
        run_video(video, model, tfm, device, classes, args.sample_every, args.confidence_threshold)
        for video in videos
    ]
    summary = {
        "experiment_id": "COND-EXP-001-local-dark-video-smoke",
        "checkpoint": str(args.checkpoint),
        "backbone": checkpoint.get("backbone", "unknown"),
        "selection_source": "COND-EXP-001 best_val_macro_f1 selected checkpoint",
        "condition_classes": classes,
        "device": str(device),
        "videos": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(args.report, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Wrote:", args.output)
    print("Wrote:", args.report)


if __name__ == "__main__":
    main()
