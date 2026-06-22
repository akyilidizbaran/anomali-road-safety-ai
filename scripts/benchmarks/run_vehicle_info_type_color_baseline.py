#!/usr/bin/env python3
"""VEHINFO-EXP-001 vehicle type/color baseline.

This local smoke test connects three low-cost signals for the FTR
``arac_bilgisi`` fields:

* OpenVINO vehicle-attributes-recognition-barrier-0039 for coarse type/color.
* HSV/Lab color heuristic as an interpretable color sanity check.
* VATTR-EXP-001 body-style classifier as secondary type evidence.

The experiment is intentionally conservative. It does not claim final vehicle
type/color accuracy; it records per-crop evidence and track-level temporal votes
so the next fine-tune phases can be scoped from observable errors.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image

try:
    from openvino import Core
except Exception:  # pragma: no cover - older OpenVINO import path
    try:
        from openvino.runtime import Core
    except Exception as exc:  # pragma: no cover
        Core = None  # type: ignore[assignment]
        OPENVINO_IMPORT_ERROR = exc
    else:
        OPENVINO_IMPORT_ERROR = None
else:
    OPENVINO_IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons.json"
DEFAULT_CROP_DIR = ROOT / "runs" / "_archive" / "plate_ocr_v1_POCR-EXP-001-target-roi-crops" / "sample_frames"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_OUTPUT_DIR = ROOT / "runs" / "vehicle_info" / "VEHINFO-EXP-001-type-color-baseline"
DEFAULT_ARTIFACT_DIR = (
    ROOT / "models" / "benchmarks" / "artifacts" / "vehicle_info" / "VEHINFO-EXP-001-type-color-baseline"
)
DEFAULT_REPORT = ROOT / "testing" / "reports" / "vehinfo_exp_001_type_color_baseline.md"
DEFAULT_ENRICHED_EVENTS = (
    ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-vehinfo001.json"
)
DEFAULT_OPENVINO_DIR = (
    ROOT / "models" / "checkpoints" / "vehicle_info" / "openvino_vehicle_attributes_0039" / "FP16"
)
DEFAULT_VATTR_CHECKPOINT = (
    ROOT / "models" / "checkpoints" / "vehicle_attribute" / "VATTR-EXP-001-efficientnet_b0-best.pth"
)
DEFAULT_VATTR_LABEL_MAP = ROOT / "models" / "checkpoints" / "vehicle_attribute" / "VATTR-EXP-001-label-map.json"

OPENVINO_XML_URL = (
    "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/"
    "vehicle-attributes-recognition-barrier-0039/FP16/"
    "vehicle-attributes-recognition-barrier-0039.xml"
)
OPENVINO_BIN_URL = (
    "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/"
    "vehicle-attributes-recognition-barrier-0039/FP16/"
    "vehicle-attributes-recognition-barrier-0039.bin"
)

OPENVINO_COLOR_LABELS = ["white", "gray", "yellow", "red", "green", "blue", "black"]
OPENVINO_TYPE_LABELS = ["car", "bus", "truck", "van"]

COLOR_TO_FTR = {
    "white": "beyaz",
    "gray": "gri",
    "yellow": "sari",
    "red": "kirmizi",
    "green": "yesil",
    "blue": "mavi",
    "black": "siyah",
    "brown": "kahverengi",
    "orange": "turuncu",
    "unknown": "unknown",
}

VATTR_TO_FTR = {
    "sedan": ("sedan", "direct"),
    "suv": ("suv", "direct"),
    "hatchback": ("hatchback", "direct"),
    "van": ("panelvan", "mapped_from_van"),
    "mpv": ("minibus", "mapped_from_mpv"),
    "combi": ("sedan", "ambiguous_combi_fallback"),
}

OPENVINO_TYPE_TO_FTR = {
    "car": ("sedan", "coarse_car_fallback"),
    "bus": ("minibus", "coarse_bus_fallback"),
    "truck": ("kamyon", "direct_coarse"),
    "van": ("panelvan", "direct_coarse"),
}


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def softmax_if_needed(values: np.ndarray) -> np.ndarray:
    values = values.astype(np.float64).reshape(-1)
    total = float(values.sum())
    if values.size and 0.98 <= total <= 1.02 and np.all(values >= 0):
        return values.astype(np.float32)
    values = values - float(values.max(initial=0.0))
    exp = np.exp(values)
    denom = float(exp.sum()) or 1.0
    return (exp / denom).astype(np.float32)


def margin(probs: list[float]) -> float:
    if len(probs) < 2:
        return float(probs[0]) if probs else 0.0
    top = sorted(probs, reverse=True)[:2]
    return float(top[0] - top[1])


def download_if_missing(url: str, target: Path, min_bytes: int) -> None:
    if target.exists() and target.stat().st_size >= min_bytes:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    print(f"Downloading {url} -> {target}")
    errors: list[str] = []
    try:
        urllib.request.urlretrieve(url, tmp)
    except Exception as exc:
        errors.append(f"urllib failed: {exc}")
        if tmp.exists():
            tmp.unlink()
    if not tmp.exists():
        for cmd in (
            ["curl", "-L", "--retry", "5", "--connect-timeout", "30", "-o", str(tmp), url],
            ["wget", "-O", str(tmp), "--tries=5", "--timeout=30", url],
        ):
            if not shutil.which(cmd[0]):
                continue
            try:
                subprocess.run(cmd, check=True)
                break
            except Exception as exc:
                errors.append(f"{cmd[0]} failed: {exc}")
                if tmp.exists():
                    tmp.unlink()
    if not tmp.exists():
        raise RuntimeError("Could not download OpenVINO model file.\n" + "\n".join(errors))
    if tmp.stat().st_size < min_bytes:
        raise RuntimeError(f"Downloaded file is unexpectedly small: {tmp} ({tmp.stat().st_size} bytes)")
    tmp.replace(target)


def ensure_openvino_model(model_dir: Path) -> tuple[Path, Path]:
    xml_path = model_dir / "vehicle-attributes-recognition-barrier-0039.xml"
    bin_path = model_dir / "vehicle-attributes-recognition-barrier-0039.bin"
    download_if_missing(OPENVINO_XML_URL, xml_path, min_bytes=10_000)
    download_if_missing(OPENVINO_BIN_URL, bin_path, min_bytes=500_000)
    return xml_path, bin_path


def load_events(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = read_json(path)
    if isinstance(payload, dict):
        events = payload.get("events") or []
        return payload, events
    if isinstance(payload, list):
        return {"events": payload}, payload
    raise ValueError(f"Unsupported events JSON shape: {path}")


def event_crop_index(crop_dir: Path, events: list[dict[str, Any]]) -> dict[str, list[Path]]:
    all_crops = sorted(crop_dir.glob("*.jpg"))
    index: dict[str, list[Path]] = {}
    for event in events:
        event_id = str(event.get("event_id") or "")
        index[event_id] = [path for path in all_crops if path.name.startswith(event_id + "_")]
    return index


def parse_frame_from_crop(path: Path) -> int | None:
    match = re.search(r"_frame_(\d+)_target_roi", path.name)
    return int(match.group(1)) if match else None


def create_vattr_model(backbone: str, num_classes: int) -> nn.Module:
    if backbone != "efficientnet_b0":
        raise ValueError(f"Unsupported VATTR backbone: {backbone}")
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def load_vattr_model(checkpoint_path: Path, label_map_path: Path, device: torch.device) -> tuple[nn.Module | None, list[str]]:
    if not checkpoint_path.exists() or not label_map_path.exists():
        return None, []
    label_map = read_json(label_map_path)
    label_names = label_map["label_names"]
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model = create_vattr_model(checkpoint.get("backbone", "efficientnet_b0"), len(label_names)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, label_names


class OpenVINOVehicleAttributes:
    def __init__(self, model_dir: Path, device: str) -> None:
        if Core is None:
            raise RuntimeError(f"OpenVINO import failed: {OPENVINO_IMPORT_ERROR!r}")
        xml_path, _ = ensure_openvino_model(model_dir)
        core = Core()
        model = core.read_model(str(xml_path))
        self.compiled = core.compile_model(model, device)
        self.input_layer = self.compiled.input(0)
        self.outputs = list(self.compiled.outputs)
        self.color_output = self._pick_output(expected_len=7, preferred="color")
        self.type_output = self._pick_output(expected_len=4, preferred="type")

    def _pick_output(self, expected_len: int, preferred: str):
        named = [
            out
            for out in self.outputs
            if preferred in (out.get_any_name() or "").lower()
            and int(np.prod([int(x) for x in out.partial_shape.to_shape()[1:]])) == expected_len
        ]
        if named:
            return named[0]
        for out in self.outputs:
            shape = out.partial_shape.to_shape()
            if int(np.prod([int(x) for x in shape[1:]])) == expected_len:
                return out
        raise RuntimeError(f"Could not identify OpenVINO output with {expected_len} classes")

    def predict(self, crop_bgr: np.ndarray) -> dict[str, Any]:
        image = cv2.resize(crop_bgr, (72, 72), interpolation=cv2.INTER_AREA)
        blob = image.transpose(2, 0, 1)[None].astype(np.float32)
        output = self.compiled([blob])
        color_probs = softmax_if_needed(np.asarray(output[self.color_output]))
        type_probs = softmax_if_needed(np.asarray(output[self.type_output]))
        color_idx = int(np.argmax(color_probs))
        type_idx = int(np.argmax(type_probs))
        return {
            "openvino_color": OPENVINO_COLOR_LABELS[color_idx],
            "openvino_color_ftr": COLOR_TO_FTR[OPENVINO_COLOR_LABELS[color_idx]],
            "openvino_color_confidence": round(float(color_probs[color_idx]), 6),
            "openvino_color_margin": round(margin(color_probs.tolist()), 6),
            "openvino_color_top3": topk(OPENVINO_COLOR_LABELS, color_probs.tolist(), 3),
            "openvino_type": OPENVINO_TYPE_LABELS[type_idx],
            "openvino_type_confidence": round(float(type_probs[type_idx]), 6),
            "openvino_type_margin": round(margin(type_probs.tolist()), 6),
            "openvino_type_top3": topk(OPENVINO_TYPE_LABELS, type_probs.tolist(), 3),
        }


def topk(labels: list[str], probs: list[float], k: int) -> list[dict[str, Any]]:
    idxs = sorted(range(len(labels)), key=lambda idx: probs[idx], reverse=True)[:k]
    return [{"label": labels[idx], "confidence": round(float(probs[idx]), 6)} for idx in idxs]


def crop_quality(crop_bgr: np.ndarray) -> dict[str, Any]:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    h, w = crop_bgr.shape[:2]
    return {
        "crop_width": int(w),
        "crop_height": int(h),
        "crop_area_px": int(w * h),
        "brightness_mean": round(brightness, 3),
        "contrast_std": round(contrast, 3),
        "laplacian_blur_var": round(blur, 3),
    }


def hsv_lab_color_heuristic(crop_bgr: np.ndarray) -> dict[str, Any]:
    h, w = crop_bgr.shape[:2]
    if h < 8 or w < 8:
        return {"heuristic_color": "unknown", "heuristic_color_ftr": "unknown", "heuristic_color_confidence": 0.0}
    roi = crop_bgr[int(h * 0.30) : int(h * 0.88), int(w * 0.12) : int(w * 0.88)]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    hch = hsv[:, :, 0].reshape(-1)
    sat = hsv[:, :, 1].reshape(-1)
    val = hsv[:, :, 2].reshape(-1)
    a = lab[:, :, 1].reshape(-1)
    b = lab[:, :, 2].reshape(-1)
    mask = (val > 18) & (val < 248)
    if int(mask.sum()) < 50:
        mask = np.ones_like(val, dtype=bool)

    med_h = float(np.median(hch[mask]))
    med_s = float(np.median(sat[mask]))
    med_v = float(np.median(val[mask]))
    med_a = float(np.median(a[mask]))
    med_b = float(np.median(b[mask]))
    pixels = int(mask.sum())

    if med_v < 58:
        label = "black"
        confidence = 0.72 if med_s < 90 else 0.62
    elif med_s < 28 and med_v > 178:
        label = "white"
        confidence = 0.68
    elif med_s < 42:
        label = "gray"
        confidence = 0.62
    elif med_h <= 8 or med_h >= 170:
        label = "red"
        confidence = 0.60
    elif 8 < med_h <= 20:
        label = "brown" if med_v < 145 or (med_a > 132 and med_b > 135) else "orange"
        confidence = 0.54
    elif 20 < med_h <= 35:
        label = "yellow"
        confidence = 0.58
    elif 35 < med_h <= 85:
        label = "green"
        confidence = 0.56
    elif 85 < med_h <= 135:
        label = "blue"
        confidence = 0.58
    else:
        label = "gray"
        confidence = 0.45

    if pixels < 1000:
        confidence *= 0.75
    if med_v < 45 or med_s < 18:
        confidence *= 0.85
    return {
        "heuristic_color": label,
        "heuristic_color_ftr": COLOR_TO_FTR.get(label, "unknown"),
        "heuristic_color_confidence": round(float(max(0.0, min(confidence, 0.9))), 6),
        "heuristic_hsv_median": {"h": round(med_h, 3), "s": round(med_s, 3), "v": round(med_v, 3)},
        "heuristic_lab_median": {"a": round(med_a, 3), "b": round(med_b, 3)},
        "heuristic_pixel_count": pixels,
    }


def predict_vattr_crop(
    model: nn.Module | None,
    label_names: list[str],
    crop_rgb: Image.Image,
    device: torch.device,
    transform: T.Compose,
) -> dict[str, Any]:
    if model is None:
        return {"vattr_status": "not_available", "vattr_failure_reason": "checkpoint_or_label_map_missing"}
    with torch.no_grad():
        logits = model(transform(crop_rgb).unsqueeze(0).to(device))
        probs = torch.softmax(logits, dim=1).detach().cpu().numpy().reshape(-1)
    idx = int(np.argmax(probs))
    label = label_names[idx]
    mapped, mapping_note = VATTR_TO_FTR.get(label, ("unknown", "unmapped"))
    return {
        "vattr_status": "computed",
        "vattr_body_label": label,
        "vattr_ftr_type": mapped,
        "vattr_mapping_note": mapping_note,
        "vattr_confidence": round(float(probs[idx]), 6),
        "vattr_margin": round(margin(probs.tolist()), 6),
        "vattr_top3": topk(label_names, probs.tolist(), 3),
    }


def weighted_vote(rows: list[dict[str, Any]], label_key: str, weight_key: str) -> tuple[str, float, dict[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for row in rows:
        label = row.get(label_key)
        if not label or label == "unknown":
            continue
        scores[str(label)] += float(row.get(weight_key) or 0.0)
    if not scores:
        return "unknown", 0.0, {}
    label = max(scores, key=scores.get)
    total = sum(scores.values()) or 1.0
    return label, float(scores[label] / total), {key: round(value, 6) for key, value in sorted(scores.items())}


def fuse_color(row: dict[str, Any]) -> dict[str, Any]:
    ov_color = row.get("openvino_color_ftr")
    ov_conf = float(row.get("openvino_color_confidence") or 0.0)
    heur_color = row.get("heuristic_color_ftr")
    heur_conf = float(row.get("heuristic_color_confidence") or 0.0)
    warnings: list[str] = []
    if ov_color == heur_color and ov_color != "unknown":
        return {
            "fused_color": ov_color,
            "fused_color_confidence": round(min(0.95, max(ov_conf, heur_conf) + 0.08), 6),
            "color_fusion_note": "openvino_hsv_agree",
            "color_warnings": warnings,
        }
    warnings.append("openvino_hsv_color_disagreement")
    if ov_conf >= 0.58:
        chosen, confidence, note = ov_color, ov_conf * 0.86, "openvino_preferred_after_disagreement"
    elif heur_conf >= 0.60:
        chosen, confidence, note = heur_color, heur_conf * 0.82, "hsv_preferred_after_disagreement"
    else:
        chosen = ov_color if ov_conf >= heur_conf else heur_color
        confidence = max(ov_conf, heur_conf) * 0.65
        note = "low_confidence_disagreement_fallback"
    return {
        "fused_color": chosen or "unknown",
        "fused_color_confidence": round(float(confidence), 6),
        "color_fusion_note": note,
        "color_warnings": warnings,
    }


def fuse_type(row: dict[str, Any]) -> dict[str, Any]:
    ov_type = row.get("openvino_type")
    ov_ftr, ov_note = OPENVINO_TYPE_TO_FTR.get(str(ov_type), ("unknown", "unmapped"))
    ov_conf = float(row.get("openvino_type_confidence") or 0.0)
    vattr_type = row.get("vattr_ftr_type")
    vattr_conf = float(row.get("vattr_confidence") or 0.0)
    vattr_margin = float(row.get("vattr_margin") or 0.0)
    warnings: list[str] = []

    if ov_type in {"truck", "bus", "van"} and ov_conf >= 0.55:
        chosen = ov_ftr
        confidence = ov_conf * 0.82
        note = "openvino_non_car_coarse_type_preferred"
    elif vattr_type and vattr_type != "unknown" and vattr_conf >= 0.55 and vattr_margin >= 0.10:
        chosen = vattr_type
        confidence = min(0.92, vattr_conf)
        note = "vattr_body_style_preferred_for_car_subtype"
    elif vattr_type and vattr_type != "unknown" and vattr_conf >= 0.40:
        chosen = vattr_type
        confidence = vattr_conf * 0.70
        note = "low_confidence_vattr_body_style_fallback"
        warnings.append("vehicle_type_low_confidence")
    else:
        chosen = ov_ftr
        confidence = ov_conf * 0.55
        note = f"openvino_{ov_note}"
        warnings.append("vehicle_type_coarse_fallback")
    if row.get("vattr_mapping_note") == "ambiguous_combi_fallback":
        warnings.append("vattr_combi_mapping_ambiguous")
    return {
        "fused_type": chosen or "unknown",
        "fused_type_confidence": round(float(confidence), 6),
        "type_fusion_note": note,
        "type_warnings": warnings,
    }


def summarize_event(event: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    event_id = event.get("event_id")
    video = (event.get("source") or {}).get("source_video")
    track = event.get("target_vehicle") or {}
    warnings: set[str] = set()
    if not rows:
        return {
            "event_id": event_id,
            "video": video,
            "track_id": track.get("track_id"),
            "status": "failed",
            "failure_reason": "no_crop_rows",
        }
    color_label, color_score, color_votes = weighted_vote(rows, "fused_color", "fused_color_confidence")
    type_label, type_score, type_votes = weighted_vote(rows, "fused_type", "fused_type_confidence")
    for row in rows:
        warnings.update(row.get("color_warnings") or [])
        warnings.update(row.get("type_warnings") or [])
    if color_score < 0.55:
        warnings.add("track_color_temporal_vote_low_confidence")
    if type_score < 0.55:
        warnings.add("track_type_temporal_vote_low_confidence")
    return {
        "event_id": event_id,
        "video": video,
        "track_id": track.get("track_id"),
        "status": "computed",
        "crop_count": len(rows),
        "target_vehicle_detector_class": track.get("vehicle_type"),
        "track_stability": track.get("track_stability"),
        "selection_score": track.get("selection_score"),
        "ftr_vehicle_type_candidate": type_label,
        "ftr_vehicle_type_confidence": round(type_score, 6),
        "ftr_vehicle_color_candidate": color_label,
        "ftr_vehicle_color_confidence": round(color_score, 6),
        "type_vote_scores": type_votes,
        "color_vote_scores": color_votes,
        "openvino_type_votes": dict(Counter(str(row.get("openvino_type")) for row in rows)),
        "openvino_color_votes": dict(Counter(str(row.get("openvino_color_ftr")) for row in rows)),
        "heuristic_color_votes": dict(Counter(str(row.get("heuristic_color_ftr")) for row in rows)),
        "vattr_body_votes": dict(Counter(str(row.get("vattr_body_label")) for row in rows if row.get("vattr_body_label"))),
        "warnings": sorted(warnings),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "event_id",
        "video",
        "track_id",
        "frame",
        "crop_uri",
        "crop_width",
        "crop_height",
        "brightness_mean",
        "contrast_std",
        "laplacian_blur_var",
        "openvino_type",
        "openvino_type_confidence",
        "openvino_type_margin",
        "openvino_color_ftr",
        "openvino_color_confidence",
        "openvino_color_margin",
        "heuristic_color_ftr",
        "heuristic_color_confidence",
        "vattr_body_label",
        "vattr_ftr_type",
        "vattr_confidence",
        "vattr_margin",
        "fused_type",
        "fused_type_confidence",
        "type_fusion_note",
        "fused_color",
        "fused_color_confidence",
        "color_fusion_note",
        "warnings",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            out = {key: row.get(key) for key in fieldnames}
            warning_list = (row.get("type_warnings") or []) + (row.get("color_warnings") or [])
            out["warnings"] = "|".join(sorted(set(warning_list)))
            writer.writerow(out)


def render_review_videos(events: list[dict[str, Any]], summaries: list[dict[str, Any]], videos_dir: Path, output_dir: Path) -> list[str]:
    summary_by_event = {row["event_id"]: row for row in summaries}
    written: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for event in events:
        event_id = event.get("event_id")
        summary = summary_by_event.get(event_id)
        if not summary or summary.get("status") != "computed":
            continue
        video_name = (event.get("source") or {}).get("source_video")
        if not video_name:
            continue
        video_path = videos_dir / video_name
        if not video_path.exists():
            continue
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            continue
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        out_path = output_dir / f"{Path(video_name).stem}_vehinfo001_overlay.mp4"
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        best_frame = int(((event.get("target_vehicle") or {}).get("frame_window") or {}).get("best_frame") or 0)
        bbox = (event.get("target_vehicle") or {}).get("bbox_xyxy") or []
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            text_lines = [
                "VEHINFO-EXP-001",
                f"track_id: {summary.get('track_id')}",
                f"tip: {summary.get('ftr_vehicle_type_candidate')} ({summary.get('ftr_vehicle_type_confidence')})",
                f"renk: {summary.get('ftr_vehicle_color_candidate')} ({summary.get('ftr_vehicle_color_confidence')})",
            ]
            y = 38
            cv2.rectangle(frame, (24, 18), (780, 172), (245, 245, 245), -1)
            cv2.rectangle(frame, (24, 18), (780, 172), (20, 20, 20), 2)
            for line in text_lines:
                cv2.putText(frame, line, (42, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (10, 10, 10), 2, cv2.LINE_AA)
                y += 34
            if bbox and abs(frame_idx - best_frame) <= int(fps):
                x1, y1, x2, y2 = [int(round(float(v))) for v in bbox[:4]]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width - 1, x2), min(height - 1, y2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 20, 20), 4)
                cv2.putText(frame, "target bbox near best_frame", (max(20, x1), max(35, y1 - 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv2.LINE_AA)
            writer.write(frame)
            frame_idx += 1
        cap.release()
        writer.release()
        written.append(rel(out_path))
    return written


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = summary.get("events") or []
    lines = [
        "# VEHINFO-EXP-001 Type/Color Baseline",
        "",
        f"- Generated: `{summary.get('generated_at_utc')}`",
        "- Scope: target vehicle ROI crop'lari uzerinde arac tipi ve renk icin ilk baseline.",
        "- This is not final FTR accuracy; it is a smoke/diagnostic run before dedicated `COLOR-EXP-001` and `TYPE-EXP-001` fine-tune.",
        "",
        "## Inputs",
        "",
        f"- Event skeleton: `{summary.get('inputs', {}).get('events')}`",
        f"- Crop directory: `{summary.get('inputs', {}).get('crop_dir')}`",
        f"- OpenVINO model: `vehicle-attributes-recognition-barrier-0039`",
        f"- VATTR checkpoint: `{summary.get('inputs', {}).get('vattr_checkpoint')}`",
        "",
        "## Event-Level Results",
        "",
        "| Video | Event | Track | Type Candidate | Type Conf. | Color Candidate | Color Conf. | Warnings |",
        "|---|---|---:|---|---:|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {video} | `{event_id}` | `{track_id}` | {typ} | {tc} | {color} | {cc} | {warn} |".format(
                video=row.get("video"),
                event_id=row.get("event_id"),
                track_id=row.get("track_id"),
                typ=row.get("ftr_vehicle_type_candidate"),
                tc=row.get("ftr_vehicle_type_confidence"),
                color=row.get("ftr_vehicle_color_candidate"),
                cc=row.get("ftr_vehicle_color_confidence"),
                warn=", ".join(row.get("warnings") or []) or "-",
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `tip` sonucu OpenVINO coarse type ile VATTR body-style kanitinin temporal oyundan gecirilmis adayidir.",
            "- `renk` sonucu OpenVINO renk sinifi ile HSV/Lab heuristic kontrolunun temporal oyundan gecirilmis adayidir.",
            "- Dusuk guven veya uyusmazlik uyarilari, sonraki dedicated fine-tune kapsaminda iyilestirilecek hata kaynaklarini isaret eder.",
            "- Bu deney, resmi `results.json` icin nihai `arac_bilgisi` karari degil; FTR adapter'a baglanmadan once review edilecek ara contract'tir.",
            "",
            "## Artifacts",
            "",
            f"- Per-crop CSV: `{summary.get('artifacts', {}).get('per_crop_csv')}`",
            f"- Summary JSON: `{summary.get('artifacts', {}).get('summary_json')}`",
            f"- Enriched events JSON: `{summary.get('artifacts', {}).get('enriched_events_json')}`",
        ]
    )
    videos = summary.get("artifacts", {}).get("review_videos") or []
    if videos:
        lines.append("- Review videos:")
        lines.extend([f"  - `{video}`" for video in videos])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--crop-dir", type=Path, default=DEFAULT_CROP_DIR)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--enriched-events", type=Path, default=DEFAULT_ENRICHED_EVENTS)
    parser.add_argument("--openvino-dir", type=Path, default=DEFAULT_OPENVINO_DIR)
    parser.add_argument("--openvino-device", default="CPU")
    parser.add_argument("--vattr-checkpoint", type=Path, default=DEFAULT_VATTR_CHECKPOINT)
    parser.add_argument("--vattr-label-map", type=Path, default=DEFAULT_VATTR_LABEL_MAP)
    parser.add_argument("--render-videos", action="store_true")
    args = parser.parse_args()

    _, events = load_events(args.events)
    crop_index = event_crop_index(args.crop_dir, events)
    ov_model = OpenVINOVehicleAttributes(args.openvino_dir, args.openvino_device)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vattr_model, vattr_labels = load_vattr_model(args.vattr_checkpoint, args.vattr_label_map, device)
    vattr_transform = T.Compose(
        [
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    all_rows: list[dict[str, Any]] = []
    rows_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        event_id = str(event.get("event_id"))
        video = (event.get("source") or {}).get("source_video")
        track_id = (event.get("target_vehicle") or {}).get("track_id")
        for crop_path in crop_index.get(event_id, []):
            crop_bgr = cv2.imread(str(crop_path), cv2.IMREAD_COLOR)
            if crop_bgr is None:
                continue
            crop_rgb = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
            row: dict[str, Any] = {
                "event_id": event_id,
                "video": video,
                "track_id": track_id,
                "frame": parse_frame_from_crop(crop_path),
                "crop_uri": rel(crop_path),
            }
            row.update(crop_quality(crop_bgr))
            row.update(ov_model.predict(crop_bgr))
            row.update(hsv_lab_color_heuristic(crop_bgr))
            row.update(predict_vattr_crop(vattr_model, vattr_labels, crop_rgb, device, vattr_transform))
            row.update(fuse_color(row))
            row.update(fuse_type(row))
            all_rows.append(row)
            rows_by_event[event_id].append(row)

    event_summaries = [summarize_event(event, rows_by_event.get(str(event.get("event_id")), [])) for event in events]
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    per_crop_csv = args.artifact_dir / "vehinfo_exp_001_type_color_per_crop.csv"
    summary_json = args.artifact_dir / "vehinfo_exp_001_type_color_summary.json"
    write_csv(per_crop_csv, all_rows)

    enriched_payload, _ = load_events(args.events)
    enriched_events = enriched_payload.get("events") or []
    summaries_by_event = {row["event_id"]: row for row in event_summaries}
    for event in enriched_events:
        event_id = event.get("event_id")
        vehinfo = summaries_by_event.get(event_id, {})
        event["vehicle_info_exp_001"] = {
            "status": vehinfo.get("status"),
            "ftr_vehicle_type_candidate": vehinfo.get("ftr_vehicle_type_candidate"),
            "ftr_vehicle_type_confidence": vehinfo.get("ftr_vehicle_type_confidence"),
            "ftr_vehicle_color_candidate": vehinfo.get("ftr_vehicle_color_candidate"),
            "ftr_vehicle_color_confidence": vehinfo.get("ftr_vehicle_color_confidence"),
            "warnings": vehinfo.get("warnings") or [],
            "source": "VEHINFO-EXP-001 OpenVINO vehicle attributes + HSV/Lab heuristic + VATTR temporal voting",
        }
    enriched_payload["vehicle_info_exp_001_generated_at_utc"] = now_utc()
    write_json(args.enriched_events, enriched_payload)

    review_videos = render_review_videos(events, event_summaries, args.videos_dir, args.output_dir) if args.render_videos else []
    summary = {
        "experiment_id": "VEHINFO-EXP-001-type-color-baseline",
        "generated_at_utc": now_utc(),
        "inputs": {
            "events": rel(args.events),
            "crop_dir": rel(args.crop_dir),
            "videos_dir": rel(args.videos_dir),
            "openvino_dir": rel(args.openvino_dir),
            "vattr_checkpoint": rel(args.vattr_checkpoint),
            "vattr_label_map": rel(args.vattr_label_map),
        },
        "events": event_summaries,
        "artifacts": {
            "per_crop_csv": rel(per_crop_csv),
            "summary_json": rel(summary_json),
            "enriched_events_json": rel(args.enriched_events),
            "review_videos": review_videos,
        },
        "notes": [
            "This baseline is diagnostic, not final FTR vehicle type/color accuracy.",
            "OpenVINO type labels are coarse; car subtype relies on VATTR evidence when confident enough.",
            "Color supports OpenVINO plus HSV/Lab agreement/disagreement warnings.",
        ],
    }
    write_json(summary_json, summary)
    write_report(args.report, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
