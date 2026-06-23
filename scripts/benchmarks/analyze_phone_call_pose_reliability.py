#!/usr/bin/env python3
"""Analyze pose reliability for phone-call behavior decisions.

This is a generalization diagnostic, not a behavior labeler. It answers:

* Is the pose evidence strong enough to make a phone-call decision?
* Where should the system prefer ``not_evaluable`` over negative/candidate?
* Which videos depend heavily on optical-flow recovery or weak keypoints?
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARM_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "ARM-EXP-001-vitpose_b_lk_arm_tracker_v1-summary.json"
)
DEFAULT_ARTIFACT = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "phone_call_baseline_v2"
    / "PHONE-CALL-EXP-007-pose_reliability.json"
)
DEFAULT_REPORT = (
    ROOT
    / "testing"
    / "reports"
    / "phone_call_baseline_v2"
    / "pose_reliability.md"
)
EXPERIMENT_ID = "PHONE-CALL-EXP-007"
MODEL_KEY = "phone_call_pose_reliability_diagnostic_v1"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def safe_ratio(numerator: float, denominator: float) -> float:
    return round(float(numerator) / float(denominator), 4) if denominator else 0.0


def longest_boolean_run(values: list[bool], target: bool = True) -> int:
    longest = 0
    current = 0
    for value in values:
        if value is target:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def point_confidences(record: dict[str, Any]) -> list[float]:
    return [
        float(point.get("confidence") or 0.0)
        for point in (record.get("points") or {}).values()
    ]


def wrist_source_counts(records: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        for side_state in (record.get("side_states") or {}).values():
            source = side_state.get("wrist_source")
            if source:
                counts[str(source)] += 1
    return counts


def summarize_video(
    video_item: dict[str, Any],
    min_evaluable_rate: float = 0.45,
    borderline_evaluable_rate: float = 0.55,
    min_complete_arm_rate: float = 0.35,
    max_optical_flow_point_rate: float = 0.35,
    borderline_optical_flow_wrist_rate: float = 0.30,
    max_identity_resets: int = 5,
    min_mean_keypoint_confidence: float = 0.45,
) -> dict[str, Any]:
    records = video_item.get("per_frame") or []
    processed = len(records)
    evaluable_flags = [bool(record.get("decision_evaluable")) for record in records]
    evaluable = [record for record in records if record.get("decision_evaluable")]
    complete_arm_total = sum(int(record.get("complete_arm_count") or 0) for record in evaluable)
    optical_flow_points = sum(int(record.get("optical_flow_point_count") or 0) for record in evaluable)
    low_confidence_points = sum(int(record.get("low_confidence_point_count") or 0) for record in evaluable)
    identity_resets = sum(1 for record in records if record.get("identity_reset"))
    visibility_counts = dict(Counter(str(record.get("visibility") or "unknown") for record in records))
    confidences = [confidence for record in evaluable for confidence in point_confidences(record)]
    wrist_counts = wrist_source_counts(evaluable)

    evaluable_rate = safe_ratio(len(evaluable), processed)
    complete_arm_rate = safe_ratio(complete_arm_total, max(1, len(evaluable) * 2))
    optical_flow_point_rate = safe_ratio(optical_flow_points, max(1, len(evaluable) * 6))
    low_confidence_point_rate = safe_ratio(low_confidence_points, max(1, len(evaluable) * 6))
    mean_keypoint_confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
    observed_wrist_rate = safe_ratio(wrist_counts["observed"], max(1, sum(wrist_counts.values())))
    optical_flow_wrist_rate = safe_ratio(wrist_counts["optical_flow"], max(1, sum(wrist_counts.values())))

    blockers = [
        blocker
        for blocker in [
            f"evaluable_rate={evaluable_rate}<{min_evaluable_rate}"
            if evaluable_rate < min_evaluable_rate else None,
            f"complete_arm_rate={complete_arm_rate}<{min_complete_arm_rate}"
            if complete_arm_rate < min_complete_arm_rate else None,
            f"optical_flow_point_rate={optical_flow_point_rate}>{max_optical_flow_point_rate}"
            if optical_flow_point_rate > max_optical_flow_point_rate else None,
            (
                f"mean_keypoint_confidence={mean_keypoint_confidence}<{min_mean_keypoint_confidence}"
                if mean_keypoint_confidence is None
                or mean_keypoint_confidence < min_mean_keypoint_confidence
                else None
            ),
        ]
        if blocker is not None
    ]
    borderline_flags = [
        flag
        for flag in [
            f"evaluable_rate={evaluable_rate}<{borderline_evaluable_rate}"
            if evaluable_rate < borderline_evaluable_rate else None,
            f"optical_flow_wrist_rate={optical_flow_wrist_rate}>{borderline_optical_flow_wrist_rate}"
            if optical_flow_wrist_rate > borderline_optical_flow_wrist_rate else None,
            f"identity_reset_count={identity_resets}>{max_identity_resets}"
            if identity_resets > max_identity_resets else None,
        ]
        if flag is not None
    ]
    reliability = "decision_usable" if not blockers else "pose_limited"
    reliability_detail = (
        "usable_borderline"
        if reliability == "decision_usable" and borderline_flags
        else reliability
    )

    return {
        "video": video_item.get("video"),
        "view_profile": video_item.get("view_profile"),
        "processed_frame_count": processed,
        "evaluable_frame_count": len(evaluable),
        "evaluable_rate": evaluable_rate,
        "complete_arm_rate": complete_arm_rate,
        "optical_flow_point_rate": optical_flow_point_rate,
        "low_confidence_point_rate": low_confidence_point_rate,
        "mean_keypoint_confidence": mean_keypoint_confidence,
        "observed_wrist_rate": observed_wrist_rate,
        "optical_flow_wrist_rate": optical_flow_wrist_rate,
        "identity_reset_count": identity_resets,
        "visibility_counts": visibility_counts,
        "longest_not_evaluable_frames": longest_boolean_run(
            [not flag for flag in evaluable_flags],
            target=True,
        ),
        "reliability": reliability,
        "reliability_detail": reliability_detail,
        "pose_reliability_blockers": blockers,
        "borderline_flags": borderline_flags,
        "decision_policy": (
            "allow_pose_temporal_decision"
            if reliability_detail == "decision_usable"
            else "allow_pose_temporal_decision_but_require_temporal_consistency"
            if reliability_detail == "usable_borderline"
            else "prefer_not_evaluable_or_candidate; do_not_emit_negative_from_pose_absence"
        ),
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# Phone-Call Pose Reliability Diagnostic",
        "",
        "Bu rapor davranış etiketi üretmez; el-kulak kararının pose kanıtı açısından",
        "ne kadar güvenilir olduğunu ölçer.",
        "",
        "| Video | Reliability | Evaluable | Complete arm | Optical-flow pts | Mean kp conf | Borderline | Policy |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for video in result["videos"]:
        lines.append(
            "| {video} | {rel} | {eval_rate} | {arm_rate} | {flow_rate} | {conf} | {borderline} | {policy} |".format(
                video=video["video"],
                rel=video["reliability_detail"],
                eval_rate=video["evaluable_rate"],
                arm_rate=video["complete_arm_rate"],
                flow_rate=video["optical_flow_point_rate"],
                conf=video["mean_keypoint_confidence"],
                borderline=", ".join(video["borderline_flags"]) or "-",
                policy=video["decision_policy"],
            )
        )
    lines.extend(
        [
            "",
            "Guardrail: pose kanıtı sınırlı olduğunda sistem negatif üretmemeli;",
            "`not_evaluable` veya düşük riskli `candidate` durumunda kalmalıdır.",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze phone-call pose reliability.")
    parser.add_argument("--arm-summary", type=Path, default=DEFAULT_ARM_SUMMARY)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-evaluable-rate", type=float, default=0.45)
    parser.add_argument("--borderline-evaluable-rate", type=float, default=0.55)
    parser.add_argument("--min-complete-arm-rate", type=float, default=0.35)
    parser.add_argument("--max-optical-flow-point-rate", type=float, default=0.35)
    parser.add_argument("--borderline-optical-flow-wrist-rate", type=float, default=0.30)
    parser.add_argument("--max-identity-resets", type=int, default=5)
    parser.add_argument("--min-mean-keypoint-confidence", type=float, default=0.45)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    arm_summary = json.loads(args.arm_summary.resolve().read_text(encoding="utf-8"))
    videos = [
        summarize_video(
            item,
            min_evaluable_rate=args.min_evaluable_rate,
            borderline_evaluable_rate=args.borderline_evaluable_rate,
            min_complete_arm_rate=args.min_complete_arm_rate,
            max_optical_flow_point_rate=args.max_optical_flow_point_rate,
            borderline_optical_flow_wrist_rate=args.borderline_optical_flow_wrist_rate,
            max_identity_resets=args.max_identity_resets,
            min_mean_keypoint_confidence=args.min_mean_keypoint_confidence,
        )
        for item in arm_summary.get("videos", [])
    ]
    result = {
        "experiment_id": EXPERIMENT_ID,
        "model_key": MODEL_KEY,
        "created_at_utc": now_utc(),
        "input_arm_summary": rel(args.arm_summary),
        "thresholds": {
            "min_evaluable_rate": args.min_evaluable_rate,
            "borderline_evaluable_rate": args.borderline_evaluable_rate,
            "min_complete_arm_rate": args.min_complete_arm_rate,
            "max_optical_flow_point_rate": args.max_optical_flow_point_rate,
            "borderline_optical_flow_wrist_rate": args.borderline_optical_flow_wrist_rate,
            "max_identity_resets": args.max_identity_resets,
            "min_mean_keypoint_confidence": args.min_mean_keypoint_confidence,
        },
        "video_count": len(videos),
        "decision_usable_count": sum(1 for video in videos if video["reliability"] == "decision_usable"),
        "pose_limited_count": sum(1 for video in videos if video["reliability"] == "pose_limited"),
        "videos": videos,
    }
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.artifact.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.report.write_text(build_report(result) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
