---
mode: agent
description: "Set up a new project using the copilot-rpi blueprint"
---
# Bootstrap New Project from copilot-rpi Blueprint

You are setting up a new project using the copilot-rpi blueprint repository. The blueprint lives at `${input:blueprintPath}`.

## Phase 1: Learn the Rules

Read these files from copilot-rpi IN ORDER. Do not skip any.

1. `patterns/quick-reference.md` — Internalize every operational rule.
2. `patterns/agent-errors.md` — Know every error pattern and its solution.
3. `methodology/README.md` — Read the one-paragraph summary and reading order.

## Phase 2: Understand the Templates

Read these files:

1. `templates/setup-checklist.md` — Your step-by-step guide.
2. `templates/AGENTS.md.template` — Starting point for this project's AGENTS.md.
3. `templates/vscode-settings.json.template` — Starting point for .vscode/settings.json.
4. `templates/README-header.md` — Standard README header structure.

## Phase 3: Set Up This Project

Execute the setup checklist:

1. **Ask me** what type of project this is (web app, library, CLI, monorepo, Python, static site).
2. **Ask me** for the project name, description, stack, and specifics.
3. Create AGENTS.md — adapt from the template, manually crafting every line.
4. Create `.vscode/settings.json` — adapt from the template.
5. Create `.github/prompts/` — copy prompt files and adjust.
6. Create `.github/instructions/` — set up path-specific instructions.
7. Create `.github/chatmodes/` — set up research and planning chat modes.
8. Create the directory structure (`docs/research/`, `docs/plans/`, `docs/decisions/`).
9. Set up the README with the standard header.
10. Walk through remaining checklist items (pre-commit hooks, CI, git setup).

## Phase 4: Save to Memory

Create `docs/agents/project-memory.md` with the following structure, filled in from everything you learned during setup:

```markdown
# Project Memory

Operational knowledge that persists across sessions. Agents read this at session start and append lessons as they work.

## Project Identity

- **Name:** [project name]
- **Type:** [web app / library / CLI / monorepo / etc.]
- **Stack:** [language, framework, key libraries]
- **Default branch:** [develop / main]
- **Production branch:** [main]

## Setup Decisions

[Decisions made during bootstrap — why certain template sections were kept, removed, or adapted]

## Internalized Rules

[Key rules from patterns/quick-reference.md that are especially relevant to this project]

## CI/CD & Environment

[CI provider, required checks, environment variables, deployment targets]

## Operational Lessons

[Append new lessons here as they are discovered — one line per lesson]
```

Fill every section from what you learned in Phases 1–3. Don't leave placeholders.

## Rules

- **Ask before assuming.** Every project is different.
- **Adapt, don't copy.** Templates are starting points.
- **Keep AGENTS.md lean.** Only include instructions that would cause mistakes if missing.
- **Always save to memory.** Phase 4 is not optional. Every bootstrap must end with a memory save.
