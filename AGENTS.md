# copilot-rpi project instructions

Copilot RPI is a standalone blueprint for GitHub Copilot projects. `templates/`
contains the exported product. Canonical workflows are in
`templates/skills/rpi-*/SKILL.md`; `patterns/` holds 40 known agent error patterns
and 55 operational rules, each with permanent IDs. Read `patterns/quick-reference.md` and
`methodology/README.md` when orienting to the product. Preserve adopter and
project-specific guidance when updating a target.

## RPI work

Use the relevant `rpi-*` skill under `.github/skills/` when installed.
`rpi-research` describes existing behavior; `rpi-assess` evaluates alternatives;
`rpi-plan` specifies phases; `rpi-implement` executes approved phases; and
`rpi-validate` verifies them. Read the approved plan and current phase in full.
For behavioral changes, write a failing test first. Complete independent review,
repair, simplify and the full local gate before each phase acceptance. An explicit
all-phases request permits continuation only after each phase passes. Record the
candidate, findings, decisions, deviations and test evidence in a durable
handoff. Revalidate actual state when resuming.

## Git and verification

`main` is the long-lived integration branch. Implement on local task branches
and isolated worktrees, then integrate completed work locally into `main`.
Preserve unrelated files, including owner customizations and `.summon`.
Check the current branch before each commit and commit intended changes before
pulling. Keep working branches local. One integration owner combines changes.

Run `bash scripts/verify-local.sh` sequentially after each implementation phase.
It aggregates Python tests, catalog/version/surface contracts, ShellCheck,
Markdown lint, offline upstream provenance and internal links. Phase plans name
additional acceptance checks. Distinguish static/local results from observed
Copilot CLI or VS Code behavior. Keep raw receipts under ignored `.rpi/local/`.
Do not use default Markdown formatting rules in place of this repository's
configured lint. Documentation contains no emoji.

Inspect CI and deployment triggers before an authorized push. Verify every
expected workflow for the exact pushed commit. Diagnose a failed remote run
locally; another push or rerun needs its own authority. No Vercel Preview or
working-branch publication is part of local RPI work.

## Authority and ownership

Complete authorized local work autonomously. Pushing, tagging, releasing,
deploying, paid or cloud inference, remote database migration, issue mutation,
and destructive owner cleanup require explicit authority. Use authority already
given in the session without asking again. A skill invocation or installation
manifest does not grant those effects. Unknown ownership is a conflict: preserve
original bytes, show a reviewed plan and a runnable recovery action.

For blueprint intake, `upstream/cc-rpi.lock.json` pins reviewed cc-rpi source
and catalog dispositions. The default checker works offline; only explicit
maintainer intake reads a supplied upstream checkout. Do not hand-edit
generated native outputs or silently update sibling projects, global Copilot
configuration or schedulers. Active legacy prompts are migration inputs until
ownership-aware retirement proves which bytes may be removed.

## Project references

| Topic | Source |
| --- | --- |
| Workflow bodies | `templates/skills/` |
| Native profiles and rendering | `templates/distribution.json`, `templates/scripts/rpi-distribution.py` |
| Catalog and retirement | `patterns/`, `CONTRIBUTING.md` |
| Method | `methodology/README.md` |
| Local gate | `scripts/verify-local.sh` |
| Current approved plan | `docs/plans/2026-09-28-copilot-blueprint-modernization.md` |

Use `file:line` references for source claims. Keep project knowledge and local
extensions intact when rendering self-application.
