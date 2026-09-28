# copilot-rpi: RPI blueprint for GitHub Copilot

[![CI](https://github.com/juan294/copilot-rpi/actions/workflows/markdown-lint.yml/badge.svg)](https://github.com/juan294/copilot-rpi/actions/workflows/markdown-lint.yml)
[![GitHub Release](https://img.shields.io/github/v/release/juan294/copilot-rpi)](https://github.com/juan294/copilot-rpi/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Copilot RPI is a standalone, repository-installed blueprint for Research,
Plan, Implement and Validate. It provides 22 canonical RPI skills plus one
local maintenance skill, three
specialist agents, five scoped instruction templates, an ownership-aware
installer, and catalogs of 40 known agent errors and 55 operational rules.
The source lives in `templates/`; rendered files are installed in a target
repository. Native client qualification is recorded separately from static
validation in [compatibility](docs/compatibility.md).

## Start with a reviewed install

Requirements: Git and Python 3.11+ for the standalone installer, plus the
selected GitHub Copilot client. Clone this repository and choose `cli` for
Copilot CLI, `agent-host` for VS Code Copilot Agent Host, or `vscode-local` for
the optional Local compatibility profile. The package renders into an empty
staging directory. The lifecycle engine then previews and applies changes to
your project; it preserves unknown and customized files.

```bash
git clone https://github.com/juan294/copilot-rpi.git
python3 "$source_dir/templates/scripts/rpi-distribution.py" render \
  --source "$source_dir" --profile cli --target "$package_dir"
python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" plan \
  --package "$package_dir" --target "$project_dir" --profile cli \
  --output "$plan_file"
```

Set `source_dir`, `package_dir`, `project_dir` and `plan_file` to real absolute
paths. Review the plan's source, actions, capabilities and ownership conflicts
before applying it. Continue with the exact apply/check commands in the
[setup checklist](templates/setup-checklist.md). Existing v1 installations
should follow the [migration guide](docs/migrations/v2.md); do not remove
legacy prompts by filename.

## What the package installs

| Surface | Purpose |
| --- | --- |
| `.github/skills/rpi-*/SKILL.md` and bundled resources | Canonical workflows for CLI and Agent Host |
| `.github/agents/*.agent.md` | Research, planning and audit roles with scoped tools |
| `AGENTS.md`, `.github/copilot-instructions.md` | Short repository guidance |
| `.github/instructions/*.instructions.md` | Rules selected by path and task |
| `.github/prompts/rpi-*.prompt.md` | Thin wrappers only in the `vscode-local` profile |
| `.rpi/copilot/` | Per-project ownership manifest and standalone runtime |

Use `/rpi-research`, `/rpi-plan`, `/rpi-implement` and `/rpi-validate` in a
qualified client. Native `/plan` and `/status` are distinct commands. The
[guide](GUIDE.md) explains the workflow; [methodology](methodology/README.md)
contains the full process. [Examples](examples/README.md) show its artifacts.

The package does not activate hooks, schedulers, MCP servers, cloud jobs or
global Copilot settings. Optional controls and their proof requirements are
documented in [native policy](docs/native-policy.md). Maintainers use the
[upstream intake procedure](docs/upstream-sync.md) to review cc-rpi changes
without creating a runtime dependency on cc-rpi.

## Develop and verify this blueprint

Install repository development dependencies with `uv sync --locked` and
`npm ci`, then run `bash scripts/verify-local.sh`. The gate runs sequential
tests, schema and generated-output checks, ShellCheck, Markdown lint, offline
upstream provenance and link validation. It writes a candidate-bound receipt
under ignored `.rpi/local/copilot/`. A static pass does not prove a Copilot
client discovered or enforced a rule. See [native qualification](tests/native/README.md)
for the separate client procedures.

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing workflow contracts,
catalog IDs or distribution behavior. [CHANGELOG.md](CHANGELOG.md) records
released changes and the proposed breaking migration in Unreleased. Security
reports follow [SECURITY.md](SECURITY.md). The project uses the [MIT license](LICENSE).

The methodology originated in [HumanLayer's RPI and ACE-FCA work](https://humanlayer.dev/).
Copilot RPI adapts it to GitHub Copilot while tracking reviewed cc-rpi source
in an explicit local lock.
