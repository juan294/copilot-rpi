---
mode: agent
description: "Cleanly remove all copilot-rpi artifacts from this project"
---
# Detach Project from copilot-rpi Blueprint

You are cleanly removing copilot-rpi artifacts from this project. The blueprint lives at `${input:blueprintPath}`.

This command removes all blueprint-managed files and configuration while preserving project-specific content and user work products.

## Phase 1: Verify Adoption

1. Check for `.github/copilot-rpi-sync.json` or RPI prompts in `.github/prompts/` (research.prompt.md, plan.prompt.md, implement.prompt.md, validate.prompt.md).
2. If neither exists: report "This project doesn't appear to use copilot-rpi. Nothing to detach." and **stop**.
3. If sync metadata exists, read it and report the current blueprint version and last sync date.

## Phase 2: Inventory Artifacts

Scan this project for all copilot-rpi artifacts. Categorize each into one of four tiers.

### Tier 1: Blueprint scaffolding (always remove)

Check for these files and note which exist:

**Prompt files** (`.github/prompts/`):

- `research.prompt.md`
- `plan.prompt.md`
- `implement.prompt.md`
- `validate.prompt.md`
- `describe-pr.prompt.md`
- `pre-launch.prompt.md`
- `quality-review.prompt.md`
- `status.prompt.md`
- `fix-ci.prompt.md`
- `update.prompt.md`

**Chat modes** (`.github/chatmodes/`):

- `rpi-research.chatmode.md`
- `rpi-planner.chatmode.md`
- `rpi-auditor.chatmode.md`

**Path-specific instructions** (`.github/instructions/`):

- `tests.instructions.md`
- `api.instructions.md`
- `migrations.instructions.md`

**Other files:**

- `.github/copilot-rpi-sync.json` (sync state tracker)
- `scripts/agents/copilot-rpi-update.sh` (nightly sync agent, if exists)

For each prompt file that exists, diff it against `<copilot-rpi-path>/templates/prompts/<name>` to detect customization. Mark as "unmodified" or "customized."

For instruction and chatmode files, diff against `<copilot-rpi-path>/templates/github/instructions/<name>.template` and `<copilot-rpi-path>/templates/github/chatmodes/<name>` respectively.

### Tier 2: Blueprint-managed AGENTS.md sections

Read the project's AGENTS.md and identify these blueprint-managed sections by their `##` or `###` headers:

- `## RPI Workflow` (including all `###` subsections under it)
- `## Agent Operational Rules` (including all `###` subsections under it)
- `## Push Accountability`
- `## TDD Protocol`
- `## Agent Autonomy`
- `## Memory Management`
- `## Project File Locations`
- `### CRITICAL: Run verification commands before committing` (subsection under Key Commands)

Note which sections exist. Do NOT touch any other sections -- they are project-specific.

### Tier 3: Configuration entries

Read `.vscode/settings.json` and identify Copilot feature flags that were added by the blueprint:

- `github.copilot.chat.codeGeneration.useInstructionFiles`
- `github.copilot.chat.generateTests.codeLens`
- `chat.agent.enabled`
- `chat.experimental.multiChatSessions`

Note which exist. Leave all other VS Code settings untouched.

Check for `.github/copilot-instructions.md` -- identify any blueprint-managed sections vs project-specific content.

Check for a launchd plist for the copilot-rpi update agent:

- `~/Library/LaunchAgents/*copilot-rpi*` or `~/Library/LaunchAgents/*blueprint*`

### Tier 4: User work products

Check for and count files in:

- `docs/research/` -- research documents
- `docs/plans/` -- implementation plans
- `docs/decisions/` -- architecture decision records
- `docs/agents/` -- agent reports and project memory
- `logs/` -- agent logs

These are the user's intellectual work. Default is to **keep** them.

## Phase 3: Preview Report

Present the full inventory to the user:

```text
== Detach Preview ==

Blueprint version: <version> (synced <date>)

WILL REMOVE (blueprint scaffolding):
  [list each Tier 1 file that exists, with "unmodified" or "customized" tag]

WILL EDIT (AGENTS.md):
  Remove sections: [list each Tier 2 section found]
  Keep sections: [list remaining sections]

WILL CLEAN (VS Code settings):
  Remove: [list Tier 3 Copilot feature flags to remove]
  Keep: [list what stays]

WILL KEEP (your work):
  [list Tier 4 directories with file counts, or "none found"]

CUSTOMIZED FILES (review recommended):
  [for each customized file, explain what custom content will be lost]
```

If no customized files exist, omit the CUSTOMIZED FILES section.

## Phase 4: Confirm and Execute

Ask the user three questions:

1. **"Proceed with detach?"** -- required. If no, stop.
2. **"Remove research docs and plans too?"** -- default: no. Only remove Tier 4 if user explicitly says yes.
3. **"Remove Copilot feature flags from VS Code settings?"** -- default: yes. If user wants to keep them, skip Tier 3.

For any customized files, ask: **"Keep [filename] as a custom prompt/instruction?"** If yes, skip that file.

Then execute in order:

1. Delete Tier 1 files (skip any the user chose to keep).
2. Edit AGENTS.md to remove Tier 2 sections. Remove each section from its `##` header through to the next `##` header (or end of file). For the `### CRITICAL` subsection, remove only that subsection, not the parent `## Key Commands`.
3. Clean Tier 3 configuration:
   - Remove blueprint Copilot feature flags from `.vscode/settings.json`. If no other settings remain, remove the file.
   - Edit `.github/copilot-instructions.md` to remove blueprint-managed sections. If only blueprint content remains, remove the file.
4. Handle Tier 4 per user decision (keep by default).
5. Clean up empty directories: remove `.github/prompts/` if empty, `.github/chatmodes/` if empty, `.github/instructions/` if empty. Do NOT remove `.github/` itself.
6. If a launchd plist was found: `launchctl unload <plist>` then delete the plist file. Ask before this step.

## Phase 5: Commit

Stage all changes and create a single atomic commit:

```text
chore: detach from copilot-rpi blueprint

Removed RPI methodology prompts, chat modes, instructions, AGENTS.md
blueprint sections, and sync metadata. Project-specific configuration
preserved.
```

## Phase 6: Report

Present the final summary:

```text
== Detach Complete ==

Removed: [N] files, [N] AGENTS.md sections, [N] VS Code settings
Kept: [list preserved Tier 4 directories with counts, or "no work products found"]
Commit: [hash]

This project no longer syncs with copilot-rpi. The prompt files, chat
modes, instructions, and methodology sections have been removed. Your
project configuration and work products are untouched.

To re-adopt later: run /adopt
```

## Rules for This Process

- **Preview before delete.** Never remove anything without showing the user what will happen first (Phase 3).
- **Preserve project identity.** Only remove blueprint-managed content. Everything project-specific stays.
- **Keep user work products by default.** Research docs, plans, and decisions are the user's work. Only remove if explicitly asked.
- **Flag customizations.** If a prompt, instruction, or chat mode has been modified from the template, warn the user before deleting it.
- **One atomic commit.** All removals go in a single commit. Don't scatter across multiple commits.
- **Idempotent.** Running on a project without copilot-rpi artifacts reports "nothing to detach" and stops. Running twice produces no changes the second time.
- **Don't touch VS Code itself.** `.vscode/` directory and non-Copilot settings are the project's own -- they exist independently of copilot-rpi.
