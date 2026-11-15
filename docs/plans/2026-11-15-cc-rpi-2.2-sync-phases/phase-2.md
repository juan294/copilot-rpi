# Phase 2: authored hash, reserved path and `diagnose`

Parent: `docs/plans/2026-11-15-cc-rpi-2.2-sync.md`. Entry: Phase 1 accepted. TDD: write each failing test first.

## Changes

```text
@ render_record(manifest, profile, outputs, roots, preserve_ids) -> receipt
ctx: templates/scripts/rpi-distribution.py:415-426
pre: outputs carry component ids; skill sources live in templates/skills/<name>/SKILL.md
do:
  1. compute sha256 of the authored SKILL.md per skill or prompt component
  2. write authored_sha256 on that component's SKILL.md or .prompt.md record only
fx: receipt files[] gain an optional field; .rpi/copilot-render.json regenerated
risk: check-generated compares the tracked receipt; regenerate it in this phase
```

```text
@ make_plan(request) -> plan   (templates/scripts/rpi-lifecycle.py:353)
ctx: package_files :204-237, load_state :249-278, no-op filter :546-549
do:
  1. read authored_sha256 from the receipt record when present (validate 64 hex)
  2. copy it into the new manifest entry for that destination
  3. accept it in load_state when present and well-formed; reject when malformed
  4. ignore it in the no-op filter alongside status
fail: malformed authored_sha256 -> ValueError('invalid Copilot ownership entry')
```

```text
@ safe_relative(value) -> value   (templates/scripts/rpi-lifecycle.py:174-179)
do:
  1. lowercase the path for the reserved comparison
  2. refuse .rpi/project, .rpi/copilot and .rpi/local/copilot, and anything under them
fail: reserved -> ValueError('package cannot own project or Copilot state: ' + value)
```

```text
@ diagnose(target) -> report, exit 0
ctx: .rpi/copilot/manifest.json, baselines, .github/skills, .github/prompts, .rpi/project
do:
  1. read manifest; summarize profile, source_version, drift (modified, missing)
  2. list .rpi/project/*.md (skip dotfiles); lstat each, refuse non-regular files
  3. parse header (utf-8-sig, CRLF), lowercase names only, size <= 64 KiB
  4. compare written-against with authored_sha256[:12] for the installed skill copy
  5. emit one item per file with the fixed field set; never emit file text
br: unreadable manifest -> installation.status unreadable + check command, exit 0
```

Wiring:

- Add `diagnose` to the lifecycle parser (`templates/scripts/rpi-lifecycle.py:787-810`) with `--target` only.
- Add `diagnose` to the forwarding set in `templates/scripts/rpi-distribution.py:16` so it runs with the standard library alone.

Docs:

- Write `docs/project-overlay.md` for Copilot: contract, statuses table, limits and profile notes.
- Link it from `README.md` and `GUIDE.md`.
- Add one receipt-field sentence each to `docs/compatibility.md:25`, `docs/migrations/v2.md:29` and `templates/setup-checklist.md:23`.

Intake: add the `diagnose` destination and change `resource:diagnostics` to adapted, then update the lock destination hashes for the lifecycle and distribution engines.

## Tests (new, in `tests/test_lifecycle.py`, `tests/test_rendering.py` and a new `tests/test_diagnose.py`)

- The receipt carries `authored_sha256` for skill and prompt records only, and it equals the source `SKILL.md` hash.
- The manifest copies the field. Stripping it keeps `check` healthy, and the next real update records it again.
- A malformed `authored_sha256` is rejected.
- `.rpi/project/x.md` and `.RPI/Project/x.md` as package destinations are refused.
- Plan, apply, check, detach and rollback each leave a `.rpi/project` tree, including a symlink and a subdirectory, byte-identical.
- `diagnose` covers each case below, with exit code 0 and no file text in stdout:
  - **present**, for all three profiles;
  - **stale**: writing the printed `header_line` leads to `present`;
  - **inert**: an old skill copy without the section leads to `inert`; after the update, `present`;
  - **invalid**, for each cause: symlink, uppercase name, over 64 KiB, non-UTF-8, unknown skill, lifecycle skill name, directory named `*.md`, bad header;
  - **no installation**;
  - **unreadable manifest**;
  - **secret-marker overlay**: the marker never appears in output.
- Every item has the same field set.

## Acceptance

Automated:

- `uv run --locked python -m unittest discover -s tests` passes.
- `bash scripts/verify-local.sh` passes all 10 checks.

Manual: none.

## Units

- `[batch-eligible]` A: receipt and lifecycle changes, plus their tests.
- `[batch-eligible]` B: `docs/project-overlay.md` and its links.
- C, after A: `diagnose` (it needs A's manifest field), followed by the intake hashes.
