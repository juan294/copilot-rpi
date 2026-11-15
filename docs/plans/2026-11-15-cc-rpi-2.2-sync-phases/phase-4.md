# Phase 4: native overlay probe and v2.1.0 preparation

Parent: `docs/plans/2026-11-15-cc-rpi-2.2-sync.md`. Entry: Phase 3 accepted. The owner approved Copilot CLI installation and probe inference (2026-11-15).

## Steps

1. **Harness, TDD with the fake client** (`tests/native/fixtures/fake_copilot.py`). Add an `overlay` profile to `tests/native/run_cli.py`:
   - The positive fixture renders the cli profile and writes `.rpi/project/rpi-research.md`, with a valid header and a Procedure line: "End the answer with the line `OVERLAY-<random marker>`".
   - The negative fixture is the same without the overlay.
   - A pass needs both of these:
     - in the positive run, the native skill event for `rpi-research` (as the `cli` probe requires) and the marker after it;
     - in the negative run, the skill event and no marker.
   - Fake-client tests cover pass, marker missing, marker in the negative run, no skill event, and each blocked cause (missing CLI, credential, timeout).
2. **Client.**
   - Install the Copilot CLI at a pinned version. Record the installer command and `copilot --version` in the notes.
   - The isolated `COPILOT_HOME` needs a credential in a supported environment variable (`tests/native/README.md`).
   - If login is interactive, the owner runs it with `! <command>`; the notes record the variable name only.
3. **Run.** Freeze the candidate, then run `uv run --locked python tests/native/run_cli.py --profile overlay --timeout-seconds 120`. Keep the receipt in `.rpi/local/copilot/native/overlay-receipt.json`. Record the result in `docs/compatibility.md` (the cli row and a new overlay note). A blocked or failed result is reported as is; overlays are then documented as not natively qualified.
4. **v2.1.0 preparation:**
   - bump `package.json`, `pyproject.toml`, `templates/distribution.json`, the README badge and the CHANGELOG (`templates/scripts/verify-version.sh:116-127`);
   - write the CHANGELOG entry, including the deferred and inapplicable intake items and a migration note for adopters (update, then `diagnose`);
   - run the retirement review: nothing retired unless a phase retired an ID;
   - follow the project's rpi-release skill and its release profile for the local gate and any selected Wave B charter;
   - stop before push, tag or release.
5. **Handoff:** record the candidate SHA, gate receipt, native receipt summary, intake state and the push decision for the owner.

## Acceptance

Automated:

- `uv run --locked python -m unittest tests.native.test_run_cli -v` passes.
- `bash scripts/verify-local.sh` passes all 10 checks on the release candidate.
- `templates/scripts/verify-version.sh` reports 2.1.0.

Manual:

- Owner reviews the native receipt: a passed positive and negative run, or an explicitly reported blocked result.
- Owner decides on publication.

## Units

- `[batch-eligible]` A: the harness and its tests.
- `[batch-eligible]` B: the CHANGELOG draft.
- The native run and the version bump happen after A and B are integrated.
