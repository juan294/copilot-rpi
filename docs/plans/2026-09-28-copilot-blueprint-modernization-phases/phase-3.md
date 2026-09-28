# Phase 3: Ownership-aware installation and migration

Entry: P2 accepted. Revalidate upstream lifecycle/config source before adapting it. The current cc-rpi renderer explicitly supports only Claude/Codex; adding an arbitrary adapter file alone is insufficient.

## Changes

1. Adapt pinned `rpi-lifecycle.py` and `rpi-config.py` behind the Copilot distribution CLI. Provide `plan`, `apply`, `check`, `rollback` and `detach`, preserving transaction and path safety. Record source patches in the upstream lock.
2. Use a distinct `.rpi/copilot/manifest.json`, content-addressed `.rpi/copilot/baselines/` and `.rpi/local/copilot/` journals so a project that also uses cc-rpi does not overwrite its `.rpi/manifest.json`. Stable component IDs and explicit capability ownership select native files, managed blocks and settings keys.
3. Make plans include source SHA, target identity, selected profile/components, current input hashes, create/update/conflict/remove actions and capability changes. Apply only when the plan still matches the actual inputs. `check` is read-only and reports each conflicting or inactive surface.
4. Read `.github/copilot-rpi-sync.json` as a legacy provenance hint. Establish ownership only from exact historical template bytes or an owner-reviewed mapping. A bare filename, heading, old commit claim or newer template never proves ownership. Preserve custom prompts, globs, agents, settings, other harnesses and curated docs.
5. Use three-way content reconciliation and field/block ownership. Preserve JSONC comments and unrelated settings; report conflicting owner fields. Keep modified removed components as local content. Detach removes only unchanged owned bytes/entries and never deletes `.github` or `.vscode` wholesale.
6. Route lifecycle skills and setup through this engine. Default to project-local content only. Native hook activation, Git-hook installation, global customization, MCP capabilities and scheduler registration are separate explicit selections. Read-only upstream intake produces a reviewable delta and never self-applies it.

Evidence: old behavior `templates/prompts/update.prompt.md:43`, `:65`, `:107`; `templates/prompts/detach.prompt.md:53`, `:85`; proven source behavior `cc-rpi/templates/scripts/rpi-lifecycle.py:532`, `:1114`, `cc-rpi/templates/scripts/rpi-config.py:160`.

## Tests and recovery

Write `tests/test_lifecycle.py` using real temporary Git repositories/files. Cases: fresh install; no-op second install/update; update with clean baseline; owner-only edit; simultaneous upstream/owner edit; unknown existing destination; stale plan; copied false sync metadata; renamed legacy chatmode; retained custom globs; malformed/symlinked manifest; destination path escape; absent source baseline; shared cc-rpi coexistence; interrupted transaction; newer edit before rollback; detach/re-adopt; Unicode/spaces; directory symlinks; partial native config ownership.

For every refusal, assert exact original bytes remain and the diagnostic contains a runnable re-plan or recovery command. Then repair the fixture through the documented path and assert progress succeeds. Tests must cover scripts and fixture writers as consumers of each new manifest schema.

```text
@ apply(plan, target) -> receipt
ctx: target filesystem, ownership baselines and local journal
pre: source and target hashes match the reviewed plan
do:
  1. validate paths, ownership and requested capability scope
  2. write durable recovery journal
  3. write reconciled owned content and manifest
  4. emit verification result and recovery instructions
fail: changed input or interrupted write -> preserved evidence and explicit recovery
```

## Acceptance and coordination

Automated: full lifecycle matrix passes on real filesystem state, check mode writes nothing, repeat apply is a no-op, no ownership conflict is auto-resolved by replacement, and rollback never destroys a newer edit. Test on macOS locally and portable Linux fixtures before release qualification; unsupported platforms remain explicit.

Commands: `uv run --locked python -m unittest discover -s tests -p 'test_lifecycle.py'`, then `bash scripts/verify-local.sh`. The lifecycle test command itself executes plan/apply/check/rollback/detach against its temporary fixtures and asserts exit codes, visible recovery and original/restored bytes.

Review: migration preview lists every active legacy surface, optional capability and retained customization; restoration uses saved bytes, not reconstructed prose. No adopter outside disposable fixtures is changed during this phase.

Units are mostly dependent: one owner handles transaction/config/manifest code. `[batch-eligible]` legacy fixture preparation may proceed against a frozen schema in a separate file set. Complete independent review, repair, simplify and all sequential gates, then stop for acceptance.
