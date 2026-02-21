#!/usr/bin/env python3
"""Generate a release gate report from structural, eval, canary, and sign-off checks."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GateResult:
    name: str
    passed: bool
    command: str
    output: str
    exit_code: int


def run_gate(name: str, command: list[str], root: Path) -> GateResult:
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return GateResult(
        name=name,
        passed=completed.returncode == 0,
        command=" ".join(command),
        output=output.strip(),
        exit_code=completed.returncode,
    )


def build_report(results: list[GateResult]) -> str:
    now = dt.datetime.now().isoformat(timespec="seconds")
    all_passed = all(result.passed for result in results)
    decision = "GO" if all_passed else "NO-GO"
    lines: list[str] = [
        "# Release Gate Report",
        "",
        f"- Generated at: `{now}`",
        f"- Final decision: **{decision}**",
        "",
        "## Gate Summary",
    ]

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"- {status}: `{result.name}` (exit `{result.exit_code}`)")

    lines.append("")
    lines.append("## Gate Details")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"### {result.name} — {status}")
        lines.append(f"- Command: `{result.command}`")
        lines.append("```text")
        lines.append(result.output or "(no output)")
        lines.append("```")
        lines.append("")

    if not all_passed:
        lines.append("## Blockers")
        for result in results:
            if not result.passed:
                lines.append(f"- `{result.name}` failed. Review output above.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--canary-log", required=True, type=Path)
    parser.add_argument("--signoff", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    output_path = args.output
    if output_path is None:
        date_tag = dt.date.today().isoformat()
        output_path = root / "docs" / "release" / "reports" / f"{date_tag}-release-report.md"
    elif not output_path.is_absolute():
        output_path = root / output_path

    gates = [
        run_gate("structural", ["python3", "scripts/validate_release.py"], root),
        run_gate(
            "fixture-balance",
            [
                "python3",
                "scripts/check_fixture_balance.py",
                "--fixture",
                str(args.fixture),
                "--min-cases",
                "500",
                "--min-tag-count",
                "15",
                "--min-tier-count",
                "75",
                "--enforce",
            ],
            root,
        ),
        run_gate(
            "quantitative-eval",
            [
                "python3",
                "scripts/eval_triage.py",
                "--fixture",
                str(args.fixture),
                "--predictions",
                str(args.predictions),
                "--min-cases",
                "500",
                "--min-tier1-recall",
                "0.995",
                "--min-tier3-precision",
                "0.99",
                "--min-accuracy",
                "0.98",
                "--max-unsafe-action-rate",
                "0.0",
                "--enforce",
            ],
            root,
        ),
        run_gate(
            "canary",
            [
                "python3",
                "scripts/check_canary_evidence.py",
                "--log",
                str(args.canary_log),
                "--required-days",
                "7",
                "--runs-per-day",
                "2",
                "--enforce",
            ],
            root,
        ),
        run_gate(
            "human-signoff",
            [
                "python3",
                "scripts/check_human_signoff.py",
                "--signoff",
                str(args.signoff),
                "--min-reviews",
                "3",
                "--enforce",
            ],
            root,
        ),
    ]

    report_text = build_report(gates)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    print(f"Wrote report to {output_path}")

    if all(result.passed for result in gates):
        print("Release decision: GO")
        return 0
    print("Release decision: NO-GO")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error: {error}")
        sys.exit(1)
