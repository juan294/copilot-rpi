#!/usr/bin/env bash
# verify-counts.sh -- reconcile hardcoded error/rule counts against the catalogs.
#
# patterns/agent-errors.md and patterns/quick-reference.md are the source of
# truth for the error and rule counts. Every other file that states those
# counts in prose must agree, or it silently drifts -- GUIDE.md carried "45
# rules" for several releases after the corpus reached 54, and nothing caught
# it. Run this from anywhere; it resolves the repo root itself.
#
# Usage: templates/scripts/verify-counts.sh
# Exit:  0 = all counts agree, 1 = at least one mismatch (see BLOCKED/WHY/FIX)

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}
cd "$REPO_ROOT"

ERRORS_FILE="patterns/agent-errors.md"
RULES_FILE="patterns/quick-reference.md"

# emit_block <what> <why> <fix> -- corrective-hint convention.
# See methodology/ci-and-guardrails.md "Block messages are corrective hints".
#
# Deliberately duplicated in each verify script rather than sourced from a
# shared lib: these files are copied into downstream projects individually, so
# a shared lib/ may not exist alongside the copy. Self-contained is the
# convention here. Keep the copies byte-identical.
emit_block() {
  printf 'BLOCKED: %s\n\nWHY: %s\n\nFIX:\n%s\n\n' "$1" "$2" "$3"
}

FAILED=0

# --- Compute the true counts from the catalogs -----------------------------
ERROR_COUNT=$(grep -c '^## Error #' "$ERRORS_FILE")
RULE_COUNT=$(grep -cE '^[0-9]+\. \*\*' "$RULES_FILE")
INSTRUCTION_COUNT=$(find templates/github/instructions -maxdepth 1 -name '*.instructions.md.template' | wc -l | tr -d ' ')

# --- check_count <file> <pattern> <expected> <label> ------------------------
# Extracts the first number matched by <pattern> in <file> and compares it
# against <expected>, which the caller computed from the catalogs. <label>
# only names the location in the failure message.
#
# A pattern that matches nothing is a FAILURE, not a skip: it means the prose
# was reworded past what this script looks for, and drift there would go
# undetected from then on.
check_count() {
  local file="$1" pattern="$2" expected="$3" label="$4"

  if [[ ! -f "$file" ]]; then
    emit_block "$label expected in $file, but the file does not exist" \
      "A count location was renamed or removed without updating verify-counts.sh." \
      "  Update templates/scripts/verify-counts.sh to match the new location, or restore $file."
    FAILED=1
    return
  fi

  local found
  found=$(grep -oE "$pattern" "$file" | grep -oE '[0-9]+' | head -1 || true)

  if [[ -z "$found" ]]; then
    emit_block "$label not found in $file" \
      "The count reference was removed or reworded past what verify-counts.sh matches, so drift here would go undetected." \
      "  Restore a line matching pattern: $pattern
  in $file, or update verify-counts.sh's pattern for this location."
    FAILED=1
    return
  fi

  if [[ "$found" != "$expected" ]]; then
    emit_block "$label in $file says $found, catalog says $expected" \
      "A stale hardcoded count misleads anyone reading $file about the size of the catalog." \
      "  sed -i '' 's/\\b'\"$found\"'\\b/'\"$expected\"'/' $file   # macOS
  sed -i 's/\\b'\"$found\"'\\b/'\"$expected\"'/' $file      # Linux
  # then re-check the edit didn't touch an unrelated number in the same file"
    FAILED=1
  fi
}

# --- Known hardcoded locations ----------------------------------------------
check_count "AGENTS.md" '[0-9]+ known agent error patterns' "$ERROR_COUNT" "Error count (AGENTS.md header)"
check_count "AGENTS.md" '[0-9]+ operational rules' "$RULE_COUNT" "Rule count (AGENTS.md header)"

check_count "GUIDE.md" 'The [0-9]+ operational rules' "$RULE_COUNT" "Rule count (progressive disclosure section)"
check_count "GUIDE.md" '[0-9]+ documented errors' "$ERROR_COUNT" "Error count (Where to Go Deeper)"
check_count "GUIDE.md" '[0-9]+ rules with scope/stack tags' "$RULE_COUNT" "Rule count (Where to Go Deeper)"

check_count "GUIDE.md" 'blueprint provides [0-9]+ instruction templates' "$INSTRUCTION_COUNT" "Instruction-template count (progressive disclosure section)"

# --- No duplicate rule numbers ----------------------------------------------
DUPES=$(grep -oE '^[0-9]+\.' "$RULES_FILE" | tr -d '.' | sort -n | uniq -d || true)
if [[ -n "$DUPES" ]]; then
  emit_block "Duplicate rule number(s) in $RULES_FILE: $DUPES" \
    "Two rules sharing one number makes cross-references (agent-errors.md, prompts, CHANGELOG.md) ambiguous." \
    "  Renumber the newer rule to one past the current maximum, per CONTRIBUTING.md's retirement/renumbering guidance."
  FAILED=1
fi

# --- No gaps that aren't in the Retirement Ledger ---------------------------
# Rule numbers are permanent: a gap is legitimate only when the ledger records
# why. An unexplained gap means a rule was deleted without going through the
# retirement path, so its inbound references were never checked.
LEDGER="CONTRIBUTING.md"
if [[ -f "$LEDGER" ]]; then
  LEDGER_RETIRED=$(
    awk '/^#### Retirement Ledger/{f=1;next} f && /^#{1,3} /{f=0} f && /^\| *[0-9]+ *\|/' "$LEDGER" \
      | awk -F'|' '{gsub(/ /,"",$2); print $2}' | sort -n || true
  )
  PRESENT=$(grep -oE '^[0-9]+\.' "$RULES_FILE" | tr -d '.' | sort -n)
  MAX=$(printf '%s\n' "$PRESENT" | tail -1)
  GAPS=""
  for ((n = 1; n <= MAX; n++)); do
    printf '%s\n' "$PRESENT" | grep -qx "$n" && continue
    printf '%s\n' "$LEDGER_RETIRED" | grep -qx "$n" && continue
    GAPS="$GAPS $n"
  done
  if [[ -n "$GAPS" ]]; then
    emit_block "Rule number(s) missing from $RULES_FILE with no ledger entry:$GAPS" \
      "A gap in the numbering that the Retirement Ledger does not explain means a rule was removed without the retirement procedure, so its inbound references were never checked." \
      "  Restore the rule to $RULES_FILE, or add a Retirement Ledger row in $LEDGER recording its ground and replacement."
    FAILED=1
  fi
fi

if [[ "$FAILED" -ne 0 ]]; then
  exit 1
fi

echo "PASS: $ERROR_COUNT errors, $RULE_COUNT rules, $INSTRUCTION_COUNT instruction"
echo "      templates -- all hardcoded locations agree, no gaps outside the ledger."
exit 0
