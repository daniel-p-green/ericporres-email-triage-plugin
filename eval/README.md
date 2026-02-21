# Triage Evaluation Harness

This folder defines a deterministic scoring workflow for inbox triage quality.

## JSONL Schema

Fixture (`--fixture`) rows:

```json
{"id":"email-id","gold_tier":1,"archive_safe":false,"send_allowed":false}
```

- `id`: stable email identifier
- `gold_tier`: `1`, `2`, or `3`
- `archive_safe`: `true` only if archiving this email is safe
- `send_allowed`: `true` only if a send action would be allowed in the test scenario

Predictions (`--predictions`) rows:

```json
{"id":"email-id","predicted_tier":1,"archive_selected":false,"send_attempted":false}
```

- `id`: must match a fixture id
- `predicted_tier`: `1`, `2`, or `3`
- `archive_selected`: whether the system attempted to include this in archive action set
- `send_attempted`: whether the system attempted send behavior

## Metrics

`scripts/eval_triage.py` reports:

- overall accuracy
- Tier 1 recall
- Tier 3 precision
- unsafe archive action count
- unsafe send action count
- unsafe action rate

## Build a Real Release Fixture

1. Export candidates to `eval/capture/raw-messages.jsonl`.
2. Label rows in `eval/capture/labels.jsonl` using `eval/LABELING_RUBRIC.md`.
3. Build fixture:

```bash
python3 scripts/build_release_fixture.py \
  --raw eval/capture/raw-messages.jsonl \
  --labels eval/capture/labels.jsonl \
  --output eval/fixtures/release-fixture.jsonl
```

4. Verify dataset coverage:

```bash
python3 scripts/check_fixture_balance.py \
  --fixture eval/fixtures/release-fixture.jsonl \
  --enforce
```

## Smoke Test (CI)

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

## Release Gate (Strict)

Use your own larger dataset (`>=500` cases):

```bash
scripts/run_release_gate.sh \
  eval/fixtures/release-fixture.jsonl \
  eval/fixtures/release-predictions.jsonl
```
