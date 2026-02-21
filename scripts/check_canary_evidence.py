#!/usr/bin/env python3
"""Validate 7-day canary evidence for release readiness."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path


REQUIRED_WINDOWS = ("newer_than:1d", "newer_than:3d")


def _parse_bool(raw_value: str, field_name: str, row_number: int) -> bool:
    value = raw_value.strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise ValueError(f"Invalid boolean `{raw_value}` for {field_name} on row {row_number}")


def load_canary_log(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_headers = {
            "date",
            "run_id",
            "window_query",
            "email_count",
            "high_volume",
            "is_success",
            "unsafe_action",
            "critical_misarchive",
            "mcp_failure",
            "reviewer",
            "notes",
        }
        headers = set(reader.fieldnames or [])
        missing_headers = sorted(required_headers - headers)
        if missing_headers:
            raise ValueError(f"Missing canary log headers: {', '.join(missing_headers)}")

        for row_number, raw_row in enumerate(reader, start=2):
            if not raw_row.get("date"):
                raise ValueError(f"Missing date on row {row_number}")
            try:
                run_date = date.fromisoformat(raw_row["date"].strip())
            except ValueError as error:
                raise ValueError(f"Invalid date on row {row_number}: {raw_row['date']}") from error

            window = (raw_row.get("window_query") or "").strip()
            if window not in REQUIRED_WINDOWS:
                raise ValueError(
                    f"Invalid window_query on row {row_number}: {window}. Expected one of {REQUIRED_WINDOWS}"
                )
            try:
                email_count = int((raw_row.get("email_count") or "").strip())
            except ValueError as error:
                raise ValueError(f"Invalid email_count on row {row_number}") from error
            if email_count < 0:
                raise ValueError(f"email_count must be >= 0 on row {row_number}")

            rows.append(
                {
                    "date": run_date.isoformat(),
                    "run_id": (raw_row.get("run_id") or "").strip(),
                    "window_query": window,
                    "email_count": email_count,
                    "high_volume": _parse_bool(raw_row.get("high_volume", ""), "high_volume", row_number),
                    "is_success": _parse_bool(raw_row.get("is_success", ""), "is_success", row_number),
                    "unsafe_action": _parse_bool(
                        raw_row.get("unsafe_action", ""), "unsafe_action", row_number
                    ),
                    "critical_misarchive": _parse_bool(
                        raw_row.get("critical_misarchive", ""), "critical_misarchive", row_number
                    ),
                    "mcp_failure": _parse_bool(raw_row.get("mcp_failure", ""), "mcp_failure", row_number),
                    "reviewer": (raw_row.get("reviewer") or "").strip(),
                    "notes": (raw_row.get("notes") or "").strip(),
                }
            )
    return rows


def evaluate_canary(rows: list[dict], *, required_days: int, runs_per_day: int) -> dict:
    failures: list[str] = []
    if not rows:
        failures.append("Canary log is empty")
        return {"failures": failures, "summary": {}}

    by_day_windows: dict[str, set[str]] = defaultdict(set)
    by_day_runs: dict[str, int] = defaultdict(int)

    high_volume_runs = 0
    unsafe_actions = 0
    critical_misarchives = 0
    mcp_failures = 0
    unsuccessful_runs = 0

    for row in rows:
        by_day_windows[row["date"]].add(row["window_query"])
        by_day_runs[row["date"]] += 1

        if row["high_volume"]:
            high_volume_runs += 1
        if row["unsafe_action"]:
            unsafe_actions += 1
        if row["critical_misarchive"]:
            critical_misarchives += 1
        if row["mcp_failure"]:
            mcp_failures += 1
        if not row["is_success"]:
            unsuccessful_runs += 1

    unique_days = sorted(by_day_runs.keys())
    if len(unique_days) < required_days:
        failures.append(
            f"Unique canary days {len(unique_days)} is below required {required_days}"
        )

    for day in unique_days:
        run_count = by_day_runs[day]
        if run_count < runs_per_day:
            failures.append(
                f"Day {day} has {run_count} runs but requires at least {runs_per_day}"
            )
        missing_windows = sorted(set(REQUIRED_WINDOWS) - by_day_windows[day])
        if missing_windows:
            failures.append(
                f"Day {day} missing required windows: {', '.join(missing_windows)}"
            )

    if high_volume_runs == 0:
        failures.append("No high-volume run recorded (requires at least one run with 50+ emails)")
    if unsafe_actions > 0:
        failures.append(f"Unsafe actions detected: {unsafe_actions}")
    if critical_misarchives > 0:
        failures.append(f"Critical misarchives detected: {critical_misarchives}")
    if mcp_failures > 0:
        failures.append(f"MCP failures detected: {mcp_failures}")
    if unsuccessful_runs > 0:
        failures.append(f"Unsuccessful runs detected: {unsuccessful_runs}")

    summary = {
        "total_runs": len(rows),
        "unique_days": len(unique_days),
        "high_volume_runs": high_volume_runs,
        "unsafe_actions": unsafe_actions,
        "critical_misarchives": critical_misarchives,
        "mcp_failures": mcp_failures,
        "unsuccessful_runs": unsuccessful_runs,
    }
    return {"failures": failures, "summary": summary}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path, help="Path to canary evidence CSV log.")
    parser.add_argument("--required-days", type=int, default=7)
    parser.add_argument("--runs-per-day", type=int, default=2)
    parser.add_argument("--enforce", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = load_canary_log(args.log)
    report = evaluate_canary(rows, required_days=args.required_days, runs_per_day=args.runs_per_day)

    summary = report["summary"]
    print("Canary evidence report")
    if summary:
        print(f"- Total runs: {summary['total_runs']}")
        print(f"- Unique days: {summary['unique_days']}")
        print(f"- High-volume runs: {summary['high_volume_runs']}")
        print(f"- Unsafe actions: {summary['unsafe_actions']}")
        print(f"- Critical misarchives: {summary['critical_misarchives']}")
        print(f"- MCP failures: {summary['mcp_failures']}")
        print(f"- Unsuccessful runs: {summary['unsuccessful_runs']}")

    if report["failures"]:
        print("Canary checks: FAIL")
        for failure in report["failures"]:
            print(f"- {failure}")
        if args.enforce:
            return 1
    else:
        print("Canary checks: PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error: {error}")
        sys.exit(1)
