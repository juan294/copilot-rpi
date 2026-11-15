# Phase 1: intake repin to cc-rpi `cec458a`

Parent: `docs/plans/2026-11-15-cc-rpi-2.2-sync.md`. Entry: owner accepted the plan; copilot-rpi `main` and cc-rpi `v2.2.0` revalidated. Work in a local worktree on a task branch.

## Steps

1. Make a clean cc-rpi checkout at `cec458a` for the comparison, either a local clone or a detached worktree outside both repositories. Run the comparison from `docs/upstream-sync.md:18-30`. Confirm the printed SHA `cec458a9769049c6dd08777768ef718ac7571a30` and record the printed changes digest. On 2026-11-15 the digest was `3b88912b...e95` against the `5920376` pin; it is recomputed after the repin.
2. Write `docs/decisions/2026-11-15-cc-rpi-2.2-sync-intake.json`, one decision per printed ID (format in `docs/upstream-sync.md:33-38`):
   - **adapted**, with the note "content adapted in Phase 2 or 3":
     - the 16 workflow skills;
     - `resource:lifecycle-engine`, for the reserved path and authored hash only (the cc-rpi WB repair series stays deferred, and the note says so);
     - `resource:distribution-manifest`.
   - **deferred**:
     - `resource:diagnostics`. Copilot gets its own `diagnose` command in Phase 2 and does not port the cc-rpi module, so this changes to adapted in Phase 2 when its destination exists.
     - `manifest:version`, which gets the cc-rpi version label 2.2.0 recorded with the decision.
   - **inapplicable**: `config:codex-marketplace` and `config:codex-package`.
3. Re-decide the 22 IDs that the 2026-11-14 intake deferred (`docs/decisions/2026-11-14-upstream-security-reference-intake.json`):
   - **adapted in Phase 3**: rpi-adopt, rpi-bootstrap, rpi-explore-release, rpi-pre-launch, rpi-release, rpi-remediate and rpi-validate; `rule:resource-lifecycle` (new Copilot instruction); `rule:supabase` (Copilot supabase instruction); `rule:rpi-details` (AGENTS.md template); `instruction:rule-map` (AGENTS.md template row); `skill:macos-rules` (one sentence of package guidance in the AGENTS.md template); `skill:git-workflow` (the worktree-removal sentence in rpi-implement and rpi-remediate).
   - **deferred**, reason "Copilot keeps its own implementation; cc-rpi repair series not ported": `resource:configuration-engine`, `resource:distribution-engine`, `resource:package-engine`.
   - **inapplicable**, reason "Copilot hook and gate already have the cc-rpi 2.1 semantics; cc-rpi-specific parser deltas not ported": `resource:policy-engine`, `resource:prepush-gate`, `hook:guard-bash`.
4. Repin the lock to `cec458a`. Refresh `upstream/snapshots`, `upstream/cc-rpi.inventory.json` and the crosswalk, as the 2026-11-14 intake did (commit `33bb1b4`). Keep each destination's bytes and hash unchanged in this phase. Rerun the checker with the decision file until it passes.
5. Add `.gitignore` exceptions so that this research report, the plan, its phase files and the decision file are tracked. Follow the existing pattern at `.gitignore:41-55`.
6. Write the Phase 1 entry in `docs/plans/2026-11-15-cc-rpi-2.2-sync-notes.md`.

## Acceptance

Automated:

- `uv run --locked python scripts/check-upstream.py --compare-source <clean cec458a> --lock upstream/cc-rpi.lock.json --inventory upstream/cc-rpi.inventory.json --decisions docs/decisions/2026-11-15-cc-rpi-2.2-sync-intake.json --check` exits 0.
- The default offline check exits 0.
- `bash scripts/verify-local.sh` passes all 10 checks.
- `tests/test_upstream.py` has one new case: the repinned lock blocks with the exact decision ID when a decision is removed.

Manual: none.

## Units

One unit; the files overlap.
