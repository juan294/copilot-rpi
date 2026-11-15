# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.2.0] - 2026-11-15

### Removed

- **`process-errors`.** The skill (`cli`, `agent-host`) and its prompt wrapper (`vscode-local`) are retired. They read error screenshots from `~/Desktop/agent-errors/` and added catalog entries. Current models make far fewer of these tool errors, and the intake had not been used for months. The error and rule catalogs in `patterns/` stay, with their permanent IDs. Copilot RPI's own legacy `.github/prompts/process-errors.prompt.md` is removed too.

### Changed

- When a package no longer contains a recorded component, `plan`, `detach` and `check` still stop. The FIX is now a runnable `plan` command (`detach` after a detach) that keeps your flags and adds one `--retired-component <id>` per named component. The lifecycle contract and [the v2 guide](docs/migrations/v2.md) describe the review.
- `--retired-component` now refuses, by name, a component that is not recorded or that the package still contains, and the FIX leaves that value out.
- `detach` with a package rendered for another profile now reports the profile difference instead of asking you to retire every component.

### Fixed

- A removal plan no longer reports an owned file that the owner already deleted as "modified owned content retained on removal" (since 2.0.0).

### Migration

- Updating from 2.0.0 or 2.1.0 stops once with `persisted ownership names components absent from this package: skill:process-errors` (`prompt:process-errors` for `vscode-local`). Replan with the printed command, which adds `--retired-component skill:process-errors` (or `prompt:process-errors`), then apply and run `check`. The plan removes the unchanged file and retains a copy you edited. An empty `.github/skills/process-errors/` directory can remain; Git does not track it, and you can delete it.

### Known issues

An independent review with exploratory runs of the 2.0.0 and 2.1.0 to 2.2.0 update, detach, check and rollback paths on synthetic targets found no S1 or S2 issue. Its findings in the new retirement messages are fixed above. These remain, accepted under the owner's rule that S3 and S4 findings do not block a release:

- S4 (since 2.0.0): on `vscode-local`, a plan also lists owned prompt wrappers under `legacy` as `retained-unproven`, so the retired `process-errors.prompt.md` appears both as a `remove` action and as a retained legacy item. The `remove` action is the one applied.
- The 2.1.0 known issues still apply.

## [2.1.0] - 2026-11-15

Sync with cc-rpi v2.2.0 (`cec458a`): project overlays, a read-only `diagnose` command and proportional release verification, adapted to Copilot.

### Added

- **Project overlays.** Each of the 16 workflow skills has a `## Project overlay` section that opens `.rpi/project/<skill>.md` by its exact path and reads it when it exists. A file search can skip the hidden `.rpi` directory, so this first sentence differs from cc-rpi. An overlay adds the project's procedure and checks and can make a workflow stricter. It cannot grant push, tag, merge, deployment or publication authority, and it cannot relax a gate. Other procedure changes go under `## Declared overrides`, with the quoted stock rule, the reason and the owner decision. The lifecycle skills (`rpi-adopt`, `rpi-bootstrap`, `rpi-detach`, `rpi-update`) have no overlay. See [project overlays](docs/project-overlay.md).
- **`diagnose`.** `rpi-lifecycle.py diagnose --target <dir>`, also through `rpi-distribution.py`, prints a JSON report of the installation and of each overlay (`present`, `stale`, `inert` or `invalid`, with a `fix` and, when known, the `header_line` to write). It is read-only, always exits 0 and never prints overlay text. `rpi-status` runs it.
- **Authored hash.** The render receipt records `authored_sha256`, the SHA-256 of the authored `templates/skills/<skill>/SKILL.md`, on each skill `SKILL.md` record and prompt wrapper record. The installation manifest copies it. An installation without it stays healthy until its next real update records it.
- **Reserved path.** No package destination can name `.rpi/project`, `.rpi/copilot` or `.rpi/local/copilot`, or anything below them, in any letter case. Plan, apply, check, rollback and detach leave `.rpi/project` byte-identical.
- **Resource-lifecycle instruction.** A new `resource-lifecycle.instructions.md` covers Docker, local stacks, database tests and task services: prove ownership before any stop or removal, finish disposable lifecycles within authorization, preserve shared and recovery data, and report retained resources. The supabase instruction and the root `AGENTS.md` template point to it, and `rpi-implement` and `rpi-remediate` follow it before removing a worktree.
- **Native overlay probe.** `tests/native/run_cli.py --profile overlay` runs the same `/rpi-research` prompt against a fixture without an overlay and then against one with `.rpi/project/rpi-research.md`. The receipt is `passed`, `failed` or `blocked`. Overlays passed this probe for the `cli` profile on Copilot CLI 1.0.88; `agent-host` and `vscode-local` were not probed. See [compatibility](docs/compatibility.md).

### Changed

- **Proportional release verification.** Wave A's truthful local gate runs for every release. Wave B exploratory charters and Waves C-H run only when the project's release profile selects them, with one Wave B round per candidate. Every finding has a severity from S1 to S4. Only an S1 or S2 finding, an unclassified finding or a skipped high-risk area blocks publication; an S3 or S4 finding can be an owner-approved accepted known issue, recorded with its severity and reason. This applies to `rpi-release`, `rpi-explore-release`, `rpi-remediate`, `rpi-pre-launch` and the bundled release playbooks.
- **Wave B selection.** `rpi-adopt` and `rpi-bootstrap` select Wave B in the release profile only for code that runs unattended or destructively on users' machines.
- **Stock rules.** `rpi-implement` commits the deviation notes with the phase and cites plans by file name. `rpi-triage` treats an old report as an agent failure, and an error-tracker, log or audit query that did not run sets the status to at least YELLOW. `rpi-validate` inspects the resource-lifecycle disposition of allocated services. `rpi-status` runs `diagnose` and reports `project_overlays`.
- **Package guidance.** The root `AGENTS.md` template says to verify a package's exact name and publisher against official documentation before installing it, and never to install a placeholder from an example.
- **Runtime wording.** `README.md` and `GUIDE.md` now say that an installed target holds the manifest and content-addressed baselines under `.rpi/copilot/`, and that the runtime stays in the rendered package.
- **Upstream intake** is pinned to cc-rpi v2.2.0 (`cec458a`), with a reviewed decision for every changed component in `docs/decisions/2026-11-15-cc-rpi-2.2-sync-intake.json`.

### Fixed

- `rpi-hook.py install --activate` failed after a real install with "The packaged hook runtime is missing", because the hook configuration runs `.rpi/copilot/runtime/rpi-hook.py` from the target and apply never installs runtime files (since 2.0.0). Activation now installs a recorded copy of the running hook runtime there, refreshes it from a newer package, and refuses symlinks and unrecorded or edited bytes. A new `--deactivate` removes the runtime copy, the record and a configuration that activation wrote, when their bytes are unchanged. Deactivate before lifecycle detach, which leaves these files in place; `rpi-detach` now says so.
- The opt-in pre-push gate had the same defect: its wrapper runs `.rpi/copilot/runtime/rpi-prepush.py`, which apply never installs (since 2.0.0). Activation now installs recorded copies of `rpi-prepush.py`, `rpi-candidate.py` and `rpi-verify.py`, and a new `--deactivate` restores the saved prior hook or removes the wrapper and the copies when their bytes are unchanged. Add `.rpi/copilot/` to `.gitignore`, because the gate requires a clean candidate; do not commit it, since its manifest and activation records hold absolute paths for one checkout.
- Scheduled jobs failed closed on Copilot CLI 1.0.112, which removed `--no-remote` (since 2.0.0). `rpi-automation.py`, the agent installer preflight and the native harness now pass `--no-remote --no-remote-export` when the client advertises them and `--sync-session=off` when it advertises only `--sync-session`, and block with the client version when it advertises neither.
- The pinned upstream reference archive refresh of 2026-11-14 removes invented package installation examples from the reference snapshots. That refresh changed no native Copilot destination.

### Known issues

One Wave B round (two fresh-context charters on candidate `59bc3ff`) found no S1 or S2 issue. These lower-severity findings are accepted for this release, under the owner's rule that S3 and S4 findings do not block a release, and are planned for a later release:

- S3 (since 2.0.0): if the scheduled runner is killed mid-run, the Copilot client keeps running without a time limit, and a rerun can start a second client beside it. Stop the orphaned `copilot` process by hand.
- S3 (since 2.0.0): a relative `--project` for `rpi-automation.py run` doubles the default report path. Pass an absolute path; `schedule-preview` already prints one.
- S3 (since 2.0.0): if another local process replaces the report directory with a symlink during a run, the report can land outside the project.
- S3: remote-flag detection treats a flag mentioned only in help prose or an example as supported. Current clients (1.0.88 and 1.0.112) are detected correctly.
- S3: an interrupted pre-push activation or deactivation can leave a backup that makes both `--activate` and `--deactivate` refuse; remove `pre-push.rpi-new` and the record by hand, or run `--activate` then `--deactivate` after an interrupted deactivation.
- S3: `diagnose` does not report an interrupted lifecycle transaction; run `check`, which names the `rollback --journal` command.
- S4: the installer preflight in `agent-utils.sh` checks fewer flags than the runner and has no help timeout; several FIX texts are advice rather than runnable commands; the concurrent-apply refusal shows a raw errno; a second `--deactivate` fails instead of reporting inactive; `rpi-prepush.py --help` prints nothing; activation replaces the runtime copy from any package with different bytes, not only a newer one; redaction does not catch encoded secrets; detach leaves baselines and empty `.github` directories (as in 2.0.0).

### Migration

- Render the 2.1.0 package for your profile, review the lifecycle plan, apply it and run `check`, as in [the v2 guide](docs/migrations/v2.md). Then run `diagnose` against the target.
- Put project additions to a workflow skill in `.rpi/project/<skill>.md`, not in the managed skill copy. Start the file with the `header_line` that `diagnose` prints. After a later update, a `stale` status means the stock skill changed: review the overlay and write the new header.

### Not taken in from cc-rpi v2.2.0

- The cc-rpi lifecycle-engine repair series (WB-L, WB2-L, WB2R3-L) and the configuration, distribution and package engine deltas: deferred. Copilot keeps its own implementations.
- The cc-rpi policy-hook, pre-push and `guard-bash` deltas: inapplicable. The Copilot hook and pre-push gate already have the cc-rpi 2.1 semantics.
- The cc-rpi diagnostics module: only the installation and overlay report is adapted. Harness, model, hook-trust and plugin-route diagnostics are Claude and Codex specific.
- The cc-rpi launcher and the Codex package and marketplace configurations: inapplicable. They have no Copilot installation target; Copilot has `rpi-automation.py` for scheduled jobs.
- The cc-rpi domain skills and rules: deferred, pending applicability review.

### Retirement review

- No rule or error ID was retired in this release.

## [2.0.0] - 2026-09-29

Breaking layout migration to native Copilot skills and ownership-aware
installation.

### Added

- Pinned cc-rpi source intake with an offline component and catalog
  disposition check. Canonical RPI skills retain bundled workflow resources.
- Copilot CLI, VS Code Agent Host and optional VS Code Local render profiles;
  repository skills, specialist agents, scoped instructions and Local prompt
  wrappers are selected by profile.
- Standalone ownership-aware plan, apply, check, rollback and detach commands.
  An installation manifest and recovery journal preserve adopter changes.
- Candidate-bound local verification receipts, findings disposition checks,
  opt-in pre-tool and Git pre-push adapters, and bounded Copilot scheduled-job
  runner. Native hook and scheduled inference activation remain separate.
- Compatibility, migration, native policy and upstream intake guides.

### Changed

- Canonical workflows move from prompt files to `.github/skills/` for the CLI
  and Agent Host profiles. The Local profile retains thin prompt wrappers.
  Existing prompt and chatmode files are migrated only when their ownership is
  proven by the lifecycle plan.
- Interactive workflows inherit the session model and effort. Scheduled jobs
  require a selected model and do not start during installation.
- Local release verification runs a sequential portable gate and records the
  tested candidate. Native CLI and VS Code results are separate evidence.

### Fixed

- A failed scheduled-report publication preserves the prior current report and
  last-good copy, including when the second write runs out of space.

### Migration

- Render a package for one selected profile, review a lifecycle plan, apply it,
  and run `check`. Follow [the v2 guide](docs/migrations/v2.md) for conflicts,
  legacy ownership and rollback. Historical v1 no-hooks statements below
  describe those releases; optional v2 hooks need native qualification.

## [1.18.0] - 2026-07-29

Catch-up sync porting the generic, Copilot-applicable parts of cc-rpi v1.25.0
through v1.28.2. The contract-layer **hooks** and their telemetry remain
un-ported for the same reason as v1.17.0 -- GitHub Copilot has no
PreToolUse/PostToolUse mechanism -- but this release closes that gap a different
way: the mechanically-checkable rules now run in CI instead.

### Added

- **Error #40 + Rule #55 -- "a finding's recommendation is a hypothesis."**
  A remediation agent implements an audit finding's proposed fix literally and
  breaks a correctness/UX invariant the fix never verified. Real case: a
  Performance finding traded server-side locale resolution for ISR on the
  highest-traffic route, breaking i18n for every cookie-based (returning) user
  -- the symptom test ("ISR restored") passed; no test guarded "an English user
  sees an English body." Error count: 39 -> 40. Rule count: 54 -> 55.
- **Three repo-invariant scripts, all CI-enforced**, each emitting BLOCKED/WHY/FIX
  with a runnable fix:
  - `verify-counts.sh` -- stated error/rule counts match the catalogs, no
    duplicate rule numbers, and no gap in the numbering that the Retirement
    Ledger does not explain.
  - `verify-version.sh` -- CHANGELOG is the source of truth; the previous
    version must survive nowhere outside it. This repo's README badge is
    *dynamic* (shields.io reads the releases API), so check 1 adapts rather than
    demanding a hardcoded location -- and stays ready for projects that have one.
  - `verify-prompts.sh` -- **the Copilot-native analogue of cc-rpi's hook layer.**
    Copilot cannot enforce at edit time, so CI is the enforcement point: prompt
    frontmatter (Rule #20), no `$ARGUMENTS` (Rule #21), `applyTo` on instruction
    files (Rule #22), chatmode placement (Error #16), template-vs-self-applied
    drift, and no emoji (Rule #54). Four rules that were advisory prose are now
    a hard gate.
- **New `Validate` workflow** running all three scripts plus shellcheck over
  every shipped script.
- **E2E Pro release-verification playbook** (`templates/e2e-pro-playbook-template.md`)
  -- a copy-and-adapt blueprint that turns release verification into auditable
  evidence: it proves every *required* check actually ran and passed against the
  exact artifact being tagged. 20-decision ledger, 8-wave implementation plan,
  capability registry, constrained-combination engine, per-release plan compiler,
  multi-layer evidence model. Its mandatory floor is **Wave A** (a release gate
  that cannot lie: zero-pass fails, required skip/fail blocks even when
  quarantined, candidate identity is fixed, tag is last); Waves C-H are adopted
  by project risk. Sits alongside `/release`, `/pre-launch` + `/remediate`, and
  `methodology/testing.md` -- it does not replace them.
- **`/explore-release` prompt** -- Wave B of E2E Pro: diff-driven, fresh-context
  exploratory charters with a mandatory eight-maneuver table, a synthetic-fixture
  safety contract, and a block-on-failure gate. Feeds evidence to `/release`;
  never tags.
- **Retirement path for the rule corpus** (`CONTRIBUTING.md`): four admissible
  grounds (superseded / tool-enforced / model-native / merged), a procedure that
  blocks while inbound references remain, and a Retirement Ledger. `/release`
  now asks what came OUT each cycle, not just what went in. The corpus had an
  intake path and no exit path.
- **Deviation log** -- `/implement` records departures taken inside its own
  authority as plan said / found / chose / why, and `/validate` reads it instead
  of reconstructing intent from the diff.
- Methodology: **"Interface Design Over Worked Examples"** (`agent-design.md`) --
  design parameters, enums, and `applyTo` globs so correct use is implied; reach
  for an example only when it encodes an environment fact the interface cannot
  carry. **"A Spec Doesn't Have to Be Prose"** (`context-engineering.md`) -- a
  failing test, a module to port semantics from, a mockup, a schema, or a rubric
  all beat prose; point at what can be executed or diffed.
- Implement-phase guard against Error #40 in `methodology/four-phases.md`.

### Changed

- **`/pre-launch`** gains a **Second-order rule** (a finding is a hypothesis, not
  a work order; when a non-functional goal conflicts with a correctness,
  security, or UX invariant, default to the invariant and flag the trade) and a
  new **required `Regression risk` field** on every finding. A blanket "none" on
  a behavior-changing finding is a contract failure.
- **`/remediate`** gains a **verify-the-recommendation gate**: worktree agents
  independently confirm a finding's assumptions in real code and write the guard
  test against the invariant (not the symptom) before implementing. A
  recommendation that fails verification or trades away an invariant **halts**
  and escalates to a human rather than being implemented literally. Adds a
  "Halted" report line.
- **`/release`** hardened against missed version strings: Step 1 now mandates a
  `git grep` of the current version instead of relying on memory, and names the
  recurring blind spots (shields.io badges carry the version up to 3x on one
  line); Step 2 re-greps the OLD version after the bump. Also adds the
  retirement review.
- **`/plan`** prefers pointing at an executable or checkable artifact over
  describing behavior in prose.
- **`/validate`** offers -- does not force -- a short explainer of what changed
  and why for whoever reviews the merge.
- `/bootstrap`, `/adopt`, `/update`, `/detach`, `templates/setup-checklist.md`,
  `GUIDE.md`, and `README.md` all wired for E2E Pro and `/explore-release`.
- The pre-release sequence is now
  `/pre-launch -> /remediate -> /update-docs -> /explore-release -> /release`.

### Fixed

- **`.github/prompts/remediate.prompt.md` had drifted several releases behind
  its template** -- the copy this repo actually runs on itself was missing the
  parser contract, the wave selector, and the grouping hierarchy. Found by the
  new `verify-prompts.sh`, which now prevents it recurring.
- **`GUIDE.md` claimed "45 rules" against a corpus of 54.** Caught by
  `verify-counts.sh` on its first run; that class of drift is now mechanically
  impossible.
- **`/detach` orphaned eight project-level prompts** it never listed
  (`brainstorm`, `debug`, `remediate`, `release`, `update-docs`, `triage`, and
  now `explore-release`), leaving them behind after a detach. `/update`'s Phase 3
  had the same partial list.
- **The deviation log would have been deleted before `/validate` could read it**
  -- `docs/plans/` was gitignored wholesale. Now `docs/plans/*` plus
  `!docs/plans/*-notes.md`. The `/*` matters: git cannot re-include a path whose
  parent **directory** is excluded, so the obvious form silently does nothing.
- **Privacy:** Error #21 illustrated itself with the maintainer's real home
  directory layout, and `morning-triage.sh` named an internal orchestrator.
  Both genericized, keeping the instructive shape -- Error #21 still contrasts a
  real parent directory against a plausible invented one, because inventing a
  believable parent is the specific failure it documents.
- `PROJECT_NAME` in `agent-utils.sh` is annotated as part of the library's public
  surface, so shellcheck can gate the scripts without a false positive.

## [1.17.0] - 2026-06-25

Catch-up sync porting cc-rpi v1.18-v1.24 learnings (the contract-layer **hooks**
and metrics from cc-rpi v1.22-v1.23 are intentionally NOT ported -- GitHub Copilot
has no PreToolUse/PostToolUse hook mechanism, so they could only land as inert
documentation).

### Added

- **7 new operational rules (#48-#54), rule count 47 -> 54.**
  - #48 **Watchdog + terminal condition** -- every spawned `copilot -p` agent gets
    a single-sentence task, an explicit stop condition, and a ~15-20 min wall-clock
    budget; kill overruns rather than assuming progress.
  - #49 **Dedup against repo state** -- check `git log`/`git status`/`grep` before
    doing or continuing work so a sibling's committed work is not duplicated.
  - #50 **Verify an API supports a call before chaining on it** -- confirm the
    method/type exists and run the targeted test BEFORE committing the first attempt.
  - #51 **Format markdown tables programmatically** -- `markdownlint --fix` /
    `prettier --write`, never hand-aligned column padding.
  - #52 **No CodeQL workflow without GHAS** -- a code-scanning workflow fails CI on
    every push unless GitHub Advanced Security is enabled; confirm first.
  - #53 **Standardize GitHub repo settings** -- squash-only merges, auto-merge,
    delete-branch-on-merge, Dependabot alerts, protected Production environment.
  - #54 **No emojis in documentation** -- text equivalents (PASS, `[x]`, `->`).
- **Methodology: "Scope Discipline and the Watchdog"** (`agent-design.md`) --
  orchestrator obligations table plus wrong/right spawn and dedup examples, drawn
  from a real 2h+ runaway agent incident.
- **Methodology: "Code Scanning Requires GHAS"** (`ci-and-guardrails.md`) --
  `gh api` probe, public-free vs private-paid distinction.
- **Methodology: "Checkpoint and Resume"** (`scheduled-agents.md`) -- bash
  step-marker pattern (`done_step`/`mark_step`) so headless `copilot -p` agents
  survive mid-flight auth/5xx/529 errors without restarting from scratch.
- **Git Workflow: "Cleanup After Merge"** (`AGENTS.md` template +
  copilot-instructions) -- complete post-merge recipe: worktree remove -> local
  branch delete -> `git fetch --prune` -> verify nothing dangling.
- **`/brainstorm` prompt** (ported from cc-rpi v1.21) -- Socratic, one-question-at-a-time
  intake that produces a design brief for `/plan`. Optional RPI pre-step.
- **`/debug` prompt** (systematic-debugging, ported from cc-rpi v1.21) -- disciplined
  root-cause loop for novel bugs (Copilot has no auto-consulted skills, so this is an
  invocable prompt).
- **`/triage` covers GitHub Security & Quality Alerts and `leanness-report.md`**
  (ported from cc-rpi v1.22). Every triage run now queries code scanning/CodeQL,
  Dependabot security, and secret scanning alerts (a failed query is itself a
  finding), and extracts each leanness recommendation as its own action item.
- **`/release` adds the develop-based flow** (ported from cc-rpi v1.20) -- detects a
  permanent `develop` integration branch and releases via a direct `develop` -> `main`
  PR, never passing `--delete-branch` on the permanent branch.

### Fixed

- `/triage` "fix everything" rule reference corrected from Rule #31 to Rule #37.

## [1.16.0] - 2026-06-12

### Added

- **Model tier system (3 tiers) bound to every workflow.** Added a
  `haiku` floor tier alongside the existing `opus`/`sonnet` tiers and
  gave every prompt an explicit `Model tier` line. `/status` and
  `/describe-pr` run on the floor; `/research`, `/plan`, `/pre-launch`
  stay frontier; the rest run mid-tier. The blueprint pins the tier; the
  org binds the tier to a concrete model on adoption.
- **`methodology/cost-monitoring.md`.** New doc on model economics: the
  four cost pools, model tiers as the primary lever, access tiers
  (frontier access for authoring loops, the floor for consumption), and
  measuring cost-per-outcome. Added to the methodology reading order.
- **Cost-report scheduled agent.** Weekly agent (runs on the floor tier)
  that turns provider usage exports into cost-per-outcome numbers and
  flags workflows drifting above their declared tier.
- **Rule #46 (Pin a model tier to every workflow)** and **Rule #47
  (Measure cost per outcome before betting beyond the floor)** in the
  quick-reference, under a new "Cost & Models" section.

### Changed

- **`context-engineering.md` model-selection section rewritten.** Replaced
  the "leave the `model` field empty" guidance — which contradicted the
  per-prompt tier lines — with the 3-tier system, a tier→concrete-model
  binding table, subagent tier-inheritance, and an
  override-upward-never-silently-downward rule.

## [1.15.0] - 2026-05-04

### Added

- **Rule #45: Triage processes Dependabot PRs.** `/triage` now scans
  open Dependabot PRs (`gh pr list --author "app/dependabot"`) as part
  of Step 1 Discovery and processes them in a new Step 5 (after the
  triage commit is pushed). Patch and minor updates with green CI
  auto-merge via `gh pr merge --squash --auto --delete-branch`. Major
  bumps defer for human review. CI red with an obvious fix (snapshot
  drift, lockfile, generated files) gets one fix attempt before
  deferring. Conflicts are rebased via `gh pr update-branch` and
  re-evaluated. Dependabot processing happens last so a flaky dependency
  PR can't block triage code fixes. Updated:
  `patterns/quick-reference.md`, `methodology/scheduled-agents.md`
  Morning Triage section, `.github/prompts/triage.prompt.md` and
  `templates/prompts/triage.prompt.md`, and `GUIDE.md`.

### Changed

- **Rule #42 is now conditional on repo visibility.** Previously, agent
  operational directories (`docs/agents/`, `logs/`, `scripts/agents/`)
  were gitignored across all projects. They are now gitignored only on
  public repos so operational details (security findings, internal
  metrics, agent status) don't leak. On private repos these directories
  are tracked, and `/triage` commits reports alongside code fixes as a
  historical audit trail. Visibility is detected via
  `gh repo view --json visibility`; missing remote or `gh` unavailable
  fail-safes to PUBLIC behavior. Ports cc-rpi v1.18.0 changes to
  copilot-rpi. Updated:
  `patterns/quick-reference.md` (Rule #42),
  `methodology/scheduled-agents.md` (Report Lifecycle, gitignore
  section, Morning Triage, Prerequisites),
  `templates/setup-checklist.md`,
  `.github/prompts/triage.prompt.md` and template counterpart,
  `templates/prompts/pre-launch.prompt.md`, and `GUIDE.md`.

## [1.14.0] - 2026-04-18

### Changed

- **`/pre-launch` prompt** -- upgraded from 6-domain audit to 8-specialist
  deep-dive. Adds Principal Architect, Staff FE, Staff BE, Performance
  Engineer, DevOps/SRE Lead, Security Reviewer, QA/Reliability Lead, and
  Product Designer/UX Lead as named specialist domains. Model tier raised to
  opus. Introduces structured finding IDs (`<DOMAIN>-(B|H|M|L|S)<COUNTER>`,
  e.g. `SE-B1`, `UX-M3`), Domain Model preamble per specialist, and
  16-section report format (sections 4-11 per domain, sections 12-16 for
  synthesis). Wave-ordering index in Section 14 drives `/remediate` grouping.
  Rule #44 enforced: only QA/Reliability Lead runs the full test suite.
- **`/remediate` prompt** -- complete restructure to 3-wave model driven by
  the pre-launch report's Section 14. Wave 1 (Before launch): launch-blockers
  and high severity, must pass before release. Wave 2 (After launch): medium
  severity, post-release sprint. Wave 3 (Later/strategic): low and strategic
  items get GitHub issues only -- no worktree fix agents spawn. Adds finding
  ID parser contract (regex: `(AR|FE|BE|PE|DO|SE|QA|UX)-(B|H|M|L|S)[0-9]+`),
  per-wave integration and cleanup steps, wave-resume via `wave=N` input,
  and updated report structure with per-wave tables.
- **`/adopt` prompt** -- Phase 2 audit now uses 3 parallel Explore agents
  (Configuration Audit, Infrastructure Audit, Workflow Audit) instead of a
  single sequential investigation. Recommended next step updated to mention
  all 8 specialist domains by name.
- **`/implement` prompt** -- batch-eligible phase detection moved to an
  explicit step (step 4) before sequential execution begins. Old inline note
  removed.
- **`/fix-ci` prompt** -- failing tests now spawn a dedicated sub-agent per
  test (step 4), matching cc-rpi behavior.
- **`/research` prompt** -- added greenfield note: skip for projects with no
  code yet, start directly with `/plan`.
- **`methodology/agent-design.md`** -- Pre-Launch Audit Pattern table updated
  from 6 to 8 specialists with domain codes and Rule #44 enforcement note.
  Adds 3-wave remediation summary.

## [1.13.1] - 2026-04-04

### Added

- **Error #39:** Parallel agents each run full test suite, exhausting local
  resources. N agents x full suite = N x workers processes competing for CPU
  and memory. Agents must run scoped tests only; full suite runs once at
  integration. Ported from cc-rpi Error #63.
- **Rule #44:** Parallel agents run scoped tests only -- full suite runs once
  at integration.

## [1.13.0] - 2026-03-28

### Added

- **Instruction templates: `deployment-safety.instructions.md` and `supabase.instructions.md`** -- new path-specific rule templates that auto-load via `applyTo` globs when deployment configs or Supabase/SQL files are in context. Projects install them selectively based on stack.
- **Authoring Principles** section in setup checklist -- guidance on keeping AGENTS.md lean (~90 lines), using `.github/instructions/` for domain rules, and budget awareness (~150 usable instruction slots).
- **Instruction sync phase** in `/update` prompt (Phase 4) -- compares blueprint instruction templates against project's `.github/instructions/`, preserves custom `applyTo` globs, adds new instructions, never deletes project-specific files. Sync metadata now tracks `instructionsSynced` and `instructionsCustom`.

### Changed

- **AGENTS.md template** -- reduced from ~225 to ~90 lines (60% reduction). Deployment Safety, Supabase Migration Rules, Supabase Migration Safety, TDD Protocol, and Working Patterns (4 `<examples>` blocks) extracted to `.github/instructions/` templates. Agent Autonomy + Memory Management merged into Agent Behavior. Push Accountability condensed to 2 lines within Agent Behavior.
- **`/bootstrap` prompt** -- removed mandatory reading of `patterns/agent-errors.md` during onboarding. Phase 3 now includes step 6 for installing `.github/instructions/` templates (tests always; deployment-safety, supabase, api, migrations conditionally). Rules section updated: "Domain rules go in `.github/instructions/`, not AGENTS.md."
- **`/adopt` prompt** -- removed mandatory `agent-errors.md` reading. Phase 2 audit now checks `.github/instructions/` coverage and whether AGENTS.md contains domain rules that should be in instructions. Phase 4 includes instruction installation and inline rule migration. Added `applyTo` adaptation guidance.
- **`/update` prompt** -- removed mandatory `agent-errors.md` reading. New Phase 4 (Update Instructions) syncs blueprint instruction templates. Phase 5 (Update AGENTS.md) blueprint-managed sections reduced to 3 (RPI Workflow, Agent Behavior, Project File Locations). Migration guidance for older sections (Working Patterns, TDD Protocol, Push Accountability, Deployment Safety, Supabase) moved to `.github/instructions/`.
- **Setup checklist** -- added Authoring Principles subsection under AGENTS.md Configuration. Path-Specific Instructions section expanded with deployment-safety and supabase templates. Updated instruction count references.
- **`tests.instructions.md` template** -- added Verification Sequencing section (run checks sequentially, never parallel).
- **AGENTS.md** (this repo) -- applied same reduction: extracted Contributing rules to dedicated section, updated structure diagram to show 5 instruction templates, updated error/rule counts.
- **GUIDE.md** -- Error Prevention section rewritten as "Three-Layer Progressive Disclosure" (AGENTS.md, `.github/instructions/`, reference catalogs). Path-Specific Instructions section expanded with deployment-safety and supabase examples. Project structure diagram updated with instruction file details and `applyTo` annotations. Where to Go Deeper table: added instruction templates row.
- **README.md** -- fixed stale error count (26 to 38). Updated templates description to include deployment safety and Supabase instructions.
- **`copilot-instructions.md` template** -- added Path-Specific Instructions section documenting auto-loaded domain rules.
- **`patterns/agent-errors.md`** -- preamble updated: file is now a debugging reference, not required for onboarding. Points to `quick-reference.md` for everyday use.

## [1.12.0] - 2026-03-26

### Added

- **Rules #42-43: Local-only agent reports and timestamp-based triage discovery** -- `docs/agents/`, `logs/`, and `scripts/agents/` are gitignored in all projects. Triage uses `.last-triage` marker file instead of git status for report discovery.
- **`templates/scripts/agents/lib/agent-utils.sh`** -- shared utility library for all agent scripts. Handles environment setup, fd limits, auth preflight, logging, and shared context read/write/prune.
- **`templates/scripts/agents/install-agents.sh`** -- automated launchd installer. Auto-discovers agent scripts via `# SCHEDULE:` comments, generates plists with all four launchd gotcha fixes.
- **Report Lifecycle** section in `methodology/scheduled-agents.md` -- codifies the separation between operational reports (local-only) and code fixes (committed).

### Changed

- **AGENTS.md template** -- context pressure optimization: "Agent Operational Rules" section (31 lines of rule lists) replaced with "Working Patterns" section (4 canonical examples in `<examples>` tags). "Push Accountability", "Agent Autonomy", and "Memory Management" sections slimmed. Project file locations updated to note gitignored agent output.
- **`patterns/quick-reference.md`** -- restructured with scope/stack tags on every rule. Sections reorganized by domain. Wording tightened per Anthropic Claude 4.6 guidance. Rule count: 41 to 43.
- **`/triage` prompt** -- Step 1 rewritten: three-layer git-based scan replaced with timestamp-based discovery. Step 4 rewritten: two-commit strategy replaced with single commit (fixes only) plus `.last-triage` marker touch.
- **Agent shell script template** in `methodology/scheduled-agents.md` -- now sources `lib/agent-utils.sh`. Uses `SHARED_CONTEXT_START/END` blocks and `# SCHEDULE:` comments. Automated launchd installation via `install-agents.sh` is now recommended.
- **Setup checklist** -- scheduled agents section updated with gitignore, `agent-utils.sh`, `install-agents.sh`, and `# SCHEDULE:` steps.

## [1.11.0] - 2026-03-25

### Added

- **Error #38: Agent pushes Supabase migration to remote without local testing** -- agent writes migration SQL and runs `supabase db push` directly without testing against the local Postgres instance. Migrations fail on remote, leaving the database in a partially migrated state. Solution: always run `supabase start` + `supabase db reset` locally, verify with `docker exec`, then push. Ported from cc-rpi Error #62.
- **Rule #41: Always test Supabase migrations locally before pushing to remote** -- use the full local Supabase stack as UAT before pushing any migration. New "Supabase Rules" section in quick-reference.md.
- **Supabase migration safety** section in AGENTS.md template -- step-by-step local testing workflow with `supabase start`, `supabase db reset`, `docker exec` verification, and `supabase db push`.

## [1.10.1] - 2026-03-25

### Added

- **Error #37: Silent fallback masks production data failure** -- agent writes "resilient" code with graceful degradation (fallback data, default responses) but no observability. Fallback activates silently in production, serving placeholder content while hiding the real bug. Solution: every fallback path needs ERROR-level logging, health endpoint degraded state, and alerting. Ported from cc-rpi Error #61.
- **Rule #40: Every fallback path must be observable** -- when writing fallback behavior, always add error logging, health check coverage, and monitoring hooks. New "Observability Rules" section in quick-reference.md.
- **Supabase migration rules** in AGENTS.md template -- every migration creating a public table must include `GRANT SELECT TO anon, authenticated`; `ALTER DEFAULT PRIVILEGES` belongs in the initial setup migration; fallback paths must log at ERROR level; health endpoints must check actual data access.

## [1.10.0] - 2026-03-25

### Fixed

- Markdownlint MD029 -- use 1. prefix for ordered list in quick-reference

### Added

- **Deployment Safety & Resource Efficiency** -- new patterns file (`patterns/deployment-safety.md`) codifying lessons from a real production incident where an agent merged 7 Dependabot PRs to `main`, triggered 80+ CI runs and 21 production deployments, and took down a live site for 2+ hours. Includes deployment topology awareness, dependency risk assessment, production recovery protocol, and resource efficiency patterns. Platform-generic (covers AWS, Vercel, Netlify, Railway, etc.).
- **Error #30: `git checkout --` fails on unmerged (conflicted) files** -- agent tries to discard changes during a merge/rebase/cherry-pick conflict; files are "unmerged" so plain checkout fails. Solution: use `--ours`/`--theirs` to pick a side, or abort the operation. Ported from cc-rpi Error #54.
- **Error #31: `git merge` blocked by untracked working tree files** -- untracked files at the same paths as files in the branch being merged cause git to abort. Common in multi-agent workflows. Solution: delete or move untracked copies before merging. Ported from cc-rpi Error #55.
- **Error #32: Agent merges to `main` without understanding deployment topology** -- agent treats "clean up PRs" as "merge them" without checking that merging to `main` triggers production deployments. Solution: cherry-pick to `develop`, close the Dependabot PR.
- **Error #33: Sequential merge cascade wastes CI resources** -- merging N PRs one-by-one with "require up-to-date" branch protection creates O(n^2) rebase cascades. Solution: batch all updates into a single PR.
- **Error #34: Agent deploys untested code to production** -- CI passing is not sufficient for framework upgrades. Build != Runtime. Local != Production. Solution: deploy to staging/preview and verify before merging to `main`.
- **Error #35: Agent improvises production recovery with repeated failed deployments** -- agent panic-deploys during an outage, each failed attempt extending downtime and costing money. Solution: roll back immediately, investigate on non-production, fix forward on `develop`.
- **Error #36: Agent treats all dependency updates as equal risk** -- applying uniform verification to framework upgrades and dev patches alike. Solution: classify dependencies by risk level before merging.
- **Rules #32-#33** -- git conflict resolution quick-reference rules.
- **Rules #34-#39** -- deployment and resource efficiency rules covering: main=production, batch dependencies, cost awareness, staging verification, recovery protocol, and action justification. New "Deployment & Resource Efficiency Rules" section in quick-reference.md.
- **Updated AGENTS.md template** -- added deployment safety section for projects with CI/CD deployment pipelines.

## [1.9.0] - 2026-03-16

### Added

- **`/remediate` prompt** -- post-pre-launch remediation automation. Parses the pre-launch audit report, creates GitHub issues for every finding (100% coverage regardless of priority), spawns parallel worktree agents that follow TDD (write failing test, implement fix, verify, `/quality-review`), merges PRs sequentially with test verification after each merge, runs a final `/quality-review` on the integrated result, monitors CI, cleans up all worktrees and branches, and generates a remediation report. Completes the release cycle: `/pre-launch` -> `/remediate` -> `/update-docs` -> `/release`.
- **`/triage` prompt** -- morning agent report processing. Three-layer exhaustive discovery (git status + file listing + cross-reference) to find every report -- never misses one. Checks `logs/` for agent failures before analyzing reports. Reads all reports completely, synthesizes findings, drafts action plan for ALL items (fix everything, Rule #31), implements fixes, commits reports as historical artifacts separately from code fixes, updates shared-context.md, pushes, and monitors CI.
- **`morning-triage.sh` script template** -- multi-project orchestration. Configurable list of project directories, runs `/triage` in each sequentially, produces a cross-project summary. Archy-compatible for higher-level orchestration.
- **Rule #31: Fix everything, always** -- new core tenet and operational rule. Categorize findings by severity, but fix 100% of them. With AI agents, the cost of fixing is near-zero -- the old prioritization model of deferring low-priority items no longer applies. Added to `methodology/philosophy.md` (core tenet #9, key lesson #17) and `patterns/quick-reference.md` (Rule #31).

## [1.8.0] - 2026-03-14

### Added

- **`/release` prompt** -- project-type-flexible release automation. Detects project type (npm, Rust, Python, Go, docs-only) and branching strategy (main-only vs feature-branch). Bumps versions in all manifest files and references, generates CHANGELOG entry from categorized commits, creates release commit and annotated tag, publishes GitHub release, and advises on registry publish (advisory only). Includes error guards (#20, #29) and 3 human confirmation gates.
- **`/update-docs` prompt** -- comprehensive documentation refresh. Investigates 4 areas (change analysis, documentation inventory, diagram analysis, version reference scan) to build an update plan from changes since the last release. After user approval, sequentially updates all markdown files, Mermaid diagrams, version badges/references, counts, and inline code docs (JSDoc, Python docstrings, Rust doc comments). Flags uncertain diagrams as `[NEEDS REVIEW]`. Saves report to `docs/agents/update-docs-report.md`.

## [1.7.0] - 2026-03-14

### Added

- **`/detach` command** -- clean removal of copilot-rpi from a project. Inventories all blueprint artifacts in 4 tiers (prompt files, chat modes, instructions, AGENTS.md sections, VS Code settings, user work products), previews what will be removed, asks for confirmation, then executes in a single atomic commit. Preserves project config and research/plan documents by default. Ported from cc-rpi v1.7.0.

## [1.6.1] - 2026-03-14

### Added

- **Error #29: Agent runs `gh pr create` without checking for existing PR** — `gh pr create` fails when a PR already exists for the head-to-base branch pair. Check with `gh pr list --head <branch>` first; if one exists, use `gh pr edit` to update it. Ported from cc-rpi Error #53.

## [1.6.0] - 2026-03-13

### Added

- **Error #27: CI explosion from parallel agent pushes** — when N agents push independently, every push triggers N x M CI runs (branches x workflows). New rule: worktree agents commit locally, main agent batch-pushes all branches in one command, creates all PRs, and monitors CI centrally. Added to `agent-errors.md` (Error #27), `quick-reference.md` (Branch & Multi-Agent Rule #6), and `agent-design.md` (Parallel Agent Push Strategy section + worktree agent row in Central Commit Rule table).
- **Error #28: Agent assumes GitHub labels exist when creating issues** — `gh issue create --label "chore"` fails if label doesn't exist. Check with `gh label list` or create first. Especially common after `/pre-launch` audits.
- **Project File Locations table** in `AGENTS.md.template` — consolidated all fixed-path references (agent reports, logs, scripts, project memory, ADRs, research docs, plans) into a single scannable table with a one-time "do not search" directive. Eliminates per-session token waste from agents searching for known locations.

## [1.5.0] - 2026-03-08

### Added

- **Errors #22–#26** — five new agent error patterns added to `agent-errors.md` and `quick-reference.md`:
  - **#22:** Scaffolding tool fails on non-empty directory — `create-next-app` and similar tools abort when AGENTS.md or `.github/` already exists. Scaffold first, configure second.
  - **#23:** Piping API response to JSON parser without error checking — `curl | jq` crashes with unhelpful parse errors when API returns non-JSON. Save response and check HTTP status first.
  - **#24:** Agent commits or pushes to the wrong branch — doesn't verify current branch before committing.
  - **#25:** Parallel agents create git conflicts from overlapping work — overlapping file edits and orphaned references. Central commit rule: designate one agent as the git committer.
  - **#26:** Agent skips test suite after config changes — config changes have broader blast radius than code. Always run full suite immediately after config/infrastructure changes.
- **`/status` prompt** — quick 5-line project orientation (branch, last commit, working tree, CI status, open items). Fast session start without beginning a full task.
- **`/fix-ci` prompt** — self-healing CI that parses failure logs, spawns parallel fix agents per failure category, and iterates until green (max 3 cycles). Automates the manual diagnose-fix-verify loop.
- **Git Protocol for Multi-Agent Work** section in `agent-design.md` — central commit rule, branch verification, file ownership for parallel agents, and branch strategy for agent orchestration.
- **Self-Healing CI** section in `push-accountability.md` — parallel fix agent pattern for multi-failure CI with retry budget and rules.
- **Branch verification, post-config test, and parallel agent rules** in `AGENTS.md.template` — three new workflow rules and a parallel agent git centralization rule.

## [1.4.0] - 2026-03-05

### Added

- **Three-tier error prevention model** — documented in `methodology/ci-and-guardrails.md`. Rules graduate from Document (advisory) to Prompt (command recipes) to Enforce (git hooks/CI). Addresses the core flaw: passive rules in AGENTS.md don't prevent errors the agent has already been told about.
- **Git command recipes** in `AGENTS.md.template` — compound command sequences the agent copies as a unit instead of composing individual commands. Covers push sequence, first push, tag push, and worktree cleanup.
- **Errors #19–#21** — three new agent error patterns added to `agent-errors.md` and `quick-reference.md`:
  - **#19:** `git pull --rebase` with uncommitted changes — the single most-repeated agent error (37% of observed errors).
  - **#20:** `git push --tags` pushes ALL local tags — old tags cause push failure. Use specific tag names or `--follow-tags`.
  - **#21:** Agent fabricates filesystem paths — guesses directory names like `GenAI_Projects` instead of using working directory or discovering with `ls`.

## [1.3.0] - 2026-03-01

### Added

- **`/quality-review` prompt** — reviews changed files for code reuse, code quality, and efficiency. Copilot-native equivalent of the quality review concept, scoped to git diff. Interactive (presents findings before fixing), not automatic.
- **Two-pass review model** — implementation phases now separate plan-compliance self-review from code-quality review (`/quality-review`). Documented in `/implement`, `AGENTS.md.template`, and `agent-design.md`.
- **Batch eligibility assessment** — plans now evaluate phase independence and mark `[batch-eligible]` where applicable. Users can parallelize via `copilot -p` fan-out or `@copilot` cloud agent issues.
- **Post-audit quality action** — `/pre-launch` now recommends `/quality-review` as the first fix action for code quality findings.
- **Post-adoption baseline audit** — `/adopt` now recommends running `/pre-launch` after setup for a full codebase quality baseline.

## [1.2.0] - 2026-02-24

### Fixed

- `/update` now adds new blueprint sections instead of skipping them — projects stay current with new knowledge
- Nightly agent shell script uses `CLAUDE_BIN` env var instead of bare command, fixing `launchd`/`cron` PATH failures

## [1.1.0] - 2026-02-23

### Added

- Memory management section in AGENTS.md template for cross-session persistence
- `/update` prompt template for incremental blueprint sync
- Scheduled update agent shell script (`templates/scripts/copilot-rpi-update-agent.sh`)
- Community files: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, CHANGELOG.md
- GitHub issue and PR templates
- CI workflow for markdown linting
- .gitignore for documentation repository

## [1.0.0] - 2026-02-22

### Added

- Full RPI (Research-Plan-Implement) methodology adapted for GitHub Copilot
- Methodology documentation (10 files covering philosophy through scheduled agents)
- Known error patterns catalog with 17 documented agent errors
- Quick reference for error patterns
- Template files: AGENTS.md, README header, VS Code settings, MCP config, setup checklist
- Prompt files: bootstrap, adopt, research, plan, implement, validate, describe-pr, pre-launch
- Path-specific instructions: tests, APIs, migrations
- Chat modes: RPI Research, RPI Planner, RPI Auditor
- Example documents: research document, implementation plan, error/success logs, pseudocode examples
- Workflow walkthroughs: bootstrap new project, add new feature, refactor existing code
- Copilot project instructions and error processing prompt
- GUIDE.md human-readable walkthrough
- MIT License
