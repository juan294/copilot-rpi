---
name: rpi-status
description: Report project orientation and read-only Copilot RPI installation diagnostics.
---

# Report project status

Inspect the current branch, latest commits and working tree with read-only Git
commands. Read AGENTS.md and the current handoff for open items. If existing CI is
relevant, inspect the exact branch and candidate SHA; distinguish unavailable,
missing, pending and completed results. Do not start a hosted run.

Resolve the actual Copilot RPI installation receipt, manifest and verified source.
Use the distribution engine's read-only `diagnose` operation when installed;
otherwise report that diagnostics are unavailable and identify the missing path.
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

Present a concise orientation and concrete limitations. Do not repair files,
change settings, enable schedules, read credentials or print private instruction
contents. Status never installs, activates or publishes anything.
