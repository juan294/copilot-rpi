# Contributing to copilot-rpi

Thank you for your interest in contributing! This project improves through community feedback and contributions.

## How to Contribute

### Reporting Issues

- Use the [issue tracker](https://github.com/juan294/copilot-rpi/issues) to report bugs or suggest improvements.
- Check existing issues before creating a new one.
- Use the provided issue templates when available.

### Submitting Changes

1. Fork the repository.
2. Create a feature branch from `main` (`git checkout -b feature/your-change`).
3. Make your changes following the guidelines below.
4. Commit with a clear message describing what and why.
5. Open a pull request against `main`.

### What We're Looking For

- **New error patterns** — If you've encountered a recurring agent mistake not in `patterns/agent-errors.md`, document it with the symptom, root cause, correct approach, and what to avoid.
- **Methodology improvements** — Refinements to the RPI workflow based on real-world usage.
- **Template enhancements** — Better defaults, missing configuration surfaces, or improved prompt files.
- **Documentation fixes** — Typos, unclear wording, broken links.

### Writing Guidelines

- Keep entries generic — no project-specific references.
- Follow the existing format and structure of each file.
- Use plain, direct language. Avoid filler words.
- When adding error patterns, include a one-liner in `patterns/quick-reference.md` alongside the detailed entry in `patterns/agent-errors.md`.

### Retiring a Rule or Error

The corpus has an intake path — "New error patterns" above — but without an exit path it only ever grows. This section is the exit path.

A rule or error is a retirement candidate only on one of four grounds:

1. **Superseded** — another rule covers it completely; name the successor.
2. **Tool-enforced** — CI, a git hook, or a `.github/instructions/` glob now catches it mechanically; the rule becomes an annotation on the enforcement rather than prose.
3. **Model-native** — current frontier models handle it by judgment, and the rule states no environment fact the model cannot observe.
4. **Merged** — folded into a broader rule; name the absorbing rule.

Rules that state an environment fact or an exact command are NOT retirement candidates on capability grounds. Model improvement does not make a CLI flag or a frontmatter key knowable.

Retirement procedure:

1. Validate the ground — confirm one of the four above applies, stated in one sentence.
2. Find every inbound reference — `patterns/quick-reference.md`, `patterns/agent-errors.md`, `templates/prompts/`, `.github/prompts/`, `templates/github/instructions/`, `templates/github/chatmodes/`, `methodology/`, `AGENTS.md`, and `GUIDE.md`. **Blocking condition:** if any inbound reference remains, stop and fix the references before continuing.
3. Write the ledger entry below: number, release, ground, replacement.
4. The number is permanently retired and never reused.

Every release runs a retirement review — "what came out this cycle" is asked every time, even when the answer is "nothing."

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
