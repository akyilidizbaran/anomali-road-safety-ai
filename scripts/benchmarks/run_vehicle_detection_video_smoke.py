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

import run_condition_profile_video_smoke as condition_smoke


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
DEFAULT_CONDITION_CHECKPOINT = (
    ROOT
    / "models"
    / "checkpoints"
    / "condition_profile"
    / "COND-EXP-001-mobilenet_v3_small-best.pt"
)
DEFAULT_MANUAL_REVIEW = (
    ROOT
    / "testing"
    / "manual_reviews"
    / "vd_exp_002_dark_video_manual_review.json"
)
UNPROMOTED_CONDITION_PROFILES = {"fog_low_visibility"}


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


def summarize_condition_result(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") != "ok":
        return {
            "status": result.get("status", "failed"),
            "failure_reason": result.get("failure_reason", "unknown"),
            "detector_profile_used": "general",
            "specialist_promoted": False,
        }
    dominant_profile = result["dominant_profile"]
    profile_supported = dominant_profile not in UNPROMOTED_CONDITION_PROFILES
    routing_reason = result["routing_reason"]
    if not profile_supported:
        routing_reason = (
            f"{dominant_profile} is outside the current supported routing scope; "
            "general detector fallback remains active"
        )
    return {
        "status": "ok",
        "dominant_profile": dominant_profile,
        "dominant_confidence_mean": round(float(result["dominant_confidence_mean"]), 3),
        "mean_confidence": round(float(result["mean_confidence"]), 3),
        "sampled_frames": result["sampled_frames"],
        "profile_counts": result["profile_counts"],
        "top_mean_scores": result["top_mean_scores"],
        "profile_supported_in_current_scope": profile_supported,
        "detector_profile_used": "general",
        "specialist_promoted": False,
        "fallback_used": True,
        "routing_reason": routing_reason,
    }


def run_condition_profiles(
    videos: list[Path],
    checkpoint: Path,
    device: str,
    sample_every: int,
    confidence_threshold: float,
) -> dict[str, dict[str, Any]]:
    if not checkpoint.exists():
        raise FileNotFoundError(
            f"Condition checkpoint not found: {checkpoint}\n"
            "Pass --no-condition-profile to run vehicle detection without router metadata."
        )
    torch_device = condition_smoke.resolve_device(device)
    condition_model, condition_classes, condition_checkpoint = condition_smoke.load_checkpoint(
        checkpoint,
        torch_device,
    )
    image_size = int(condition_checkpoint.get("image_size", 224))
    tfm = condition_smoke.frame_transform(image_size)
    results = {}
    for video in videos:
        condition_result = condition_smoke.run_video(
            video=video.resolve(),
            model=condition_model,
            tfm=tfm,
            device=torch_device,
            classes=condition_classes,
            sample_every=sample_every,
            threshold=confidence_threshold,
        )
        results[str(video.resolve())] = summarize_condition_result(condition_result)
    return results


def load_manual_review(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Manual review file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def class_quality_from_manual_review(review: dict[str, Any] | None) -> dict[str, Any]:
    if not review:
        return {
            "manual_review_status": "not_reviewed",
            "class_review_required": False,
            "raw_detector_class_counts_are_final": False,
            "class_reliability": "unchecked",
            "warnings": ["manual_review_missing"],
            "event_policy": "do_not_claim_final_class_accuracy",
        }

    issue_confirmed = bool(review.get("class_confusion_confirmed"))
    if issue_confirmed:
        mitigation = review.get("runtime_mitigation", {}) or {}
        return {
            "manual_review_status": review.get("manual_status", "reviewed"),
            "class_review_required": bool(mitigation.get("class_review_required", False)),
            "raw_detector_class_counts_are_final": bool(
                mitigation.get("use_raw_detector_class_as_event_label", True)
            ),
            "class_reliability": "raw_detector_prediction_used",
            "warnings": ["manual_review_observed_motorcycle_car_confusion_model_improvement_needed"],
            "affected_object": review.get("affected_object"),
            "expected_class": review.get("expected_class"),
            "observed_raw_detector_class": review.get("observed_raw_detector_class"),
            "recommended_event_label": mitigation.get(
                "recommended_event_label",
                review.get("observed_raw_detector_class", "car"),
            ),
            "model_improvement_experiment": review.get("model_improvement_experiment"),
            "evidence_note": mitigation.get("evidence_note"),
            "event_policy": (
                "carry the detector class as predicted in event/evidence; use the manual observation only "
                "as a model improvement signal, not as a per-video runtime override"
            ),
        }

    return {
        "manual_review_status": review.get("manual_status", "reviewed"),
        "class_review_required": False,
        "raw_detector_class_counts_are_final": True,
        "class_reliability": "manual_review_passed_for_observed_scope",
        "warnings": [],
        "event_policy": "raw_detector_class_counts_can_be_reported_as_smoke-test_observation_only",
    }


def apply_manual_review(
    rows: list[dict[str, Any]],
    manual_review: dict[str, Any] | None,
) -> None:
    video_reviews = (manual_review or {}).get("videos", {})
    for row in rows:
        review = video_reviews.get(row["video"]) or video_reviews.get(Path(row["video"]).name)
        if review:
            row["manual_review"] = review
        row["class_quality"] = class_quality_from_manual_review(review)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {summary['report_title']}",
        "",
        "## Kapsam",
        "",
        "Bu rapor, secilen fine-tuned vehicle detector checkpoint'i ile lokal dark video",
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
        f"* Condition profile enabled: `{summary['condition_profile_enabled']}`",
        f"* Detector routing policy: `{summary['detector_routing_policy']}`",
        f"* Unpromoted condition profiles: `{summary['unpromoted_condition_profiles']}`",
        f"* Manual review enabled: `{summary['manual_review_enabled']}`",
        f"* Manual review source: `{summary.get('manual_review_source')}`",
        "",
        "## Video Sonuclari",
        "",
        "| Video | Condition | Cond Conf | Detector Profile | Evidence Class Policy | Frames | Detected Frames | Detections | Classes | Mean Conf | Mean ms | p95 ms | FPS | Annotated |",
        "|---|---|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in summary["videos"]:
        classes = ", ".join(f"{key}:{value}" for key, value in row["detections_by_class"].items()) or "-"
        condition = row.get("condition_profile") or {}
        class_quality = row.get("class_quality") or {}
        class_policy = (
            "raw_detector_class"
            if class_quality.get("raw_detector_class_counts_are_final")
            else "review_required"
        )
        lines.append(
            "| {video} | {condition_label} | {condition_conf} | {detector_profile} | {class_policy} | "
            "{frames_processed} | {frames_with_detections} | {total_detections} | "
            "{classes} | {mean_confidence} | {mean_pipeline_ms} | {p95_pipeline_ms} | "
            "{effective_fps} | {annotated} |".format(
                video=row["video"],
                condition_label=f"`{condition.get('dominant_profile', '-')}`",
                condition_conf=condition.get("dominant_confidence_mean", "-"),
                detector_profile=f"`{condition.get('detector_profile_used', 'general')}`",
                class_policy=f"`{class_policy}`",
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
            "* 2026-06-15 manuel review kararina gore ana arac `Test/video_1-3.mp4` boyunca her frame'de yakalanmaktadir.",
            "* Ana arac bbox davranisi stabil kabul edilmistir.",
            "* Düsuk threshold degerlerinde false positive gozlenmistir; `0.60` mevcut manual review kapsaminda false-positive pruning icin aday downstream evidence/final-acceptance gate degeridir.",
            "* Final confidence threshold degeri bu smoke test ile sabitlenmez; threshold sweep + manuel review sonrasi secilecektir.",
            "* `VD-EXP-002-GENERAL-YOLO11N`, mevcut MVP icin active/best detector olarak sabitlenmistir.",
            "* Condition classifier bu fazda detector secimini otomatik degistirmez; specialist modeller general modele gore daha iyi oldugu kanitlanmadan `general` fallback korunur.",
            "* `night_low_light` profilinin `general` fallback'e dusmesi condition classifier'in kotu cikmasi anlamina gelmez. Bu, night/rain/fog specialist detector'larin henuz general detector'a gore ustunlugunun kanitlanmamis olmasindan kaynaklanan bilincli runtime politikasidir.",
            "* `fog_low_visibility` bu fazda promoted/supported routing kapsami disinda tutulur.",
            "* Manual review ile bir failure case gorulse bile bu smoke pipeline raw detector class etiketini event/evidence tarafina oldugu gibi tasir.",
            "* Motorcycle/car karisikligi bu 3 videoya ozel runtime override ile ele alinmaz; `VD-EXP-006` denemesi basarisiz/regresyon kabul edildigi icin motorcycle ozel fine-tune simdilik ertelenmistir.",
        ]
    )
    issue_rows = [
        row
        for row in summary["videos"]
        if row.get("class_quality", {}).get("model_improvement_experiment")
        or int(row.get("detections_by_class", {}).get("motorcycle", 0)) > 0
    ]
    if issue_rows:
        lines.extend(
            [
                "",
                "## Motorcycle / Car Class Confusion Notu",
                "",
                "Kullanici manuel gozlemine gore `video_3` icinde normalde 1 araba + 1 motosiklet vardir.",
                "Ana arac her frame'de dogru tespit edilmektedir. Arka plandaki cok karanlik motosiklet ise gorunur oldugu karelerde sistematik bicimde `car` olarak siniflandirilmaktadir.",
                "Bu gozlem event/evidence tarafinda per-video override olarak kullanilmaz; detector `car` diyorsa event/evidence sinifi `car` olarak tasinir.",
                "Bu konu condition classifier ile cozulmez. Motorcycle-focused `VD-EXP-006` denemesi beklenen sonucu vermedigi icin bu baslik simdilik ertelenir; mevcut MVP raporunda ana arac / car detection ve evidence pipeline guvenceye alinir.",
                "",
                "Runtime politikasi:",
                "",
                "* Raw detector class count korunur ve event/evidence tarafina oldugu gibi tasinir.",
                "* Etkilenen sample, model gelistirme failure case'i olarak kaydedilir.",
                "* Runtime/demo downstream evidence/final-acceptance gate degeri henuz final degildir; `0.60` yalniz mevcut manual review adayidir.",
                "* Zaman kisiti nedeniyle agir vehicle/motorcycle tune yerine diger AI modullerinin baseline/tune asamasina gecilir.",
                "",
                "Detay aksiyon dosyasi:",
                "",
                "* `testing/reports/vd_exp_002_motorcycle_class_confusion_action.md`",
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
    parser.add_argument("--condition-checkpoint", type=Path, default=DEFAULT_CONDITION_CHECKPOINT)
    parser.add_argument("--condition-sample-every", type=int, default=15)
    parser.add_argument("--condition-confidence-threshold", type=float, default=0.65)
    parser.add_argument("--no-condition-profile", action="store_true")
    parser.add_argument("--manual-review", type=Path, default=DEFAULT_MANUAL_REVIEW)
    parser.add_argument("--no-manual-review", action="store_true")
    parser.add_argument("--experiment-id", default="VD-EXP-002-dark-video-smoke")
    parser.add_argument("--report-title", default="VD-EXP-002 Dark Video Smoke Test Summary")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    weights = args.weights.resolve()
    runs_dir = args.runs_dir.resolve()
    artifact_path = args.artifact.resolve()
    report_path = args.report.resolve()
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
    condition_results: dict[str, dict[str, Any]] = {}
    if not args.no_condition_profile:
        condition_results = run_condition_profiles(
            videos=[video.resolve() for video in args.videos],
            checkpoint=args.condition_checkpoint.resolve(),
            device=args.device,
            sample_every=args.condition_sample_every,
            confidence_threshold=args.condition_confidence_threshold,
        )

    model = YOLO(str(weights))
    runs_dir.mkdir(parents=True, exist_ok=True)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    videos = [
        run_video(
            model=model,
            video_path=video.resolve(),
            runs_dir=runs_dir,
            device=device,
            imgsz=args.imgsz,
            conf=args.conf,
            classes=args.classes or None,
            save_annotated=not args.no_save_annotated,
            max_frames=args.max_frames or None,
        )
        for video in args.videos
    ]
    for row in videos:
        abs_video = str((ROOT / row["video"]).resolve())
        row["condition_profile"] = condition_results.get(
            abs_video,
            {
                "status": "disabled",
                "detector_profile_used": "general",
                "specialist_promoted": False,
                "routing_reason": "condition profile disabled",
            },
        )
    manual_review = None if args.no_manual_review else load_manual_review(args.manual_review.resolve())
    apply_manual_review(videos, manual_review)
    summary = {
        "experiment_id": args.experiment_id,
        "report_title": args.report_title,
        "weights": str(weights.relative_to(ROOT)) if weights.is_relative_to(ROOT) else str(weights),
        "device": device,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "classes": args.classes,
        "runs_dir": str(runs_dir.relative_to(ROOT)) if runs_dir.is_relative_to(ROOT) else str(runs_dir),
        "condition_profile_enabled": not args.no_condition_profile,
        "condition_checkpoint": str(args.condition_checkpoint.relative_to(ROOT))
        if args.condition_checkpoint.is_relative_to(ROOT)
        else str(args.condition_checkpoint),
        "condition_sample_every": args.condition_sample_every,
        "condition_confidence_threshold": args.condition_confidence_threshold,
        "unpromoted_condition_profiles": sorted(UNPROMOTED_CONDITION_PROFILES),
        "detector_routing_policy": (
            "condition profile is advisory; specialist detector profiles are not promoted "
            "until condition-specific benchmarks beat the general detector"
        ),
        "manual_review_enabled": manual_review is not None,
        "manual_review_source": str(args.manual_review.relative_to(ROOT))
        if manual_review and args.manual_review.is_relative_to(ROOT)
        else (str(args.manual_review) if manual_review else None),
        "manual_review_id": manual_review.get("review_id") if manual_review else None,
        "videos": videos,
    }
    artifact_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(summary, report_path)
    print(f"Wrote JSON summary: {artifact_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
