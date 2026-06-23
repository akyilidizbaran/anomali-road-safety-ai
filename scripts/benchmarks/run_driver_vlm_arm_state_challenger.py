#!/usr/bin/env python3
"""Run a local vision-language challenger for driver arm-state audit labels."""

from __future__ import annotations

import argparse
import base64
import json
import re
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import requests


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "driver_vlm_arm_state"
EXPERIMENT_ID = "VLM-ARM-EXP-001"
MODEL_KEY = "local_vlm_driver_arm_state_json"

ALLOWED_STATES = {
    "hand_near_face",
    "arm_raised",
    "hands_on_wheel_candidate",
    "hand_off_wheel_candidate",
    "arms_visible_other",
    "unknown",
    "not_evaluable",
}

PROMPT = """You are auditing a traffic-safety driver cabin crop.
Return ONLY valid JSON, no markdown.

Schema:
{
  "driver_visible": true|false|null,
  "arms_visible": true|false|null,
  "arm_state": "hand_near_face"|"arm_raised"|"hands_on_wheel_candidate"|"hand_off_wheel_candidate"|"arms_visible_other"|"unknown"|"not_evaluable",
  "phone_visible": true|false|null,
  "confidence": number between 0 and 1,
  "reasons": ["short visual reasons"]
}

Rules:
- Use "hands_on_wheel_candidate" only when a driver's hand/arm is plausibly on the wheel area.
- Use "hand_near_face" when a driver's hand is close to the face or mouth.
- Use "unknown" when the image is too dark, occluded, or ambiguous.
- Do not infer a violation. This is metadata only.
"""


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def extract_first_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from an LLM response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    if start < 0:
        raise ValueError("No JSON object found")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(stripped)):
        char = stripped[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(stripped[start : index + 1])
    raise ValueError("Unclosed JSON object")


def normalize_response(raw: dict[str, Any]) -> dict[str, Any]:
    state = str(raw.get("arm_state") or "unknown")
    if state not in ALLOWED_STATES:
        state = "unknown"
    confidence = raw.get("confidence")
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = None
    reasons = raw.get("reasons")
    if not isinstance(reasons, list):
        reasons = []
    return {
        "driver_visible": raw.get("driver_visible"),
        "arms_visible": raw.get("arms_visible"),
        "arm_state": state,
        "phone_visible": raw.get("phone_visible"),
        "confidence": round(confidence, 4) if confidence is not None else None,
        "reasons": [str(item)[:120] for item in reasons[:5]],
    }


def encode_jpeg(image: Any, max_width: int, quality: int) -> str:
    height, width = image.shape[:2]
    if width > max_width:
        scale = max_width / width
        image = cv2.resize(
            image,
            (max_width, int(round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    ok, buffer = cv2.imencode(
        ".jpg",
        image,
        [int(cv2.IMWRITE_JPEG_QUALITY), quality],
    )
    if not ok:
        raise RuntimeError("Could not encode crop")
    return base64.b64encode(buffer.tobytes()).decode("ascii")


def crop_frame(
    frame: Any,
    record: dict[str, Any],
    source: str,
    padding: float,
) -> Any:
    height, width = frame.shape[:2]
    if source == "full_frame":
        return frame
    bbox = record.get("cabin_bbox_xyxy")
    if source == "vehicle":
        bbox = record.get("vehicle_bbox_xyxy") or bbox
    if not bbox:
        return frame
    x1, y1, x2, y2 = [float(value) for value in bbox]
    pad_x = (x2 - x1) * padding
    pad_y = (y2 - y1) * padding
    x1 = max(0, int(round(x1 - pad_x)))
    y1 = max(0, int(round(y1 - pad_y)))
    x2 = min(width, int(round(x2 + pad_x)))
    y2 = min(height, int(round(y2 + pad_y)))
    if x2 <= x1 or y2 <= y1:
        return frame
    return frame[y1:y2, x1:x2]


def call_ollama(
    endpoint: str,
    model: str,
    image_b64: str,
    prompt: str,
    timeout: float,
) -> tuple[str, float]:
    started = time.perf_counter()
    response = requests.post(
        endpoint,
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }
            ],
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=timeout,
    )
    latency_ms = (time.perf_counter() - started) * 1000.0
    response.raise_for_status()
    payload = response.json()
    content = (payload.get("message") or {}).get("content")
    if content is None:
        content = payload.get("response")
    if content is None:
        raise ValueError("Ollama response did not include message.content")
    return str(content), latency_ms


def select_records(
    records: list[dict[str, Any]],
    frame_numbers: set[int] | None,
    sample_stride: int,
    include_poor: bool,
) -> list[dict[str, Any]]:
    selected = []
    for item in records:
        frame = int(item["frame"])
        if frame_numbers is not None and frame not in frame_numbers:
            continue
        if frame_numbers is None and frame % sample_stride != 0:
            continue
        if not include_poor and item.get("visibility") not in {"good", "limited"}:
            continue
        selected.append(item)
    return selected


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[int(round((len(ordered) - 1) * 0.95))], 3)


def process_video(
    video_path: Path,
    cabin_video: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    frame_numbers = set(args.frames or []) if args.frames else None
    selected = select_records(
        cabin_video.get("per_frame", []),
        frame_numbers,
        args.sample_stride,
        args.include_poor,
    )
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    output_dir = args.runs_root / "vlm_arm_exp_001" / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    latencies = []
    parse_failures = 0
    try:
        for record in selected:
            frame_number = int(record["frame"])
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
            ok, frame = cap.read()
            if not ok:
                continue
            crop = crop_frame(frame, record, args.crop_source, args.crop_padding)
            crop_path = output_dir / f"frame_{frame_number:06d}_{args.crop_source}.jpg"
            cv2.imwrite(str(crop_path), crop)
            image_b64 = encode_jpeg(crop, args.max_width, args.jpeg_quality)
            try:
                text, latency = call_ollama(
                    args.endpoint,
                    args.model,
                    image_b64,
                    args.prompt,
                    args.timeout,
                )
                latencies.append(latency)
                normalized = normalize_response(extract_first_json_object(text))
                status = "ok"
            except Exception as exc:  # noqa: BLE001 - preserve model/API failure context.
                parse_failures += 1
                latency = None
                text = ""
                normalized = {
                    "driver_visible": None,
                    "arms_visible": None,
                    "arm_state": "unknown",
                    "phone_visible": None,
                    "confidence": None,
                    "reasons": [type(exc).__name__, str(exc)[:160]],
                }
                status = "failed"
            results.append(
                {
                    "frame": frame_number,
                    "visibility": record.get("visibility"),
                    "crop_uri": rel(crop_path),
                    "status": status,
                    "latency_ms": round(latency, 3) if latency is not None else None,
                    "vlm": normalized,
                    "raw_text": text[:1000],
                    "risk_enabled": False,
                }
            )
    finally:
        cap.release()
    states = Counter(item["vlm"]["arm_state"] for item in results)
    total = len(results)
    return {
        "video": video_path.name,
        "status": "completed",
        "view_profile": cabin_video.get("view_profile"),
        "sampled_frame_count": total,
        "parse_failure_count": parse_failures,
        "mean_vlm_latency_ms": mean(latencies),
        "p95_vlm_latency_ms": p95(latencies),
        "state_rates": {
            state: round(count / total, 4) if total else 0.0
            for state, count in sorted(states.items())
        },
        "per_frame": results,
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = []
    for video in summary["videos"]:
        rows.append(
            f"| {video['video']} | {video['sampled_frame_count']} | "
            f"{video['parse_failure_count']} | {video['state_rates']} | "
            f"{video['mean_vlm_latency_ms']} | {video['p95_vlm_latency_ms']} |"
        )
    return "\n".join(
        [
            "# VLM-ARM-EXP-001 Driver Arm-State Challenger",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            "Bu deney local VLM'i arm-state audit/challenger olarak ölçer. "
            "Risk üretmez ve pose baseline yerine geçmez.",
            "",
            f"* Provider: `{summary['provider']}`",
            f"* Model: `{summary['model']}`",
            f"* Crop source: `{summary['crop_source']}`",
            "",
            "| Video | Samples | Parse Fail | State Rates | Mean ms | P95 ms |",
            "|---|---:|---:|---|---:|---:|",
            *rows,
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local VLM arm-state challenger on cabin frames."
    )
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", choices=["ollama"], default="ollama")
    parser.add_argument("--endpoint", default="http://localhost:11434/api/chat")
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument(
        "--crop-source",
        choices=["cabin", "vehicle", "full_frame"],
        default="cabin",
    )
    parser.add_argument("--crop-padding", type=float, default=0.15)
    parser.add_argument("--sample-stride", type=int, default=25)
    parser.add_argument("--frames", type=int, nargs="*")
    parser.add_argument("--include-poor", action="store_true")
    parser.add_argument("--max-width", type=int, default=960)
    parser.add_argument("--jpeg-quality", type=int, default=88)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cabin_summary = json.loads(args.cabin_summary.resolve().read_text(encoding="utf-8"))
    selected_names = (
        {path.name for path in args.videos}
        if args.videos
        else {item.get("video") for item in cabin_summary.get("videos", [])}
    )
    videos = []
    for cabin_video in cabin_summary.get("videos", []):
        name = cabin_video.get("video")
        if name not in selected_names or cabin_video.get("status") != "completed":
            continue
        print(f"\n=== {name}: VLM driver arm-state challenger ===")
        videos.append(
            process_video(
                (args.videos_dir / str(name)).resolve(),
                cabin_video,
                args,
            )
        )
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "stage": "driver_vlm_arm_state_challenger",
        "created_at_utc": now_utc(),
        "decision": "candidate_not_selected_pending_manual_review",
        "provider": args.provider,
        "model": args.model,
        "model_key": MODEL_KEY,
        "endpoint": args.endpoint,
        "crop_source": args.crop_source,
        "sample_stride": args.sample_stride,
        "frames": args.frames,
        "risk_enabled": False,
        "input_cabin_summary": rel(args.cabin_summary.resolve()),
        "videos": videos,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    model_slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.model).strip("_") or "model"
    summary_path = args.artifact_dir / f"{EXPERIMENT_ID}-{model_slug}-summary.json"
    report_path = args.report_dir / "vlm_arm_exp_001_summary.md"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(build_report(summary) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": rel(summary_path),
                "report": rel(report_path),
                "completed_videos": len(videos),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
