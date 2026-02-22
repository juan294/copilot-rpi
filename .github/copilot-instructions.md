# copilot-rpi — Project Instructions

<!-- Auto-loaded by Copilot every session. This is the operational memory for maintaining this repo. -->
<!-- For repo structure and purpose, read AGENTS.md. This file covers runtime behavior only. -->

## Key Operational Rules

Always internalize `patterns/quick-reference.md` before any work. The most critical rules:

1. Run typecheck/lint BEFORE committing — don't discover failures at commit time
2. `git pull --rebase` before pushing — remote may have advanced
3. Remove worktrees BEFORE merging PRs with `--delete-branch`
4. `git worktree remove --force` — always force; use `;` not `&&` for chains
5. `git branch -D` (uppercase) for worktree branches — squash merges mean they're never "fully merged"
6. Don't guess `gh` CLI `--json` field names — run `gh <cmd> --json 2>&1 | head -5` first
7. Always TDD — Red-Green-Refactor, no "tests later"
8. Exhaust all tools before suggesting manual steps

## User Preferences

- **Maximum autonomy** — encode solutions into the repo, never rediscover the same fix twice
- **All new patterns go into repo files** — not just chat history or ephemeral notes
- **Keep everything generic** — no project-specific references in this blueprint repo
- **Commit and push** when changes are complete — don't wait to be asked unless the change is risky

## Error Screenshot Workflow

Juan drops agent error screenshots into `~/Desktop/agent-errors/`. When he says "process my error screenshots", use the `/process-errors` prompt or follow this flow:

1. List all images in `~/Desktop/agent-errors/`
2. Read each image to identify the error pattern
3. Cross-reference against existing patterns in `patterns/agent-errors.md`
4. **Skip duplicates** — if the error is already cataloged, ignore it
5. For new errors, add them to `patterns/agent-errors.md` following the existing format (Error #N — Title, Symptom, Root Cause, Correct Approach, What NOT to Do)
6. Add a one-liner to `patterns/quick-reference.md` for each new entry
7. Commit and push
8. **Delete all processed images** from the folder so only pending items remain

This is the standard flow — no need for Juan to check if errors are already cataloged.

## Contributing to This Repo

- New error patterns → `patterns/agent-errors.md` + one-liner in `patterns/quick-reference.md`
- New methodology insights → appropriate file under `methodology/`
- New templates → `templates/` directory with clear naming
- Keep entries generic — no project-specific references

## Available Prompt Files

This repo includes prompt files in `.github/prompts/` for maintaining itself:

- `/process-errors` — Process error screenshots from the Desktop folder

## Relationship to cc-rpi

This repo is the Copilot counterpart to cc-rpi (Claude Code Reference & Project Intelligence). They share ~60% of content (philosophy, phases, testing, logging) but differ in tool-specific mechanics. Keep them conceptually aligned but tool-appropriate.
