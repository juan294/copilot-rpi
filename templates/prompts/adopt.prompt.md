---
mode: agent
description: "Audit an existing project and adopt copilot-rpi best practices"
---
# Adopt copilot-rpi Best Practices into Existing Project

You are auditing and migrating an existing project to follow the copilot-rpi blueprint. The blueprint lives at `${input:blueprintPath}`.

This project already exists and may already follow some practices. Your job is to assess what's in place, identify gaps, and create a migration plan — NOT to blindly overwrite what's already working.

## Phase 1: Learn the Rules

Read these files from copilot-rpi IN ORDER:

1. `patterns/quick-reference.md` — Internalize every operational rule.
2. `patterns/agent-errors.md` — Know every error pattern and its solution.
3. `methodology/README.md` — Read the one-paragraph summary.
4. `templates/setup-checklist.md` — Understand the target state.
5. `templates/AGENTS.md.template` — Know what a well-configured AGENTS.md looks like.

## Phase 2: Audit This Project

Investigate THIS project systematically:

**Configuration:** Does AGENTS.md exist? .vscode/settings.json? .github/prompts/? .github/instructions/? .github/chatmodes/? .vscode/mcp.json?

**Infrastructure:** What's the stack? Pre-commit hooks? CI? Git workflow? README?

**Workflow:** Does docs/ exist? Research documents, plans, decision records? Testing setup?

## Phase 3: Present the Audit Report

### What's Already In Place
List everything that aligns with copilot-rpi practices.

### What's Missing (by priority)
**HIGH:** Missing AGENTS.md, no prompt files, no docs/ structure
**MEDIUM:** No pre-commit hooks, incomplete CI, no path-specific instructions
**LOW:** No chat modes, no scheduled agents, no error logging

### What Needs Adaptation (Not Replacement)
Things that exist but differ from the blueprint.

## Phase 4: Get Approval and Execute

1. Ask which items to adopt and which to skip.
2. Ask about conflicts with existing conventions.
3. Create a migration checklist.
4. Execute item by item, confirming after each major change.

## Rules

- **Audit first, change nothing.** No files modified until user approves.
- **Respect what exists.** Don't overwrite working configurations.
- **Merge, don't replace.** Add missing pieces to existing files.
- **One thing at a time.** Logical, reviewable changes.
