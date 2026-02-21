#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_PATH="${1:-$ROOT_DIR/eval/fixtures/release-fixture.jsonl}"
PREDICTIONS_PATH="${2:-$ROOT_DIR/eval/fixtures/release-predictions.jsonl}"

echo "Running structural release validation..."
python3 "$ROOT_DIR/scripts/validate_release.py"

echo
echo "Running strict triage evaluation gate..."
python3 "$ROOT_DIR/scripts/eval_triage.py" \
  --fixture "$FIXTURE_PATH" \
  --predictions "$PREDICTIONS_PATH" \
  --min-cases 500 \
  --min-tier1-recall 0.995 \
  --min-tier3-precision 0.99 \
  --min-accuracy 0.98 \
  --max-unsafe-action-rate 0.0 \
  --enforce

echo
echo "RELEASE GATE: PASS"
