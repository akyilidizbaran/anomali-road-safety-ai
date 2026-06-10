#!/usr/bin/env python3
"""Run vehicle tracking baseline experiments on local test videos.

This script writes large annotated videos under ignored `runs/` paths and
small JSON summaries under `models/benchmarks/artifacts/`.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import torch
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VIDEOS = [ROOT / "Test" / f"video_{idx}.mp4" for idx in range(1, 4)]
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_COMPARISON_CSV = ROOT / "models" / "benchmarks" / "tracking" / "tracking_baseline_comparison.csv"
DEFAULT_RUNS_DIR = ROOT / "runs" / "tracking"

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

EXPERIMENTS = {
    "TRK-EXP-001": {
        "tracker": "ByteTrack",
        "tracker_config": "bytetrack.yaml",
        "decision": "completed_first_baseline",
    },
    "TRK-EXP-002": {
        "tracker": "BoT-SORT",
        "tracker_config": "botsort.yaml_reid_off",
        "ultralytics_tracker": "botsort.yaml",
        "decision": "completed_second_baseline",
    },
}


@dataclass
class TrackState:
    seen_frames: list[int] = field(default_factory=list)
    centers: list[tuple[float, float]] = field(default_factory=list)
    class_votes: Counter[str] = field(default_factory=Counter)
    raw_classes: list[str] = field(default_factory=list)
    confs: list[float] = field(default_factory=list)
    last_frame: int | None = None
    missing_gaps: list[int] = field(default_factory=list)
    best_frame_idx: int | None = None
    best_conf: float = 0.0
    best_bbox_xyxy: list[float] | None = None


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * 0.95))
    return round(ordered[idx], 3)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.fmean(values), 3)


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def open_writer(video_path: Path, output_path: Path, fps: float, width: int, height: int) -> cv2.VideoWriter:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer for {output_path} from {video_path}")
    return writer


def update_track_state(
    states: dict[int, TrackState],
    frame_idx: int,
    track_id: int,
    class_name: str,
    conf: float,
    bbox_xyxy: list[float],
    center: tuple[float, float],
) -> None:
    state = states[track_id]
    if state.last_frame is not None and frame_idx - state.last_frame > 1:
        state.missing_gaps.append(frame_idx - state.last_frame - 1)
    state.last_frame = frame_idx
    state.seen_frames.append(frame_idx)
    state.centers.append(center)
    state.raw_classes.append(class_name)
    state.class_votes[class_name] += conf
    state.confs.append(conf)
    if conf > state.best_conf:
        state.best_conf = conf
        state.best_frame_idx = frame_idx
        state.best_bbox_xyxy = [round(float(v), 2) for v in bbox_xyxy]


def draw_trails(frame: Any, history: dict[int, list[tuple[int, int]]]) -> None:
    for track_id, points in history.items():
        if len(points) < 2:
            continue
        color = (
            int((track_id * 37) % 255),
            int((track_id * 17) % 255),
            int((track_id * 67) % 255),
        )
        for start, end in zip(points[-20:-1], points[-19:]):
            cv2.line(frame, start, end, color, 2)


def summarize_tracks(states: dict[int, TrackState]) -> dict[str, Any]:
    track_ages = [len(state.seen_frames) for state in states.values()]
    missing_counts = [sum(state.missing_gaps) for state in states.values()]
    raw_switches = 0
    suppressed = 0
    track_rows = []

    for track_id, state in sorted(states.items()):
        stable_class = state.class_votes.most_common(1)[0][0] if state.class_votes else "unknown"
        switches = sum(
            1 for prev, cur in zip(state.raw_classes, state.raw_classes[1:]) if prev != cur
        )
        raw_switches += switches
        suppressed += sum(1 for cls in state.raw_classes if cls != stable_class)
        first = state.seen_frames[0] if state.seen_frames else None
        last = state.seen_frames[-1] if state.seen_frames else None
        track_rows.append(
            {
                "track_id": track_id,
                "track_age_frames": len(state.seen_frames),
                "first_frame": first,
                "last_frame": last,
                "stable_class": stable_class,
                "class_votes": {k: round(float(v), 3) for k, v in state.class_votes.items()},
                "raw_class_switches": switches,
                "missing_frame_count": sum(state.missing_gaps),
                "missing_gap_count": len(state.missing_gaps),
                "mean_confidence": mean(state.confs),
                "best_frame_idx": state.best_frame_idx,
                "best_confidence": round(float(state.best_conf), 4),
                "best_bbox_xyxy": state.best_bbox_xyxy,
            }
        )

    return {
        "unique_track_count": len(states),
        "average_track_age_frames": mean(track_ages),
        "max_track_age_frames": max(track_ages) if track_ages else 0,
        "average_missing_frame_count": mean(missing_counts),
        "class_switch_raw_count": raw_switches,
        "class_switch_suppressed_count": suppressed,
        "tracks": track_rows,
    }


def run_video(
    experiment_id: str,
    tracker_config: str,
    model_path: Path,
    video_path: Path,
    output_dir: Path,
    device: str,
    imgsz: int,
    conf: float,
) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    output_video = output_dir / f"{video_path.stem}_tracked.mp4"
    writer = open_writer(video_path, output_video, fps, width, height)

    model = YOLO(str(model_path))
    states: dict[int, TrackState] = defaultdict(TrackState)
    trail_history: dict[int, list[tuple[int, int]]] = defaultdict(list)

    active_counts: list[int] = []
    pipeline_ms: list[float] = []
    preprocess_ms: list[float] = []
    inference_ms: list[float] = []
    postprocess_ms: list[float] = []
    frames_with_tracks = 0
    total_track_observations = 0
    frame_idx = 0
    start_wall = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        frame_start = time.perf_counter()
        results = model.track(
            frame,
            persist=True,
            tracker=tracker_config,
            classes=list(VEHICLE_CLASSES.keys()),
            conf=conf,
            imgsz=imgsz,
            device=device,
            verbose=False,
        )
        frame_ms = (time.perf_counter() - frame_start) * 1000.0
        pipeline_ms.append(frame_ms)

        result = results[0]
        speed = getattr(result, "speed", {}) or {}
        if "preprocess" in speed:
            preprocess_ms.append(float(speed["preprocess"]))
        if "inference" in speed:
            inference_ms.append(float(speed["inference"]))
        if "postprocess" in speed:
            postprocess_ms.append(float(speed["postprocess"]))

        active_this_frame = 0
        if result.boxes is not None and getattr(result.boxes, "is_track", False):
            ids = result.boxes.id
            cls = result.boxes.cls
            confs = result.boxes.conf
            xyxy = result.boxes.xyxy
            xywh = result.boxes.xywh
            if ids is not None:
                ids_list = ids.int().cpu().tolist()
                cls_list = cls.int().cpu().tolist()
                conf_list = confs.cpu().tolist()
                xyxy_list = xyxy.cpu().tolist()
                xywh_list = xywh.cpu().tolist()
                active_this_frame = len(ids_list)
                total_track_observations += active_this_frame
                for track_id, class_id, score, box_xyxy, box_xywh in zip(
                    ids_list, cls_list, conf_list, xyxy_list, xywh_list
                ):
                    class_name = VEHICLE_CLASSES.get(int(class_id), str(class_id))
                    center = (float(box_xywh[0]), float(box_xywh[1]))
                    update_track_state(
                        states,
                        frame_idx,
                        int(track_id),
                        class_name,
                        float(score),
                        [float(v) for v in box_xyxy],
                        center,
                    )
                    trail_history[int(track_id)].append((int(center[0]), int(center[1])))
                    if len(trail_history[int(track_id)]) > 40:
                        trail_history[int(track_id)].pop(0)

        if active_this_frame:
            frames_with_tracks += 1
        active_counts.append(active_this_frame)

        annotated = result.plot()
        draw_trails(annotated, trail_history)
        writer.write(annotated)

    cap.release()
    writer.release()

    wall_time_s = time.perf_counter() - start_wall
    track_summary = summarize_tracks(states)
    return {
        "video": video_path.name,
        "input_frame_count_reported": frame_count,
        "frames_processed": frame_idx,
        "fps_source": round(fps, 3),
        "resolution": f"{width}x{height}",
        "frames_with_tracks": frames_with_tracks,
        "track_frame_ratio": round(frames_with_tracks / frame_idx, 4) if frame_idx else 0,
        "total_track_observations": total_track_observations,
        "active_track_count_mean": mean(active_counts),
        "active_track_count_max": max(active_counts) if active_counts else 0,
        "mean_pipeline_ms": mean(pipeline_ms),
        "p95_pipeline_ms": p95(pipeline_ms),
        "mean_preprocess_ms": mean(preprocess_ms),
        "mean_inference_ms": mean(inference_ms),
        "p95_inference_ms": p95(inference_ms),
        "mean_postprocess_ms": mean(postprocess_ms),
        "wall_time_s": round(wall_time_s, 3),
        "processed_fps_wall": round(frame_idx / wall_time_s, 3) if wall_time_s else None,
        "annotated_video": str(output_video.relative_to(ROOT)),
        **track_summary,
    }


def update_comparison_csv(csv_path: Path, summary: dict[str, Any]) -> None:
    if not csv_path.exists():
        return
    rows: list[dict[str, str]] = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            if row.get("experiment_id") == summary["experiment_id"]:
                row.update(
                    {
                        "tracker": summary["tracker"],
                        "tracker_config": summary["tracker_config"],
                        "detector": Path(summary["model"]).name,
                        "source": "Test/video_1-3_manual",
                        "condition_profile": summary["condition_profile"],
                        "processed_frames": str(summary["totals"]["frames_processed"]),
                        "active_track_count": str(summary["totals"]["unique_track_count"]),
                        "new_track_count": str(summary["totals"]["unique_track_count"]),
                        "lost_track_count": "TBD_manual",
                        "recovered_track_count": "TBD_manual",
                        "mean_pipeline_latency_ms": str(summary["totals"]["mean_pipeline_ms"]),
                        "p95_pipeline_latency_ms": str(summary["totals"]["p95_pipeline_ms"]),
                        "pipeline_fps": str(summary["totals"]["processed_fps_wall"]),
                        "avg_track_age_frames": str(summary["totals"]["average_track_age_frames"]),
                        "id_switch_count": "TBD_manual",
                        "fragmentation_count": "TBD_manual",
                        "class_switch_raw_count": str(summary["totals"]["class_switch_raw_count"]),
                        "class_switch_suppressed_count": str(summary["totals"]["class_switch_suppressed_count"]),
                        "speed_trail_usable": "TBD_manual",
                        "plate_temporal_voting_usable": "TBD_manual",
                        "evidence_track_usable": "TBD_manual",
                        "decision": summary["decision"],
                        "notes": "Automated tracking run completed; ID switches and usability require manual review",
                    }
                )
            rows.append(row)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_totals(videos: list[dict[str, Any]]) -> dict[str, Any]:
    frames = sum(v["frames_processed"] for v in videos)
    observations = sum(v["total_track_observations"] for v in videos)
    unique_tracks = sum(v["unique_track_count"] for v in videos)
    wall = sum(v["wall_time_s"] for v in videos)
    return {
        "frames_processed": frames,
        "total_track_observations": observations,
        "unique_track_count": unique_tracks,
        "mean_pipeline_ms": mean([v["mean_pipeline_ms"] for v in videos if v["mean_pipeline_ms"] is not None]),
        "p95_pipeline_ms": max(v["p95_pipeline_ms"] for v in videos if v["p95_pipeline_ms"] is not None),
        "processed_fps_wall": round(frames / wall, 3) if wall else None,
        "average_track_age_frames": mean(
            [v["average_track_age_frames"] for v in videos if v["average_track_age_frames"] is not None]
        ),
        "class_switch_raw_count": sum(v["class_switch_raw_count"] for v in videos),
        "class_switch_suppressed_count": sum(v["class_switch_suppressed_count"] for v in videos),
    }


def run_experiment(args: argparse.Namespace, experiment_id: str) -> dict[str, Any]:
    cfg = EXPERIMENTS[experiment_id]
    tracker_yaml = cfg.get("ultralytics_tracker", cfg["tracker_config"])
    run_dir = args.runs_dir / f"{experiment_id}-{Path(args.model).stem}-{cfg['tracker'].lower().replace('-', '')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    videos = [
        run_video(
            experiment_id=experiment_id,
            tracker_config=tracker_yaml,
            model_path=args.model,
            video_path=video,
            output_dir=run_dir,
            device=args.device,
            imgsz=args.imgsz,
            conf=args.conf,
        )
        for video in args.videos
    ]
    summary = {
        "experiment_id": experiment_id,
        "tracker": cfg["tracker"],
        "tracker_config": cfg["tracker_config"],
        "ultralytics_tracker": tracker_yaml,
        "model": str(args.model.relative_to(ROOT) if args.model.is_relative_to(ROOT) else args.model),
        "condition_profile": args.condition_profile,
        "device": args.device,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "classes": {str(k): v for k, v in VEHICLE_CLASSES.items()},
        "decision": cfg["decision"],
        "runs_dir": str(run_dir.relative_to(ROOT)),
        "videos": videos,
        "totals": build_totals(videos),
        "manual_review_required": True,
        "manual_review_template": "testing/templates/manual_tracking_review.csv",
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    out = args.artifact_dir / f"{experiment_id}-{Path(args.model).stem}-{cfg['tracker'].lower().replace('-', '')}-summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    update_comparison_csv(args.comparison_csv, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=ROOT / "yolo11n.pt")
    parser.add_argument("--videos", type=Path, nargs="+", default=DEFAULT_VIDEOS)
    parser.add_argument("--experiments", nargs="+", default=["TRK-EXP-001", "TRK-EXP-002"])
    parser.add_argument("--device", default="auto")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--condition-profile", default="dark")
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--comparison-csv", type=Path, default=DEFAULT_COMPARISON_CSV)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    args = parser.parse_args()
    args.model = args.model.resolve()
    args.videos = [video.resolve() for video in args.videos]
    args.artifact_dir = args.artifact_dir.resolve()
    args.comparison_csv = args.comparison_csv.resolve()
    args.runs_dir = args.runs_dir.resolve()
    args.device = resolve_device(args.device)
    unknown = [exp for exp in args.experiments if exp not in EXPERIMENTS]
    if unknown:
        raise SystemExit(f"Unknown experiments: {unknown}")
    return args


def main() -> None:
    args = parse_args()
    summaries = []
    for experiment_id in args.experiments:
        print(f"Running {experiment_id} on {len(args.videos)} video(s) with {args.model.name}")
        summaries.append(run_experiment(args, experiment_id))
    print(json.dumps({s["experiment_id"]: s["totals"] for s in summaries}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
