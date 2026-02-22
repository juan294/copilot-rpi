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

4. `templates/setup-checklist.md` — Your step-by-step guide.
5. `templates/AGENTS.md.template` — Starting point for this project's AGENTS.md.
6. `templates/vscode-settings.json.template` — Starting point for .vscode/settings.json.
7. `templates/README-header.md` — Standard README header structure.

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

## Rules

- **Ask before assuming.** Every project is different.
- **Adapt, don't copy.** Templates are starting points.
- **Keep AGENTS.md lean.** Only include instructions that would cause mistakes if missing.
