#!/usr/bin/env python3
"""Check release fixture size and scenario balance before strict evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_REQUIRED_TAGS = [
    "work",
    "personal",
    "school",
    "medical",
    "finance",
    "marketing",
    "thread-reply",
    "ambiguity",
]


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


def _validate_fixture_rows(rows: list[dict]) -> None:
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        required = ("id", "gold_tier", "archive_safe", "send_allowed", "scenario_tags")
        missing = [field for field in required if field not in row]
        if missing:
            raise ValueError(f"Fixture row {index} missing fields: {', '.join(missing)}")

        row_id = row["id"]
        if not isinstance(row_id, str) or not row_id.strip():
            raise ValueError(f"Fixture row {index} has invalid id")
        if row_id in seen_ids:
            raise ValueError(f"Duplicate id in fixture: {row_id}")
        seen_ids.add(row_id)

        if row["gold_tier"] not in (1, 2, 3):
            raise ValueError(f"Fixture row {index} has invalid gold_tier: {row['gold_tier']}")
        if not isinstance(row["archive_safe"], bool):
            raise ValueError(f"Fixture row {index} has non-boolean archive_safe")
        if not isinstance(row["send_allowed"], bool):
            raise ValueError(f"Fixture row {index} has non-boolean send_allowed")
        if not isinstance(row["scenario_tags"], list):
            raise ValueError(f"Fixture row {index} has non-list scenario_tags")
        for tag in row["scenario_tags"]:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError(f"Fixture row {index} has invalid scenario tag")


def evaluate_fixture(
    rows: list[dict],
    *,
    min_cases: int,
    required_tags: list[str],
    min_tag_count: int,
    min_tier_count: int,
) -> dict:
    _validate_fixture_rows(rows)

    total = len(rows)
    tier_counts = {1: 0, 2: 0, 3: 0}
    tag_counts: dict[str, int] = {}
    archive_safe_true = 0
    archive_safe_false = 0

    for row in rows:
        tier_counts[row["gold_tier"]] += 1
        if row["archive_safe"]:
            archive_safe_true += 1
        else:
            archive_safe_false += 1
        for tag in sorted(set(row["scenario_tags"])):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    failures: list[str] = []
    if total < min_cases:
        failures.append(f"Case count {total} is below required minimum {min_cases}")

    for tier in (1, 2, 3):
        if tier_counts[tier] < min_tier_count:
            failures.append(
                f"Tier {tier} count {tier_counts[tier]} is below required minimum {min_tier_count}"
            )

    missing_required = [tag for tag in required_tags if tag_counts.get(tag, 0) < min_tag_count]
    if missing_required:
        failures.append(
            "Missing required tag coverage: "
            + ", ".join(
                f"{tag}({tag_counts.get(tag, 0)}/{min_tag_count})" for tag in missing_required
            )
        )

    if archive_safe_true == 0 or archive_safe_false == 0:
        failures.append(
            "Fixture must include both archive_safe=true and archive_safe=false examples"
        )

    return {
        "total": total,
        "tier_counts": tier_counts,
        "tag_counts": tag_counts,
        "archive_safe_true": archive_safe_true,
        "archive_safe_false": archive_safe_false,
        "failures": failures,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path, help="Path to release fixture JSONL.")
    parser.add_argument("--min-cases", type=int, default=500)
    parser.add_argument("--min-tag-count", type=int, default=15)
    parser.add_argument("--min-tier-count", type=int, default=75)
    parser.add_argument(
        "--required-tags",
        default=",".join(DEFAULT_REQUIRED_TAGS),
        help="Comma-separated required scenario tags.",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Fail with exit code 1 when balance checks fail.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required_tags = [tag.strip() for tag in args.required_tags.split(",") if tag.strip()]
    rows = load_jsonl(args.fixture)
    report = evaluate_fixture(
        rows,
        min_cases=args.min_cases,
        required_tags=required_tags,
        min_tag_count=args.min_tag_count,
        min_tier_count=args.min_tier_count,
    )

    print("Fixture balance report")
    print(f"- Cases: {report['total']}")
    print(
        f"- Tier counts: T1={report['tier_counts'][1]} "
        f"T2={report['tier_counts'][2]} T3={report['tier_counts'][3]}"
    )
    print(f"- archive_safe=true: {report['archive_safe_true']}")
    print(f"- archive_safe=false: {report['archive_safe_false']}")
    for tag in required_tags:
        print(f"- tag {tag}: {report['tag_counts'].get(tag, 0)}")

    if report["failures"]:
        print("Balance checks: FAIL")
        for failure in report["failures"]:
            print(f"- {failure}")
        if args.enforce:
            return 1
    else:
        print("Balance checks: PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error: {error}")
        sys.exit(1)
