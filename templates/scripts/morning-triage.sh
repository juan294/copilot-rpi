#!/usr/bin/env bash
# Report-only morning triage. Explicit project paths are required.
# Preview a scheduler entry with `python3 rpi-automation.py schedule-preview
# --job triage --project /absolute/project`; activation is separate.
# Usage: COPILOT_MODEL=selected-model bash morning-triage.sh /absolute/project [...]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$#" -eq 0 ]; then
  echo "BLOCKED: pass one or more project directories" >&2
  exit 2
fi
result=0
for project in "$@"; do
  python3 "$SCRIPT_DIR/rpi-automation.py" run --job triage --project "$project" || result=1
done
exit "$result"
