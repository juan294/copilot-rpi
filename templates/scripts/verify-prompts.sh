#!/usr/bin/env bash
# Validate declared Copilot native surfaces and the no-emoji documentation rule.
set -u
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || exit 1
cd "$repo_root" || exit 1
failed=0

if [[ ! -f templates/scripts/rpi-distribution.py ]]; then
  printf 'BLOCKED: missing templates/scripts/rpi-distribution.py\nWHY: native metadata cannot be checked\nFIX: restore the renderer and rerun this script\n'
  failed=1
elif ! uv run --locked python templates/scripts/rpi-distribution.py validate --source .; then
  printf 'BLOCKED: Copilot native surface validation failed\nWHY: a declared profile, resource or active file is invalid\nFIX: review the named error and rerun uv run --locked python templates/scripts/rpi-distribution.py validate --source .\n'
  failed=1
fi

if [[ -f templates/scripts/rpi-distribution.py ]] &&
   ! uv run --locked python templates/scripts/rpi-distribution.py check-generated --source . --profile cli; then
  printf 'BLOCKED: self-applied Copilot surfaces differ from the declared CLI profile\nWHY: an expected active file is missing or changed\nFIX: review the drift and rerun uv run --locked python templates/scripts/rpi-distribution.py check-generated --source . --profile cli\n'
  failed=1
fi

if command -v perl >/dev/null 2>&1; then
  while IFS= read -r -d '' file; do
    [[ -f "$file" ]] || continue
    grep -q 'contract:allow-emoji' "$file" && continue
    hits="$(perl -CSD -ne 'while (/([\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{FE0F}])/g) { printf "line %d: U+%04X\n", $., ord($1) }' "$file" 2>/dev/null)"
    if [[ -n "$hits" ]]; then
      printf 'BLOCKED: emoji in %s\nWHY: documentation policy forbids emoji\nFIX: replace these glyphs with text: %s\n' "$file" "$hits"
      failed=1
    fi
  done < <(git ls-files -z '*.md')
fi

if [[ "$failed" -eq 0 ]]; then
  printf 'PASS: declared Copilot surfaces and no-emoji rule\n'
fi
exit "$failed"
