---
mode: agent
description: "Sync this project with the latest copilot-rpi blueprint improvements"
---
# Update Project from copilot-rpi Blueprint

You are syncing this project with the latest copilot-rpi blueprint. The blueprint lives at `${input:blueprintPath}`.

This command works for both interactive use (`/update`) and headless scheduled agents.

## Prerequisites

Before starting, verify this project was bootstrapped or adopted from copilot-rpi:

- If `.github/prompts/` exists with RPI prompts (research, plan, implement, validate) → proceed.
- If AGENTS.md exists with "RPI Workflow" section → proceed.
- If neither exists → this project hasn't been set up with copilot-rpi. Tell the user to run `/adopt` first and stop.

## Phase 1: Check for Updates

1. Pull the latest copilot-rpi: `git -C <copilot-rpi-path> pull --rebase`
2. Check if `.github/copilot-rpi-sync.json` exists in THIS project.
   - If YES: read it and note the `lastSyncCommit` hash.
   - If NO: this is the first sync. Treat everything as new.
3. If `lastSyncCommit` exists:
   - Run `git -C <copilot-rpi-path> log --oneline <lastSyncCommit>..HEAD` to see what changed.
   - Run `git -C <copilot-rpi-path> diff --name-only <lastSyncCommit>..HEAD` to get changed files.
   - If nothing changed, report "Already up to date" and stop.

## Phase 2: Internalize New Knowledge

Read these files from copilot-rpi to internalize the latest rules and patterns:

1. `patterns/quick-reference.md` — All operational rules.
2. `patterns/agent-errors.md` — All known error patterns.
3. `methodology/README.md` — Methodology overview.

On incremental syncs (lastSyncCommit exists), prioritize reading files that appear in the git diff. You can skip unchanged methodology files.

## Phase 3: Update Prompt Files

1. Compare each file in copilot-rpi `templates/prompts/` against this project's `.github/prompts/`:
   - **Skip** `bootstrap.prompt.md` and `adopt.prompt.md` — these are blueprint-level commands, not project-level.
   - For each remaining prompt (research, plan, implement, validate, describe-pr, pre-launch, update):
     - If it exists in both locations and the copilot-rpi version is different → replace the project version.
     - If it exists in copilot-rpi but not in this project → add it.
     - If it exists only in this project → leave it (project-specific prompt).
   - The update prompt itself (`update.prompt.md`) IS replaced — this command is self-updating.

## Phase 4: Update AGENTS.md

1. Read this project's AGENTS.md fully.
2. Read copilot-rpi's `templates/AGENTS.md.template`.
3. Identify **blueprint-managed sections** by their headers. These sections come from the template and should be kept in sync:
   - `## RPI Workflow` (and all `###` subsections under it: Context Management, Rules for All Phases, Rules for Implementation, Testing Philosophy)
   - `## Agent Operational Rules` (and all `###` subsections under it: Git Operations, GitHub CLI)
   - `## Push Accountability`
   - `## TDD Protocol`
   - `## Agent Autonomy`
   - `## Memory Management`
4. For each blueprint-managed section:
   - If the project's version differs from the template → update to match.
   - If the project has added project-specific content *within* a blueprint section (e.g., extra rules), preserve it — only update the parts that came from the template.
   - If a section doesn't exist in the project → skip it (don't add sections, that's `/adopt`'s job).
5. **Do NOT touch** project-specific sections: Project name, One-liner, Stack, Key Commands, Git Workflow, Deployment, Commit Messages, Research Documents, Implementation Plans, or any custom section.
6. The `### CRITICAL: Run verification commands before committing` section under Key Commands is blueprint-originated — update it if it exists.

## Phase 5: Update Copilot Config

### Instructions (direct replacement)

1. Compare each file in copilot-rpi `templates/github/instructions/` against this project's `.github/instructions/`:
   - For each `.instructions.md.template` in copilot-rpi, check if the corresponding `.instructions.md` exists in the project.
   - If it exists and differs → replace it.
   - If it doesn't exist → skip (adding is `/adopt`'s job).
   - Never touch project-specific instruction files not in the template.

### Chat Modes (direct replacement)

1. Compare each file in copilot-rpi `templates/github/chatmodes/` against this project's `.github/chatmodes/`:
   - For each `.chatmode.md` in copilot-rpi, check if it exists in the project.
   - If it exists and differs → replace it.
   - If it doesn't exist → skip.
   - Never touch project-specific chat modes not in the template.

### Copilot Instructions (smart merge)

1. If `.github/copilot-instructions.md` exists in this project:
   - Read copilot-rpi's `templates/github/copilot-instructions.md.template`.
   - Update blueprint-managed sections. Preserve project-specific content.
   - If the file doesn't exist → skip.

### VS Code Settings (additive only)

1. If `.vscode/settings.json` exists in this project:
   - Read copilot-rpi's `templates/vscode-settings.json.template`.
   - Add any new keys from the template that are missing in the project.
   - **Never remove or change** existing project settings.

## Phase 6: Write Sync Metadata

1. Get the current HEAD commit hash of copilot-rpi: `git -C <copilot-rpi-path> rev-parse HEAD`
2. Get the current version tag: `git -C <copilot-rpi-path> describe --tags --abbrev=0 2>/dev/null`
3. Write/update `.github/copilot-rpi-sync.json`:

```json
{
  "lastSyncCommit": "<commit-hash>",
  "lastSyncDate": "YYYY-MM-DD",
  "blueprintVersion": "<version-tag>"
}
```

## Phase 7: Report and Commit

1. If any project files were changed (prompts, AGENTS.md, instructions, chat modes, settings):
   - Stage only the changed files (not unrelated changes).
   - Commit with: `chore: sync with copilot-rpi blueprint <version-tag>`
   - Always update the sync metadata even if no other files changed.
2. Present a summary:
   - copilot-rpi version synced to (tag + commit hash)
   - Prompts updated/added (list them)
   - AGENTS.md sections updated (list them)
   - Instructions/chat modes updated (list them)
   - VS Code settings changes (list them)
   - Notable new content: new error patterns, new rules, methodology changes
   - "Already up to date" if nothing changed

## Rules

- **Never delete project content.** Only add or update blueprint-managed sections.
- **Preserve project identity.** Stack, deployment, key commands, commit conventions — these are the project's own.
- **Be idempotent.** Running twice with no copilot-rpi changes should produce zero file changes.
- **Commit atomically.** All sync changes go in one commit with the sync metadata.
- **If unsure, skip and report.** When a section has been heavily customized beyond the template, leave it alone and note it in the report as "skipped — heavily customized."
- **No interactive prompts.** This command must work headlessly for scheduled agents. Don't ask for confirmation — just apply safe updates and report what you did.
