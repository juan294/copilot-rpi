# cc-rpi and Copilot RPI: current state and native capability research

Date: 2026-09-28. Scope: local repository research and current primary-source Copilot documentation. This report describes observed behavior; the separate plan makes adaptation decisions. No product implementation, pull, push, release, scheduler execution, or native inference was performed.

## Baselines and direct answer

| Repository | Branch and observed commit | Version evidence | Working state |
| --- | --- | --- | --- |
| `/Users/juan/code/cc-rpi` | `main`, `aa3ea57fb26ae2e1e167acada4b769e073a417f4` | Source manifest 2.1.0; latest published GitHub release v2.0.2 | Clean |
| `/Users/juan/code/copilot-rpi` | `main`, `56efd8e1fe242054123761f92a74a0ae86d13eca` | v1.18.0, dated 2026-07-29 | Untracked `.summon`, preserved |
| Copilot remote `main` | `b2a502a20fe935a776fbbf42ee5ab283ecb2ce44` | Three commits beyond local | Only `.github/workflows/sutura.yml` differs |

Copilot RPI's last explicit synchronization imported generic cc-rpi changes from v1.25.0 through v1.28.2. Its current product remains a prompt/chatmode blueprint. cc-rpi subsequently added v1.29 agent-interface work and the v2 portable skills, lifecycle, policy, verification, and workflow contracts. Thus a pull of Copilot's three remote commits would not incorporate the missing blueprint changes. Evidence: `CHANGELOG.md:9`, `CHANGELOG.md:11`, and cc-rpi `CHANGELOG.md:9`, `templates/distribution.json:3`, `docs/migrations/v2.md:10`.

Git observations used `git status --short --branch`, `git rev-parse HEAD origin/main`, `git log HEAD..origin/main --oneline`, and `git diff --stat HEAD origin/main`. Live read-only ref/release requests confirmed both remote identities and publication state: [cc-rpi main](https://api.github.com/repos/juan294/cc-rpi/git/ref/heads/main), [cc-rpi latest release](https://github.com/juan294/cc-rpi/releases/tag/v2.0.2), [Copilot v1.18.0](https://github.com/juan294/copilot-rpi/releases/tag/v1.18.0). The cc-rpi release lookup used the GitHub connector after shell approval policy rejected that read. No remote state was changed.

Repository citations below use paths relative to Copilot RPI unless prefixed `cc-rpi/`, which means the sibling `/Users/juan/code/cc-rpi` at the recorded SHA. Line numbers describe these baselines, not future edits.

## R01: Product layout and synchronization

Copilot has 20 canonical prompts, three active prompts, five domain instruction templates, three legacy chatmodes, two VS Code configuration templates, and seven shell scripts. `git ls-files` contains no skills, `.agent.md` profiles, distribution manifest, ownership engine, test directory, or hook configuration. Its onboarding copies prompts, instructions and chatmodes (`AGENTS.md:15`, `AGENTS.md:24`, `templates/setup-checklist.md:39`). Active prompts are `process-errors`, `remediate`, and `triage`; only counterparts are compared for drift (`templates/scripts/verify-prompts.sh:120`).

cc-rpi's manifest describes 20 workflows, 12 domain skills, one helper, six rules, one instruction, two hooks, four configuration components and 15 resources. The source validator counts 61 components and 339 rendered files. Sources live under `templates/skills`, with resources declared in `templates/distribution.json`; native metadata belongs to adapter files. Supported harnesses are explicitly Claude and Codex, not Copilot (`cc-rpi/templates/distribution.json:7`, `cc-rpi/templates/scripts/rpi-distribution.py:194`, `cc-rpi/templates/scripts/rpi-distribution.py:280`).

Copilot update behavior uses `.github/copilot-rpi-sync.json.lastSyncCommit`, replaces differing canonical prompts/chatmodes, preserves custom-only files, merges selected AGENTS headings, preserves instruction globs and adds missing settings. Metadata records a commit/date/version and instruction names, not per-file ownership baselines (`templates/prompts/update.prompt.md:21`, `:43`, `:55`, `:65`, `:83`, `:107`). Detach uses separate filename, heading and settings lists. Its three instruction names and settings list differ from the updater's five instruction families and current settings template (`templates/prompts/detach.prompt.md:53`, `:85`, `templates/vscode-settings.json.template:1`).

cc-rpi lifecycle behavior uses content-addressed baselines, native capability distinctions and recoverable transactions. An existing destination without proven ownership produces a conflict; removal preserves modified content. Interrupted transactions disclose rollback commands, whose implementation checks current bytes and newer journals (`cc-rpi/templates/scripts/rpi-lifecycle.py:532`, `:1114`, `cc-rpi/docs/migrations/v2.md:40`, `:72`). Legacy sync metadata alone is not ownership proof.

## R02: Workflow and methodology evolution

| Concern | Copilot baseline | Current cc-rpi behavior |
| --- | --- | --- |
| Research | Descriptive, cited, complete reads; one research artifact (`templates/prompts/research.prompt.md:9`) | Separate research/assessment; observed recovery paths, source provenance and delegated coverage gaps (`cc-rpi/templates/skills/rpi-research/SKILL.md:8`) |
| Planning | Phases, pseudocode and criteria; independent phases may use CLI processes or remote issue delegation (`templates/prompts/plan.prompt.md:11`, `:26`) | Explicit stuck-state recovery tests, searched consumer/writer coverage, independent units inside sequential acceptance phases (`cc-rpi/templates/skills/rpi-plan/SKILL.md:30`) |
| Implementation | Self-review, verification, separate quality pass and stop (`templates/prompts/implement.prompt.md:13`) | Independent review, repair, simplify, full local gate and durable handoff; bounded ownership and worker count (`cc-rpi/templates/skills/rpi-implement/SKILL.md:24`) |
| Validation | Plan and deviation criteria (`templates/prompts/validate.prompt.md:11`) | Also checks real owned-code tests, falsifiable assertions, recovery and consumer coverage (`cc-rpi/templates/skills/rpi-validate/SKILL.md:27`) |
| Findings | Remediation creates external issues, waves of push/PR/merge, strategic issue-only results (`templates/prompts/remediate.prompt.md:23`, `:91`, `:184`) | Validated findings retain dispositions; local completion precedes separately authorized publication (`cc-rpi/templates/rules/rpi-details.md:64`) |
| Models | Opus/Sonnet/Haiku prose tiers (`templates/prompts/research.prompt.md:5`, `patterns/quick-reference.md:110`) | Session model/effort inheritance; cost claims need measured outcome and rework (`cc-rpi/methodology/cost-monitoring.md:8`) |
| Agent interfaces | No separate tool-design workflow in tracked prompt inventory | Conditional tool-design workflow, role-play transcripts, recovery errors, seed evaluations (`cc-rpi/templates/skills/rpi-tool-design/SKILL.md:14`, `:29`) |

Copilot already includes eight pre-launch audit domains, regression-risk fields, E2E Pro Wave A candidate identity and tag-last ordering. These are existing assets, not missing capabilities (`templates/prompts/pre-launch.prompt.md:42`, `:125`, `CHANGELOG.md:43`, `templates/setup-checklist.md:201`).

## R03: Publication, policy and evidence boundaries

Copilot still describes preview verification, fix-and-repush loops, batch working-branch publication, automatic repository-setting changes and force cleanup (`patterns/quick-reference.md:20`, `:44`, `:76`, `:98`, `:106`). Triage has an approval stop followed by publication/retry/Dependabot merge behavior (`templates/prompts/triage.prompt.md:213`, `:277`, `:293`).

cc-rpi 2.1 replaced the original v2 shell allowlist with a narrow destructive-operation denylist. Ordinary operations pass to native permissions; this is supplemental protection, not a complete shell security boundary or publication authorization mechanism. The optional candidate-receipt gate moved to Git pre-push and is not silently installed (`cc-rpi/docs/native-policy.md:3`, `:85`, `:161`, `:226`). Historical v2.0 publication-trust files are not the current source design (`cc-rpi/CHANGELOG.md:132`).

The verifier records a running/non-success state before checks, aggregates sequential exits and checks candidate/runtime identity before and after execution. It distinguishes portable checks from separately required database/native acceptance (`cc-rpi/templates/scripts/rpi-verify.py:163`). Handoffs bind authority, findings, decisions and results to exact state, and require revalidation on resume (`cc-rpi/templates/references/handoff.md:8`).

## R04: Automation and native configuration

Despite Copilot branding, the scheduled updater invokes `CLAUDE_BIN` and `claude`; morning triage also uses Claude-specific arguments. The shared library provides `preflight_claude` with an inference probe. Morning triage's embedded prompt authorizes fixes, pushes and retries automatically (`templates/scripts/copilot-rpi-update-agent.sh:87`, `:108`, `:146`; `templates/scripts/morning-triage.sh:97`, `:179`, `:203`; `templates/scripts/agents/lib/agent-utils.sh:66`). These scripts were inspected, not executed.

Current settings include experimental thinking-tool behavior and agent task flags. MCP uses a VS Code `servers` object and `${input:apiKey}` without an input declaration (`templates/vscode-settings.json.template:1`, `templates/vscode-mcp.json.template:1`). Chatmodes use historical `codebase`, `file`, `githubRepo`, and auditor `terminal` tools (`templates/github/chatmodes/rpi-research.chatmode.md:1`, `templates/github/chatmodes/rpi-auditor.chatmode.md:1`). Native discovery and enforcement were not measured.

## R05: Existing checks and observed results

All following Copilot checks passed at `56efd8e1fe242054123761f92a74a0ae86d13eca`, before research/plan files were added:

| Check | Observed result |
| --- | --- |
| `bash templates/scripts/verify-counts.sh` | 40 errors, 55 rules, five instruction templates |
| `bash templates/scripts/verify-version.sh` | v1.18.0 consistency |
| `bash templates/scripts/verify-prompts.sh` | 23 prompt files including active copies, five instruction files, three chatmodes; drift/emoji checks pass |
| `shellcheck --severity=warning templates/scripts/*.sh templates/scripts/agents/*.sh templates/scripts/agents/lib/*.sh` | Exit 0 |
| `npx --yes markdownlint-cli2 '**/*.md' '#node_modules' '#.claude' '#graphify-out'` | CLI2 0.23.3 / markdownlint 0.41.1; 65 files, zero issues |

The surface validator requires `mode` and `description` via an awk key-presence test and contains the statement that Copilot lacks PreToolUse/PostToolUse. It does not parse a complete native schema or exercise harness loading (`templates/scripts/verify-prompts.sh:3`, `:44`, `:53`). CI runs these scripts plus Markdown lint and ShellCheck (`.github/workflows/validate.yml:3`, `.github/workflows/markdown-lint.yml:3`). Passing these checks establishes the old contract, not compatibility with current clients.

cc-rpi `python3 templates/scripts/rpi-distribution.py validate --source /Users/juan/code/cc-rpi` passed: 61 components, 339 files, 6,573 managed-root bytes per harness. Its full verification suite was not run for this read-only research. Raw Copilot check output is in `/Users/juan/code/cc-rpi/.rpi/local/copilot-research-2026-09-28/baseline-checks.json`.

## R06: Current official Copilot capabilities

All external sources below were opened on 2026-09-28. GitHub Docs are rolling documentation without a pinned client version. The opened VS Code custom-agent page displays 2026-09-16. Documentation establishes documented support, not measured behavior on this machine.

| ID | Primary source | Observed contract |
| --- | --- | --- |
| E01 | [Instruction support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support) | Support differs across Chat, review, CLI and cloud; repository, path-specific and AGENTS instructions are not interchangeable across every surface. |
| E02 | [CLI instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions) | Applicable files are combined without a general precedence rule. Path rules use `applyTo`; `/instructions` exposes discovery. Instruction changes require a new/resumed session. |
| E03 | [Agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) | Skills bundle instructions/resources, with project roots including `.github/skills`, `.claude/skills` and `.agents/skills`; they support several Copilot surfaces. |
| E04 | [CLI skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills) | Skills may be invoked by name with a slash; resources are part of the skill directory. |
| E05 | [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents) | Migrate `.chatmode.md` to `.agent.md`; handoffs can wait for user submission; tool restrictions must use supported tools. |
| E06 | [Agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration) | Omitted tools grants all tools; unknown tool names are ignored. `model` is optional. Cloud ignores IDE handoffs; `infer` is retired. |
| E07 | [CLI custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli) | Subagents do not receive repository custom instructions by default; `include-custom-instructions: true` opts them in. |
| E08 | [VS Code prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files) | Agent Host does not load prompt files. Local still supports them; migration to skills is documented. Frontmatter is optional; current agent selection uses `agent`. |
| E09 | [Copilot hook reference](https://docs.github.com/en/copilot/reference/hooks-reference) | CLI/cloud hooks exist, including pre-tool decisions. Cloud treats ask as deny. Hook timeouts fail open; native enforcement cannot be inferred from a JSON file. |
| E10 | [VS Code hooks](https://code.visualstudio.com/docs/agent-customization/hooks) | Selected harness owns schema and lifecycle. Local hooks differ from Agent Host Copilot's SDK implementation; VS Code hook UX is Preview. |
| E11 | [Cloud best practices](https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results) | Bounded tasks, clear acceptance criteria, repository context and research/planning before publication improve task specification. |
| E12 | [Cloud environment setup](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/customize-the-agent-environment) | `.github/workflows/copilot-setup-steps.yml` uses a `copilot-setup-steps` job. A setup failure skips remaining setup but the agent can still start. |
| E13 | [CLI permissions](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools) | Limit available tools and permissions separately; deny rules win. Persistent broad allow-all aliases are discouraged. |
| E14 | [Programmatic CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/run-cli-programmatically) | Use minimal permissions, bounded execution and deliberate output capture; reproducible scheduled runs can select a model explicitly. |
| E15 | [VS Code skills](https://code.visualstudio.com/docs/agent-customization/agent-skills) | Skills support progressive loading and named invocation; names match directories and have schema limits. Additional resources need explicit links. |
| E16 | [VS Code settings](https://code.visualstudio.com/docs/agents/reference/ai-settings) | Several legacy settings remain experimental; default agent enablement does not require a blanket settings preset. |

One external inconsistency remains: the VS Code skills page's comparison table describes custom instructions as VS Code/GitHub.com-only, while GitHub's dedicated CLI instructions page documents CLI support. This report uses the dedicated surface reference E02 for CLI behavior. Generic feature tables are not native acceptance evidence.

## Evidence limits and handoff

Graphify was queried first for both repositories. The cc-rpi graph was generated September 26 with 2,964 nodes; Copilot's September 28 graph had 41 nodes, mostly scripts. Claims above were confirmed with source reads. The skill's suggested graph-directory argument produced a duplicate `graphify-out` path; using each repository root correctly resolved its own graph symlink. No graph memory or vocabulary writes occurred.

VS Code application metadata reports 1.137.0 at `/Applications/Visual Studio Code.app`; `code` and `copilot` were absent from this shell's PATH. No Copilot extension version was returned from the inspected user extension registry. No conclusion is drawn about authentication, account access, alternate installs, UI discovery or actual Copilot behavior. cc-rpi explicitly requires separate positive/negative Copilot native discovery and authorization fixtures (`cc-rpi/docs/compatibility-followups.md:35`).

The user authorized research, web verification and a plan; implementation and publication remain outside this turn. Both research assignments returned complete source inventories with no missing helper result. The `.summon` file and remote CI delta remain unchanged. This artifact is local-only under the existing `.gitignore:31` policy. Resume by rechecking both SHAs and worktree state, then read the accompanying plan. Future native qualification remains an implementation acceptance requirement, not an unresolved design decision in the plan.
