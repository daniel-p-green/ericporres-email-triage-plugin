#!/usr/bin/env python3
"""Deterministic release validation for the email triage plugin."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")

PLACEHOLDER_PATTERNS = [
    ("yourdomain placeholder", re.compile(r"\byourdomain(?:\.com)?\b", re.IGNORECASE)),
    ("yourcompany placeholder", re.compile(r"\byourcompany(?:\.com)?\b", re.IGNORECASE)),
    ("[Your Name] placeholder", re.compile(r"\[Your Name\]")),
    ("<your-...> placeholder", re.compile(r"<\s*your[^>]*>", re.IGNORECASE)),
    ("TODO marker", re.compile(r"\bTODO\b")),
    ("FIXME marker", re.compile(r"\bFIXME\b")),
    ("TBD marker", re.compile(r"\bTBD\b")),
]

TARGET_GLOBS = [
    "README.md",
    "commands/*.md",
    "skills/**/*.md",
    ".claude-plugin/plugin.json",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(markdown_text: str) -> str | None:
    if not markdown_text.startswith("---\n"):
        return None
    end_index = markdown_text.find("\n---\n", 4)
    if end_index == -1:
        return None
    return markdown_text[4:end_index]


def check_manifest(root: Path, failures: list[str]) -> None:
    manifest_path = root / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        failures.append(f"Missing manifest: {manifest_path}")
        return

    try:
        manifest = json.loads(read_text(manifest_path))
    except json.JSONDecodeError as error:
        failures.append(f"Invalid JSON in {manifest_path}: {error}")
        return

    required = [
        ("name", manifest.get("name")),
        ("version", manifest.get("version")),
        ("description", manifest.get("description")),
        ("author.name", (manifest.get("author") or {}).get("name")),
    ]
    for key, value in required:
        if not isinstance(value, str) or not value.strip():
            failures.append(f"Manifest key `{key}` must be a non-empty string in {manifest_path}")

    version = manifest.get("version")
    if isinstance(version, str) and not SEMVER_PATTERN.match(version):
        failures.append(f"Manifest version must be semver in {manifest_path}: {version}")


def check_frontmatter_fields(root: Path, failures: list[str]) -> None:
    command_files = sorted((root / "commands").glob("*.md"))
    if not command_files:
        failures.append("No command files found in commands/")
        return

    for command_file in command_files:
        frontmatter = parse_frontmatter(read_text(command_file))
        if frontmatter is None:
            failures.append(f"Missing YAML frontmatter in {command_file}")
            continue

        if not re.search(r"(?m)^description\s*:\s*(.+)$", frontmatter):
            failures.append(f"Missing or empty `description` in {command_file}")

    skill_file = root / "skills" / "email-triage" / "SKILL.md"
    if not skill_file.exists():
        failures.append(f"Missing skill file: {skill_file}")
        return

    skill_frontmatter = parse_frontmatter(read_text(skill_file))
    if skill_frontmatter is None:
        failures.append(f"Missing YAML frontmatter in {skill_file}")
        return

    for field in ("name", "description"):
        if not re.search(rf"(?m)^{field}\s*:\s*(.+)$", skill_frontmatter):
            failures.append(f"Missing or empty `{field}` in {skill_file}")


def check_placeholders(root: Path, failures: list[str]) -> None:
    files_to_scan: set[Path] = set()
    for glob_pattern in TARGET_GLOBS:
        files_to_scan.update(root.glob(glob_pattern))

    for file_path in sorted(files_to_scan):
        if not file_path.is_file():
            continue

        content = read_text(file_path)
        lines = content.splitlines()
        for index, line in enumerate(lines, start=1):
            for label, pattern in PLACEHOLDER_PATTERNS:
                if pattern.search(line):
                    relpath = file_path.relative_to(root)
                    failures.append(
                        f"Placeholder check failed ({label}) at {relpath}:{index}: {line.strip()}"
                    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []

    check_manifest(root, failures)
    check_frontmatter_fields(root, failures)
    check_placeholders(root, failures)

    if failures:
        print("Release validation failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Release validation passed.")
    print("- Manifest is complete and semver-valid.")
    print("- Command and skill frontmatter are present.")
    print("- No blocked template placeholders were found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
