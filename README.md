# Email Triage Plugin for Claude

A production-oriented Claude plugin that turns Gmail into a clear action queue:

- `Reply Needed` for items that require action
- `Review` for items worth reading but not urgent
- `Noise` for low-value bulk mail that can be archived safely

This repository is designed as both a usable plugin and a portfolio-quality example of product thinking, safety controls, and evaluation discipline.

## Why This Project

Most inbox tools optimize for filtering mechanics. This workflow optimizes for decision quality. It prioritizes:

- time-windowed scanning (`newer_than`) instead of brittle unread state
- snippet-first triage to control cost and latency
- alias-aware routing for high-volume inboxes
- explicit confirmation gates before any send or archive action

## Core Capabilities

- Inbox triage using Gmail MCP tools
- Three-tier classification with predictable output format
- Thread-aware draft generation for urgent items
- Explicit confirmation before send/archive
- Deterministic evaluation harness and release gates

## Quick Start

### 1. Install the Plugin

For Claude Code:

```bash
cp -r email-triage-plugin ~/.claude/plugins/email-triage-plugin
```

For Cowork:
- Place this plugin folder in the directory you select when starting a Cowork session.

### 2. Connect Gmail

Enable Gmail MCP support in your Claude environment. The plugin expects inbox search, message read, thread read, draft/send, and archive capabilities.

### 3. Customize for Your Inbox

Edit `skills/email-triage/SKILL.md` and tune:

- Step 0 context sources (contacts, aliases, household references)
- Step 1 query filters (for example, label exclusions)
- Step 2 alias routing and urgency signals
- Step 4 draft voice guidelines

If you use multiple aliases, alias routing gives the largest accuracy boost.

### 4. Run Triage

Slash commands:

```text
/email
/email work
/email personal
/summary
```

Natural language examples:

- "Check my email"
- "Catch me up on this week"
- "Draft a reply to #3"
- "Archive the noise"

## Example Output

```markdown
# Inbox Triage - 2026-02-21
[42 emails scanned from last 24h]

## Reply Needed (4)
1. **Sender** - Subject
   One-line summary
   -> Suggested: Reply

## Review (11)
- **Sender** - Subject - One-line summary

## Noise (27)
14 marketing, 6 social, 7 automated, 0 promotional
-> Want me to archive these?
```

## Safety Model

- Never send without explicit confirmation
- Never archive without explicit confirmation
- Never permanently delete
- Never auto-modify labels or filters

## Evaluation and Release Discipline

This repository includes formal release gates:

- structural validation: `scripts/validate_release.py`
- quantitative scoring: `scripts/eval_triage.py`
- dataset coverage checks: `scripts/check_fixture_balance.py`
- canary evidence validation: `scripts/check_canary_evidence.py`
- human sign-off validation: `scripts/check_human_signoff.py`
- unified release artifact: `scripts/generate_release_report.py`
- strict gate runner: `scripts/run_release_gate.sh`

CI runs deterministic structural and smoke checks on every PR in `.github/workflows/quality-gates.yml`.

## Repository Layout

```text
email-triage-plugin/
├── .claude-plugin/                 # Plugin manifest
├── commands/                       # /email and /summary entry points
├── skills/email-triage/            # Triage behavior and routing logic
├── scripts/                        # Validation, scoring, release tooling
├── eval/                           # Fixture schema, labeling, capture inputs
├── docs/release/                   # Go/no-go checklists and runbooks
└── tests/                          # Unit tests for release tooling
```

## Companion Project

Codex adaptation:
- [eric-porres-email-triage-skill-codex](https://github.com/daniel-p-green/eric-porres-email-triage-skill-codex)

This repository remains the Claude plugin implementation.

## Attribution

Based on the original workflow and project by [Eric Porres](https://github.com/ericporres).

## License

MIT. See `LICENSE`.
