# Copilot RPI modernization implementation notes

## Authority and starting state

The owner authorized all five implementation phases, local integration into
`main`, task worktree cleanup, and a new blueprint release on 2026-09-28.
The task worktree is `/Users/juan/code/copilot-rpi-modernization` on
`task/copilot-blueprint-modernization`, based on Copilot remote `main` at
`b2a502a20fe935a776fbbf42ee5ab283ecb2ce44`. Its three Sutura workflow
commits were inspected and retained. The original checkout's untracked `.summon`
was not copied or modified. The pinned upstream source is cc-rpi
`aa3ea57fb26ae2e1e167acada4b769e073a417f4`.

## Deviations

### P1 snapshot lint scope

Plan said: run the exact Markdown lint command over active project Markdown.
Found: the immutable cc-rpi source snapshots have 66 formatting findings under
Copilot's Markdown rules. Chose: `.markdownlint-cli2.jsonc` excludes only
`upstream/snapshots/**`, while inventory hashes verify every original byte.
Why: reformatting source snapshots would break provenance, and inactive source
history is not product Markdown.

## Phase 1 acceptance

Phase 1 implementation was committed locally as `9d96b13` on
`task/copilot-blueprint-modernization`. It added 23 canonical skills, complete
upstream intake for 61 components and 156 catalog entries, a 40-error/55-rule
meaning crosswalk, the pinned development toolchain, and the sequential portable
gate. The intake inventory checks 76 original source/resource files and 36
upstream skill symlinks. The old canonical prompts remain as legacy inputs until
the Phase 2 migration.

Independent review found seven catalog/methodology issues, two intake schema and
path issues, and two link-checker coverage issues. All were repaired and
re-reviewed. The simplify pass checked reuse, quality and efficiency. It kept
the self-contained skill resources because each installed skill must resolve its
own references; it found no further behavior-preserving change worth adding.

The complete local gate passed on the Phase 1 committed tree: 25 Python tests,
count/version/prompt contracts, ShellCheck, Markdown lint (126 active files),
the offline upstream checker and 93 internal Markdown links. The explicit
maintainer comparison against cc-rpi at the pinned SHA also passed. This is
portable local evidence only; Copilot native discovery, permissions and
installation remain Phase 2-5 acceptance requirements.

## Phase 2 acceptance

Phase 2 rendered the pinned workflows as 23 Copilot skills and added three
bounded custom agents, five scoped instructions, repository guidance, and
explicit CLI, Agent Host, and Local profiles. The manifest owns 59 components.
The renderer validates inputs before writing, rejects collisions and unsupported
metadata, and emits a self-contained package for the Phase 3 lifecycle. The
active CLI self-render preserves owner guidance and declares three legacy prompt
files for Phase 3 retirement.

Independent reviews found and repaired agent delegation metadata, profile-kind
selection, duplicate names, malformed metadata diagnostics, missing active
surface checks, and root contract wording. Renderer tests cover deterministic
outputs, cross-profile isolation, and standalone package verification without
PyYAML or a sibling repository. The simplify review found no additional
behavior-preserving change.

The complete Phase 2 local gate passed on the staged candidate: 58 Python
tests, count/version/prompt contracts, renderer validation and generated-file
check, ShellCheck, Markdown lint over 188 active files, the offline upstream
checker, and 138 internal Markdown links. The managed root is 3,874 bytes;
active root plus repository Copilot instructions is 5,134 bytes, under the
8,192-byte limit. This is portable rendering evidence; live native discovery
and lifecycle ownership remain later acceptance requirements.

## Phase 3 acceptance

Phase 3 added a standalone standard-library lifecycle runtime to rendered
packages. It plans, applies, checks, rolls back and detaches project-local
Copilot components. Managed files and baselines live under `.rpi/copilot/`;
transaction journals live under `.rpi/local/copilot/`. Plans bind the package
receipt, target identity and observed bytes. Existing files need exact
historical template bytes and an explicit legacy source revision, or an
explicit reviewed `--adopt-exact` component selection, before ownership is
claimed. Legacy sync metadata alone remains an untrusted hint.

Independent review found and repaired inactive-setting diagnostics, active
MCP/hook path injection, JSONC comment and multi-key edits, hidden symlinked
and nested legacy surfaces, malformed manifests, and forged file/key ownership
records. A simplify review checked reuse, quality and efficiency. The native
capability currently available for explicit selection is `vscode-settings`;
hooks, MCP, schedulers and global configuration remain outside this lifecycle
selection. The active self-render and four lifecycle skills now point to the
rendered package runtime. The upstream lock records the adapted lifecycle and
configuration sources and all changed destination hashes.

The complete Phase 3 local gate passed on the staged candidate: 98 Python
tests, count/version/prompt contracts, renderer validation and generated-file
check, ShellCheck, Markdown lint over 188 active files, pinned upstream intake,
and 137 internal links. The fixture matrix uses real temporary Git repositories
and covers fresh/no-op installation, updates, conflict and stale-plan refusal,
ownership tampering, JSONC preservation, interrupted rollback, detach/re-adopt,
historical migration, symlinks, Unicode paths and cc-rpi state coexistence.
This is local lifecycle evidence; native Copilot loading is a Phase 5 gate.

## Phase 4 acceptance

Phase 4 added candidate-bound sequential verification and an opt-in pre-push
receipt gate. The renderer now includes their standalone Python runtime in an
adopter package. The native hook adapter is preview-only until explicitly
activated. Scheduled automation uses a bounded Copilot process, local locks,
sanitized atomic reports and direct standalone runtime entry points. The
remediation skill's bundled parser now checks the final disposition record.

Independent review found unsafe custom-hook parent symlinks, scheduled-job
lock and plist symlink paths, and a preview that depended on absent shell
wrappers. Red tests reproduced each issue before repair. A simplify pass
removed duplicated shell behavior in favor of the Python runner and retained
the standalone adapters needed in rendered packages.

The complete Phase 4 local gate passed on the staged candidate: 144 Python
tests and all 10 receipt checks, including schema, generated bytes, ShellCheck,
Markdown lint over 188 files, pinned upstream intake and 137 internal links.
The receipt is `.rpi/local/copilot/verification.json`. This is portable local
evidence; no native Copilot inference or scheduled service was activated.

## Phase 5 local preparation

The package initially kept its released version at 1.18.0 and placed the
proposed breaking changes under `Unreleased`. Compatibility, migration,
upstream intake and native-policy guides now describe the selected profiles,
ownership lifecycle, opt-in controls and recovery. The active guide and
scheduled-jobs methodology preserve still-valid design and operating guidance
while replacing obsolete prompt and Claude examples. Linux CI now runs the
same complete portable gate; its actual hosted result remains unobserved.

The future-intake checker compared the clean cc-rpi checkout at
`de1845596a346b9f30ac375a07a1338401c409eb` with the pinned snapshot and
reported no source differences. Synthetic tests prove changed and new items,
resource-link changes, dirty checkout refusal, SHA/digest-bound decisions and
a real no-op. An isolated Python 3.11.2 run passed all 165 tests. A disposable
Debian Linux clone with Node 24.21.0, uv 0.12.19, ShellCheck 0.9.0 and Python
3.14.7 passed the complete portable gate: 165 tests, all 10 checks and 179
internal links. The first read-only Linux mount could not run Git tests that
write objects; the writable clone resolved that environment limitation.

The owner then authorized isolated client setup, native inference and version
2.0.0. Copilot CLI 1.0.88 was installed under ignored task-local state; VS Code
was updated to 1.139.1 with bundled GitHub Copilot Chat 0.67.0. No scheduler,
cloud job or global Copilot CLI configuration was activated. The CLI harness
has 22 passing fake-process tests, which verify its controls rather than native
product behavior. Independent review found and repaired prompt-echo discovery,
prose-only denial, overwritten receipts, candidate identity gaps, process-group
cleanup and client event-shape mismatches.

On committed candidate `5942d6e`, both real Copilot CLI 1.0.88 entry points
passed. The `cli` receipt proves project skill discovery, a successful native
skill invocation before the marker answer, a renamed-skill negative control,
and unchanged product/remote bytes. The `cli-programmatic` receipt proves the
shipped runner's allowed report, bounded exit, linked native denied-write event
and unchanged denied file/remote. Native receipts are in ignored
`.rpi/local/copilot/native/`; they store no credential value. A separate
isolated CLI session resumed a stale handoff, read actual Git refs and rejected
its prior green receipt for the different candidate.

VS Code's Copilot Agent Host provider `copilotcli` loaded the rendered
`rpi-research` skill and bundled resource, reported the README marker with a
line citation, and failed to load that skill after it was renamed. A custom
research role exposed only read/search tools; the harmless denied-write file
remained unchanged. A delegated research subagent read a temporary repository
instruction nonce in a fresh session, used the role's read/search tools and
inherited the parent model. The temporary instruction was restored. The six
workflow fixtures were run in native Agent Host sessions and independently
scored. Four passed initially. Research omitted the explicit `rpi-assess`
handoff, and missing-review mislabeled a scenario marker as candidate identity.
The canonical skills were repaired and reapplied through the ownership engine.
An intermediate research retest still made an unsupported quality judgment;
the skill now requires literal observations and forbids quality labels.
Fresh Agent Host retests invoked each repaired skill successfully: research
stayed descriptive and named `rpi-assess`; missing-review used the inspected
fixture commit and blocked acceptance without reviewer evidence. The original
failure and the retests remain in ignored native evidence for review.
The pinned upstream intake records the two repaired destination hashes; its
source pin and snapshots are unchanged.

The initial VS Code UI observation used the Local extension host, so it is
optional compatibility evidence only. The computer-use native pipe then failed
repeatedly, including after a reset. The selected Agent Host UI, visual
discovery inventory and Local-to-Agent-Host handoff could not be inspected.
Native session state and `code agent ps` prove Agent Host execution, while the
visual acceptance step remains unobserved. The owner subsequently accepted
the specific native-session evidence substitution recorded below.

The ownership engine self-applied 31 exact canonical components in the task
worktree with zero file actions and conflicts; its `check` reported healthy.
The local `process-errors` extension and three unproven legacy prompts were
retained. The ownership manifest binds to the worktree path and is ignored by
Git; self-application must be repeated in the final integration checkout.

The retained pre-repair portable log shows 168 Python tests and all 10 checks;
the 174-test run reported during later CLI harness work has no retained passing
receipt, so it is not used as acceptance evidence. The `codex-simplify` reuse,
quality and efficiency pass found no further safe code reduction then. A full
rerun after the skill repairs found stale destination hashes in the upstream
lock; those two hashes were updated, and the standalone pinned-intake check
passed. Commit `5d1666d` then passed a saved complete portable gate: 174
Python tests, all 10 checks and 179 internal links, with unchanged candidate
identity in the receipt.

Native CLI requalification on `5d1666d` observed the automatic model return
the fixture marker without a native skill tool event. The harness correctly
blocked the run. A failing fake-client control modeled this gap when the prompt
did not explicitly request a skill tool call. The prompt now requests that call
before file reads; the focused fake test and a real diagnostic CLI run passed.
This later harness and note change invalidates
the `5d1666d` acceptance package. The repaired candidate still needs the full
portable gate and both native CLI entry points before Phase 5 acceptance.

The first full gate on the prompt repair failed one elapsed-time assertion:
fixture rendering and local Git setup exceeded the test's five-second total
bound, while the one-second native child timeout was recorded correctly. The
test now checks the blocked receipt independently of setup duration. A direct
one-second process test verifies process termination and that a descendant never
writes its delayed marker after process-group cleanup. Both focused tests pass;
the complete gate subsequently passed on commit `663685f` with 176 Python
tests, all 10 checks and 179 internal links. Python 3.11.16 passed the same
176 tests. A writable disposable Linux checkout from the exact commit passed
the portable gate with Node 24.21.0 and Python 3.14.7. Both required real
Copilot CLI 1.0.88 profiles passed on `663685f`; the programmatic receipt
includes a native denied-write event and unchanged denied file. Their receipts
are under ignored `.rpi/local/copilot/`.

Two fresh-context Wave B exploratory charters ran against `663685f` using
synthetic, cleaned-up fixtures. The lifecycle charter passed all eight
maneuvers, including repeated apply/detach, stale plans, interrupted rollback,
owner edits, separate processes, C-locale Unicode paths and false legacy
ownership. The automation charter attempted all eight maneuvers and found two
failures. A locally edited ignored green receipt could pass the optional
pre-push gate for an unverified newer fixture commit. A local hook and its
receipt cannot authenticate against an actor who can edit both; the owner
must review this explicit trust limit before release. `docs/native-policy.md`
now states it, and exact-commit remote CI remains the publication gate. The
other failure was actionable: if writing `.last-good` failed, the automation
runner left the current report changed despite returning failure. A red test
reproduced it. Independent review found the reversed write order could also
change `.last-good` when the current write failed. A second red test reproduced
that path. The runner now restores the prior recovery copy if the second
write fails, using a staged hard link so an out-of-space error does not need a
new data write during rollback. A third red/green test covers that case.
Independent re-review found no remaining scoped issue, and all 19 automation
tests pass. The complete gate remains pending on this new candidate.

## Phase 5 acceptance deviation and release preparation

The plan required visual Agent Host selection, discovery inventory and a
Local-to-Agent-Host handoff before release. The computer-use pipe repeatedly
failed or timed out, even after the console was unlocked. Several VS Code
windows were open, so further UI attempts would have disrupted the owner's
desktop. The owner explicitly accepted a substitution on 2026-09-29 and
instructed continuation of the release. Native Agent Host sessions with
provider `copilotcli` loaded the rendered skill and resource, rejected a
renamed skill, enforced the selected research role, passed the repaired
research and missing-review retests, and completed six independently scored
workflow fixtures. These observations qualify the native Agent Host behavior
for this release. The visual picker, inventory and UI handoff remain
unobserved; their behavior is not claimed as tested for this VS Code build.

The owner separately accepted the documented limit that a local actor can edit
both a pre-push hook and its receipt. Exact-commit GitHub CI remains the remote
publication check. The release preparation sets version 2.0.0 in the changelog
and package manifests; final candidate gates and publication outcomes must be
recorded from their actual runs.

The first versioned portable gate passed its tests, generated-output check,
ShellCheck, Markdown lint and internal links, then found that the pinned
destination hash for `templates/distribution.json` still described the prior
version. The destination hash was updated without changing the pinned upstream
source. A post-fix Wave B automation charter passed all eight maneuvers on the
unchanged runner source, including both report-write failure orders. Its
disposable fixture was removed. An independent release diff review found no
material issue, and the reuse, quality and efficiency simplify pass found no
safe further reduction in the version/documentation changes. The final
committed candidate still requires a complete gate and publication checks.
