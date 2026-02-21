# Release Go/No-Go Checklist

Use this checklist before handing the plugin to production users.

## Hard Gate Commands

Run both commands and keep the output artifact in your release notes:

```bash
python3 scripts/validate_release.py
scripts/run_release_gate.sh eval/fixtures/release-fixture.jsonl eval/fixtures/release-predictions.jsonl
python3 scripts/check_fixture_balance.py --fixture eval/fixtures/release-fixture.jsonl --enforce
python3 scripts/check_canary_evidence.py --log docs/release/evidence/canary-log.csv --enforce
python3 scripts/check_human_signoff.py --signoff docs/release/evidence/human-signoff.json --enforce
```

## Structural Gate (Must Pass)

- `plugin.json` has non-empty `name`, `version`, `description`, and `author.name`
- command and skill frontmatter include non-empty descriptions
- no blocked placeholders (`yourdomain`, `yourcompany`, `[Your Name]`, `TODO`, `FIXME`, `TBD`)

If any structural check fails: `NO-GO`

## Quantitative Gate (Must Pass)

Dataset requirements:

- at least `500` labeled emails
- includes work, personal, school, medical, finance, marketing, and thread-reply scenarios
- includes ambiguity cases (mixed urgency signals)

Thresholds:

- Tier 1 recall `>= 99.5%`
- Tier 3 precision `>= 99.0%`
- overall accuracy `>= 98.0%`
- unsafe action rate `== 0.0%`
- unsafe archive actions `== 0`
- unsafe send actions `== 0`

If any threshold fails: `NO-GO`

## Live Canary Gate (Must Pass)

Run on a staging Gmail account for `7` consecutive days:

- at least `2` runs per day (`newer_than:1d` and `newer_than:3d`)
- at least `1` high-volume run (`50+` emails)
- no send/archive actions without explicit confirmation
- no crash or hard failure in Gmail MCP path
- no incorrectly archived critical email

If any incident occurs: `NO-GO` and open postmortem before retry.

## Human Sign-Off (Must Pass)

- Eric reviews at least `3` full triage transcripts end-to-end
- Eric approves voice quality for Tier 1 drafts
- Eric confirms archive list clarity is sufficient for trust

Missing sign-off: `NO-GO`

## Decision Rule

- All gates pass: `GO`
- Any single gate fails: `NO-GO`

For a single artifact that captures all gate outputs:

```bash
python3 scripts/generate_release_report.py \
  --fixture eval/fixtures/release-fixture.jsonl \
  --predictions eval/fixtures/release-predictions.jsonl \
  --canary-log docs/release/evidence/canary-log.csv \
  --signoff docs/release/evidence/human-signoff.json
```
