#!/usr/bin/env bash
# Run the portable checks through the candidate-bound receipt gate.
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run --locked python templates/scripts/rpi-verify.py --root .
