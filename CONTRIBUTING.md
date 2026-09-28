# Contributing to copilot-rpi

Thank you for your interest in contributing! This project improves through community feedback and contributions.

## How to Contribute

### Reporting Issues

- Use the [issue tracker](https://github.com/juan294/copilot-rpi/issues) to report bugs or suggest improvements.
- Check existing issues before creating a new one.
- Use the provided issue templates when available.

### Submitting Changes

1. Fork the repository.
2. Create a local task worktree or temporary branch from `main`.
3. Make your changes following the guidelines below.
4. Commit with a clear message describing what and why.
5. Integrate completed work into local `main` after review and verification. A maintainer publishes only with explicit authorization. External contributors may propose a pull request; agents do not publish working branches for experiments.

### What We're Looking For

- **New error patterns** — If you've encountered a recurring agent mistake not in `patterns/agent-errors.md`, document it with the symptom, root cause, correct approach, and what to avoid.
- **Methodology improvements** — Refinements to the RPI workflow based on real-world usage.
- **Template enhancements** — Better defaults, missing Copilot surfaces, or improved canonical skills and resources.
- **Documentation fixes** — Typos, unclear wording, broken links.

### Writing Guidelines

- Keep entries generic — no project-specific references.
- Follow the existing format and structure of each file.
- Use plain, direct language. Avoid filler words.
- When adding error patterns, include a one-liner in `patterns/quick-reference.md` alongside the detailed entry in `patterns/agent-errors.md`.

### Retiring a Rule or Error

The corpus has an intake path — "New error patterns" above — but without an exit path it only ever grows. This section is the exit path.

A rule or error is a retirement candidate only on one of three grounds:

1. **Superseded** — another rule covers it completely; name the successor.
2. **Tool-enforced** — CI, a git hook, or a `.github/instructions/` glob now catches it mechanically; the rule becomes an annotation on the enforcement rather than prose.
3. **Merged** — folded into a broader rule; name the absorbing rule.

Rules that state an environment fact or an exact command are NOT retirement candidates on capability grounds. Model improvement alone never proves an error fixed or justifies retirement.

Retirement procedure:

1. Validate the ground — confirm one of the three above applies, stated in one sentence.
2. Find every inbound reference — `patterns/quick-reference.md`, `patterns/agent-errors.md`, `templates/skills/`, `templates/github/`, `.github/skills/`, `.github/agents/`, `.github/instructions/`, selected Local prompt wrappers, `methodology/`, `AGENTS.md`, and `GUIDE.md`. **Blocking condition:** if an active inbound reference remains, stop and fix it before continuing.
3. Write the ledger entry below: number, release, ground, replacement.
4. The number is permanently retired and never reused.

Every release runs a retirement review — "what came out this cycle" is asked every time, even when the answer is "nothing."

Review upstream changes through [the pinned intake procedure](docs/upstream-sync.md).
Keep Copilot catalog IDs stable even when an upstream cc-rpi item has the same
meaning. Treat skill resources, renderer manifests and lifecycle tests as one
contract when changing distribution. Run `bash scripts/verify-local.sh` on the
final candidate; client discovery and hook behavior need separate native
evidence before a support claim.

#### Retirement Ledger

| Rule | Retired in | Ground | Replacement |
|------|------------|--------|-------------|
| —    | —          | —      | No retirements yet |

### Markdown Style

- Use ATX-style headings (`#`, `##`, `###`).
- One sentence per line where practical (aids diffs).
- Use fenced code blocks with language identifiers.
- Keep lines under 120 characters where possible.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards.

## Questions?

Open an issue or start a discussion. We're happy to help.
