#!/usr/bin/env bash
# Preview or explicitly register report-only project agents with macOS launchd.
# Agent files need `# SCHEDULE: daily HH:MM` (or weekly DAY HH:MM) and
# `# RPI_AUTOMATION_MODE: report-only`. No inference or scheduler action occurs
# during the default preview.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR" | tr -cd '[:alnum:]-')"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
SYSTEM_LOGS_DIR="${HOME}/Library/Logs/${PROJECT_NAME}"
LABEL_PREFIX="com.${PROJECT_NAME}"
OWNER_MARKER='Managed by Copilot RPI installer'

# Print weekday, hour and minute. Return nonzero for invalid schedules.
parse_schedule() {
  local line="$1" kind day clock hour minute weekday
  read -r kind day clock <<< "${line#\# SCHEDULE: }"
  if [ "$kind" = daily ]; then
    clock="$day"
    weekday='-'
  elif [ "$kind" = weekly ]; then
    case "$day" in
      sunday|sun) weekday=0 ;; monday|mon) weekday=1 ;;
      tuesday|tue) weekday=2 ;; wednesday|wed) weekday=3 ;;
      thursday|thu) weekday=4 ;; friday|fri) weekday=5 ;;
      saturday|sat) weekday=6 ;; *) return 1 ;;
    esac
  else
    return 1
  fi
  [[ "$clock" =~ ^[0-9][0-9]:[0-9][0-9]$ ]] || return 1
  hour=$((10#${clock%:*}))
  minute=$((10#${clock#*:}))
  [ "$hour" -lt 24 ] && [ "$minute" -lt 60 ] || return 1
  printf '%s %s %s\n' "$weekday" "$hour" "$minute"
}

# Discover only explicitly marked report-only agents. Legacy or unmarked
# scripts are not silently installed under a new permission model.
discover_agents() {
  local script name schedule
  for script in "$SCRIPT_DIR"/*.sh; do
    [ -f "$script" ] || continue
    name="$(basename "$script" .sh)"
    [ "$name" = install-agents ] && continue
    grep -Fqx '# RPI_AUTOMATION_MODE: report-only' "$script" || continue
    schedule="$(grep -m1 '^# SCHEDULE:' "$script" || true)"
    [ -n "$schedule" ] || continue
    printf '%s|%s|%s\n' "$name" "$script" "$schedule"
  done
}

render_plist() {
  local name="$1" script="$2" weekday="$3" hour="$4" minute="$5" target="$6"
  python3 - "$LABEL_PREFIX.$name" "$script" "$SYSTEM_LOGS_DIR" "$weekday" "$hour" "$minute" "${COPILOT_MODEL}" "${COPILOT_BIN}" "${COPILOT_RPI_PATH:-}" "$target" <<'PY'
import os
import plistlib
import secrets
import sys
label, script, logs, weekday, hour, minute, model, binary, blueprint, target = sys.argv[1:]
interval = {'Hour': int(hour), 'Minute': int(minute)}
if weekday != '-':
    interval['Weekday'] = int(weekday)
env = {'HOME': os.environ['HOME'],
       'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
       'COPILOT_MODEL': model, 'COPILOT_BIN': binary}
if blueprint:
    env['COPILOT_RPI_PATH'] = blueprint
value = {'Label': label, 'ProgramArguments': ['/bin/bash', script],
         'StartCalendarInterval': interval,
         'StandardOutPath': f'{logs}/{label.rsplit(".", 1)[-1]}.log',
         'StandardErrorPath': f'{logs}/{label.rsplit(".", 1)[-1]}.error.log',
         'EnvironmentVariables': env}
output = plistlib.dumps(value).decode()
output = output.replace('<plist version="1.0">', '<!-- Managed by Copilot RPI installer -->\n<plist version="1.0">').encode()
name = os.path.basename(target)
if os.path.abspath(os.path.dirname(target)) != os.path.abspath(os.path.join(os.environ['HOME'], 'Library', 'LaunchAgents')):
    raise ValueError('plist target is outside the owned LaunchAgents directory')
home = os.open(os.environ['HOME'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
try:
    library = os.open('Library', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                      dir_fd=home)
finally:
    os.close(home)
try:
    directory = os.open('LaunchAgents', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=library)
finally:
    os.close(library)
temporary = f'.copilot-rpi-{secrets.token_hex(12)}.tmp'
try:
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(output)
        stream.flush()
        os.fsync(stream.fileno())
    # link fails if even a dangling target symlink appeared after preflight.
    os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory,
            follow_symlinks=False)
finally:
    try:
        os.unlink(temporary, dir_fd=directory)
    except FileNotFoundError:
        pass
    os.fsync(directory)
    os.close(directory)
PY
}

preview() {
  local name script schedule parsed weekday hour minute count=0
  echo "Preview only: $PROJECT_DIR"
  while IFS='|' read -r name script schedule; do
    parsed="$(parse_schedule "$schedule")" || {
      echo "BLOCKED: invalid schedule in $script" >&2
      return 2
    }
    read -r weekday hour minute <<< "$parsed"
    echo "$LABEL_PREFIX.$name: $schedule -> /bin/bash $script"
    count=$((count + 1))
  done < <(discover_agents)
  echo "$count report-only job(s). No plist was written or loaded."
  echo "Review the preview, then use --activate to register these jobs."
}

activate() {
  [ -n "${COPILOT_MODEL:-}" ] || {
    echo 'BLOCKED: set COPILOT_MODEL for scheduled runs' >&2
    return 2
  }
  # shellcheck source=templates/scripts/agents/lib/agent-utils.sh
  source "$SCRIPT_DIR/lib/agent-utils.sh"
  preflight_copilot || return 2
  COPILOT_BIN="$(command -v "$COPILOT_BIN")"
  command -v launchctl >/dev/null || {
    echo 'BLOCKED: launchctl is required for --activate' >&2
    return 2
  }
  local name script schedule target parsed weekday hour minute count=0
  # Validate the entire selection and ownership before any registration.
  while IFS='|' read -r name script schedule; do
    parse_schedule "$schedule" >/dev/null || {
      echo "BLOCKED: invalid schedule in $script" >&2
      return 2
    }
    target="$LAUNCH_AGENTS_DIR/$LABEL_PREFIX.$name.plist"
    if [ -L "$target" ] || { [ -e "$target" ] && ! grep -Fq "$OWNER_MARKER" "$target"; }; then
      echo "BLOCKED: unowned launchd registration at $target; preserve and review it" >&2
      return 2
    fi
  done < <(discover_agents)
  local parent
  for parent in "$HOME/Library" "$LAUNCH_AGENTS_DIR" "$HOME/Library/Logs" "$SYSTEM_LOGS_DIR"; do
    if [ -L "$parent" ]; then
      echo "BLOCKED: symlinked scheduler directory $parent; preserve and review it" >&2
      return 2
    fi
  done
  mkdir -p "$LAUNCH_AGENTS_DIR" "$SYSTEM_LOGS_DIR"
  for parent in "$HOME/Library" "$LAUNCH_AGENTS_DIR" "$HOME/Library/Logs" "$SYSTEM_LOGS_DIR"; do
    if [ -L "$parent" ]; then
      echo "BLOCKED: scheduler directory changed to symlink $parent" >&2
      return 2
    fi
  done
  while IFS='|' read -r name script schedule; do
    target="$LAUNCH_AGENTS_DIR/$LABEL_PREFIX.$name.plist"
    if [ -e "$target" ] || [ -L "$target" ]; then
      echo "PRESERVED: already registered $target; unload explicitly before replacing"
      continue
    fi
    parsed="$(parse_schedule "$schedule")"
    read -r weekday hour minute <<< "$parsed"
    render_plist "$name" "$script" "$weekday" "$hour" "$minute" "$target" || {
      echo "BLOCKED: could not create exclusive plist $target; inspect concurrent or unowned files" >&2
      return 2
    }
    if ! launchctl bootstrap "gui/$(id -u)" "$target"; then
      echo "FAILED: launchctl bootstrap $target; owned plist preserved for inspection" >&2
      return 1
    fi
    echo "ACTIVATED: $LABEL_PREFIX.$name"
    count=$((count + 1))
  done < <(discover_agents)
  echo "$count new job(s) activated. Authentication and model access are checked at run time."
}

unload() {
  local plist label count=0
  for plist in "$LAUNCH_AGENTS_DIR/$LABEL_PREFIX."*.plist; do
    [ -e "$plist" ] || [ -L "$plist" ] || continue
    if [ -L "$plist" ]; then
      echo "PRESERVED: symlinked $plist"
      continue
    fi
    if ! grep -Fq "$OWNER_MARKER" "$plist"; then
      echo "PRESERVED: unowned $plist"
      continue
    fi
    label="$(basename "$plist" .plist)"
    launchctl bootout "gui/$(id -u)/$label" || {
      echo "FAILED: bootout $label; plist preserved" >&2
      return 1
    }
    rm "$plist"
    echo "REMOVED: $label"
    count=$((count + 1))
  done
  echo "$count owned job(s) removed."
}

status() {
  local name script schedule target label
  while IFS='|' read -r name script schedule; do
    label="$LABEL_PREFIX.$name"
    target="$LAUNCH_AGENTS_DIR/$label.plist"
    if [ ! -e "$target" ] && [ ! -L "$target" ]; then
      echo "$label: NOT REGISTERED"
    elif [ -L "$target" ] || ! grep -Fq "$OWNER_MARKER" "$target"; then
      echo "$label: UNOWNED REGISTRATION (preserved)"
    elif command -v launchctl >/dev/null && launchctl list "$label" >/dev/null 2>&1; then
      echo "$label: LOADED"
    else
      echo "$label: REGISTERED, NOT LOADED"
    fi
  done < <(discover_agents)
}

case "${1:-}" in
  ''|--preview) preview ;;
  --activate) activate ;;
  --unload) unload ;;
  --status) status ;;
  --list) preview ;;
  --help|-h) echo 'Usage: install-agents.sh [--preview|--activate|--unload|--status|--list]' ;;
  *) echo "BLOCKED: unknown option $1" >&2; exit 2 ;;
esac
