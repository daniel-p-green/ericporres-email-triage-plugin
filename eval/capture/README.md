# Capture Inputs for Release Fixture

This folder stores raw capture and human labels used to build the strict release fixture.

## Files

- `raw-messages.jsonl`: exported candidate messages (id + context metadata)
- `labels.jsonl`: reviewer labels aligned to `raw-messages` by `id`

Use the templates in this folder to start.

## Build Fixture

```bash
python3 scripts/build_release_fixture.py \
  --raw eval/capture/raw-messages.jsonl \
  --labels eval/capture/labels.jsonl \
  --output eval/fixtures/release-fixture.jsonl
```
