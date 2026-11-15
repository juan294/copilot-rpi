# Phase 3: workflow text

Parent: `docs/plans/2026-11-15-cc-rpi-2.2-sync.md`. Entry: Phase 2 accepted, so the `diagnose` command exists.

The source hunks are the cc-rpi diff `aa3ea57..cec458a` for each file. Use `git -C <cc-rpi> diff aa3ea57 cec458a -- <path>`. On 2026-11-15, `git apply --check` showed which hunks apply cleanly to copilot `087fab7`. Port the rest by hand and keep the Copilot-specific text.

## Changes

1. **Overlay section in the 16 workflow skills.** Use cc-rpi's text unchanged. Insert it before each skill's first `##` heading:

   | Skill | First `##` heading |
   | --- | --- |
   | rpi-assess | `:13` |
   | rpi-brainstorm | `:13` |
   | rpi-describe-pr | `:25` |
   | rpi-explore-release | `:23` |
   | rpi-fix-ci | `:13` |
   | rpi-implement | `:18` |
   | rpi-plan | `:66` |
   | rpi-pre-launch | `:12` |
   | rpi-release | `:15` |
   | rpi-remediate | `:15` |
   | rpi-research | `:22` |
   | rpi-tool-design | `:14` |
   | rpi-triage | `:15` |
   | rpi-update-docs | `:13` |
   | rpi-validate | `:58` |

   rpi-status has no `##` heading: put the section after the H1 at `:6`, then add `## Project orientation` above the existing body at `:8`. The four lifecycle skills get no section.
2. **Release severities (clean hunks):**
   - rpi-explore-release (description `:3`, selection paragraph `:23`, S1-S4 table `:112`, block list `:115-120`, rule bullets `:130`, `:135`);
   - rpi-release (`:41-63`);
   - rpi-remediate (`:3`, `:11`, `:99`, `:336`);
   - rpi-bootstrap (`:59-62`).

   By hand: rpi-adopt (`:70-71`, context differs at `:72`) and rpi-pre-launch (`:326-327`, `:339-340`; keep the Copilot wording at `:336`).

   Also update the four skill copies of `references/e2e-pro-playbook.md` (adopt, bootstrap, release, explore-release) with the cc-rpi playbook diff. Each copy was identical to the `aa3ea57` playbook on 2026-11-15. Reconcile the top-level `templates/e2e-pro-playbook-template.md` by hand, because it already differs.
3. **Stock rules:**
   - rpi-implement after `:61-62`: commit the notes with the phase and cite plans by file name;
   - rpi-triage after `:36` (an older report from a failed run counts as an agent failure) and after `:389` (an observability gap is YELLOW);
   - rpi-validate after `:29`: check the resource-lifecycle disposition;
   - rpi-status after `:29`: report `project_overlays` from `diagnose`, and replace the "when installed" fallback at `:13-14` with the real command.
4. **Resource-lifecycle family:**
   - a new `templates/github/instructions/resource-lifecycle.instructions.md.template`, short like the existing five (`templates/github/instructions/supabase.instructions.md.template`), with `applyTo: "**/Dockerfile*,**/compose*.yml,**/compose*.yaml,**/docker-compose*,supabase/**"`, no braces;
   - a component next to the other instructions in `templates/distribution.json`;
   - the supabase instruction gains a lifecycle-first sentence at `:10`;
   - `templates/AGENTS.md.template` gains one lifecycle sentence and one proportional-release sentence (near `:11`);
   - the 12 `references/handoff.md` copies gain the resource-disposition bullet after `:19`;
   - rpi-implement (`:74`) and rpi-remediate (`:252-254`) gain the worktree-removal sentence. rpi-remediate's reference to a git-workflow skill that does not exist is replaced with that sentence.
5. **Package guidance:** one sentence in `templates/AGENTS.md.template` near `:15`. Verify package names and publishers against official documentation; never run a placeholder install.
6. **Consumers:**
   - `tests/test_native_templates.py:59-78`: add resource-lifecycle to the instruction map with its required clauses;
   - the root-size budget test `:81-91` must still pass (3874 of 8192 bytes on 2026-11-15);
   - `GUIDE.md` instruction count from 5 to 6 (`templates/scripts/verify-counts.sh:90`);
   - `tests/test_workflow_contracts.py:46-71`: the required clauses still present; descriptions within 1024 characters (`templates/scripts/rpi-distribution.py:109`).
7. Regenerate the self-application (`.github/` and the receipt) with the repository's render command, and confirm `check-generated` passes.
8. **Intake:** update the destination hashes and adaptation notes for every Phase 3 destination named in the Phase 1 decisions.

## Acceptance

Automated:

- `bash scripts/verify-local.sh` passes all 10 checks.
- `grep -c '^## Project overlay' templates/skills/rpi-{assess,brainstorm,describe-pr,explore-release,fix-ci,implement,plan,pre-launch,release,remediate,research,status,tool-design,triage,update-docs,validate}/SKILL.md` gives 1 for each file.
- The same grep gives 0 for adopt, bootstrap, detach and update.
- `python3 templates/scripts/rpi-distribution.py render` for each of the three profiles into scratch directories shows the overlay section in the skill copies, and, for `vscode-local`, in the wrapper bodies.

Manual: none.

## Units

- `[batch-eligible]` A: the overlay section in the 16 skills.
- `[batch-eligible]` B: release severities and playbook copies, in different files from A's insertions.
- `[batch-eligible]` C: the instruction, the AGENTS template and the handoff copies.

These touch the same skill files where they overlap, for example rpi-release in both A and B. Run A and B in one worktree in sequence, and C in parallel. Then do the stock rules, consumers, regeneration and intake as the integration owner.
