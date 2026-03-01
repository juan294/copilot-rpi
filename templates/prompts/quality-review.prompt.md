---
mode: agent
description: "Review changed code for reuse, quality, and efficiency — then fix issues found"
---
Review all changed files for code reuse, code quality, and efficiency. Fix any issues found.

## Phase 1: Identify Changes

Run `git diff` (or `git diff HEAD` if there are staged changes) via #tool:terminal to see what changed. If there are no git changes, review the most recently modified files that were edited earlier in this conversation.

## Phase 2: Review for Three Concerns

Review the diff for each of the following. Check each concern thoroughly before moving to the next.

### Concern 1: Code Reuse

For each change:

1. Use #codebase to search for existing utilities and helpers that could replace newly written code. Check utility directories, shared modules, and files adjacent to the changed ones.
2. Flag any new function that duplicates existing functionality. Suggest the existing function to use instead.
3. Flag any inline logic that could use an existing utility — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards.

### Concern 2: Code Quality

Review the same changes for:

1. **Redundant state** — state that duplicates existing state, cached values that could be derived
2. **Parameter sprawl** — adding new parameters instead of generalizing or restructuring
3. **Copy-paste with slight variation** — near-duplicate code blocks that should be unified
4. **Leaky abstractions** — exposing internal details that should be encapsulated
5. **Stringly-typed code** — using raw strings where constants, enums, or branded types already exist

### Concern 3: Efficiency

Review the same changes for:

1. **Unnecessary work** — redundant computations, repeated file reads, duplicate API calls, N+1 patterns
2. **Missed concurrency** — independent operations run sequentially that could run in parallel
3. **Hot-path bloat** — new blocking work on startup or per-request/per-render paths
4. **Unnecessary existence checks** — pre-checking before operating (TOCTOU anti-pattern)
5. **Memory** — unbounded data structures, missing cleanup, event listener leaks
6. **Overly broad operations** — reading entire files when only a portion is needed

## Phase 3: Fix Issues

Fix each real issue directly. If a finding is a false positive or not worth addressing, skip it — don't argue with it.

When done, briefly summarize what was fixed (or confirm the code was already clean).

## Rules

- **This is interactive, not automatic.** Present significant findings to the user before applying fixes that change behavior. Cosmetic and clear-cut fixes (using existing utility, removing dead code) can be applied directly.
- **Don't over-fix.** Only address real issues in the changed code. Don't refactor surrounding code that wasn't part of the diff.
- **Run verification after fixes.** Run typecheck, lint, and tests after applying any fixes.
