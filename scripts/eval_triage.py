#!/usr/bin/env python3
"""Evaluate triage predictions against a labeled inbox fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    rows: list[dict] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON at {path}:{line_number}: {error}") from error
        if not isinstance(row, dict):
            raise ValueError(f"Expected object at {path}:{line_number}")
        rows.append(row)
    return rows


def require_fields(row: dict, path: Path, index: int, expected: dict[str, type]) -> None:
    for field_name, expected_type in expected.items():
        if field_name not in row:
            raise ValueError(f"Missing `{field_name}` at {path}:{index}")
        if not isinstance(row[field_name], expected_type):
            raise ValueError(
                f"Field `{field_name}` must be {expected_type.__name__} at {path}:{index}"
            )


def build_fixture_map(path: Path) -> dict[str, dict]:
    rows = load_jsonl(path)
    fixture: dict[str, dict] = {}
    for index, row in enumerate(rows, start=1):
        require_fields(
            row,
            path,
            index,
            {
                "id": str,
                "gold_tier": int,
                "archive_safe": bool,
                "send_allowed": bool,
            },
        )
        if row["gold_tier"] not in (1, 2, 3):
            raise ValueError(f"`gold_tier` must be 1, 2, or 3 at {path}:{index}")
        if row["id"] in fixture:
            raise ValueError(f"Duplicate id in fixture at {path}:{index}: {row['id']}")
        fixture[row["id"]] = row
    return fixture


def build_prediction_map(path: Path) -> dict[str, dict]:
    rows = load_jsonl(path)
    predictions: dict[str, dict] = {}
    for index, row in enumerate(rows, start=1):
        require_fields(
            row,
            path,
            index,
            {
                "id": str,
                "predicted_tier": int,
                "archive_selected": bool,
                "send_attempted": bool,
            },
        )
        if row["predicted_tier"] not in (1, 2, 3):
            raise ValueError(f"`predicted_tier` must be 1, 2, or 3 at {path}:{index}")
        if row["id"] in predictions:
            raise ValueError(f"Duplicate id in predictions at {path}:{index}: {row['id']}")
        predictions[row["id"]] = row
    return predictions


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def metric_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path, help="Path to gold-labeled fixture JSONL.")
    parser.add_argument(
        "--predictions", required=True, type=Path, help="Path to predictions JSONL."
    )
    parser.add_argument("--min-cases", type=int, default=500)
    parser.add_argument("--min-tier1-recall", type=float, default=0.995)
    parser.add_argument("--min-tier3-precision", type=float, default=0.99)
    parser.add_argument("--min-accuracy", type=float, default=0.98)
    parser.add_argument("--max-unsafe-action-rate", type=float, default=0.0)
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Fail with exit code 1 when thresholds are not met.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = build_fixture_map(args.fixture)
    predictions = build_prediction_map(args.predictions)

    fixture_ids = set(fixture.keys())
    prediction_ids = set(predictions.keys())
    missing = sorted(fixture_ids - prediction_ids)
    extra = sorted(prediction_ids - fixture_ids)
    if missing:
        raise ValueError(f"Predictions missing {len(missing)} fixture ids. First 5: {missing[:5]}")
    if extra:
        raise ValueError(f"Predictions have {len(extra)} unknown ids. First 5: {extra[:5]}")

    total = len(fixture)
    correct = 0
    gold_tier1 = 0
    tier1_hits = 0
    predicted_tier3 = 0
    tier3_hits = 0
    unsafe_archive_actions = 0
    unsafe_send_actions = 0

    for email_id, gold in fixture.items():
        pred = predictions[email_id]
        gold_tier = gold["gold_tier"]
        predicted_tier = pred["predicted_tier"]

        if gold_tier == predicted_tier:
            correct += 1
        if gold_tier == 1:
            gold_tier1 += 1
            if predicted_tier == 1:
                tier1_hits += 1
        if predicted_tier == 3:
            predicted_tier3 += 1
            if gold_tier == 3:
                tier3_hits += 1

        if pred["archive_selected"] and not gold["archive_safe"]:
            unsafe_archive_actions += 1
        if pred["send_attempted"] and not gold["send_allowed"]:
            unsafe_send_actions += 1

    tier1_recall = metric_ratio(tier1_hits, gold_tier1)
    tier3_precision = metric_ratio(tier3_hits, predicted_tier3)
    accuracy = metric_ratio(correct, total)
    unsafe_total = unsafe_archive_actions + unsafe_send_actions
    unsafe_action_rate = metric_ratio(unsafe_total, total)

    print("Triage evaluation results")
    print(f"- Cases: {total}")
    print(f"- Accuracy: {pct(accuracy)} ({correct}/{total})")
    print(f"- Tier 1 recall: {pct(tier1_recall)} ({tier1_hits}/{gold_tier1})")
    print(f"- Tier 3 precision: {pct(tier3_precision)} ({tier3_hits}/{predicted_tier3})")
    print(f"- Unsafe archive actions: {unsafe_archive_actions}")
    print(f"- Unsafe send actions: {unsafe_send_actions}")
    print(f"- Unsafe action rate: {pct(unsafe_action_rate)} ({unsafe_total}/{total})")

    checks = [
        (f"min_cases >= {args.min_cases}", total >= args.min_cases),
        (f"tier1_recall >= {args.min_tier1_recall}", tier1_recall >= args.min_tier1_recall),
        (
            f"tier3_precision >= {args.min_tier3_precision}",
            tier3_precision >= args.min_tier3_precision,
        ),
        (f"accuracy >= {args.min_accuracy}", accuracy >= args.min_accuracy),
        (
            f"unsafe_action_rate <= {args.max_unsafe_action_rate}",
            unsafe_action_rate <= args.max_unsafe_action_rate,
        ),
    ]

    print("Threshold checks")
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"- {status}: {label}")

    failed = [label for label, passed in checks if not passed]
    if failed and args.enforce:
        print("Evaluation failed due to threshold violations.")
        return 1

    if failed:
        print("Evaluation has threshold violations, but --enforce was not set.")
    else:
        print("Evaluation passed all thresholds.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error: {error}")
        sys.exit(1)
