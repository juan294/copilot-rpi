# Phase 2: Native Copilot rendering

Entry: P1 accepted. Read research R04/R06 and E01-E10, E15-E16; recheck current official schemas before implementation.

## Changes

1. Add `templates/distribution.json`, explicit Copilot adapter/profile metadata and a deterministic renderer at `templates/scripts/rpi-distribution.py`. Use one manifest for installation, removal and verification, including resource dependencies and former paths. Preserve attribution for reused upstream logic.
2. Render standard skills to `.github/skills/rpi-*/SKILL.md`; no Claude/Codex native headers or `$ARGUMENTS` reach those outputs. Skills use portable natural-language argument instructions. Keep explicit invocation for lifecycle/publication workflows and distinguish invocation from authorization.
3. Replace the three chatmode roles with `.github/agents/*.agent.md`. Use supported explicit tool sets, optional model inheritance and safe delegation. A read-only research role returns cited findings; an authorized parent writes the research artifact. The plan must not promise artifact writes from a role with no write tool. Enable repository instructions for CLI subagents using the supported field and test this on the actual client. Audit/review roles do not receive unrestricted shell solely to read files.
4. Render VS Code Local prompt wrappers using current `agent` metadata only under its compatibility profile. Reserve `/rpi-plan` and `/rpi-status`; do not shadow native `/plan` or `/status`. Give retained old names migration notices only where native discovery supports them; do not install duplicate skill/prompt commands in the same profile.
5. Keep `AGENTS.md` concise and `.github/copilot-instructions.md` complementary, with no conflicting duplicate policy. Use path instructions for tests/API/migrations/deployment and selected domains. Budget the managed always-loaded root text at no more than 8,192 UTF-8 bytes; report total observed instruction sources separately. Do not invent percentage-based context thresholds.
6. Replace blanket VS Code settings with a minimal documented profile. Retain only schema-verified settings that serve a concrete need. Provide separate optional VS Code and CLI MCP examples, with correct schema, declared secret inputs/environment references and no automatic server start. Do not enable experimental flags, trust or broad approvals by default.
7. Update `templates/scripts/verify-prompts.sh` and its rejection fixtures in this phase to delegate native metadata validation to the profile-aware parser. The new `agent` wrappers and skills must not wait until P4 to replace the old mandatory `mode` check. Explicitly inventory retained legacy files during migration; self-application drift checks compare only matching declared profiles, and reject undeclared active surfaces rather than silently skipping them.

Evidence: `templates/scripts/verify-prompts.sh:3`, `:53`; `templates/github/chatmodes/rpi-research.chatmode.md:1`; `templates/vscode-settings.json.template:1`; `templates/vscode-mcp.json.template:1`. Primary contracts are linked as E01-E10/E15-E16 in the research report.

## Tests and recovery

Write `tests/test_rendering.py` and real fixture trees before renderer changes. Cover valid and malformed YAML/frontmatter, missing resources, path escape and symlinks, duplicate names, unsupported metadata, empty versus omitted tools, wrong profile, accidental model pins and root budget overflow. YAML parsing must reject duplicate keys, not merely find required strings. Preserve owner-authored general YAML outside the generated authoring grammar.

Render twice into separate temporary directories and compare all bytes. A fixture with legacy chatmodes produces a migration plan, not an unowned deletion. A missing tool is a diagnosed capability failure, not assumed read-only safety. Statically test that each output only uses its declared profile metadata; native discovery is P5.

```text
@ render(manifest, profile) -> native file tree
ctx: canonical workflows and adapter metadata
pre: profile is explicit and all resources are declared
do:
  1. validate metadata, tool names and paths
  2. compute profile-specific outputs and collision set
  3. write deterministic bytes to the requested staging directory
fail: unsupported field or collision -> nonzero with source path
```

## Acceptance and coordination

Automated: all schema/renderer tests and existing gates pass; resource links resolve in the rendered tree; no duplicate active command names; no unknown executable settings/MCP placeholder is shipped as active configuration. Deliberate malformed input fails and corrected input succeeds.

Commands: `uv run --locked python -m unittest discover -s tests -p 'test_rendering.py'`, then `uv run --locked python templates/scripts/rpi-distribution.py validate --source .`, then `uv run --locked python templates/scripts/rpi-distribution.py check-generated --source .`, then `bash scripts/verify-local.sh`. Add both renderer commands to the full runner in this phase.

Review: user can distinguish primary Copilot/CLI support from Local compatibility. Shared workflow semantics match P1 and no provider-specific field silently broadens tools. Discovery remains marked unmeasured until P5.

Independent units: `[batch-eligible]` native agent/instruction templates and their fixtures; renderer/manifest tests after output contract is frozen. Integration owner owns shared metadata and generated self-application. Run full local gate once sequentially after integration, independent review, repair and simplify, then stop for acceptance.
