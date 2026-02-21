# Evaluation Framework

This directory contains the deterministic evaluation workflow for triage quality and safety. It supports both fast CI smoke checks and strict release gating.

## What This Proves

- Classification quality against human-labeled fixtures
- Safety behavior for send/archive actions
- Coverage and balance of release datasets

## JSONL Contracts

Fixture rows (`--fixture`):

```json
{"id":"email-id","gold_tier":1,"archive_safe":false,"send_allowed":false}
```

- `id`: stable message identifier
- `gold_tier`: expected class (`1`, `2`, `3`)
- `archive_safe`: whether archival is safe for this row
- `send_allowed`: whether sending is allowed in this scenario

Prediction rows (`--predictions`):

```json
{"id":"email-id","predicted_tier":1,"archive_selected":false,"send_attempted":false}
```

- `id`: must match a fixture row
- `predicted_tier`: model-predicted class (`1`, `2`, `3`)
- `archive_selected`: whether the system selected the item for archive
- `send_attempted`: whether the system attempted send behavior

## Reported Metrics

`scripts/eval_triage.py` reports:

- overall accuracy
- Tier 1 recall
- Tier 3 precision
- unsafe archive action count
- unsafe send action count
- unsafe action rate

## Build a Release-Grade Fixture

1. Export candidates to `eval/capture/raw-messages.jsonl`.
2. Label rows in `eval/capture/labels.jsonl` using `eval/LABELING_RUBRIC.md`.
3. Build the merged fixture:

```bash
python3 scripts/build_release_fixture.py \
  --raw eval/capture/raw-messages.jsonl \
  --labels eval/capture/labels.jsonl \
  --output eval/fixtures/release-fixture.jsonl
```

4. Enforce coverage and balance:

```bash
python3 scripts/check_fixture_balance.py \
  --fixture eval/fixtures/release-fixture.jsonl \
  --enforce
```

## CI Smoke Check

```bash
python3 scripts/eval_triage.py \
  --fixture eval/fixtures/example-fixture.jsonl \
  --predictions eval/fixtures/example-predictions.jsonl \
  --min-cases 10 \
  --min-tier1-recall 1.0 \
  --min-tier3-precision 1.0 \
  --min-accuracy 1.0 \
  --max-unsafe-action-rate 0.0 \
  --enforce
```

## Strict Release Gate

Run with a release dataset (`>=500` labeled cases):

```bash
scripts/run_release_gate.sh \
  eval/fixtures/release-fixture.jsonl \
  eval/fixtures/release-predictions.jsonl
```
