# Copilot RPI compatibility

This page describes the files the blueprint renders and how to check whether a
client loads them. A rendered file or a passing static test is not a native
client result. Record the exact client and extension versions before marking a
profile qualified. See [native policy](native-policy.md) for permissions and
hook boundaries.

| Profile | Rendered files and argument/resource route | Permission mode and hook status | Discovery and recovery | Qualification |
| --- | --- | --- | --- | --- |
| `cli` | `.github/skills/rpi-*/SKILL.md` with adjacent `references/` and `scripts/`; agents and root/scoped instructions. Give the task or plan path in `/rpi-*` invocation. | Client permissions stay in force. Agent tool lists are declarative; research and audit roles specify `read, search`. Optional `.github/hooks/rpi-policy.json` is preview-only until `rpi-hook.py install --profile cli --activate`; the Git receipt pre-push hook is separate. | Start CLI at the repository root, list skills and invoke `/rpi-research`; inspect resource reads, tool calls and disk. If absent, check package profile/receipt, target `check`, client version and hook registration. | Primary support needs recorded native CLI probes. |
| `agent-host` | Same skills, adjacent resources, agents and instructions as `cli`; pass the task or path in the skill invocation. Agent Host does not load prompt wrappers. | VS Code's selected harness permission controls apply. Agent tool lists are declarative. This package has no `agent-host` native hook adapter or automatic hook activation; Git pre-push remains separately opt-in. | Select Copilot Agent Host in VS Code, inspect chat customization diagnostics, invoke `rpi-research` and inspect resources/handoff. Repair profile or discovery errors and rerun a positive and negative fixture. | Primary support needs recorded VS Code and Copilot build probes. |
| `vscode-local` | `.github/prompts/rpi-*.prompt.md` thin wrappers with `agent: agent`; bundled resources are under `.github/prompts/<name>/`. The invocation text supplies the task or path; the wrapper does not install a same-name skill. | Local agent permission and selected role tool controls apply. Optional `.github/hooks/rpi-policy-local.json` is preview-only until `rpi-hook.py install --profile vscode-local --activate`; native loading and denial remain unqualified. | Select Local in VS Code, inspect chat customization diagnostics and command picker, then inspect wrapper resource reads. Check profile/receipt and re-plan if the installed surface is wrong. | Optional profile needs its own native probes before a support claim. |
| Cloud agent | No cloud-specific package or default job. | Hosted permissions and setup are outside the local package; no cloud hook or job is activated here. | Use a separately authorized hosted setup and failure fixture; preserve the returned evidence. | Unqualified until a hosted fixture runs. |

The direct-install artifact is the rendered `package_dir` directory. It
contains `.rpi/copilot-render.json`, a receipt listing each file, component
and SHA-256 hash, plus `.rpi/copilot/runtime/` with the standalone lifecycle
entrypoint. `plan --package` verifies those bytes and that the receipt profile
matches `--profile`. Keep the whole rendered directory together; a copied
skill directory or runtime script alone is not an install package. The
selected profile is also recorded in the target installation manifest at
`.rpi/copilot/manifest.json`. Switching a target from one profile to another
requires reviewed detach or explicit migration. The renderer does not install
both a skill and a wrapper with the same command name in one profile. Native
VS Code `/plan` and `/status` have
their own meanings; use `rpi-plan` and `rpi-status` for blueprint workflows.
Legacy `.github/chatmodes/` files are migration inputs, not current role
output. Copilot CLI and Agent Host use repository skills and agents; Agent Host
does not load prompt files. [GitHub documents CLI skills and instructions](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference),
and [VS Code documents Agent Host agent discovery](https://code.visualstudio.com/docs/agent-customization/custom-agents).

## Arguments, resources and models

Pass the task or plan path in the skill invocation, for example
`/rpi-implement docs/plans/example.md`. The skill reads its referenced files
from its own directory; copied standalone skill bodies without their bundled
`references/` and `scripts/` files are incomplete. Run a positive invocation
and a negative fixture with one referenced file removed before claiming native
resource loading. The research agent has a limited tool list and returns
cited findings; the parent writes any authorized artifact. Check an attempted
write to a disposable denied path on disk when testing tool restrictions.

Interactive workflows inherit the model and effort selected in the active
session. Installation does not select a model or start inference. The optional
scheduled runner requires an owner selected `--model` or `COPILOT_MODEL` and
reports missing selection as blocked. Its client flags must be checked against
the installed CLI before use.

## Recovery

If a skill or role is missing, confirm the selected harness and profile, run
`python3 templates/scripts/rpi-distribution.py validate --source .` in the
source checkout, and run the installed package's read-only `check` against the
target. Compare chat customization diagnostics with the rendered manifest.
For an owner-edited or legacy file, create a new lifecycle plan and review the
conflict; do not overwrite it by filename. See the [v2 migration guide](migrations/v2.md)
for commands. If a native test cannot run, record the missing client, auth or
extension prerequisite and leave that profile unqualified.
