# Canary Runbook (7-Day Release Gate)

Use this runbook to collect canary evidence before shipment.

## Scope

- Duration: 7 consecutive days
- Frequency: 2 runs per day
- Required windows per day:
  - `newer_than:1d`
  - `newer_than:3d`
- At least one high-volume run (`50+` emails) in the full canary period

## Evidence Files

- Log file: `docs/release/evidence/canary-log.csv`
- Human sign-off file: `docs/release/evidence/human-signoff.json`
- Final report output: `docs/release/reports/<date>-release-report.md`

Use templates:

- `docs/release/evidence/canary-log-template.csv`
- `docs/release/evidence/human-signoff.template.json`

## Per-Run Checklist

1. Execute triage for one required window (`1d` or `3d`).
2. Confirm explicit confirmation is required before archive/send.
3. Record one CSV row in `canary-log.csv` with:
   - date
   - run id
   - window query
   - email count
   - high volume flag
   - success/failure
   - unsafe action flag
   - critical misarchive flag
   - MCP failure flag
   - reviewer
   - notes

## Daily Exit Criteria

- Two runs logged (`1d` and `3d`)
- No unsafe action
- No critical misarchive
- No MCP failure

## End-of-Canary Validation

```bash
python3 scripts/check_canary_evidence.py \
  --log docs/release/evidence/canary-log.csv \
  --required-days 7 \
  --runs-per-day 2 \
  --enforce
```

## Full Release Packet

After canary and sign-off are complete:

```bash
python3 scripts/generate_release_report.py \
  --fixture eval/fixtures/release-fixture.jsonl \
  --predictions eval/fixtures/release-predictions.jsonl \
  --canary-log docs/release/evidence/canary-log.csv \
  --signoff docs/release/evidence/human-signoff.json
```
