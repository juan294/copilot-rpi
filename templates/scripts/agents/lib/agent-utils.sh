#!/usr/bin/env bash
# Shared report context and non-inference Copilot CLI preflight for opt-in agents.
# Sourcing scripts set SCRIPT_DIR to their own directory first.
set -euo pipefail

PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck disable=SC2034 # Public variables consumed by sourcing agent scripts.
PROJECT_NAME="$(basename "${PROJECT_DIR}")"
# shellcheck disable=SC2034 # Public variable consumed by sourcing agent scripts.
LOGS_DIR="${PROJECT_DIR}/logs"
AGENTS_DIR="${PROJECT_DIR}/docs/agents"
SHARED_CONTEXT_FILE="${AGENTS_DIR}/shared-context.md"
COPILOT_BIN="${COPILOT_BIN:-copilot}"

log_info()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]  $*"; }
log_warn()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN]  $*" >&2; }
log_error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2; }

# Check executable and supported flags only. Authentication and model access are
# reported by the bounded run; preflight never spends inference or edits files.
preflight_copilot() {
  local binary help
  binary=$(command -v "$COPILOT_BIN") || {
    log_error "Copilot CLI missing; install it or set COPILOT_BIN"
    return 1
  }
  "$binary" --version >/dev/null || return 1
  help=$("$binary" --help) || return 1
  local flag
  for flag in --prompt --silent --no-ask-user --available-tools --allow-tool --model --no-remote; do
    if [[ "$help" != *"$flag"* ]]; then
      log_error "Copilot CLI missing $flag; update the CLI"
      return 1
    fi
  done
}

# ---------------------------------------------------------------------------
# Shared context — cross-agent intelligence
# ---------------------------------------------------------------------------

# read_shared_context [exclude_agent]
# Reads shared context file. Optionally excludes entries from a specific
# agent (useful to avoid reading your own stale entries).
read_shared_context() {
  local exclude="${1:-}"

  if [ ! -f "${SHARED_CONTEXT_FILE}" ]; then
    echo ""
    return
  fi

  if [ -z "${exclude}" ]; then
    cat "${SHARED_CONTEXT_FILE}"
  else
    # Remove entries from the excluded agent
    python3 -c "
import sys, re
content = open('${SHARED_CONTEXT_FILE}').read()
pattern = r'<!-- ENTRY:START agent=${exclude} .*?-->.*?<!-- ENTRY:END -->\n?'
cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
print(cleaned.strip())
" 2>/dev/null || cat "${SHARED_CONTEXT_FILE}"
  fi
}

# extract_and_write_shared_context <agent_key> <report_file>
# Extracts the SHARED_CONTEXT block from a report and appends it to
# shared-context.md. The report must contain a block delimited by:
#   SHARED_CONTEXT_START
#   ...content...
#   SHARED_CONTEXT_END
extract_and_write_shared_context() {
  local agent_key="$1"
  local report_file="$2"

  if [ ! -f "${report_file}" ]; then
    log_warn "Report file not found: ${report_file}"
    return
  fi

  local entry
  entry=$(python3 -c "
import re, sys
content = open('${report_file}').read()
match = re.search(r'SHARED_CONTEXT_START\n(.*?)SHARED_CONTEXT_END', content, re.DOTALL)
if match:
    print(match.group(1).strip())
else:
    sys.exit(1)
" 2>/dev/null) || true

  if [ -z "${entry}" ]; then
    log_warn "No shared context block found in ${report_file}"
    return
  fi

  local timestamp
  timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

  # Append new entry
  {
    echo ""
    echo "<!-- ENTRY:START agent=${agent_key} timestamp=${timestamp} -->"
    echo "${entry}"
    echo "<!-- ENTRY:END -->"
  } >> "${SHARED_CONTEXT_FILE}"

  # Prune old entries (keep last 3 per agent)
  prune_shared_context "${agent_key}"

  log_info "Shared context updated for ${agent_key}"
}

# prune_shared_context <agent_key>
# Keeps only the last 3 entries per agent type. Oldest are removed.
prune_shared_context() {
  local agent_key="$1"

  python3 -c "
import re

with open('${SHARED_CONTEXT_FILE}', 'r') as f:
    content = f.read()

pattern = r'(<!-- ENTRY:START agent=${agent_key} .*?-->.*?<!-- ENTRY:END -->)'
entries = re.findall(pattern, content, re.DOTALL)

if len(entries) <= 3:
    exit(0)

# Remove oldest entries (keep last 3)
for old_entry in entries[:-3]:
    content = content.replace(old_entry, '')

# Clean up extra blank lines
content = re.sub(r'\n{3,}', '\n\n', content)

with open('${SHARED_CONTEXT_FILE}', 'w') as f:
    f.write(content.strip() + '\n')
" 2>/dev/null || log_warn "Failed to prune shared context for ${agent_key}"
}
