# Capture Inputs

This directory holds raw capture data and human labels used to build release fixtures.

## Files

- `raw-messages.jsonl`: exported candidate messages with stable IDs and minimal context
- `labels.jsonl`: reviewer labels keyed by `id`
- `raw-messages.template.jsonl`: starter schema for raw capture rows
- `labels.template.jsonl`: starter schema for label rows

## Build the Fixture

```bash
python3 scripts/build_release_fixture.py \
  --raw eval/capture/raw-messages.jsonl \
  --labels eval/capture/labels.jsonl \
  --output eval/fixtures/release-fixture.jsonl
```

## Data Handling Guidance

- Keep raw capture files local and sanitized.
- Use stable IDs so labels and predictions map deterministically.
- Follow `eval/LABELING_RUBRIC.md` for tier and safety consistency.
