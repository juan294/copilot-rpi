# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
