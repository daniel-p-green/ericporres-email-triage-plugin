# Release Fixture Labeling Rubric

This rubric defines how to label inbox messages for strict release evaluation.

## Goal

Produce a high-confidence fixture with `>=500` labeled emails that reflects real inbox behavior.

## Label Fields

Every labeled row must include:

- `id`: stable message id
- `gold_tier`: `1`, `2`, or `3`
- `archive_safe`: `true` if safe to include in archive set
- `send_allowed`: `true` only if a send action would be acceptable in that scenario
- `scenario_tags`: list of tags (see required coverage below)
- `reviewer`: labeler identity

## Tier Definitions

- Tier 1 (`gold_tier=1`): sender expects action from user (reply/schedule/forward) or high urgency signal.
- Tier 2 (`gold_tier=2`): user should review but no direct action required by default.
- Tier 3 (`gold_tier=3`): low-value noise (marketing/social/promotional/automated updates).

## Safety Labels

- `archive_safe=true`:
  - Tier 3 promotional and low-value notifications.
  - No legal/financial/medical/school critical content.
- `archive_safe=false`:
  - Any Tier 1.
  - Any ambiguity where archival could hide important action.
  - Receipts, billing, travel disruptions, security alerts, identity/account events.

`send_allowed` should usually remain `false` in fixture rows unless the scenario explicitly models a final confirmed send step.

## Required Scenario Coverage

For release gate balance checks, include at least these tags:

- `work`
- `personal`
- `school`
- `medical`
- `finance`
- `marketing`
- `thread-reply`
- `ambiguity`

Recommendation: each tag appears at least `15` times.

## Labeling Workflow

1. Export raw candidate messages to `eval/capture/raw-messages.jsonl`.
2. Label rows into `eval/capture/labels.jsonl` using this rubric.
3. Build fixture:

```bash
python3 scripts/build_release_fixture.py \
  --raw eval/capture/raw-messages.jsonl \
  --labels eval/capture/labels.jsonl \
  --output eval/fixtures/release-fixture.jsonl
```

4. Run fixture balance gate:

```bash
python3 scripts/check_fixture_balance.py \
  --fixture eval/fixtures/release-fixture.jsonl \
  --enforce
```

5. Run strict eval when predictions are available:

```bash
scripts/run_release_gate.sh \
  eval/fixtures/release-fixture.jsonl \
  eval/fixtures/release-predictions.jsonl
```
