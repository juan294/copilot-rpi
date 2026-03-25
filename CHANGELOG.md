# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
