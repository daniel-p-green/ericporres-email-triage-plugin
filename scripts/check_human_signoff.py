#!/usr/bin/env python3
"""Validate human release sign-off criteria."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "eric_transcript_reviews",
    "voice_quality_approved",
    "archive_clarity_approved",
    "approved_by",
    "approved_at",
}


def load_signoff(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    return data


def evaluate_signoff(data: dict, *, min_reviews: int) -> dict:
    missing = sorted(REQUIRED_FIELDS - set(data.keys()))
    if missing:
        raise ValueError(f"Missing signoff fields: {', '.join(missing)}")

    failures: list[str] = []
    reviews = data["eric_transcript_reviews"]
    if not isinstance(reviews, int):
        raise ValueError("`eric_transcript_reviews` must be an integer")
    if reviews < min_reviews:
        failures.append(f"Transcript reviews {reviews} is below required minimum {min_reviews}")

    for key in ("voice_quality_approved", "archive_clarity_approved"):
        if not isinstance(data[key], bool):
            raise ValueError(f"`{key}` must be a boolean")
        if not data[key]:
            failures.append(f"{key} is false")

    for key in ("approved_by", "approved_at"):
        if not isinstance(data[key], str) or not data[key].strip():
            failures.append(f"{key} is empty")

    return {"failures": failures, "summary": data}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signoff", required=True, type=Path, help="Path to signoff JSON.")
    parser.add_argument("--min-reviews", type=int, default=3)
    parser.add_argument("--enforce", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    signoff = load_signoff(args.signoff)
    report = evaluate_signoff(signoff, min_reviews=args.min_reviews)

    print("Human sign-off report")
    print(f"- Transcript reviews: {signoff['eric_transcript_reviews']}")
    print(f"- Voice quality approved: {signoff['voice_quality_approved']}")
    print(f"- Archive clarity approved: {signoff['archive_clarity_approved']}")
    print(f"- Approved by: {signoff['approved_by']}")
    print(f"- Approved at: {signoff['approved_at']}")

    if report["failures"]:
        print("Human sign-off checks: FAIL")
        for failure in report["failures"]:
            print(f"- {failure}")
        if args.enforce:
            return 1
    else:
        print("Human sign-off checks: PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error: {error}")
        sys.exit(1)
