# Copilot guidance

AGENTS.md holds shared project facts, RPI phase rules, Git topology and authority. Keep this file for Copilot-specific discovery and tool behavior; do not duplicate or override project policy here.

Canonical workflows live in `.github/skills/`. Select the relevant `rpi-*` skill by name and read its bundled resources. Project role profiles live in `.github/agents/`. A research or audit agent with only `read` and `search` tools returns cited findings to its parent; its parent writes artifacts and runs checks. If a selected client lacks a declared tool or cannot load a resource, report the capability gap and use a qualified profile.

Scoped guidance in `.github/instructions/` applies by path or task relevance. Verify the active Copilot CLI or VS Code harness loaded the expected instructions and tools before claiming native support. A file's presence alone is not discovery proof. Interactive workflows inherit the session's selected model and effort; no project template pins a model.

Legacy Local `.prompt.md` wrappers and `.chatmode.md` files are optional compatibility surfaces. Do not install a wrapper that collides with a skill name in the same profile. Native `/plan` and `/status` are distinct from `rpi-plan` and `rpi-status`.
