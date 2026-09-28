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

The current package keeps its released version at 1.18.0 and places the
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
a real no-op. The minimum Python and disposable Linux gates remain to run.

The CLI native harness has 14 passing fake-process tests. Independent review
found and repaired prompt-echo discovery, prose-only denial, overwritten
receipts and candidate identity gaps. It preserves separate profile receipts
and fails closed on an unrecognized native denial event. This evidence does not
qualify the actual Copilot CLI. The installed VS Code app is 1.137.0, but its
extension inventory has no GitHub Copilot extension, and no `copilot` executable
is on PATH. The requested isolated setup, inference and release-version
decisions remain pending. No native inference, global install, cloud job or
scheduled service ran.

The ownership engine self-applied 31 exact canonical components in the task
worktree with zero file actions and conflicts; its `check` reported healthy.
The local `process-errors` extension and three unproven legacy prompts were
retained. The ownership manifest binds to the worktree path and is ignored by
Git; self-application must be repeated in the final integration checkout.

The complete portable gate passed on the Phase 5 local preparation: 165 Python
tests and all 10 checks, including catalog/version contracts, rendered bytes,
ShellCheck, Markdown lint over 193 files, pinned upstream intake and 179 local
links. The `codex-simplify` reuse, quality and efficiency pass found no further
safe code reduction in the changed scope. This is a local preparation gate;
Phase 5 native primary acceptance and release remain open.
