# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
