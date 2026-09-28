# Copilot RPI lifecycle contract

The explicit target repository and locally verified source determine the plan.
Invocation of a skill does not grant permission to mutate another project, a
user profile, a plugin cache or a remote service. Read the target's instruction
chain and its existing installation evidence before changing files.

## Source and ownership

Use the Copilot blueprint's declared manifest and local distribution engine. Keep project-selected components separate from the source inventory.
Legacy `.github/copilot-rpi-sync.json` and matching filenames are evidence to
inspect, not proof that a file is owned. Preserve unknown or edited content.
Copilot ownership lives in `.rpi/copilot/manifest.json`, with content-addressed
baselines in `.rpi/copilot/baselines/` and local journals in
`.rpi/local/copilot/`. Do not read or replace a coinstalled cc-rpi
`.rpi/manifest.json`. Plan per file, managed block and settings key against
recoverable baseline bytes.
An upstream-only change may update an unchanged owned item. A local-only edit
stays local; an overlapping edit is a conflict until explicitly resolved.

Do not write a global Copilot profile, start paid inference, create hosted jobs or
merge plugin caches as a side effect of install, update or detach. The four
lifecycle skills may be explicitly selected for a target; project setup does
not silently claim a shared user installation. Keep canonical skills and any
legacy compatibility prompt names from colliding in native discovery.

## Engine commands

Resolve `package_dir` and `project_dir` to verified absolute paths. Select
`cli`, `agent-host` or `vscode-local` for the actual client. The engine is
`$package_dir/.rpi/copilot/runtime/rpi-distribution.py` (Python 3.11+) and
its project route is:

```text
plan --package "$package_dir" --target "$project_dir" --profile cli --output "$plan_file"
apply --plan "$plan_file"
check --package "$package_dir" --target "$project_dir"
detach --package "$package_dir" --target "$project_dir" --output "$plan_file"
rollback --journal "$journal_file"
```

Review the generated plan before apply; an action name or skill invocation is
not authority for a new external effect. Run `check` after apply. If the engine
stops mid-transaction, use its exact journal path for rollback. Replan after
any source or target input changes.

## Transaction and recovery

Record reviewed source identity, target preconditions, selected components,
per-path dispositions and recovery location before apply. Reject a stale plan if
source, target or relevant bytes changed. Apply safe owned changes transactionally
and save nonsecret original bytes in the recovery journal. On interruption, show
journal state and a runnable resume or rollback path. Rollback must not overwrite
newer user edits. Replanning after conflict resolution must be possible without
manual deletion of unknown files.

## Copilot surfaces

Keep shared project facts in AGENTS.md. Preserve existing scoped API, migration,
test, deployment and Supabase instructions where applicable. Render native skills,
custom agents and instructions only for a qualified Copilot client profile; keep
legacy prompt/chatmode snapshots outside active discovery. Preserve JSONC comments,
unknown settings keys, permissions and local extensions. Never infer ownership
from a familiar heading, path or old sync timestamp alone.

## Verification and handoff

Check the complete installed resource graph, native discovery evidence when
available, unique names/scopes, instruction budgets, preserved custom bytes,
settings validity, idempotence and recovery. A static file check is not a claim
that VS Code or Copilot CLI loaded the surface. Report exact local candidate,
client/runtime versions, every conflict, incomplete check and required next
operation. Keep outward actions behind their own authorization.
