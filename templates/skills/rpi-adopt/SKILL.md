---
name: rpi-adopt
description: "Audit and safely migrate an existing project to shared RPI workflows while preserving custom instructions, settings, resources and conventions."
---

# Adopt RPI into an Existing Project

Audit what exists, preserve what works, and migrate only the authorized scope.
The request may authorize a complete adoption; do not add repeated approval gates
for routine safe items already within that scope.

Read [the lifecycle contract](references/lifecycle-contract.md) completely.
Resolve the installed package/source and target project from actual metadata and
the request; do not assume the current directory is the intended target. Use
the engine commands in the lifecycle contract with explicit package and target
paths. Skill invocation or tool visibility does not grant extra authority.

## Audit before mutation

Read the current instruction chain, settings, skill/command/rule registrations,
legacy sync metadata, and any ownership manifest/baselines. Identify:

- Configuration: AGENTS.md, scoped Copilot instructions, native and legacy entry points,
  custom commands/skills/hooks, permissions, environment and local extensions.
- Infrastructure: stack, package manager, tests/coverage, lint/build, CI triggers,
  git topology, deployment targets, README and agent-facing surfaces.
- Workflow knowledge: curated research, plans, decisions, handoffs, reports,
  logging and any existing schedule. A missing optional feature is not a defect.

Use bounded independent read-only assignments when useful. Cover all relevant
areas and synthesize after assigned work completes. Read source intelligence,
manifest/templates and relevant domain rules from the resolved local package.
Do not infer ownership from a matching path, title or familiar section header.

## Migration plan

Save a concrete adoption plan in `docs/plans/YYYY-MM-DD-rpi-adoption.md` with:

1. Already aligned content to preserve.
2. Required gaps and optional choices, prioritized by impact.
3. Adaptation conflicts: custom instructions, merge/deployment semantics, rules,
   settings, hooks and legacy command names.
4. Harness/route/domain selection and native invocation names.
5. File/block/key ownership, recovery location, verification and completion gates.

Shared project facts live in AGENTS.md. Preserve custom Copilot instructions,
agent files, settings and existing API/migration/test guidance. Select universal
RPI/budget constraints plus applicable domain skills and scoped rules. Map paths
from the actual repository and preserve local extensions.

## Execute authorized adoption

1. Run `plan --package --target --profile --output` and review its source,
   target and selected components. Existing v1 metadata is evidence, not
   permission to overwrite unknown custom files. Missing baseline bytes produce
   retained/conflicted candidates.
2. Run `apply --plan` for the unchanged reviewed plan. Keep user settings and
   custom content, preserve recovery bytes, and stop only dependent work at a real
   conflict or new decision. Do not replace the entire AGENTS.md or instruction files.
3. Install full selected native skill directories and resources without duplicate
   user/project or plugin/direct registrations. Never merge or edit a plugin cache.
4. Migrate only proven managed legacy `.prompt.md` and `.chatmode.md` copies.
   Retire colliding names with recovery and a rename notice. Unknown custom
   aliases remain untouched and diagnosed. Do not claim native forwarding unless proven.
5. Migrate owned inline rule blocks only when their complete behavior survives in
   shared instructions or relevant scoped rules. Preserve custom policy.
6. Preserve curated research/plans/decisions/handoffs. Apply visibility policy to
   raw reports/logs; never stage entire ignored directories.
7. Adapt [the release playbook](references/e2e-pro-playbook.md): Wave A always;
   structural Waves C-H by actual risk with N/A reasons. Wave B exercises an
   existing authorized immutable candidate through `rpi-explore-release`.
8. Run `check --package --target` and complete applicable local gates. Verify actual
   native entries/resources, rule reachability, settings preservation and recovery.

## Completion

Save the adoption result and durable handoff: what existed, what migrated,
customizations preserved, conflicts, skipped optional features, component/route
selection, actual invocation names, verification and next actions. Update available
project/session memory with nonsecret facts. Commit reviewed local changes
atomically where appropriate; do not publish working branches or trigger remote
compute. An optional `rpi-pre-launch` audit is a later workflow unless authorized.
