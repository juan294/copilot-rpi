#!/usr/bin/env bash
# verify-version.sh -- keep every hand-maintained version string in agreement.
#
# CHANGELOG.md is the source of truth: its newest released `## [X.Y.Z]` header
# is the version this repo currently claims to be. Every other version string is
# hand-maintained, which is why they drift.
#
# /release hardened the PROMPT against that (a mandatory `git grep` before and
# after the bump). This script is the mechanical backstop: a release done by
# hand, or by an agent that skimmed the instructions, still cannot ship stale.
#
# Three checks:
#   1. Declared locations match the CHANGELOG version exactly.
#   2. The PREVIOUS released version appears nowhere outside CHANGELOG history
#      -- this is what catches "bumped some files, missed one".
#   3. The Retirement Ledger does not pre-commit to more than one unreleased
#      version, and only does so while a release is actually pending.
#
# Usage: templates/scripts/verify-version.sh
# Exit:  0 = every version string agrees, 1 = drift (see BLOCKED/WHY/FIX)

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}
cd "$REPO_ROOT"

CHANGELOG="CHANGELOG.md"
LEDGER="CONTRIBUTING.md"

# emit_block <what> <why> <fix> -- corrective-hint convention.
# See methodology/ci-and-guardrails.md "Block messages are corrective hints".
# Deliberately duplicated per script; keep the copies byte-identical.
emit_block() {
  printf 'BLOCKED: %s\n\nWHY: %s\n\nFIX:\n%s\n\n' "$1" "$2" "$3"
}

FAILED=0

# released_versions -- newest first, excluding [Unreleased].
released_versions() {
  grep -oE '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$1" | tr -d '#[] '
}

# --- Source of truth ---------------------------------------------------------
VERSION="$(released_versions "$CHANGELOG" | head -1)"
PREV_VERSION="$(released_versions "$CHANGELOG" | sed -n '2p')"

if [[ -z "$VERSION" ]]; then
  emit_block "No released version header found in $CHANGELOG" \
    "The newest '## [X.Y.Z]' header is the version this repo claims to be; without it there is nothing to check the other files against." \
    "  Add a released section header to $CHANGELOG, e.g.:  ## [1.0.0] - YYYY-MM-DD"
  exit 1
fi

# --- Check 1: declared locations ---------------------------------------------
# check_version <file> <grep-pattern> <label> [expected-occurrences]
# Every occurrence must match; a shields.io badge repeats the version up to
# three times on one line (label text, image URL, releases/tag href) and
# partial bumps there are the most common form of this bug.
check_version() {
  local file="$1" pattern="$2" label="$3" want_n="${4:-}"

  if [[ ! -f "$file" ]]; then
    emit_block "$label expected in $file, but the file does not exist" \
      "A version location was renamed or removed without updating verify-version.sh, so drift there would go undetected." \
      "  Restore $file, or update templates/scripts/verify-version.sh to match the new location."
    FAILED=1
    return
  fi

  local found_all bad n
  found_all="$(grep -oE "$pattern" "$file" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || true)"

  if [[ -z "$found_all" ]]; then
    emit_block "$label not found in $file" \
      "The version reference was removed or reworded past what verify-version.sh matches, so it would silently stop being checked." \
      "  Restore a version string matching pattern: $pattern
  in $file, or update verify-version.sh's pattern for this location."
    FAILED=1
    return
  fi

  n="$(printf '%s\n' "$found_all" | wc -l | tr -d ' ')"
  if [[ -n "$want_n" && "$n" != "$want_n" ]]; then
    emit_block "$label in $file has $n version strings, expected $want_n" \
      "This location is known to repeat the version (a shields.io badge carries it in the label, the image URL, and the release link). A changed count means the shape changed and a partial bump could now hide here." \
      "  Check $file and update verify-version.sh's expected occurrence count if the change is intentional."
    FAILED=1
  fi

  bad="$(printf '%s\n' "$found_all" | grep -v "^${VERSION}$" || true)"
  if [[ -n "$bad" ]]; then
    emit_block "$label in $file says $(printf '%s' "$bad" | tr '\n' ' '), $CHANGELOG says $VERSION" \
      "A stale version string tells users they are on a release they are not on." \
      "  sed -i '' 's/$(printf '%s' "$bad" | head -1)/$VERSION/g' $file   # macOS
  sed -i 's/$(printf '%s' "$bad" | head -1)/$VERSION/g' $file      # Linux
  # then re-run this script -- a badge can repeat the version more than once"
    FAILED=1
  fi
}

# copilot-rpi's README badge is DYNAMIC -- shields.io reads the version from
# the GitHub releases API (`img.shields.io/github/v/release/...`), so it cannot
# go stale and there is nothing to check. That is the preferred shape.
#
# A hardcoded badge (`Version-1.2.3-blue`) carries the version up to three
# times on one line and is the single most common source of this bug. If this
# repo -- or a downstream project copying this script -- ever adopts one, or
# gains a manifest, declare it here. Optional locations are checked only when
# present, so a project without them is not blocked.
DECLARED=0
for manifest in package.json vsc-extension-quickstart.json; do
  if [[ -f "$manifest" ]]; then
    check_version "$manifest" '"version": *"[0-9]+\.[0-9]+\.[0-9]+"' "Manifest version ($manifest)" 1
    DECLARED=$((DECLARED + 1))
  fi
done

if grep -qE 'shields\.io/badge/Version-[0-9]+\.[0-9]+\.[0-9]+' README.md 2>/dev/null; then
  check_version "README.md" 'Version[-: ]+v?[0-9]+\.[0-9]+\.[0-9]+|releases/tag/v[0-9]+\.[0-9]+\.[0-9]+' "Version badge" 3
  DECLARED=$((DECLARED + 1))
fi

# --- Check 2: the previous version lingers nowhere ---------------------------
# This is the check that catches a partial bump. After releasing X, any file
# still naming X-1 outside CHANGELOG history was missed. Illustrative versions
# in prompt examples (v1.0.0, v1.2.3) never collide with a real prior release.
#
# Excluded, because these record version HISTORY rather than declaring the
# current version -- naming an old release in them is correct, not stale:
#   CHANGELOG.md    -- the history itself
#   CONTRIBUTING.md -- the Retirement Ledger's "Retired in" column; check 3
#                      validates those separately against real releases
#   docs/           -- plans and deviation logs describe the release they
#                      shipped in
if [[ -n "$PREV_VERSION" ]]; then
  STALE="$(git grep -n -F "$PREV_VERSION" -- \
             ':!CHANGELOG.md' ':!CONTRIBUTING.md' \
             ':!docs/' ':!*.lock' 2>/dev/null || true)"
  if [[ -n "$STALE" ]]; then
    emit_block "Previous version $PREV_VERSION still appears outside $CHANGELOG:
$(printf '%s' "$STALE" | sed 's/^/  /')" \
      "After a bump to $VERSION, any surviving reference to $PREV_VERSION is a file the release missed." \
      "  Update each line above to $VERSION, or -- if the reference is deliberately historical -- move it into $CHANGELOG where history belongs."
    FAILED=1
  fi
fi

# --- Check 3: the Retirement Ledger does not invent versions -----------------
# The ledger records which release each retirement shipped in, and it is written
# BEFORE that release exists. One pending version is legitimate; two means an
# earlier pending entry was never reconciled when its release actually shipped.
if [[ -f "$LEDGER" ]]; then
  RELEASED_LIST="$(released_versions "$CHANGELOG")"
  LEDGER_VERSIONS="$(
    awk '/^#### Retirement Ledger/{f=1;next} f && /^#{1,3} /{f=0} f && /^\| *[0-9]+ *\|/' "$LEDGER" \
      | awk -F'|' '{gsub(/[ v]/,"",$3); print $3}' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -u || true
  )"

  PENDING=""
  while IFS= read -r lv; do
    [[ -n "$lv" ]] || continue
    printf '%s\n' "$RELEASED_LIST" | grep -qxF "$lv" || PENDING="$PENDING $lv"
  done <<< "$LEDGER_VERSIONS"
  PENDING="${PENDING# }"

  PENDING_N="$(printf '%s' "$PENDING" | wc -w | tr -d ' ')"

  if [[ "$PENDING_N" -gt 1 ]]; then
    emit_block "Retirement Ledger references more than one unreleased version: $PENDING" \
      "A ledger entry names the release its retirement shipped in. More than one unreleased version means an earlier entry was never reconciled when that release actually went out, so the ledger now misstates when a rule was retired." \
      "  Correct the stale 'Retired in' values in $LEDGER to the versions those retirements actually shipped in (see $CHANGELOG)."
    FAILED=1
  elif [[ "$PENDING_N" -eq 1 ]] && ! grep -q '^## \[Unreleased\]' "$CHANGELOG"; then
    emit_block "Retirement Ledger references unreleased version $PENDING, but $CHANGELOG has no [Unreleased] section" \
      "The ledger is pre-committing to a release that is not pending, so either the release shipped under a different number or the entry was never updated." \
      "  Set the 'Retired in' value in $LEDGER to the release it actually shipped in, or restore the [Unreleased] section in $CHANGELOG."
    FAILED=1
  fi
fi

if [[ "$FAILED" -ne 0 ]]; then
  exit 1
fi

if [[ "$DECLARED" -eq 0 ]]; then
  echo "PASS: version $VERSION -- no hardcoded version location to check (the README"
  echo "      badge is dynamic); $PREV_VERSION appears nowhere outside $CHANGELOG;"
  echo "      ledger versions all released."
else
  echo "PASS: version $VERSION agrees across $DECLARED declared location(s);"
  echo "      no stale prior version outside $CHANGELOG; ledger versions all released."
fi
exit 0
