#!/usr/bin/env bash
# Copilot RPI update discovery. Opt in by invoking this script or scheduling it
# after reviewing `python3 rpi-automation.py schedule-preview --job update ...`.
# The script writes a ready plan only. It never applies, commits or publishes.
# Usage: COPILOT_RPI_PATH=/absolute/blueprint COPILOT_MODEL=selected-model \
#   bash copilot-rpi-update-agent.sh /absolute/project
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BLUEPRINT="${COPILOT_RPI_PATH:-}"
if [ -z "$BLUEPRINT" ]; then
  echo "BLOCKED: set COPILOT_RPI_PATH to the reviewed local blueprint checkout" >&2
  exit 2
fi
exec python3 "$SCRIPT_DIR/rpi-automation.py" run --job update \
  --project "$PROJECT_ROOT" --blueprint "$BLUEPRINT"
