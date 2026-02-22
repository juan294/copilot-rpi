# New Project Setup Checklist

Use this when setting up a new project to follow copilot-rpi best practices.

## README Header

- [ ] Structure every project README with the standard header (adapt from `templates/README-header.md`):
  1. `# Project Name — Tagline`
  2. GitHub badges (CI, Security Scan, Secret Scanning, stack versions, license)
  3. One-line project description
  4. Chapa badge: `![Chapa Badge](https://chapa.thecreativetoken.com/u/juan294/badge.svg)`
  5. Horizontal divider (`---`)
  6. Rest of the README content below the divider
- [ ] Adjust badge URLs to match the project's GitHub owner/repo
- [ ] Add or remove stack badges as relevant

## Directory Setup

- [ ] Create `AGENTS.md` at project root (adapt from `AGENTS.md.template`)
  - Manually craft every line — don't auto-generate
  - Keep it lean: only universally applicable instructions
  - This is the cross-tool instruction file (read by Copilot, Claude Code, Cursor, Gemini CLI)
- [ ] Create `.github/prompts/` and copy prompt files from `templates/prompts/`
- [ ] Create `.github/instructions/` for path-specific rules (auto-loaded by glob):
  - e.g., `tests.instructions.md` (applies to `**/*.test.{ts,tsx}`)
  - e.g., `api.instructions.md` (applies to `**/routes/**`, `**/api/**`)
  - Rules fire automatically when matching files are in context
- [ ] Create `.github/chatmodes/` for specialized chat personas:
  - e.g., `rpi-research.chatmode.md` (documentarian-constrained research mode)
  - e.g., `rpi-planner.chatmode.md` (planning mode with pseudocode output)
- [ ] Create `docs/` directory with subdirectories:
  - `docs/research/` — Research documents
  - `docs/plans/` — Implementation plans
  - `docs/decisions/` — Architecture decision records
- [ ] Configure `.vscode/settings.json` (adapt from `templates/vscode-settings.json.template`):
  - Enable agent mode: `"chat.agent.enabled": true`
  - Enable thinking: `"github.copilot.chat.agent.thinkingTool": true`
  - Enable auto-fix: `"github.copilot.chat.agent.autoFix": true`
- [ ] Create `.vscode/mcp.json` if the project uses MCP servers (adapt from `templates/vscode-mcp.json.template`)
- [ ] Optionally create `.github/copilot-instructions.md` for Copilot-specific addenda
  - Only needed if you have rules that apply only to Copilot (not Claude Code/Cursor)
  - Most projects can skip this — AGENTS.md covers everything

## AGENTS.md Configuration

- [ ] Fill in project name, description, and stack
- [ ] Document build/test/lint commands
- [ ] Document deployment pipeline (which branch deploys where)
- [ ] Document git workflow (default branch, production branch)
- [ ] Include all Agent Operational Rules from the template
- [ ] Add project-specific context (key routes, data types, code ownership)

## Prompt Files

Copy and adapt from `templates/prompts/`:

- [ ] `/research` — Codebase research with documentarian constraint
- [ ] `/plan` — Interactive plan creation with phases
- [ ] `/implement` — Phase-by-phase execution with review gates
- [ ] `/validate` — Post-implementation verification
- [ ] `/describe-pr` — PR description generation
- [ ] `/pre-launch` — Multi-specialist production audit

Verify each file has valid YAML frontmatter with `mode:` and `description:` fields.

**Prompt files vs instructions:** Prompts (`.github/prompts/`) are user-invoked workflows. Instructions (`.github/instructions/`) are auto-loaded rules. Use prompts for RPI phases; use instructions for domain conventions.

## Path-Specific Instructions

- [ ] Create test conventions: `.github/instructions/tests.instructions.md` with `applyTo: "**/*.test.{ts,tsx}"`
- [ ] Create API conventions: `.github/instructions/api.instructions.md` with `applyTo: "**/routes/**"`
- [ ] Create migration conventions: `.github/instructions/migrations.instructions.md` with `applyTo: "**/migrations/**"` (if applicable)

Each file must have `applyTo` in YAML frontmatter — without it, the file is silently ignored.

## Chat Modes

- [ ] Create research mode: `.github/chatmodes/rpi-research.chatmode.md`
  - Bakes in the documentarian constraint at the session level
  - Restricts tools to read-only (no file writes, no terminal)
- [ ] Create planning mode: `.github/chatmodes/rpi-planner.chatmode.md`
  - Includes pseudocode notation reference
  - Focuses on interactive plan development
- [ ] Create auditor mode: `.github/chatmodes/rpi-auditor.chatmode.md` (optional)
  - Read-only validation with structured report output

## Pre-Commit Hooks

- [ ] Install a hook framework (e.g., Husky for Node.js, pre-commit for Python)
- [ ] Configure pre-commit to run typecheck + lint:

  ```bash
  # Example: Husky
  npx husky init
  echo "pnpm run typecheck && pnpm run lint" > .husky/pre-commit
  ```

- [ ] Test that the hook rejects a commit with a deliberate type error
- [ ] Add a note to AGENTS.md reminding agents to run checks before committing

## CI Setup

- [ ] Create a CI workflow (GitHub Actions, etc.) that runs on push and PR:
  - Typecheck
  - Lint
  - Unit tests
  - Build verification
  - (Optional) Security audit, E2E tests
- [ ] Mark critical CI jobs as required for PR merges
- [ ] Enable branch protection on the production branch (require CI + review)
- [ ] Verify CI runs successfully on the development branch

## Git Setup

- [ ] Initialize repo with `main` as production branch
- [ ] Create `develop` as default working branch
- [ ] Set up branch protection rules on GitHub
- [ ] Configure pre-commit hooks (typecheck, lint, test) — see Pre-Commit Hooks above

## Push Accountability

- [ ] Add push accountability instructions to AGENTS.md:
  - After every push to develop, verify CI passes
  - Investigate failures, fix, and re-push
- [ ] Test the workflow: push a deliberate failure, verify the process catches it

## Scheduled Agents (Optional)

- [ ] Create `scripts/agents/` directory for agent shell scripts
- [ ] Create `docs/agents/` directory for agent reports and shared context
- [ ] Create `logs/` directory for agent output capture
- [ ] Write at least one agent script (e.g., test-health, security-audit)
- [ ] Ensure Copilot CLI is authenticated (`copilot auth`)
- [ ] Schedule with launchd (macOS) or cron (Linux)
- [ ] Verify the agent runs successfully and produces a report

## Workflow Habits

- [ ] Always `/research` before `/plan`
- [ ] Always `/plan` before `/implement`
- [ ] Always review plans before approving
- [ ] Never skip the human confirmation gate between implementation phases
- [ ] Use `/validate` after implementation
- [ ] Start a new Chat window between unrelated tasks to reset context
- [ ] Run each RPI phase in its own conversation
- [ ] Research and plan on the default branch; implement in feature branches
- [ ] Read research output critically — throw out and redo if wrong
- [ ] Invest most review time on research and plans, not generated code
- [ ] Follow TDD: write failing tests before implementation code
- [ ] Monitor CI after every push — never push and forget

## Project-Type Adaptation

The defaults above assume a web application. Adapt these sections based on your project type:

### Web Application (default)

The standard setup applies as-is.

### Library / npm Package

- **Git workflow:** May use `main` only (no `develop`) if releases are tagged from `main`
- **CI additions:** Add `npm pack` or `pnpm pack` verification, publish dry-run
- **AGENTS.md:** Document the public API surface

### CLI Tool

- **CI additions:** Test the CLI binary end-to-end
- **AGENTS.md:** Document all commands and flags. ESM CLI files use shebang — never run with `node`

### Monorepo

- **CI additions:** Use `turbo`/`nx` affected detection
- **AGENTS.md:** Document the workspace structure, how packages depend on each other
- **Pre-commit:** Run typecheck across ALL workspace packages

### Python Project

- **Pre-commit hooks:** Use the `pre-commit` framework (not Husky)
- **Key commands:** Replace `pnpm run *` with equivalents: `pytest`, `mypy .`, `ruff check .`

### Static Site / Documentation

- **Git workflow:** May deploy directly from `main`
- **CI:** Build verification + link checking

## Thoughts Directory Structure

```text
docs/
├── research/                  # Research documents
│   └── YYYY-MM-DD-topic.md
├── plans/                     # Implementation plans
│   ├── YYYY-MM-DD-feature.md  # Main plan
│   └── YYYY-MM-DD-feature-phases/
│       ├── phase-1.md
│       └── phase-2.md
├── decisions/                 # ADRs / decision records
└── prs/                       # PR descriptions
    └── {number}_description.md
```
