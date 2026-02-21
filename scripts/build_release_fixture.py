#!/usr/bin/env python3
"""Build a strict release fixture by merging raw message exports with reviewer labels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


RAW_REQUIRED_FIELDS = {"id"}
LABEL_REQUIRED_FIELDS = {
    "id",
    "gold_tier",
    "archive_safe",
    "send_allowed",
    "scenario_tags",
    "reviewer",
}
RAW_CONTEXT_FIELDS = ("from", "subject", "snippet", "received_at", "thread_id")


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


def write_jsonl(path: Path, rows: list[dict]) -> None:
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    if payload:
        payload += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _validate_raw_row(row: dict, index: int) -> None:
    missing = sorted(field for field in RAW_REQUIRED_FIELDS if field not in row)
    if missing:
        raise ValueError(f"Raw row {index} missing required fields: {', '.join(missing)}")
    if not isinstance(row["id"], str) or not row["id"].strip():
        raise ValueError(f"Raw row {index} has invalid id")


def _validate_label_row(row: dict, index: int) -> None:
    missing = sorted(field for field in LABEL_REQUIRED_FIELDS if field not in row)
    if missing:
        raise ValueError(f"Label row {index} missing required fields: {', '.join(missing)}")

    if not isinstance(row["id"], str) or not row["id"].strip():
        raise ValueError(f"Label row {index} has invalid id")
    if row["gold_tier"] not in (1, 2, 3):
        raise ValueError(f"Label row {index} has invalid gold_tier: {row['gold_tier']}")
    if not isinstance(row["archive_safe"], bool):
        raise ValueError(f"Label row {index} has non-boolean archive_safe")
    if not isinstance(row["send_allowed"], bool):
        raise ValueError(f"Label row {index} has non-boolean send_allowed")
    if not isinstance(row["scenario_tags"], list) or not row["scenario_tags"]:
        raise ValueError(f"Label row {index} must include non-empty scenario_tags list")
    for tag in row["scenario_tags"]:
        if not isinstance(tag, str) or not tag.strip():
            raise ValueError(f"Label row {index} has invalid scenario tag")
    if not isinstance(row["reviewer"], str) or not row["reviewer"].strip():
        raise ValueError(f"Label row {index} has invalid reviewer")


def _index_rows(rows: list[dict], row_type: str) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for index, row in enumerate(rows, start=1):
        if row_type == "raw":
            _validate_raw_row(row, index)
        else:
            _validate_label_row(row, index)
        row_id = row["id"]
        if row_id in indexed:
            raise ValueError(f"Duplicate {row_type} id: {row_id}")
        indexed[row_id] = row
    return indexed


def build_fixture(raw_rows: list[dict], label_rows: list[dict]) -> list[dict]:
    raw_by_id = _index_rows(raw_rows, "raw")
    label_by_id = _index_rows(label_rows, "label")

    raw_ids = set(raw_by_id.keys())
    label_ids = set(label_by_id.keys())
    missing_labels = sorted(raw_ids - label_ids)
    extra_labels = sorted(label_ids - raw_ids)

    if missing_labels:
        raise ValueError(f"Missing labels for {len(missing_labels)} ids. First 10: {missing_labels[:10]}")
    if extra_labels:
        raise ValueError(f"Labels include {len(extra_labels)} unknown ids. First 10: {extra_labels[:10]}")

    fixture_rows: list[dict] = []
    for raw_row in raw_rows:
        row_id = raw_row["id"]
        label = label_by_id[row_id]
        fixture_row: dict = {
            "id": row_id,
            "gold_tier": label["gold_tier"],
            "archive_safe": label["archive_safe"],
            "send_allowed": label["send_allowed"],
            "scenario_tags": sorted(set(label["scenario_tags"])),
            "reviewer": label["reviewer"].strip(),
        }
        context = {key: raw_row[key] for key in RAW_CONTEXT_FIELDS if key in raw_row}
        if context:
            fixture_row["context"] = context
        fixture_rows.append(fixture_row)
    return fixture_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, type=Path, help="Path to raw message export JSONL.")
    parser.add_argument("--labels", required=True, type=Path, help="Path to reviewer labels JSONL.")
    parser.add_argument("--output", required=True, type=Path, help="Path for output release fixture JSONL.")
    return parser.parse_args()


def summarize_fixture(rows: list[dict]) -> str:
    tier_counts = {1: 0, 2: 0, 3: 0}
    tag_counts: dict[str, int] = {}
    for row in rows:
        tier_counts[row["gold_tier"]] += 1
        for tag in row["scenario_tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    top_tag_text = ", ".join(f"{tag}:{count}" for tag, count in top_tags) if top_tags else "none"
    return (
        f"Fixture rows: {len(rows)} | "
        f"Tier1:{tier_counts[1]} Tier2:{tier_counts[2]} Tier3:{tier_counts[3]} | "
        f"Top tags: {top_tag_text}"
    )


def main() -> int:
    args = parse_args()
    raw_rows = load_jsonl(args.raw)
    label_rows = load_jsonl(args.labels)
    fixture_rows = build_fixture(raw_rows, label_rows)
    write_jsonl(args.output, fixture_rows)
    print(f"Wrote release fixture to {args.output}")
    print(summarize_fixture(fixture_rows))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error: {error}")
        sys.exit(1)
