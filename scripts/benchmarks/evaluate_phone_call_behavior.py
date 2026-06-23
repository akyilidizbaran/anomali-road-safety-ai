#!/usr/bin/env python3
"""Evaluate phone-call behavior at session/event level from manual labels.

Hardened acceptance harness:

* Coverage is counted by distinct ``session_id`` (not rows), so neighboring clips
  from the same recording cannot inflate the positive/negative video count.
* Specificity is reported overall *and* on the hard-negative subset (rows that
  declare a confusable ``negative_subtype``). A baseline is not accepted unless the
  hard-negative specificity also clears the bar; easy negatives alone cannot pass.
* At least one occluded positive (``phone_visibility`` not_visible / partially)
  must be present, because the phone-not-visible case is the hard half of recall.
* ``not_evaluable`` predictions never count as a confident negative.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-002-phone_yolo26s_vitpose_lk_ear_temporal_fusion_v2-summary.json"
)
DEFAULT_REVIEW = ROOT / "testing" / "templates" / "manual_phone_call_review.csv"
DEFAULT_ARTIFACT = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-002-evaluation.json"
)
DEFAULT_REPORT = (
    ROOT / "testing" / "reports" / "phone_call_baseline_v2" / "evaluation.md"
)

POSITIVE_PREDICTION = "handheld_call_likely"
# A "hard" negative declares a behavior that is geometrically confusable with a
# call. Any non-empty declared subtype counts; a blank subtype is an easy negative.
HARD_NEGATIVE_SUBTYPES = {
    "face_scratch",
    "hair_glasses_adjust",
    "cheek_rest",
    "smoke_eat_drink",
    "passenger_phone",
    "earphone_adjust",
}
OCCLUDED_VISIBILITIES = {"not_visible", "partially_occluded"}


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def clean(value: Any) -> str:
    return str(value or "").strip().lower()


def evaluate_rows(
    rows: list[dict[str, str]],
    predictions: dict[str, str],
    min_positive_sessions: int = 3,
    min_negative_sessions: int = 5,
    min_hard_negative_sessions: int = 2,
    min_occluded_positive_sessions: int = 1,
    minimum_recall: float = 0.80,
    minimum_specificity: float = 0.90,
) -> dict[str, Any]:
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    hard_counts = {"tn": 0, "fp": 0}
    evaluated: list[dict[str, Any]] = []
    pending: list[str] = []

    positive_sessions: set[str] = set()
    negative_sessions: set[str] = set()
    hard_negative_sessions: set[str] = set()
    occluded_positive_sessions: set[str] = set()
    hard_subtype_counts: dict[str, int] = {}

    for row in rows:
        video = str(row.get("video") or "").strip()
        session_id = str(row.get("session_id") or video).strip() or video
        ground_truth = clean(row.get("ground_truth")) or "unknown"
        negative_subtype = clean(row.get("negative_subtype"))
        phone_visibility = clean(row.get("phone_visibility"))
        predicted_status = predictions.get(
            video, str(row.get("predicted_status") or "unknown")
        )
        predicted_positive = predicted_status == POSITIVE_PREDICTION

        if ground_truth not in {"positive", "negative"}:
            pending.append(video)
            continue

        actual_positive = ground_truth == "positive"
        is_hard_negative = (not actual_positive) and bool(negative_subtype)
        is_occluded_positive = actual_positive and phone_visibility in OCCLUDED_VISIBILITIES

        outcome = (
            "tp" if actual_positive and predicted_positive
            else "fn" if actual_positive
            else "fp" if predicted_positive
            else "tn"
        )
        counts[outcome] += 1

        if actual_positive:
            positive_sessions.add(session_id)
            if is_occluded_positive:
                occluded_positive_sessions.add(session_id)
        else:
            negative_sessions.add(session_id)
            if is_hard_negative:
                hard_negative_sessions.add(session_id)
                hard_subtype_counts[negative_subtype] = (
                    hard_subtype_counts.get(negative_subtype, 0) + 1
                )
                hard_counts["fp" if predicted_positive else "tn"] += 1

        evaluated.append(
            {
                "video": video,
                "session_id": session_id,
                "ground_truth": ground_truth,
                "predicted_status": predicted_status,
                "outcome": outcome,
                "negative_subtype": negative_subtype or None,
                "phone_visibility": phone_visibility or None,
                "is_hard_negative": is_hard_negative,
                "is_occluded_positive": is_occluded_positive,
            }
        )

    positive_count = counts["tp"] + counts["fn"]
    negative_count = counts["tn"] + counts["fp"]
    precision = safe_ratio(counts["tp"], counts["tp"] + counts["fp"])
    recall = safe_ratio(counts["tp"], positive_count)
    specificity = safe_ratio(counts["tn"], negative_count)
    hard_negative_specificity = safe_ratio(
        hard_counts["tn"], hard_counts["tn"] + hard_counts["fp"]
    )
    f1 = (
        round(2 * precision * recall / (precision + recall), 4)
        if precision is not None and recall is not None and precision + recall
        else None
    )

    coverage_blockers = [
        blocker
        for blocker in [
            f"positive_sessions={len(positive_sessions)}<{min_positive_sessions}"
            if len(positive_sessions) < min_positive_sessions else None,
            f"negative_sessions={len(negative_sessions)}<{min_negative_sessions}"
            if len(negative_sessions) < min_negative_sessions else None,
            f"hard_negative_sessions={len(hard_negative_sessions)}<{min_hard_negative_sessions}"
            if len(hard_negative_sessions) < min_hard_negative_sessions else None,
            f"occluded_positive_sessions={len(occluded_positive_sessions)}<{min_occluded_positive_sessions}"
            if len(occluded_positive_sessions) < min_occluded_positive_sessions else None,
        ]
        if blocker is not None
    ]
    quality_blockers = [
        blocker
        for blocker in [
            f"recall={recall}<{minimum_recall}"
            if recall is None or recall < minimum_recall else None,
            f"specificity={specificity}<{minimum_specificity}"
            if specificity is None or specificity < minimum_specificity else None,
            f"hard_negative_specificity={hard_negative_specificity}<{minimum_specificity}"
            if hard_negative_specificity is None
            or hard_negative_specificity < minimum_specificity else None,
        ]
        if blocker is not None
    ]
    coverage_ready = not coverage_blockers
    quality_ready = not quality_blockers

    return {
        "counts": counts,
        "hard_negative_counts": hard_counts,
        "labeled_video_count": len(evaluated),
        "positive_session_count": len(positive_sessions),
        "negative_session_count": len(negative_sessions),
        "hard_negative_session_count": len(hard_negative_sessions),
        "occluded_positive_session_count": len(occluded_positive_sessions),
        "hard_negative_subtypes": hard_subtype_counts,
        "pending_review_videos": pending,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "hard_negative_specificity": hard_negative_specificity,
        "f1": f1,
        "coverage_gate_passed": coverage_ready,
        "quality_gate_passed": quality_ready,
        "baseline_accepted": coverage_ready and quality_ready,
        "coverage_blockers": coverage_blockers,
        "quality_blockers": quality_blockers,
        "acceptance_requirements": {
            "min_positive_sessions": min_positive_sessions,
            "min_negative_sessions": min_negative_sessions,
            "min_hard_negative_sessions": min_hard_negative_sessions,
            "min_occluded_positive_sessions": min_occluded_positive_sessions,
            "minimum_recall": minimum_recall,
            "minimum_specificity": minimum_specificity,
        },
        "evaluated": evaluated,
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# Phone-Call Behavior Evaluation",
        "",
        f"* Baseline accepted: `{result['baseline_accepted']}`",
        f"* Coverage gate: `{result['coverage_gate_passed']}`",
        f"* Quality gate: `{result['quality_gate_passed']}`",
        f"* TP/FP/TN/FN: `{result['counts']}`",
        f"* Precision: `{result['precision']}`",
        f"* Recall: `{result['recall']}`",
        f"* Specificity (overall): `{result['specificity']}`",
        f"* Specificity (hard-negative): `{result['hard_negative_specificity']}`",
        f"* F1: `{result['f1']}`",
        "",
        "## Coverage (distinct sessions)",
        f"* Positive: `{result['positive_session_count']}` "
        f"(occluded: `{result['occluded_positive_session_count']}`)",
        f"* Negative: `{result['negative_session_count']}` "
        f"(hard: `{result['hard_negative_session_count']}`)",
        f"* Hard-negative subtypes: `{result['hard_negative_subtypes']}`",
        f"* Pending review: `{result['pending_review_videos']}`",
        "",
        "## Blockers",
        f"* Coverage: `{result['coverage_blockers'] or 'none'}`",
        f"* Quality: `{result['quality_blockers'] or 'none'}`",
        "",
        "Aday model, minimum pozitif/negatif/hard-negative/occluded-positive session",
        "kapsami ve hem genel hem hard-negative kalite esikleri ayni anda gecilmeden",
        "baseline olarak sabitlenmez.",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate phone-call behavior.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--manual-review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-positive-sessions", type=int, default=3)
    parser.add_argument("--min-negative-sessions", type=int, default=5)
    parser.add_argument("--min-hard-negative-sessions", type=int, default=2)
    parser.add_argument("--min-occluded-positive-sessions", type=int, default=1)
    parser.add_argument("--minimum-recall", type=float, default=0.80)
    parser.add_argument("--minimum-specificity", type=float, default=0.90)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = json.loads(args.summary.resolve().read_text(encoding="utf-8"))
    with args.manual_review.resolve().open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    predictions = {
        str(item.get("video")): str((item.get("behavior") or {}).get("phone_call_status"))
        for item in summary.get("videos", [])
    }
    result = evaluate_rows(
        rows,
        predictions,
        min_positive_sessions=args.min_positive_sessions,
        min_negative_sessions=args.min_negative_sessions,
        min_hard_negative_sessions=args.min_hard_negative_sessions,
        min_occluded_positive_sessions=args.min_occluded_positive_sessions,
        minimum_recall=args.minimum_recall,
        minimum_specificity=args.minimum_specificity,
    )
    result.update(
        {
            "experiment_id": summary.get("experiment_id"),
            "model_key": summary.get("model_key"),
            "created_at_utc": now_utc(),
            "summary": str(args.summary.resolve()),
            "manual_review": str(args.manual_review.resolve()),
        }
    )
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.artifact.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(build_report(result) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
