# Phase 1: Source intake and workflow contracts

Entry: accepted [main plan](../2026-09-28-copilot-blueprint-modernization.md); read research R01-R03 and both instruction chains. No implementation is authorized by creation of this file.

## Changes

1. Preserve local state and reconcile the existing remote Sutura commits before implementation, after inspecting the diff and preserving intended work. Use a task worktree and document `main` integration with no automatic publication. Do not alter Sutura configuration.
2. Add `upstream/cc-rpi.lock.json`, its schema, `upstream/cc-rpi.inventory.json`, original imported source snapshots and a read-only intake checker. Pin full SHA `aa3ea57fb26ae2e1e167acada4b769e073a417f4` and source 2.1.0 separately from Copilot's version. List all 61 upstream components and every catalog entry, including explicit inapplicable/deferred reasons. Record source/destination hashes and adaptation notes for imported code/resources. Preserve upstream license notices. The default gate checks these self-contained snapshots; an explicit `--source` enables maintainer comparison with a supplied checkout. Test that a clean clone with no sibling cc-rpi and no network passes local consistency checks, while a simulated new upstream component is reported only by explicit intake.
3. Add canonical `templates/skills/` bodies for the 22 mapped workflows plus local maintenance `process-errors`. Bundle research, handoff, pseudocode, findings and E2E resources. Keep upstream concept changes separate from Copilot syntax transformations.
4. Port recovery/disclosure criteria, consumer sweeps, source provenance, independent review, simplify, TDD/test quality, exact candidate evidence and bounded delegation. Keep research descriptive and assessment evaluative. Preserve all audit domains and confirmed finding dispositions. Replace remote-wave/auto-merge/preview defaults with the accepted local authority contract.
5. Convert model-tier policy to interactive inheritance; select domain skills by applicability. Crosswalk all 40 Copilot errors and 55 rules by meaning to upstream entries; retain IDs, record additions/retirements and eliminate contradictions in methodology. Never claim an error fixed solely because the model improved.
6. Retain this selected research/plan tree through narrow ignore exceptions; ignore only runtime observations. Add behavioral review fixtures before editing corresponding workflow behavior.
7. Create the pinned development setup and initial sequential `scripts/verify-local.sh` from the main plan's executable contract, plus `scripts/check-upstream.py` and `scripts/check-links.py`. Pin dependencies and check in both lockfiles; these are development dependencies, not new runtime requirements for adopters.

Keep original imported source snapshots under `upstream/`, outside every active customization/discovery root. The snapshot inventory validates their hashes and attribution. Active-surface metadata checks and current-version checks must select the authored/rendered product explicitly, so historical upstream bytes cannot become runnable customizations or false current-version declarations. Test both boundaries. Adapt count/index checks and their rejection fixtures alongside any P1 catalog-format change, preserving permanent IDs and retirement coverage.

Evidence: Copilot `CHANGELOG.md:9`, `patterns/quick-reference.md:44`, `:98`, `:110`; cc-rpi `templates/skills/rpi-plan/SKILL.md:30`, `templates/skills/rpi-implement/SKILL.md:24`, `templates/rules/testing.md:41`, `templates/references/handoff.md:8`.

## Behavioral oracles

Create `tests/fixtures/workflows/` scenarios and `tests/test_workflow_contracts.py` for deterministic requirements; reserve model behavior for native qualification. Required cases: research receives evaluative request and routes explicitly; missing reviewer evidence prevents acceptance; a blocking cache requires both prevention and recovery evidence; a changed shared schema requires writer/caller coverage; user authorizes local implementation and output contains no implied remote work; existing handoff is stale and must be revalidated. A rubric records expected artifact fields and prohibited claims for each scenario.

```text
@ checkUpstream(source, lock) -> disposition report
ctx: pinned Git tree and local authored sources
pre: source identity and lock schema are valid
do:
  1. validate source and destination hashes
  2. compute complete component and catalog inventory
  3. emit missing, changed and explicitly excluded items
fail: unknown item or stale hash -> nonzero with review command
```

## Acceptance

Automated: every upstream item has one disposition; every old prompt maps once; all destination/resource paths resolve; duplicate IDs and accidental renumbering fail; altered source hash fails; correcting the reviewed pin succeeds. Preserve catalog/version checks and Markdown lint. The intake checker never downloads, applies or publishes changes.

Commands: `uv sync --locked`, then `npm ci`, then `uv run --locked python -m unittest discover -s tests -p 'test_workflow_contracts.py'`, then `bash scripts/verify-local.sh`. Use the main plan's sequential aggregation contract to retain failures; do not replace it with a last-command exit status.

Review: compare each workflow to the research evidence and scenario rubric, including existing Copilot-specific behavior. Confirm local knowledge and stable identity survive. No Copilot runtime support claim is made yet.

Independent units: `[batch-eligible]` catalog/methodology crosswalk; workflow/resource adaptation; intake schema/checker/tests. Assign disjoint paths; integration owner alone changes root docs and shared manifest. Do not run multiple complete suites.

Exit: independent review and simplify findings resolved; all current local gates pass sequentially. Record changed paths, tested commit/tree and dispositions in the handoff, then stop for acceptance. P2 depends on the completed source layout.
