#!/usr/bin/env python3
"""Analyze plate OCR temporal stability from per-crop OCR summaries.

This tool does not run OCR. It reads OCR summary JSON files produced with
`run_plate_ocr_baseline.py --keep-per-crop` and reports when a plate result
first becomes readable, expected, and stable enough for evidence use.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "models" / "benchmarks" / "artifacts" / "plate_ocr" / "POCR-EXP-007-cct-xs-stability"
DEFAULT_REPORT = ROOT / "testing" / "reports" / "pocr_exp_007_cct_xs_stability.md"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_summary_arg(value: str) -> tuple[str, Path]:
    if "=" in value:
        label, raw_path = value.split("=", 1)
        return label.strip(), Path(raw_path).expanduser()
    path = Path(value).expanduser()
    return path.parent.name, path


def per_crop(video_summary: dict[str, Any]) -> list[dict[str, Any]]:
    data = video_summary.get("per_crop")
    if not isinstance(data, list):
        raise ValueError(
            f"{video_summary.get('video')} summary has no per_crop list. "
            "Re-run run_plate_ocr_baseline.py with --keep-per-crop."
        )
    return sorted(data, key=lambda item: int(item.get("frame") or 0))


def first_frame(items: list[dict[str, Any]], predicate: Any) -> int | None:
    for item in items:
        if predicate(item):
            return int(item["frame"])
    return None


def first_stable_frame(
    items: list[dict[str, Any]],
    stable_count: int,
    window_size: int,
    min_confidence: float,
    require_format_valid: bool,
    require_province_valid: bool,
) -> tuple[int | None, str | None, int]:
    window: deque[dict[str, Any]] = deque(maxlen=window_size)
    for item in items:
        text = str(item.get("normalized_text") or "")
        confidence = float(item.get("ocr_confidence") or 0.0)
        if not text or confidence < min_confidence:
            window.append({"text": None})
            continue
        if require_format_valid and not item.get("format_valid"):
            window.append({"text": None})
            continue
        if require_province_valid and not item.get("province_code_valid"):
            window.append({"text": None})
            continue
        window.append({"text": text})
        counts: dict[str, int] = defaultdict(int)
        for seen in window:
            if seen["text"]:
                counts[str(seen["text"])] += 1
        if not counts:
            continue
        best_text, best_count = max(counts.items(), key=lambda pair: (pair[1], pair[0]))
        if best_count >= stable_count:
            return int(item["frame"]), best_text, best_count
    return None, None, 0


def analyze_video(
    label: str,
    summary_path: Path,
    video_summary: dict[str, Any],
    expected_plate: str | None,
    stable_count: int,
    window_size: int,
    min_confidence: float,
) -> dict[str, Any]:
    crops = per_crop(video_summary)
    first_any = first_frame(crops, lambda item: bool(item.get("normalized_text")))
    first_format = first_frame(
        crops,
        lambda item: bool(item.get("normalized_text"))
        and bool(item.get("format_valid"))
        and bool(item.get("province_code_valid")),
    )
    first_expected = None
    if expected_plate:
        first_expected = first_frame(crops, lambda item: item.get("normalized_text") == expected_plate)

    stable_frame, stable_text, stable_observations = first_stable_frame(
        crops,
        stable_count=stable_count,
        window_size=window_size,
        min_confidence=min_confidence,
        require_format_valid=True,
        require_province_valid=True,
    )
    vote = video_summary.get("temporal_vote") or {}
    return {
        "config": label,
        "summary": rel(summary_path),
        "video": video_summary.get("video"),
        "processed_crops": video_summary.get("processed_crops"),
        "ocr_read_count": video_summary.get("ocr_read_count"),
        "format_valid_count": video_summary.get("format_valid_count"),
        "province_valid_count": video_summary.get("province_valid_count"),
        "temporal_vote": vote.get("plate_text"),
        "temporal_vote_confidence": vote.get("vote_confidence"),
        "first_any_read_frame": first_any,
        "first_format_valid_frame": first_format,
        "first_expected_plate_frame": first_expected,
        "first_stable_vote_frame": stable_frame,
        "first_stable_vote_text": stable_text,
        "first_stable_vote_observations": stable_observations,
        "stable_count_required": stable_count,
        "stable_window_size": window_size,
        "stable_min_confidence": min_confidence,
        "mean_ocr_latency_ms": video_summary.get("mean_ocr_latency_ms"),
        "p95_ocr_latency_ms": video_summary.get("p95_ocr_latency_ms"),
    }


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_report(rows: list[dict[str, Any]], args: argparse.Namespace) -> str:
    lines = [
        "# POCR-EXP-007 CCT-XS OCR Stability Review",
        "",
        f"Tarih: `{now_utc()}`",
        "",
        "## Amaç",
        "",
        "Bu rapor, video üzerinde geç başlayan OCR davranışının model fine-tune gerektirip "
        "gerektirmediğini veya temporal stability gating ile yönetilip yönetilemeyeceğini "
        "kontrol eder. Mevcut per-crop OCR çıktıları okunur; OCR yeniden çalıştırılmaz.",
        "",
        "## Stabilite Kuralı",
        "",
        f"* Stabil tekrar sayısı: `{args.stable_count}` aynı format-valid/province-valid okuma",
        f"* Kayan pencere: `{args.window_size}` OCR crop gözlemi",
        f"* Minimum OCR confidence: `{args.min_confidence}`",
        f"* Manuel karşılaştırma beklenen plaka: `{args.expected_plate or 'not_set'}`",
        "",
        "## Sonuçlar",
        "",
        "| Config | Video | Read / Crop | Vote | İlk Okuma | İlk Beklenen | İlk Stabil | Stabil Metin | Ort. ms |",
        "|---|---|---:|---|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['config']} | {row['video']} | {row['ocr_read_count']}/{row['processed_crops']} | "
            f"{row['temporal_vote']} | {row['first_any_read_frame']} | {row['first_expected_plate_frame']} | "
            f"{row['first_stable_vote_frame']} | {row['first_stable_vote_text']} | {row['mean_ocr_latency_ms']} |"
        )
    lines += [
        "",
        "## Yorum",
        "",
        "* `first_stable_vote_frame`, `first_expected_plate_frame` değerine yakınsa ilk çözüm fine-tune değildir.",
        "* Upscale yalnız stabil doğru okumayı anlamlı biçimde öne çekiyor ve yanlış erken vote üretmiyorsa promote edilmelidir.",
        "* Upscale erken düşük güvenli/yanlış okumaları artırıyorsa CCT-XS original yol korunmalı ve stability gate kullanılmalıdır.",
        "",
        "## Karar",
        "",
        "* Bu analiz fine-tune ihtiyacını kanıtlamaz; gecikme uzak/karanlık frame'lerde okunabilirlik sınırına bağlıdır.",
        "* CCT-XS original baseline aktif kalmalıdır.",
        "* Runtime evidence için final OCR değeri, tek frame sonucu değil, stabil tekrar sonrası temporal vote olarak yazılmalıdır.",
        "* Upscale/CLAHE manuel review'da ayrıca izlenebilir; fakat latency artışı ve erken yanlış vote riski nedeniyle varsayılan yapılmamalıdır.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze per-crop OCR temporal stability.")
    parser.add_argument("--summary", action="append", required=True, help="label=path to OCR summary JSON.")
    parser.add_argument("--video", default=None, help="Optional video name filter, e.g. video_3.mp4.")
    parser.add_argument("--expected-plate", default=None)
    parser.add_argument("--stable-count", type=int, default=3)
    parser.add_argument("--window-size", type=int, default=7)
    parser.add_argument("--min-confidence", type=float, default=0.75)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    for raw_summary in args.summary:
        label, path = parse_summary_arg(raw_summary)
        path = path.resolve()
        summary = load_json(path)
        for video_summary in summary.get("videos", []):
            if args.video and video_summary.get("video") != args.video:
                continue
            rows.append(
                analyze_video(
                    label=label,
                    summary_path=path,
                    video_summary=video_summary,
                    expected_plate=args.expected_plate,
                    stable_count=args.stable_count,
                    window_size=args.window_size,
                    min_confidence=args.min_confidence,
                )
            )
    if not rows:
        raise SystemExit("No matching video rows found.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "pocr_exp_007_cct_xs_stability_summary.json"
    csv_path = args.output_dir / "pocr_exp_007_cct_xs_stability_summary.csv"
    payload = {
        "generated_at_utc": now_utc(),
        "expected_plate": args.expected_plate,
        "stable_count": args.stable_count,
        "window_size": args.window_size,
        "min_confidence": args.min_confidence,
        "rows": rows,
    }
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(rows, csv_path)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(build_report(rows, args), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": rel(summary_path),
                "csv": rel(csv_path),
                "report": rel(args.report.resolve()),
                "rows": len(rows),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
