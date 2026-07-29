#!/usr/bin/env bash
# verify-prompts.sh -- enforce the Copilot configuration-surface contract.
#
# GitHub Copilot has no PreToolUse/PostToolUse hook mechanism, so this blueprint
# cannot enforce rules at edit time the way a hook would. CI is the enforcement
# point instead: this script moves the mechanically-checkable subset of the
# Copilot-specific rules from advisory prose into a hard gate.
#
# What it checks, and the rule each check enforces:
#   1. Every *.prompt.md has YAML frontmatter with `mode:` and `description:`
#      (Rule #20 / Error #13 -- no frontmatter = invisible in the `/` menu).
#   2. No `$ARGUMENTS` in prompt files (Rule #21 / Error #14 -- that is Claude
#      Code syntax; Copilot uses `${input:varName}`).
#   3. Every *.instructions.md* has `applyTo:` in frontmatter
#      (Rule #22 / Error #15 -- no applyTo = the file never loads).
#   4. Chat modes live in a `chatmodes/` directory and declare `description:`
#      (Error #16 -- a chat mode in the wrong directory is silently ignored).
#   5. Self-applied .github/prompts/ copies match their templates/prompts/
#      counterpart, so the repo does not drift from the blueprint it ships.
#   6. No emoji in any tracked markdown (Rule #54).
#
# Usage: templates/scripts/verify-prompts.sh
# Exit:  0 = contract satisfied, 1 = at least one violation (BLOCKED/WHY/FIX)

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}
cd "$REPO_ROOT"

# emit_block <what> <why> <fix> -- corrective-hint convention.
# See methodology/ci-and-guardrails.md "Block messages are corrective hints".
# Deliberately duplicated per script; keep the copies byte-identical.
emit_block() {
  printf 'BLOCKED: %s\n\nWHY: %s\n\nFIX:\n%s\n\n' "$1" "$2" "$3"
}

FAILED=0

# has_frontmatter_key <file> <key> -- true if <key>: appears inside the leading
# `---` fenced YAML block. Checking the whole file would false-pass on a prompt
# that merely mentions the key in its body.
has_frontmatter_key() {
  awk -v key="$2" '
    NR == 1 && $0 != "---" { exit 1 }
    NR > 1 && $0 == "---"  { exit 1 }
    NR > 1 && $0 ~ "^" key ":" { found = 1; exit 0 }
    END { exit(found ? 0 : 1) }
  ' "$1"
}

# --- Check 1 & 2: prompt files ----------------------------------------------
PROMPT_FILES=$(git ls-files '*.prompt.md')
for f in $PROMPT_FILES; do
  for key in mode description; do
    if ! has_frontmatter_key "$f" "$key"; then
      emit_block "$f is missing '$key:' in its YAML frontmatter" \
        "A .prompt.md without frontmatter does not appear in Copilot's '/' command menu, so the prompt is invisible to the user (Rule #20, Error #13). 'mode:' selects agent vs ask; 'description:' is what the menu displays." \
        "  Add a frontmatter block at the very top of $f:

  ---
  mode: agent
  description: \"One line describing what this prompt does\"
  ---"
      FAILED=1
    fi
  done

  if grep -q '\$ARGUMENTS' "$f"; then
    emit_block "$f uses \$ARGUMENTS" \
      "\$ARGUMENTS is Claude Code syntax and is never substituted by Copilot -- the prompt receives the literal string (Rule #21, Error #14)." \
      "  Replace \$ARGUMENTS with a named Copilot input in $f:
  grep -n '\$ARGUMENTS' $f
  # then rewrite each as \${input:descriptiveName}"
    FAILED=1
  fi
done

# --- Check 3: path-specific instruction files -------------------------------
INSTRUCTION_FILES=$(git ls-files '*.instructions.md' '*.instructions.md.template')
for f in $INSTRUCTION_FILES; do
  if ! has_frontmatter_key "$f" "applyTo"; then
    emit_block "$f is missing 'applyTo:' in its YAML frontmatter" \
      "An instructions file without an applyTo glob is never loaded into context by Copilot -- it is inert, and its absence is silent (Rule #22, Error #15)." \
      "  Add the glob that should trigger this file to $f's frontmatter:

  ---
  applyTo: \"**/*.test.{ts,tsx}\"
  ---"
    FAILED=1
  fi
done

# --- Check 4: chat modes ----------------------------------------------------
CHATMODE_FILES=$(git ls-files '*.chatmode.md')
for f in $CHATMODE_FILES; do
  case "$(dirname "$f")" in
    */chatmodes) ;;
    *)
      emit_block "$f is not in a chatmodes/ directory" \
        "Copilot only discovers chat modes under .github/chatmodes/ (or the templates mirror of it). A .chatmode.md anywhere else is silently ignored (Error #16)." \
        "  git mv $f \$(dirname \$(dirname $f))/chatmodes/\$(basename $f)"
      FAILED=1
      ;;
  esac

  if ! has_frontmatter_key "$f" "description"; then
    emit_block "$f is missing 'description:' in its YAML frontmatter" \
      "A chat mode without a description has no label in the mode picker, so a user cannot tell what it does before selecting it." \
      "  Add 'description: \"...\"' to the frontmatter block at the top of $f."
    FAILED=1
  fi
done

# --- Check 5: self-applied copies match their templates ---------------------
# This repo eats its own dog food: .github/prompts/ holds the prompts it runs
# on itself. Those are copies, not symlinks, so they go stale silently -- and
# did, for several releases. Only files that HAVE a template counterpart are
# compared; repo-specific prompts with no counterpart are left alone.
for active in $(git ls-files '.github/prompts/*.prompt.md'); do
  template="templates/prompts/$(basename "$active")"
  [[ -f "$template" ]] || continue
  if ! diff -q "$template" "$active" >/dev/null; then
    emit_block "$active has drifted from $template" \
      "The self-applied copy is what this repo actually runs, and the template is what it ships to adopters. When they diverge, the blueprint is no longer testing what it publishes." \
      "  diff $template $active     # review the drift first
  cp $template $active       # then adopt the template, or update the template if the active copy is the improvement"
    FAILED=1
  fi
done

# --- Check 6: no emoji in tracked markdown ----------------------------------
# Ranges target true emoji/pictographs. Deliberately EXCLUDE arrows
# (U+2190-21FF, e.g. ->), em-dash (U+2014), and box-drawing (U+2500-257F),
# all of which this repo's docs use legitimately.
if command -v perl >/dev/null 2>&1; then
  for f in $(git ls-files '*.md'); do
    grep -q 'contract:allow-emoji' "$f" 2>/dev/null && continue
    HITS=$(perl -CSD -ne \
      'while (/([\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{FE0F}])/g) {
         printf "    line %d: U+%04X\n", $., ord($1) }' "$f" 2>/dev/null)
    if [[ -n "$HITS" ]]; then
      emit_block "emoji in $f" \
        "Project policy (Rule #54): docs use text equivalents (PASS, [x], ->), not emoji." \
        "  Remove the emoji at:
$HITS
  (Only if a glyph is a required literal example, add a line containing
  <!-- contract:allow-emoji --> to that file to skip this check.)"
      FAILED=1
    fi
  done
fi

if [[ "$FAILED" -ne 0 ]]; then
  exit 1
fi

P_N=$(printf '%s\n' "$PROMPT_FILES" | grep -c . || true)
I_N=$(printf '%s\n' "$INSTRUCTION_FILES" | grep -c . || true)
C_N=$(printf '%s\n' "$CHATMODE_FILES" | grep -c . || true)
echo "PASS: $P_N prompt files, $I_N instruction files, $C_N chat modes satisfy the"
echo "      Copilot surface contract; no template/active drift; no emoji."
exit 0
