---
name: rpi-status
description: Report project orientation and read-only Copilot RPI installation diagnostics.
---

# Report project status

## Project overlay

Open `.rpi/project/rpi-status.md` directly by that path (a file search or glob can skip the hidden `.rpi` directory). If it exists, read it completely before you start, together with the controlling instructions. It adds this project's procedure and checks and can make this workflow stricter. It cannot grant push, tag, merge, deployment or publication authority. It cannot relax a gate: a rule that blocks or permits a release, publication, merge, deployment or phase acceptance, or a safety or authorization rule. It can change other procedure detail only under a `## Declared overrides` heading that quotes the stock rule, gives the reason and names the owner decision. Name the overlay you read, and any declared override you applied, in the handoff.

## Project orientation

Inspect the current branch, latest commits and working tree with read-only Git
commands. Read AGENTS.md and the current handoff for open items. If existing CI is
relevant, inspect the exact branch and candidate SHA; distinguish unavailable,
missing, pending and completed results. Do not start a hosted run.

Resolve the actual Copilot RPI installation receipt, manifest and verified source.
Run the distribution engine's read-only `diagnose` operation:
`python3 "$engine_dir/rpi-distribution.py" diagnose --target "$project_dir"`.
The target holds only the ownership manifest and baselines under `.rpi/copilot/`,
not the engine. Set `engine_dir` to the rendered package's `.rpi/copilot/runtime/`
or to a verified blueprint checkout's `templates/scripts/`. If neither exists,
report that diagnostics are unavailable and identify the missing path. The
command prints JSON and exits 0; problems are data in the report.
Do not invent a cache or global installation. Report:

- Expected versus present project skill, custom-agent and instruction paths;
  duplicate names, unresolved resources, customized files and drift.
- The current AGENTS.md chain and managed-root size, with any client-specific
  instruction limits identified as configured or unverified.
- Selected Copilot CLI and VS Code Agent Host version/profile and actual native
  discovery observations, separate from filesystem inspection.
- Requested model versus observed session model when evidence exists. Omitted
  model metadata means interactive inheritance; it does not prove a model ran.
- Configured hooks, native trust and observed execution as separate facts.
  Missing telemetry is unobserved, never zero violations.
- Actual Git state, documented topology, verification prerequisites and exact
  candidate bound to any prior local or CI result.
- `project_overlays`: one item per `.rpi/project/*.md` file, never its text.
  `present` is healthy; when it carries a `reason`, report it (staleness not yet
  checked, or a malformed declared override and its `fix`). `stale` means the stock skill changed since the overlay was reviewed
  (review it, then use the printed `header_line`); `inert` means the installed
  copy lacks the overlay section (run `rpi-update`); `invalid` gives the reason
  and the `fix`. An empty list is normal.

Present a concise orientation and concrete limitations. Do not repair files,
change settings, enable schedules, read credentials or print private instruction
contents. Status never installs, activates or publishes anything.
