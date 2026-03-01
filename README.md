# copilot-rpi — GitHub Copilot Reference & Project Intelligence

[![CI](https://github.com/juan294/copilot-rpi/actions/workflows/markdown-lint.yml/badge.svg)](https://github.com/juan294/copilot-rpi/actions/workflows/markdown-lint.yml)
[![GitHub Release](https://img.shields.io/github/v/release/juan294/copilot-rpi)](https://github.com/juan294/copilot-rpi/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/juan294/copilot-rpi)
[![GitHub Copilot](https://img.shields.io/badge/Built%20for-GitHub%20Copilot-blue.svg)](https://docs.github.com/en/copilot)

A blueprint repository for setting up and running projects with [GitHub Copilot](https://docs.github.com/en/copilot). Contains the RPI (Research-Plan-Implement) methodology, a catalog of known agent errors, and operational rules learned from hundreds of real sessions.

![Chapa Badge](https://chapa.thecreativetoken.com/u/juan294/badge.svg)

---

## Requirements

- [GitHub Copilot](https://docs.github.com/en/copilot) with agent mode enabled in VS Code
- Git
- (Optional) [Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line) for headless mode and scheduled agents

## Quick Start

Clone the repository:

```bash
git clone https://github.com/juan294/copilot-rpi.git
```

Then tell Copilot in your target project:

> Go read the copilot-rpi repository and set up this project following all the best practices. Read the quick reference, error catalog, and methodology, then configure AGENTS.md, prompt files, and instructions for this project.

## Guide

New here? Read **[GUIDE.md](GUIDE.md)** — a human-readable walkthrough of the philosophy, the workflow, and every command. It covers everything you need to know without diving into every file.

## What's Inside

### Methodology (`methodology/`)

The full Research-Plan-Implement pattern adapted for GitHub Copilot, based on HumanLayer's opencode-rpi and ACE-FCA framework. Organized by topic (10 files, in reading order):

- **Philosophy** — Core tenets, error amplification principle, mental alignment
- **Context Engineering** — Compaction, context quality, Copilot configuration surfaces (7 config files)
- **Four Phases** — Research, Plan, Implement, Validate with detailed processes
- **Agent Design** — Documentarian rule, research catalog, quality review pattern, batch-eligible parallelism, autonomy principles
- **Pseudocode Notation** — Compact notation for writing implementation plans
- **Testing** — Automated-first verification hierarchy, TDD protocol
- **Push Accountability** — Post-push CI ownership, background polling, fix-and-repush cycle
- **CI & Guardrails** — Pre-commit hooks, CI workflows, development guardrails
- **Scheduled Agents** — Recurring quality agents on cron/launchd via `copilot -p`
- **Error & Success Logging** — Framework for systematic improvement

### Known Error Patterns (`patterns/`)

A catalog of 17 recurring agent errors documented from real sessions. Each entry includes the symptom, root cause, correct approach, and what to avoid:

- Git operations (pre-commit hooks, push rejections, worktrees)
- GitHub CLI (`gh` field names, CI status checking)
- Node.js/TypeScript (ESM shebangs, Buffer vs string)
- CI & workflow (push-and-forget, skipping TDD, suggesting manual steps)
- **Copilot-specific** (missing frontmatter, `${input:var}` syntax, instruction globs, chatmode directory, CLI auth)

### Examples (`examples/`)

Sample documents illustrating the methodology in practice — a research document, implementation plan with phase files, error/success log entries, pseudocode notation examples, and end-to-end workflow walkthroughs.

### Templates (`templates/`)

Ready-to-use starting points for new projects:

- **AGENTS.md template** — Cross-tool instruction file with all operational rules
- **README header template** — Standard project README structure with badges
- **VS Code settings template** — `.vscode/settings.json` for Copilot configuration
- **MCP config template** — `.vscode/mcp.json` for external tool access
- **Setup checklist** — Step-by-step guide including prompt files, instructions, chatmodes, CI, and hooks
- **Prompt files** — `/bootstrap`, `/adopt`, `/research`, `/plan`, `/implement`, `/validate`, `/quality-review`, `/describe-pr`, `/pre-launch`
- **Path-specific instructions** — Auto-loaded rules for tests, APIs, and migrations
- **Chat modes** — RPI Research (documentarian), RPI Planner (interactive planning), RPI Auditor (validation)

## Copilot-Specific Features

This blueprint takes advantage of capabilities unique to GitHub Copilot:

| Feature | How It's Used |
|---------|--------------|
| **`.github/prompts/*.prompt.md`** | RPI workflow commands invoked with `/` in chat |
| **`.github/instructions/*.instructions.md`** | Domain rules auto-loaded by file glob (`applyTo`) |
| **`.github/chatmodes/*.chatmode.md`** | Behavioral constraints (documentarian rule) enforced at session level |
| **`copilot -p "prompt"`** | Headless CLI for scheduled agents and parallel research |
| **`@copilot` cloud agent** | Async implementation via GitHub Issues |
| **`#codebase` / `#file:`** | Context references in chat |

## Relationship to cc-rpi

This repository is the GitHub Copilot counterpart to [cc-rpi](https://github.com/juan294/cc-rpi) (Claude Code). Both share the same RPI methodology and philosophy — ~60% of the content is identical. The differences are in tool-specific configuration:

| | cc-rpi | copilot-rpi |
|--|--------|-------------|
| **Primary tool** | Claude Code | GitHub Copilot |
| **Instruction file** | `CLAUDE.md` | `AGENTS.md` (cross-tool) |
| **Commands** | `.claude/commands/*.md` | `.github/prompts/*.prompt.md` |
| **Domain rules** | `.claude/skills/` | `.github/instructions/*.instructions.md` |
| **Personas** | (per-prompt injection) | `.github/chatmodes/*.chatmode.md` |
| **Settings** | `.claude/settings.json` | `.vscode/settings.json` + `.vscode/mcp.json` |
| **Parallelism** | Task tool + Agent Teams | `copilot -p` + `@copilot` cloud agent |
| **Headless mode** | `claude -p` | `copilot -p` |

## Adding New Patterns

When you discover a new recurring error or best practice:

1. Add it to `patterns/agent-errors.md` (detailed entry with symptom/root cause/solution)
2. Add a one-liner to `patterns/quick-reference.md`
3. Keep entries generic — no project-specific references

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting changes, adding error patterns, and writing style.

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

For security issues, see [SECURITY.md](SECURITY.md). For a history of changes, see [CHANGELOG.md](CHANGELOG.md).

## Credits

- [HumanLayer](https://humanlayer.dev/) — ACE-FCA framework and opencode-rpi implementation
- Adapted for GitHub Copilot's native capabilities (AGENTS.md, prompt files, path-specific instructions, chat modes)

## License

[MIT](LICENSE)
