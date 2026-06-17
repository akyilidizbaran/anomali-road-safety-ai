#!/usr/bin/env python3
"""Plate OCR baseline over detector-produced plate crops.

Bu script plaka detection smoke test'inin uretdigi crop'lari okuyup
OCR baseline'larini olculebilir hale getirir.

Akis:
  1) `POCR-EXP-001` summary JSON icinden secilen detector'un crop klasorlerini bul.
  2) Crop'lar ustunde secili OCR engine'lerini (PaddleOCR / EasyOCR / Tesseract) calistir.
  3) Ham OCR metnini Turk plaka formatina gore normalize et, il kodu ve regex kontrolu yap.
  4) Ayni target track (bu veri setinde video basi 1 track) icin temporal voting uygula.
  5) Kucuk summary JSON + Markdown raporu + manuel review seed CSV uret.

Ham crop'lar ve OCR inceleme materyali `runs/` altinda ignore'lu kalir; Git'e yalniz kucuk
JSON / Markdown / CSV cikar.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DETECTION_SUMMARY = (
    ROOT / "models" / "benchmarks" / "artifacts" / "POCR-EXP-001-plate-detection-yolo-summary.json"
)
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "pocr_exp_002_004_plate_ocr_summary.md"
DEFAULT_RUNS_DIR = ROOT / "runs" / "plate_ocr" / "POCR-EXP-002-004-ocr"

ENGINE_META = {
    "fastplate": {
        "experiment_id": "POCR-EXP-006",
        "summary_name": "POCR-EXP-006-fast-plate-ocr-summary.json",
        "label": "fast-plate-ocr",
        "license_note": "MIT; ONNX Runtime tabanli plate-specific OCR, model hub lisansi ayrica dogrulanmali",
    },
    "paddle": {
        "experiment_id": "POCR-EXP-002",
        "summary_name": "POCR-EXP-002-paddleocr-summary.json",
        "label": "PaddleOCR",
        "license_note": "Apache-2.0 line, package + model card dogrulanmali",
    },
    "easyocr": {
        "experiment_id": "POCR-EXP-003",
        "summary_name": "POCR-EXP-003-easyocr-summary.json",
        "label": "EasyOCR",
        "license_note": "Apache-2.0, package/model kaynaklari tekrar kontrol edilmeli",
    },
    "tesseract": {
        "experiment_id": "POCR-EXP-004",
        "summary_name": "POCR-EXP-004-tesseract-summary.json",
        "label": "Tesseract",
        "license_note": "Apache-2.0 / binary dagitim notlari kontrol edilmeli",
    },
}

VARIANT_CHOICES = ("original", "gray", "clahe", "otsu")
TRANSLITERATION = str.maketrans(
    {
        "Ç": "C",
        "Ğ": "G",
        "İ": "I",
        "I": "I",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
        "ç": "C",
        "ğ": "G",
        "ı": "I",
        "i": "I",
        "ö": "O",
        "ş": "S",
        "ü": "U",
    }
)
LETTER_FIXES = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "4": "A",
    "5": "S",
    "6": "G",
    "7": "T",
    "8": "B",
    "9": "G",
}
DIGIT_FIXES = {
    "A": "4",
    "B": "8",
    "D": "0",
    "G": "6",
    "I": "1",
    "L": "1",
    "O": "0",
    "Q": "0",
    "S": "5",
    "T": "1",
    "U": "0",
    "Z": "2",
}


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_rootish(path_value: str | Path | None) -> Path:
    if not path_value:
        return ROOT
    path = Path(path_value)
    return path if path.is_absolute() else (ROOT / path)


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[int(round((len(ordered) - 1) * 0.95))], 3)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frame_number(path: Path) -> int:
    match = re.search(r"frame_(\d+)", path.name)
    if not match:
        raise ValueError(f"Kare numarasi dosya adindan parse edilemedi: {path.name}")
    return int(match.group(1))


def sort_key_for_bbox(item: dict[str, Any]) -> tuple[float, float]:
    bbox = item.get("bbox")
    if not bbox:
        return (0.0, 0.0)
    return (float(bbox[1]), float(bbox[0]))


def clean_text(text: str) -> str:
    text = (text or "").translate(TRANSLITERATION).upper()
    return re.sub(r"[^A-Z0-9]", "", text)


def convert_segment(segment: str, expected: str) -> tuple[str | None, int]:
    out: list[str] = []
    fixes = LETTER_FIXES if expected == "letter" else DIGIT_FIXES
    for ch in segment:
        if expected == "letter":
            if "A" <= ch <= "Z":
                out.append(ch)
                continue
        else:
            if ch.isdigit():
                out.append(ch)
                continue
        repl = fixes.get(ch)
        if repl is None:
            return None, 0
        out.append(repl)
    corrections = sum(1 for a, b in zip(segment, out, strict=False) if a != b)
    return "".join(out), corrections


def build_plate_candidates(cleaned: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    raw_options = [cleaned]
    if cleaned and len(cleaned) in {6, 7, 8} and cleaned[0].isdigit() and not cleaned.startswith("0"):
        raw_options.append(f"0{cleaned}")
    for candidate_raw in raw_options:
        for letter_count in range(1, 4):
            for digit_count in range(2, 5):
                if len(candidate_raw) != 2 + letter_count + digit_count:
                    continue
                province_raw = candidate_raw[:2]
                letters_raw = candidate_raw[2 : 2 + letter_count]
                suffix_raw = candidate_raw[2 + letter_count :]
                province, province_fix = convert_segment(province_raw, "digit")
                letters, letter_fix = convert_segment(letters_raw, "letter")
                suffix, suffix_fix = convert_segment(suffix_raw, "digit")
                if province is None or letters is None or suffix is None:
                    continue
                province_num = int(province)
                province_valid = 1 <= province_num <= 81
                normalized = f"{province}{letters}{suffix}"
                candidates.append(
                    {
                        "normalized": normalized,
                        "province_code_valid": province_valid,
                        "format_valid": True,
                        "correction_count": province_fix + letter_fix + suffix_fix + (0 if candidate_raw == cleaned else 1),
                    }
                )
    return candidates


def normalize_plate_text(text: str) -> dict[str, Any]:
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "raw_text": text,
            "cleaned_text": "",
            "normalized_text": "",
            "format_valid": False,
            "province_code_valid": False,
            "correction_count": None,
        }

    candidates = build_plate_candidates(cleaned)
    if candidates:
        best = min(
            candidates,
            key=lambda item: (
                0 if item["province_code_valid"] else 1,
                item["correction_count"],
                abs(len(item["normalized"]) - 8),
            ),
        )
        return {
            "raw_text": text,
            "cleaned_text": cleaned,
            "normalized_text": best["normalized"],
            "format_valid": best["format_valid"],
            "province_code_valid": best["province_code_valid"],
            "correction_count": best["correction_count"],
        }

    return {
        "raw_text": text,
        "cleaned_text": cleaned,
        "normalized_text": cleaned,
        "format_valid": False,
        "province_code_valid": False,
        "correction_count": None,
    }


def preprocess_variants(image_bgr: np.ndarray, variants: list[str], upscale: float) -> dict[str, np.ndarray]:
    if upscale <= 0:
        raise ValueError("--upscale pozitif olmali")
    if upscale != 1.0:
        width = max(1, int(round(image_bgr.shape[1] * upscale)))
        height = max(1, int(round(image_bgr.shape[0] * upscale)))
        base = cv2.resize(image_bgr, (width, height), interpolation=cv2.INTER_CUBIC)
    else:
        base = image_bgr.copy()

    gray = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    outputs = {
        "original": base,
        "gray": gray,
        "clahe": clahe,
        "otsu": otsu,
    }
    return {name: outputs[name] for name in variants}


class OcrEngine:
    key = "base"

    def recognize(self, image: np.ndarray) -> list[dict[str, Any]]:
        raise NotImplementedError


class PaddleOcrEngine(OcrEngine):
    key = "paddle"

    def __init__(self, lang: str) -> None:
        from paddleocr import PaddleOCR

        self.reader = PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        self.model_ref = f"PaddleOCR(lang={lang})"

    def recognize(self, image: np.ndarray) -> list[dict[str, Any]]:
        result = self.reader.ocr(image)
        lines: list[dict[str, Any]] = []
        if not result:
            return lines
        # PaddleOCR 3.x yeni pipeline formatı: her sayfa bir dict ve metinler
        # `rec_texts` / `rec_scores` / `rec_polys` altında gelir.
        if result and isinstance(result[0], dict):
            for page in result:
                texts = page.get("rec_texts") or []
                scores = page.get("rec_scores") or []
                polys = page.get("rec_polys") or page.get("dt_polys") or []
                for idx, text in enumerate(texts):
                    text = str(text).strip()
                    if not text:
                        continue
                    confidence = float(scores[idx]) if idx < len(scores) else 0.0
                    polygon = polys[idx] if idx < len(polys) else None
                    if polygon is not None:
                        xs = [float(point[0]) for point in polygon]
                        ys = [float(point[1]) for point in polygon]
                        bbox = [min(xs), min(ys), max(xs), max(ys)]
                    else:
                        bbox = [0.0, 0.0, float(image.shape[1]), float(image.shape[0])]
                    lines.append({"text": text, "confidence": confidence, "bbox": bbox})
            return lines
        for page in result:
            if not page:
                continue
            for item in page:
                if not item or len(item) < 2:
                    continue
                polygon = item[0]
                text_info = item[1]
                if not isinstance(text_info, (list, tuple)) or len(text_info) < 2:
                    continue
                text = str(text_info[0]).strip()
                confidence = float(text_info[1])
                xs = [float(point[0]) for point in polygon]
                ys = [float(point[1]) for point in polygon]
                lines.append(
                    {
                        "text": text,
                        "confidence": confidence,
                        "bbox": [min(xs), min(ys), max(xs), max(ys)],
                    }
                )
        return lines


class FastPlateOcrEngine(OcrEngine):
    key = "fastplate"

    def __init__(self, model_name: str, device: str) -> None:
        from fast_plate_ocr import LicensePlateRecognizer

        self.reader = LicensePlateRecognizer(model_name, device=device)
        self.model_ref = f"fast-plate-ocr({model_name}, device={device})"

    def recognize(self, image: np.ndarray) -> list[dict[str, Any]]:
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        predictions = self.reader.run(image, return_confidence=True)
        lines: list[dict[str, Any]] = []
        for prediction in predictions:
            text = str(getattr(prediction, "plate", "") or "").strip()
            if not text:
                continue
            char_probs = getattr(prediction, "char_probs", None)
            confidence = float(np.mean(char_probs)) if char_probs is not None and len(char_probs) else 0.0
            lines.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "bbox": [0.0, 0.0, float(image.shape[1]), float(image.shape[0])],
                    "region": getattr(prediction, "region", None),
                    "region_prob": getattr(prediction, "region_prob", None),
                }
            )
        return lines


def bbox_components(raw_bbox: Any, width: int, height: int) -> tuple[list[float], list[float]]:
    if raw_bbox is None:
        return [0.0, float(width)], [0.0, float(height)]
    if (
        isinstance(raw_bbox, (list, tuple))
        and len(raw_bbox) == 4
        and all(isinstance(value, (int, float)) for value in raw_bbox)
    ):
        x0, x1, y0, y1 = [float(value) for value in raw_bbox]
        return [x0, x1], [y0, y1]
    xs: list[float] = []
    ys: list[float] = []
    for point in raw_bbox:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        xs.append(float(point[0]))
        ys.append(float(point[1]))
    if xs and ys:
        return xs, ys
    return [0.0, float(width)], [0.0, float(height)]


class EasyOcrEngine(OcrEngine):
    key = "easyocr"

    def __init__(self, lang: str, gpu: bool, detector: bool) -> None:
        import easyocr

        self.detector = detector
        self.reader = easyocr.Reader([lang], gpu=gpu, detector=detector, recognizer=True, verbose=False)
        mode = "detector+recognizer" if detector else "recognizer_only"
        self.model_ref = f"EasyOCR(lang={lang}, gpu={gpu}, mode={mode})"

    def recognize(self, image: np.ndarray) -> list[dict[str, Any]]:
        allowlist = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if self.detector:
            result = self.reader.readtext(image, detail=1, paragraph=False, allowlist=allowlist)
        else:
            grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
            result = self.reader.recognize(
                grey,
                detail=1,
                paragraph=False,
                allowlist=allowlist,
                reformat=False,
            )
        lines: list[dict[str, Any]] = []
        for item in result:
            if len(item) < 3:
                continue
            polygon, text, confidence = item[0], item[1], item[2]
            xs, ys = bbox_components(polygon, image.shape[1], image.shape[0])
            lines.append(
                {
                    "text": str(text).strip(),
                    "confidence": float(confidence),
                    "bbox": [min(xs), min(ys), max(xs), max(ys)],
                }
            )
        return lines


class TesseractOcrEngine(OcrEngine):
    key = "tesseract"

    def __init__(self, lang: str, config: str) -> None:
        import pytesseract
        from pytesseract import Output

        self.pytesseract = pytesseract
        self.output = Output
        self.lang = lang
        self.config = config
        self.model_ref = f"tesseract(lang={lang}, config={config})"

    def recognize(self, image: np.ndarray) -> list[dict[str, Any]]:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.ndim == 3 else image
        data = self.pytesseract.image_to_data(
            rgb, lang=self.lang, config=self.config, output_type=self.output.DICT
        )
        lines: list[dict[str, Any]] = []
        count = len(data.get("text", []))
        for idx in range(count):
            text = str(data["text"][idx]).strip()
            conf_raw = str(data["conf"][idx]).strip()
            if not text:
                continue
            try:
                confidence = max(0.0, float(conf_raw) / 100.0)
            except ValueError:
                continue
            x = float(data["left"][idx])
            y = float(data["top"][idx])
            w = float(data["width"][idx])
            h = float(data["height"][idx])
            lines.append({"text": text, "confidence": confidence, "bbox": [x, y, x + w, y + h]})
        return lines


def build_engines(args: argparse.Namespace) -> list[OcrEngine]:
    engines: list[OcrEngine] = []
    if "fastplate" in args.engines:
        try:
            engines.append(FastPlateOcrEngine(model_name=args.fastplate_model, device=args.fastplate_device))
            print(f"[ok] fast-plate-ocr yuklendi ({args.fastplate_model}, device={args.fastplate_device})")
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] fast-plate-ocr yuklenemedi -> {exc}")
    if "paddle" in args.engines:
        try:
            engines.append(PaddleOcrEngine(lang=args.paddle_lang))
            print("[ok] PaddleOCR yuklendi")
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] PaddleOCR yuklenemedi -> {exc}")
    if "easyocr" in args.engines:
        try:
            engines.append(
                EasyOcrEngine(
                    lang=args.easyocr_lang,
                    gpu=args.easyocr_gpu,
                    detector=args.easyocr_detector,
                )
            )
            print(f"[ok] EasyOCR yuklendi (gpu={args.easyocr_gpu}, detector={args.easyocr_detector})")
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] EasyOCR yuklenemedi -> {exc}")
    if "tesseract" in args.engines:
        try:
            engines.append(TesseractOcrEngine(lang=args.tesseract_lang, config=args.tesseract_config))
            print("[ok] Tesseract OCR yuklendi")
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] Tesseract OCR yuklenemedi -> {exc}")
    return engines


def read_event_specs(events_path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(events_path)
    specs: dict[str, dict[str, Any]] = {}
    for event in data.get("events", []):
        source = event.get("source") or {}
        target = event.get("target_vehicle") or {}
        frame_window = target.get("frame_window") or {}
        video = source.get("source_video")
        if not video:
            continue
        specs[video] = {
            "event_id": event.get("event_id"),
            "track_id_label": target.get("track_id"),
            "best_frame": int(frame_window.get("best_frame") or 1),
            "first_frame": int(frame_window.get("first_frame") or 1),
            "last_frame": int(frame_window.get("last_frame") or frame_window.get("best_frame") or 1),
        }
    return specs


def resolve_detector_key(summary: dict[str, Any], requested: str) -> str:
    if requested != "auto":
        return requested
    loaded = summary.get("models_loaded") or []
    if len(loaded) == 1:
        return str(loaded[0])
    for video in summary.get("videos", []):
        models = video.get("models") or {}
        if len(models) == 1:
            return next(iter(models))
    raise SystemExit(
        "Detector secimi belirsiz. Summary birden fazla detector iceriyor; "
        "--detector-key yolo veya --detector-key yolos verin."
    )


def collect_video_inputs(
    summary: dict[str, Any],
    detector_key: str,
    event_specs: dict[str, dict[str, Any]],
    frame_stride: int,
    limit_per_video: int | None,
) -> list[dict[str, Any]]:
    videos: list[dict[str, Any]] = []
    for video in summary.get("videos", []):
        name = video.get("video")
        if not name:
            continue
        models = video.get("models") or {}
        model_info = models.get(detector_key)
        if not model_info:
            videos.append(
                {
                    "video": name,
                    "status": "failed",
                    "failure_reason": f"detector_key_not_found:{detector_key}",
                    "crop_files": [],
                }
            )
            continue
        crop_dir_rel = model_info.get("plate_crop_dir")
        crop_dir = resolve_rootish(crop_dir_rel).resolve()
        if not crop_dir.exists():
            videos.append(
                {
                    "video": name,
                    "status": "failed",
                    "failure_reason": "plate_crop_dir_not_found",
                    "crop_dir": rel(crop_dir),
                    "crop_files": [],
                }
            )
            continue
        crop_files = sorted(crop_dir.glob("*.jpg"))
        if frame_stride > 1:
            crop_files = crop_files[::frame_stride]
        if limit_per_video is not None:
            crop_files = crop_files[:limit_per_video]
        videos.append(
            {
                "video": name,
                "status": "ready",
                "failure_reason": None,
                "crop_dir": rel(crop_dir),
                "crop_files": crop_files,
                "frame_meta": video.get("frame_meta") or {},
                "target_track_id": video.get("target_track_id"),
                "target_frame_count": video.get("target_frame_count"),
                "detector_model_ref": model_info.get("model_ref"),
                "detector_plate_detection_rate": model_info.get("plate_detection_rate"),
                "event": event_specs.get(name, {}),
            }
        )
    return videos


def collapse_lines(lines: list[dict[str, Any]]) -> tuple[str, float]:
    if not lines:
        return "", 0.0
    ordered = sorted(lines, key=sort_key_for_bbox)
    texts = [str(item.get("text") or "").strip() for item in ordered if str(item.get("text") or "").strip()]
    confidences = [float(item.get("confidence") or 0.0) for item in ordered if str(item.get("text") or "").strip()]
    return "".join(texts), (statistics.fmean(confidences) if confidences else 0.0)


def choose_variant_result(variant_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not variant_results:
        return {
            "raw_text": "",
            "cleaned_text": "",
            "normalized_text": "",
            "ocr_confidence": 0.0,
            "format_valid": False,
            "province_code_valid": False,
            "correction_count": None,
            "variant": None,
            "line_count": 0,
            "failure_reason": "no_text",
        }
    return max(
        variant_results,
        key=lambda item: (
            int(item["format_valid"]),
            int(item["province_code_valid"]),
            int(bool(item["normalized_text"])),
            float(item["ocr_confidence"]),
            -(item["correction_count"] if item["correction_count"] is not None else 999),
            -abs(len(item["normalized_text"]) - 8),
        ),
    )


def temporal_vote(
    crop_results: list[dict[str, Any]],
    min_confidence: float,
) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    usable = [item for item in crop_results if item["normalized_text"]]
    preferred = [item for item in usable if item["ocr_confidence"] >= min_confidence]
    source = preferred or usable
    if not source:
        return {
            "plate_text": None,
            "vote_confidence": 0.0,
            "format_valid": False,
            "province_code_valid": False,
            "candidate_count": 0,
            "top_candidates": [],
        }

    for item in source:
        key = item["normalized_text"]
        weight = float(item["ocr_confidence"])
        if item["format_valid"]:
            weight += 0.5
        if item["province_code_valid"]:
            weight += 0.25
        bucket = grouped.setdefault(
            key,
            {
                "plate_text": key,
                "score": 0.0,
                "count": 0,
                "max_confidence": 0.0,
                "format_valid": False,
                "province_code_valid": False,
            },
        )
        bucket["score"] += weight
        bucket["count"] += 1
        bucket["max_confidence"] = max(bucket["max_confidence"], float(item["ocr_confidence"]))
        bucket["format_valid"] = bucket["format_valid"] or bool(item["format_valid"])
        bucket["province_code_valid"] = bucket["province_code_valid"] or bool(item["province_code_valid"])

    ranked = sorted(
        grouped.values(),
        key=lambda item: (
            int(item["format_valid"]),
            int(item["province_code_valid"]),
            item["score"],
            item["count"],
            item["max_confidence"],
        ),
        reverse=True,
    )
    total_score = sum(item["score"] for item in ranked) or 1.0
    best = ranked[0]
    return {
        "plate_text": best["plate_text"],
        "vote_confidence": round(best["score"] / total_score, 4),
        "format_valid": best["format_valid"],
        "province_code_valid": best["province_code_valid"],
        "candidate_count": len(ranked),
        "top_candidates": [
            {
                "plate_text": item["plate_text"],
                "score": round(item["score"], 4),
                "count": item["count"],
                "max_confidence": round(item["max_confidence"], 4),
                "format_valid": item["format_valid"],
                "province_code_valid": item["province_code_valid"],
            }
            for item in ranked[:5]
        ],
    }


def process_video_for_engine(
    engine: OcrEngine,
    video_input: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    if video_input["status"] != "ready":
        return {
            "video": video_input["video"],
            "status": "failed",
            "failure_reason": video_input["failure_reason"],
            "crop_count": 0,
            "processed_crops": 0,
            "ocr_read_count": 0,
            "format_valid_count": 0,
            "province_valid_count": 0,
            "temporal_vote": {
                "plate_text": None,
                "vote_confidence": 0.0,
                "format_valid": False,
                "province_code_valid": False,
                "candidate_count": 0,
                "top_candidates": [],
            },
        }

    event = video_input.get("event") or {}
    crop_results: list[dict[str, Any]] = []
    latencies: list[float] = []

    for index, crop_path in enumerate(video_input["crop_files"], start=1):
        image = cv2.imread(str(crop_path))
        if image is None:
            crop_results.append(
                {
                    "crop_file": rel(crop_path),
                    "frame": parse_frame_number(crop_path),
                    "raw_text": "",
                    "cleaned_text": "",
                    "normalized_text": "",
                    "ocr_confidence": 0.0,
                    "format_valid": False,
                    "province_code_valid": False,
                    "correction_count": None,
                    "variant": None,
                    "line_count": 0,
                    "failure_reason": "image_read_failed",
                }
            )
            continue

        variants = preprocess_variants(image, args.variants, args.upscale)
        variant_results: list[dict[str, Any]] = []
        t0 = time.perf_counter()
        for variant_name, variant_image in variants.items():
            try:
                lines = engine.recognize(variant_image)
            except Exception as exc:  # noqa: BLE001
                variant_results.append(
                    {
                        "raw_text": "",
                        "cleaned_text": "",
                        "normalized_text": "",
                        "ocr_confidence": 0.0,
                        "format_valid": False,
                        "province_code_valid": False,
                        "correction_count": None,
                        "variant": variant_name,
                        "line_count": 0,
                        "failure_reason": f"ocr_error:{exc}",
                    }
                )
                continue
            raw_text, confidence = collapse_lines(lines)
            normalized = normalize_plate_text(raw_text)
            variant_results.append(
                {
                    "raw_text": raw_text,
                    "cleaned_text": normalized["cleaned_text"],
                    "normalized_text": normalized["normalized_text"],
                    "ocr_confidence": round(float(confidence), 4),
                    "format_valid": normalized["format_valid"],
                    "province_code_valid": normalized["province_code_valid"],
                    "correction_count": normalized["correction_count"],
                    "variant": variant_name,
                    "line_count": len(lines),
                    "failure_reason": None if raw_text else "no_text",
                }
            )
        latency_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(latency_ms)
        best = choose_variant_result(variant_results)
        best["crop_file"] = rel(crop_path)
        best["frame"] = parse_frame_number(crop_path)
        best["latency_ms"] = round(latency_ms, 3)
        crop_results.append(best)
        if index % 50 == 0 or index == len(video_input["crop_files"]):
            print(f"  {engine.key} / {video_input['video']}: {index}/{len(video_input['crop_files'])} crop")

    readable = [item for item in crop_results if item["normalized_text"]]
    format_valid = [item for item in crop_results if item["format_valid"]]
    province_valid = [item for item in crop_results if item["province_code_valid"]]
    temporal = temporal_vote(crop_results, args.min_ocr_confidence)

    best_frame = int(event.get("best_frame") or 1)
    nearest_best = min(
        crop_results,
        key=lambda item: abs(int(item["frame"]) - best_frame),
        default=None,
    )
    highest_conf = max(
        readable,
        key=lambda item: (
            int(item["format_valid"]),
            int(item["province_code_valid"]),
            float(item["ocr_confidence"]),
        ),
        default=None,
    )
    first_frame = int(event.get("first_frame") or 1)
    first_readable = min((int(item["frame"]) for item in readable), default=None)
    fps = float(video_input.get("frame_meta", {}).get("fps") or 0.0)

    result = {
        "video": video_input["video"],
        "status": "completed",
        "failure_reason": None,
        "event_id": event.get("event_id"),
        "track_id": event.get("track_id_label"),
        "best_frame": best_frame,
        "target_track_id": video_input.get("target_track_id"),
        "source_plate_crop_dir": video_input.get("crop_dir"),
        "crop_count": len(video_input["crop_files"]),
        "processed_crops": len(crop_results),
        "ocr_read_count": len(readable),
        "format_valid_count": len(format_valid),
        "province_valid_count": len(province_valid),
        "mean_ocr_latency_ms": mean(latencies),
        "p95_ocr_latency_ms": p95(latencies),
        "source_detector_plate_detection_rate": video_input.get("detector_plate_detection_rate"),
        "best_frame_result": nearest_best,
        "highest_confidence_result": highest_conf,
        "temporal_vote": temporal,
        "time_to_first_readable_plate_frames": None if first_readable is None else first_readable - first_frame,
        "time_to_first_readable_plate_seconds": None
        if first_readable is None or not fps
        else round((first_readable - first_frame) / fps, 3),
        "sample_results": sorted(
            readable,
            key=lambda item: (
                int(item["format_valid"]),
                int(item["province_code_valid"]),
                float(item["ocr_confidence"]),
            ),
            reverse=True,
        )[:5],
        "latency_samples_ms": [round(item, 3) for item in latencies],
        "per_crop": crop_results if args.keep_per_crop else "omitted_use_--keep-per-crop",
    }
    if not crop_results:
        result["status"] = "failed"
        result["failure_reason"] = "no_crop_files"
    return result


def write_manual_review_seed(
    engine_key: str,
    summary: dict[str, Any],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "video",
                "event_id",
                "track_id",
                "best_frame",
                "plate_visible_manual",
                "plate_detected_model",
                "plate_bbox_correct_manual",
                "ocr_text_model",
                "ocr_text_normalized",
                "ocr_readable_manual",
                "ocr_correct_manual",
                "partial_match_manual",
                "format_valid_model",
                "province_code_valid_model",
                "failure_reason",
                "needs_qod_manual",
                "reviewer_note",
            ]
        )
        for video in summary["videos"]:
            vote = video.get("temporal_vote") or {}
            best = video.get("highest_confidence_result") or {}
            writer.writerow(
                [
                    video.get("video"),
                    video.get("event_id"),
                    video.get("track_id"),
                    video.get("best_frame"),
                    "",
                    engine_key,
                    "",
                    best.get("raw_text"),
                    vote.get("plate_text") or best.get("normalized_text"),
                    "",
                    "",
                    "",
                    vote.get("format_valid"),
                    vote.get("province_code_valid"),
                    video.get("failure_reason"),
                    "",
                    "",
                ]
            )


def build_report(run_meta: dict[str, Any], summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Plate OCR Baselines",
        "",
        f"Tarih: {run_meta['generated_at_utc']}",
        "",
        "## Amaç",
        "",
        "Plate detector crop'lari ustunde OCR baseline'larini calistirip Turk plaka normalize + "
        "temporal voting hattini olculebilir hale getirmek.",
        "",
        "## Konfigurasyon",
        "",
        f"* Detection summary: `{run_meta['detection_summary']}`",
        f"* Kaynak detector: `{run_meta['detector_key']}`",
        f"* OCR engine'leri: `{', '.join(run_meta['engines'])}`",
        f"* Variantlar: `{', '.join(run_meta['variants'])}` | upscale `{run_meta['upscale']}`",
        f"* OCR confidence esigi: `{run_meta['min_ocr_confidence']}`",
        "* OCR model ref'leri: "
        + "; ".join(
            f"{summary['ocr_engine']}={summary.get('model_ref', summary['ocr_engine'])}"
            for summary in summaries
        ),
        "",
        "## Sonuc (engine x video)",
        "",
        "| Engine | Video | Crop | Okunabilir | Format Valid | Province Valid | Vote | Vote Conf | Ort. Latency (ms) |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for summary in summaries:
        engine_key = summary["ocr_engine"]
        for video in summary["videos"]:
            vote = video.get("temporal_vote") or {}
            lines.append(
                f"| {engine_key} | {video['video']} | {video['crop_count']} | {video['ocr_read_count']} | "
                f"{video['format_valid_count']} | {video['province_valid_count']} | "
                f"{vote.get('plate_text')} | {vote.get('vote_confidence')} | {video.get('mean_ocr_latency_ms')} |"
            )
    lines += [
        "",
        "## Ciktilar",
        "",
        "* Summary JSON'ler: `models/benchmarks/artifacts/POCR-EXP-00X-*-summary.json`",
        f"* Manuel review seed CSV: `{run_meta['runs_dir']}/manual_review_<engine>.csv`",
        "* Manuel review referansi: `testing/templates/manual_plate_ocr_review.csv`",
        "",
        "## Notlar",
        "",
        "* Bu faz final OCR accuracy iddiasi kurmaz; detector sonrasi baseline usability calismasidir.",
        "* Temporal vote, ayni track icindeki tekrarli crop'larda en istikrarli metni secer.",
        "* Format valid = Turk plaka regex uyumu; province valid = 01-81 il kodu kontrolu.",
        "* Ham crop'lar ve OCR uzerine yazili goruntuler Git'e eklenmez.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plate OCR baseline over detector-produced crops.")
    parser.add_argument("--detection-summary", type=Path, default=DEFAULT_DETECTION_SUMMARY)
    parser.add_argument("--detector-key", default="auto", choices=["auto", "yolo", "yolos"])
    parser.add_argument("--engines", nargs="+", default=["paddle"], choices=list(ENGINE_META))
    parser.add_argument("--variants", nargs="+", default=["original", "gray"], choices=VARIANT_CHOICES)
    parser.add_argument("--upscale", type=float, default=2.0)
    parser.add_argument("--frame-stride", type=int, default=1, help="Crop listesinden her N'inci dosyayi isle.")
    parser.add_argument("--limit-per-video", type=int, default=None)
    parser.add_argument("--min-ocr-confidence", type=float, default=0.35)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--keep-per-crop", action="store_true")
    parser.add_argument("--paddle-lang", default="en")
    parser.add_argument("--easyocr-lang", default="en")
    parser.add_argument("--easyocr-gpu", action="store_true")
    parser.add_argument(
        "--easyocr-detector",
        action="store_true",
        help="Plate crop yerine tam goruntu OCR denenmek istenirse EasyOCR text detector'u da yukle.",
    )
    parser.add_argument("--tesseract-lang", default="eng")
    parser.add_argument("--tesseract-config", default="--psm 7")
    parser.add_argument("--fastplate-model", default="cct-s-v2-global-model")
    parser.add_argument("--fastplate-device", default="cpu", choices=["auto", "cpu", "cuda"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    detection_summary = load_json(args.detection_summary.resolve())
    detector_key = resolve_detector_key(detection_summary, args.detector_key)
    input_events = resolve_rootish(detection_summary.get("input_events"))
    event_specs = read_event_specs(input_events.resolve()) if input_events.exists() else {}
    videos = collect_video_inputs(
        summary=detection_summary,
        detector_key=detector_key,
        event_specs=event_specs,
        frame_stride=args.frame_stride,
        limit_per_video=args.limit_per_video,
    )

    engines = build_engines(args)
    if not engines:
        raise SystemExit(
            "Hic OCR engine yuklenemedi. Ornek kurulum: "
            "pip install fast-plate-ocr onnxruntime easyocr paddleocr pytesseract"
        )

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.runs_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    for engine in engines:
        meta = ENGINE_META[engine.key]
        print(f"\n=== {engine.key} basliyor ===")
        video_results = [process_video_for_engine(engine, video, args) for video in videos]
        all_latencies = [
            float(sample)
            for video in video_results
            for sample in video.get("latency_samples_ms", [])
        ]
        all_readable = sum(int(video.get("ocr_read_count") or 0) for video in video_results)
        all_format_valid = sum(int(video.get("format_valid_count") or 0) for video in video_results)
        all_province_valid = sum(int(video.get("province_valid_count") or 0) for video in video_results)
        summary = {
            "experiment_id": meta["experiment_id"],
            "ocr_engine": engine.key,
            "ocr_engine_label": meta["label"],
            "generated_at_utc": now_utc(),
            "source_experiment_id": detection_summary.get("experiment_id"),
            "source_stage": detection_summary.get("stage"),
            "source_detector_key": detector_key,
            "source_detection_summary": rel(args.detection_summary.resolve()),
            "input_events": rel(input_events.resolve()) if input_events.exists() else None,
            "model_ref": getattr(engine, "model_ref", engine.key),
            "variants": args.variants,
            "upscale": args.upscale,
            "frame_stride": args.frame_stride,
            "limit_per_video": args.limit_per_video,
            "min_ocr_confidence": args.min_ocr_confidence,
            "license_note": meta["license_note"],
            "videos": video_results,
            "aggregate": {
                "processed_tracks": len(video_results),
                "processed_crops": sum(int(video.get("processed_crops") or 0) for video in video_results),
                "ocr_read_count": all_readable,
                "format_valid_count": all_format_valid,
                "province_valid_count": all_province_valid,
                "tracks_with_temporal_vote": sum(
                    1 for video in video_results if (video.get("temporal_vote") or {}).get("plate_text")
                ),
                "mean_ocr_latency_ms": mean(all_latencies),
                "p95_ocr_latency_ms": p95(all_latencies),
            },
            "manual_review_template": "testing/templates/manual_plate_ocr_review.csv",
            "notes": [
                "Plate detector crop ciktilari kaynaktir.",
                "OCR sonucu raw + normalized olarak raporlanir.",
                "Turk plaka validasyonu regex + il kodu kurali ile yapilir.",
            ],
        }
        summary_path = args.artifact_dir / meta["summary_name"]
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        manual_review_path = args.runs_dir / f"manual_review_{engine.key}.csv"
        write_manual_review_seed(engine.key, summary, manual_review_path)
        summary["manual_review_seed"] = rel(manual_review_path)
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summaries.append(summary)
        print(
            json.dumps(
                {
                    "engine": engine.key,
                    "summary": rel(summary_path),
                    "manual_review_seed": rel(manual_review_path),
                    "tracks_with_vote": summary["aggregate"]["tracks_with_temporal_vote"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    report_suffix = "-".join(engine.key for engine in engines)
    report_path = args.report.with_name(f"{args.report.stem}_{report_suffix}{args.report.suffix}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    run_meta = {
        "generated_at_utc": now_utc(),
        "detection_summary": rel(args.detection_summary.resolve()),
        "detector_key": detector_key,
        "engines": [engine.key for engine in engines],
        "variants": args.variants,
        "upscale": args.upscale,
        "min_ocr_confidence": args.min_ocr_confidence,
        "runs_dir": rel(args.runs_dir.resolve()),
    }
    report_path.write_text(build_report(run_meta, summaries), encoding="utf-8")

    print("\n=== OCR OZET ===")
    print(
        json.dumps(
            {
                "report": rel(report_path),
                "summaries": [
                    {
                        "engine": summary["ocr_engine"],
                        "experiment_id": summary["experiment_id"],
                        "processed_crops": summary["aggregate"]["processed_crops"],
                        "tracks_with_vote": summary["aggregate"]["tracks_with_temporal_vote"],
                    }
                    for summary in summaries
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
