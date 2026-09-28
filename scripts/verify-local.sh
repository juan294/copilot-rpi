#!/usr/bin/env bash
# Run the portable checks in order, retaining every failure.
set -u
cd "$(dirname "$0")/.." || exit 1

failed=0
run_check() {
  printf '\nCHECK: %s\n' "$*"
  "$@"
  result=$?
  printf 'EXIT: %s (%s)\n' "$result" "$*"
  if [ "$result" -ne 0 ]; then failed=1; fi
}

run_check uv run --locked python -m unittest discover -s tests -p 'test_*.py'
run_check bash templates/scripts/verify-counts.sh
run_check bash templates/scripts/verify-version.sh
run_check bash templates/scripts/verify-prompts.sh
run_check shellcheck --severity=warning templates/scripts/*.sh templates/scripts/agents/*.sh templates/scripts/agents/lib/*.sh scripts/*.sh
run_check npm exec -- markdownlint-cli2 '**/*.md' '#node_modules' '#.venv' '#.claude' '#graphify-out' '#.rpi/local'
run_check uv run --locked python scripts/check-upstream.py --lock upstream/cc-rpi.lock.json --inventory upstream/cc-rpi.inventory.json --check
run_check uv run --locked python scripts/check-links.py
exit "$failed"
