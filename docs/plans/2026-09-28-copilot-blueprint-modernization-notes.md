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
