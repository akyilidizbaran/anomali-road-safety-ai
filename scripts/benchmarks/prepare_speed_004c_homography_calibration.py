#!/usr/bin/env python3
"""Prepare SPEED-EXP-004C semi-manual homography calibration inputs.

This step extracts representative frames from the local demo videos and creates
a calibration profile template. It intentionally does not estimate km/h. The
template must be filled with measured road/world reference points before the
absolute-candidate speed experiment can run.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import cv2
except ImportError as exc:  # pragma: no cover - exercised by environment only
    raise SystemExit(
        "OpenCV is required for frame extraction. Run with `.venv-yolo-run/bin/python` "
        "or install `opencv-python` in the active environment."
    ) from exc


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = ROOT / "models" / "benchmarks" / "artifacts" / "TRK-EXP-001-yolo11n-bytetrack-event-skeletons-speed004b.json"
DEFAULT_VIDEOS_DIR = ROOT / "Test"
DEFAULT_RUNS_DIR = ROOT / "runs" / "speed" / "SPEED-EXP-004C-homography"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts" / "speed" / "SPEED-EXP-004C-homography"
DEFAULT_PROFILE = ROOT / "configs" / "speed_calibration" / "CALIB-DEMO-001.template.json"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "speed_exp_004c_homography_calibration_preparation.md"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def video_stem(video_name: str) -> str:
    return Path(video_name).stem


def unique_sorted(values: list[int]) -> list[int]:
    return sorted({max(0, int(v)) for v in values})


def event_frame_candidates(event: dict[str, Any]) -> list[dict[str, Any]]:
    target = event.get("target_vehicle") or {}
    frame_window = target.get("frame_window") or {}
    first_frame = int(frame_window.get("first_frame") or 0)
    last_frame = int(frame_window.get("last_frame") or first_frame)
    best_frame = int(frame_window.get("best_frame") or first_frame)
    mid_frame = int(round((first_frame + last_frame) / 2)) if last_frame >= first_frame else best_frame
    candidates = [
        ("first_track_frame", first_frame),
        ("mid_track_frame", mid_frame),
        ("best_target_frame", best_frame),
        ("last_track_frame", last_frame),
    ]
    return [
        {
            "role": role,
            "frame_id": max(0, int(frame_id)),
            "event_id": event.get("event_id"),
            "track_id": target.get("track_id"),
        }
        for role, frame_id in candidates
    ]


def read_frame(video_path: Path, frame_id: int) -> tuple[bool, Any, dict[str, Any]]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return False, None, {"failure_reason": "video_open_failed"}
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    safe_frame = min(max(0, frame_id), max(0, frame_count - 1)) if frame_count else max(0, frame_id)
    cap.set(cv2.CAP_PROP_POS_FRAMES, safe_frame)
    ok, frame = cap.read()
    cap.release()
    metadata = {
        "requested_frame": frame_id,
        "extracted_frame": safe_frame,
        "frame_count": frame_count,
        "fps": round(fps, 6),
        "source_resolution": f"{width}x{height}" if width and height else None,
    }
    if not ok:
        metadata["failure_reason"] = "frame_read_failed"
    return ok, frame, metadata


def extract_frames(
    events: list[dict[str, Any]],
    videos_dir: Path,
    runs_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_video: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        source = event.get("source") or {}
        source_video = source.get("source_video")
        if source_video:
            by_video[source_video].extend(event_frame_candidates(event))

    frame_dir = runs_dir / "calibration_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for source_video, candidates in sorted(by_video.items()):
        video_path = videos_dir / source_video
        if not video_path.exists():
            failures.append(
                {
                    "video": source_video,
                    "status": "failed",
                    "failure_reason": "source_video_not_found",
                    "checked_path": rel(video_path),
                }
            )
            continue

        # Keep one image per role/frame. If multiple events share a frame, the
        # first candidate carries the event reference and the filename stays
        # deterministic.
        unique: dict[tuple[str, int], dict[str, Any]] = {}
        for candidate in candidates:
            unique.setdefault((candidate["role"], int(candidate["frame_id"])), candidate)

        for (role, frame_id), candidate in sorted(unique.items(), key=lambda item: (item[0][1], item[0][0])):
            ok, frame, metadata = read_frame(video_path, frame_id)
            row = {
                "video": source_video,
                "event_id": candidate.get("event_id"),
                "track_id": candidate.get("track_id"),
                "role": role,
                **metadata,
            }
            if not ok:
                row["status"] = "failed"
                failures.append(row)
                continue
            output_path = frame_dir / f"{video_stem(source_video)}_{role}_frame_{metadata['extracted_frame']:06d}.jpg"
            cv2.imwrite(str(output_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
            row.update(
                {
                    "status": "written",
                    "frame_uri": rel(output_path),
                    "git_tracking": "ignored_runs_artifact",
                }
            )
            extracted.append(row)

    return extracted, failures


def make_profile_template(
    profile_path: Path,
    events: list[dict[str, Any]],
    extracted_frames: list[dict[str, Any]],
    overwrite: bool,
) -> dict[str, Any]:
    if profile_path.exists() and not overwrite:
        return load_json(profile_path)

    primary_frame = next(
        (row for row in extracted_frames if row.get("role") == "best_target_frame" and row.get("status") == "written"),
        extracted_frames[0] if extracted_frames else None,
    )
    videos = sorted({(event.get("source") or {}).get("source_video") for event in events if (event.get("source") or {}).get("source_video")})
    profile = {
        "calibration_profile_id": "CALIB-DEMO-001",
        "experiment_id": "SPEED-EXP-004C",
        "status": "needs_manual_points",
        "created_at": now_utc(),
        "calibration_method": "semi_manual_planar_homography",
        "scope": {
            "camera_setup": "fixed_roadside_demo_camera",
            "speed_output_role": "absolute_candidate_only",
            "not_for_legal_enforcement": True,
            "requires_measured_reference": True,
        },
        "source": {
            "videos": videos,
            "recommended_calibration_frame_uri": primary_frame.get("frame_uri") if primary_frame else None,
            "recommended_video": primary_frame.get("video") if primary_frame else None,
            "recommended_frame_id": primary_frame.get("extracted_frame") if primary_frame else None,
        },
        "manual_inputs_required": {
            "image_points_px": [
                {"id": "P1", "x": None, "y": None, "description": "road-plane reference point"},
                {"id": "P2", "x": None, "y": None, "description": "road-plane reference point"},
                {"id": "P3", "x": None, "y": None, "description": "road-plane reference point"},
                {"id": "P4", "x": None, "y": None, "description": "road-plane reference point"},
            ],
            "world_points_m": [
                {"id": "P1", "x_m": None, "y_m": None},
                {"id": "P2", "x_m": None, "y_m": None},
                {"id": "P3", "x_m": None, "y_m": None},
                {"id": "P4", "x_m": None, "y_m": None},
            ],
            "road_roi_px": [
                {"id": "R1", "x": None, "y": None},
                {"id": "R2", "x": None, "y": None},
                {"id": "R3", "x": None, "y": None},
                {"id": "R4", "x": None, "y": None},
            ],
            "reference_measurement_note": "Measure at least four coplanar road points in meters. Prefer lane markings, curb corners, or taped reference points visible in the frame.",
        },
        "validation_requirements": [
            "At least four non-collinear image/world point pairs on the road plane.",
            "Reference points must be measured in the same metric coordinate system.",
            "Do not use vehicle body or plate corners as world-plane calibration points unless their ground contact projection is known.",
            "Report reprojection error before using the profile for any absolute speed candidate.",
        ],
        "output_policy": {
            "estimated_kmh_field": "candidate only",
            "required_warning_flags": [
                "semi_manual_calibration",
                "absolute_candidate_not_final",
                "not_for_legal_enforcement",
            ],
        },
    }
    write_json(profile_path, profile)
    return profile


def write_report(
    report_path: Path,
    summary: dict[str, Any],
    profile_path: Path,
) -> None:
    rows = summary["extracted_frames"]
    failures = summary["failures"]
    lines = [
        "# SPEED-EXP-004C Homography Calibration Preparation",
        "",
        "Bu rapor `SPEED-EXP-004C` için yarı manuel homografi kalibrasyon hazırlığını özetler.",
        "Bu aşama **mutlak km/s üretmez**; yalnız ölçülü referans noktaları seçilecek kareleri ve kalibrasyon profil şablonunu hazırlar.",
        "",
        "## Karar",
        "",
        "* Çalıştırma yeri: local MacBook.",
        "* Gerekçe: Eğitim/GPU yok; işlem OpenCV frame extraction + manuel ölçüm noktası seçimi + homografi doğrulamasıdır.",
        "* Colab gerekmez; Drive I/O ve küçük dosya yönetimi bu adım için gereksiz yavaşlık üretir.",
        "",
        "## Üretilen Kalibrasyon Girdileri",
        "",
        f"* Kalibrasyon profil şablonu: `{rel(profile_path)}`",
        f"* Frame çıktı klasörü: `{summary['runs_dir']}`",
        f"* Summary JSON: `{summary['summary_json']}`",
        "",
        "## Çıkarılan Kareler",
        "",
        "| Video | Rol | Frame | Çözünürlük | Çıktı |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['video']}` | `{row['role']}` | {row['extracted_frame']} | "
            f"{row.get('source_resolution') or '-'} | `{row['frame_uri']}` |"
        )

    if failures:
        lines.extend(["", "## Hatalar", ""])
        for failure in failures:
            lines.append(
                f"* `{failure.get('video')}` frame `{failure.get('requested_frame', '-')}`: "
                f"{failure.get('failure_reason')}"
            )

    lines.extend(
        [
            "",
            "## Manuel Doldurulacak Alanlar",
            "",
            "1. `configs/speed_calibration/CALIB-DEMO-001.template.json` dosyasını kopyalayarak aktif bir profil oluştur.",
            "2. En az dört adet yol düzlemi noktasını piksel koordinatı olarak gir: `image_points_px`.",
            "3. Aynı noktaların gerçek dünyadaki metre koordinatlarını gir: `world_points_m`.",
            "4. Kullanılacak yol bölgesini `road_roi_px` ile sınırla.",
            "5. Homografi reprojection error kabul edilebilir değilse mutlak hız adayı üretme.",
            "",
            "## Notlar",
            "",
            "* Bu deney yasal/hukuki hız ölçümü değildir; yalnız karar destek için `absolute_candidate` üretmeye hazırlanır.",
            "* Plaka ölçeği ve VATTR sinyalleri 004B'de sanity-check olarak kalır; 004C'nin ana katkısı yol düzlemi kalibrasyonudur.",
            "* Ölçülü referans yoksa sistem 004A relative speed + 004B sanity-check fallback hattında kalmalıdır.",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--overwrite-profile", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_json(args.events)
    events = data.get("events") or []
    if not events:
        raise SystemExit(f"No events found in {args.events}")

    extracted, failures = extract_frames(events, args.videos_dir, args.runs_dir)
    profile = make_profile_template(args.profile, events, extracted, args.overwrite_profile)

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.artifact_dir / "speed_exp_004c_homography_calibration_prep_summary.json"
    summary = {
        "experiment_id": "SPEED-EXP-004C",
        "stage": "homography_calibration_preparation",
        "created_at": now_utc(),
        "status": "prepared" if extracted else "failed",
        "source_events": rel(args.events),
        "videos_dir": rel(args.videos_dir),
        "runs_dir": rel(args.runs_dir),
        "profile_template": rel(args.profile),
        "profile_status": profile.get("status"),
        "summary_json": rel(summary_path),
        "extracted_frame_count": len(extracted),
        "failure_count": len(failures),
        "extracted_frames": extracted,
        "failures": failures,
        "next_step": "Fill image_points_px/world_points_m in a copied calibration profile, then run homography validation.",
    }
    write_json(summary_path, summary)
    write_report(args.report, summary, args.profile)
    print(json.dumps({k: summary[k] for k in ["status", "extracted_frame_count", "failure_count", "profile_template", "summary_json"]}, indent=2))


if __name__ == "__main__":
    main()
