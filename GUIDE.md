# Guide to Copilot RPI

Copilot RPI gives a project a repeatable Research, Plan, Implement and
Validate workflow. Research documents what exists, planning defines testable
phases, implementation changes one accepted phase at a time, and validation
checks the result against the plan. Errors in early assumptions can spread
through later work, so review research and plans before implementation.

## Why the phases matter

A wrong research claim can become a wrong plan and then many lines of code.
Research therefore describes the present system with `file:line` evidence.
Planning turns that evidence into explicit behavior and checks. Implementation
proves one phase at a time. Validation asks whether the final result matches
the approved plan and its acceptance criteria.

```text
Research: What exists? -> Plan: What changes? -> Implement: Make the change
         -> Validate: Did the planned behavior and checks pass?
```

Review the research and plan closely; they carry decisions into later work.
Keep them in versioned `docs/research/` and `docs/plans/`. A fresh conversation
per phase can reduce context pressure, while a durable handoff carries the
candidate, scope, decisions, findings and verification to the next session.
An explicit all-phases request may continue through successive complete
phase gates without asking for the same authorization again.

## Install in a project

Clone the blueprint and follow the [setup checklist](templates/setup-checklist.md).
Render a package for the selected Copilot profile into an empty staging
directory. Review the lifecycle `plan` before `apply`; run `check` afterward.
The installer tracks owned bytes under `.rpi/copilot/` and preserves project
guidance, customized files and unrelated `.rpi/manifest.json` data. For an old
prompt-based installation, read [the v2 migration guide](docs/migrations/v2.md).

Copilot CLI and VS Code Copilot Agent Host use project skills in
`.github/skills/`, specialist roles in `.github/agents/`, and repository and
scoped instructions. `vscode-local` generates prompt wrappers for the Local
harness only. Check actual discovery in the selected client; a file on disk
does not prove it was loaded. The [compatibility matrix](docs/compatibility.md)
lists each profile and recovery path.

## Run the four phases

| Skill | Input and result |
| --- | --- |
| `/rpi-research` | Give a codebase question. It writes a factual, cited research artifact; it does not recommend a fix. |
| `/rpi-plan` | Give the accepted research and intended change. It writes phased scope and measurable acceptance criteria. |
| `/rpi-implement` | Give the approved plan path and authorized phases. Each phase goes through implementation, independent review, repair, simplify and the full local gate. |
| `/rpi-validate` | Give the plan path. It checks completed work and actual test evidence against acceptance criteria. |

The agent pauses at each phase boundary unless the request already authorized
continuation. A continuation still requires that phase's review, verification
and durable handoff. Use a new conversation when context grows heavy; the
handoff must name the actual candidate, checks, decisions and next entry
condition. Interactive skills inherit the model and effort selected in the
current session. They do not bind a model tier.

`rpi-brainstorm` helps refine a vague idea; `rpi-assess` evaluates options;
`rpi-debug` finds a non-obvious root cause. `rpi-pre-launch`,
`rpi-remediate`, `rpi-update-docs` and `rpi-release` form the release workflow.
`rpi-quality-review` examines reuse, quality and efficiency. Setup and
maintenance use `rpi-bootstrap`, `rpi-adopt`, `rpi-update` and `rpi-detach`.
The canonical skill bodies and bundled resources are in `templates/skills/`.
Native `/plan` and `/status` are client commands; use `rpi-plan` and
`rpi-status` for the blueprint. The [methodology reading order](methodology/README.md)
explains each contract in detail.

## What happens in each phase

### Research

Ask `/rpi-research how does authentication work here?` in a repository with
existing code. The agent searches for the relevant routes, callers, tests and
historical decisions, reads the source, and writes a cited map to
`docs/research/`. It describes behavior without proposing changes. In a truly
empty project, begin with `/rpi-plan` because there is no implementation to
research yet. Read the artifact and correct inaccurate or incomplete claims
before planning.

### Plan

Give `/rpi-plan` the accepted research and desired outcome. The agent asks
focused questions for decisions it cannot derive from code, weighs options,
and writes a plan plus phase files under `docs/plans/`. Each phase names its
scope, behavioral oracles, automated checks, manual observations and recovery
route. Review the design and the checks before authorizing implementation;
an ambiguous success criterion is a reason to revise the plan.

### Implement

Give `/rpi-implement` the approved plan path and authorized phases. Behavioral
changes begin with a failing test. Each phase then uses an independent
plan-compliance review, repairs confirmed findings, runs a quality/simplify
pass and completes all required local checks. The agent records exact
candidate and check evidence before a phase can be accepted. Independent
work units may run in parallel within a phase when file ownership does not
overlap, with one integration owner. The phases themselves remain sequential.

### Validate

Give `/rpi-validate` the plan path after implementation. The validator reads
the approved criteria, diff and test evidence, checks that required commands
actually ran against the candidate, and reports unmet conditions. A green
wrapper, an old receipt or a test on another commit cannot establish success.

## Other workflows

| Skill | Use |
| --- | --- |
| `rpi-bootstrap`, `rpi-adopt`, `rpi-update`, `rpi-detach` | Plan and reconcile project installation while preserving owner files. |
| `rpi-brainstorm`, `rpi-assess`, `rpi-tool-design` | Refine vague goals, evaluate alternatives or design agent-facing tools. |
| `rpi-debug`, `rpi-fix-ci`, `rpi-quality-review` | Investigate defects, diagnose exact-commit CI failures or simplify changed code. |
| `rpi-pre-launch`, `rpi-remediate` | Audit eight launch domains and disposition every confirmed finding. |
| `rpi-update-docs`, `rpi-explore-release`, `rpi-release` | Prepare documentation, exploratory evidence and an authorized publication. |
| `rpi-triage`, `rpi-status`, `rpi-describe-pr` | Read operational reports, orient a session or draft a change description. |
| `process-errors` | Maintain the local error corpus; this is a Copilot RPI maintenance skill. |

`rpi-describe-pr` drafts text from the actual diff and verification. It does
not publish a PR by invocation. `rpi-triage` stops at a read-only briefing;
later remediation needs authorized scope. `rpi-release` checks the requested
version and release candidate before any tag or GitHub publication.

## Instructions and authority

The root `AGENTS.md` and `.github/copilot-instructions.md` carry short shared
guidance. Files in `.github/instructions/` use `applyTo` globs for tests, APIs,
migrations, deployment and selected stack rules. Research, planning and audit
agents in `.github/agents/` declare their tool scopes; a read-only role reports
findings to a parent that can write the authorized artifact. Verify discovery,
resource loading and tool restrictions in the actual client.
The blueprint provides 5 instruction templates for these scoped topics.
The 55 operational rules in [the quick reference](patterns/quick-reference.md)
are read when a task matches their scope.

### Context and the documentarian rule

Use source search and targeted reads instead of filling a chat with whole
directories. Keep research, plans and handoffs concise enough for a fresh
session to revalidate. Start a new conversation for unrelated work; when
continuing a long task, preserve exact refs and evidence first. A prior
handoff is context, not a substitute for inspecting the current checkout.

The research role is deliberately descriptive. It records what the code does
and where, including uncertainty, without judging the design or prescribing a
fix. Use `rpi-assess` for an evaluation. The research agent declares only
`read` and `search` tools and returns findings to its parent; verify its tool
boundary in the selected native client. A prose instruction alone does not
prove that a write was prevented.

### Progressive disclosure

| Layer | When to use it | Location |
| --- | --- | --- |
| Root guidance | Short project facts and universal rules for every task | `AGENTS.md` and `.github/copilot-instructions.md` |
| Scoped guidance | Tests, API, migrations, deployment or selected stack paths | `.github/instructions/*.instructions.md` with `applyTo` |
| Catalogs | Exact error or rule when relevant to a task | `patterns/agent-errors.md`, `patterns/quick-reference.md` |

Review the actual `applyTo` glob against the target paths. A file on disk
does not prove the chosen client loaded it. Keep project knowledge and local
extensions during a blueprint update instead of replacing whole files.

Publication, paid inference, cloud jobs and remote mutations follow the
project's authority boundary. Local verification precedes an authorized
integration push, then expected CI runs are checked against the exact pushed
commit. Native hooks and the candidate receipt pre-push gate are separate
opt-in controls. A configured hook is not proof that it ran. See
[native policy](docs/native-policy.md).

## Verify and recover

The local blueprint gate is `bash scripts/verify-local.sh`. It stores a
candidate-bound receipt in `.rpi/local/copilot/`. Failed, interrupted or stale
receipts do not count as success. Native client tests are separately recorded
in [tests/native](tests/native/README.md); static validation cannot establish
CLI or VS Code behavior.

If a lifecycle plan reports a conflict, preserve the owner bytes and inspect
its source/base evidence. A stale plan needs a new preview. If apply stops
mid-transaction, use its printed journal with `rollback`, then re-plan;
rollback refuses to overwrite newer owner edits. [Migration commands](docs/migrations/v2.md)
cover install, check, detach and recovery. The optional Local, hook, scheduler
and cloud profiles each need their own qualification before support is claimed.

## Pre-launch and release evidence

`/rpi-pre-launch` covers architecture, frontend, backend, performance,
operations, security, QA/reliability and UX. Its structured report identifies
each finding and regression risk. `/rpi-remediate` validates that report,
checks the proposed repair against the invariant it might break, and records
resolved, evidenced false-positive or owner-reviewed architectural
dispositions. External issues are created only when separately authorized.

The pre-release sequence is `rpi-pre-launch`, `rpi-remediate`,
`rpi-update-docs`, `rpi-explore-release`, then `rpi-release` on the
fixed candidate. The [E2E Pro playbook](templates/e2e-pro-playbook-template.md)
binds required checks to the exact artifact. Wave A fails if no required
check ran, a required check skipped or failed, or the candidate changed.
Wave B uses independent exploratory charters against that candidate; its
eight maneuvers include repeat, recover, interrupt, second role,
locale/viewport, copy versus outcome, downstream readback and whether a
feature should exist. Structural Waves C-H are selected by project risk and
recorded as applicable or not applicable. Tagging and publication follow the
accepted evidence and the user's release authorization.

## Project layout and adaptation

A default CLI or Agent Host install may contain the following managed files.
Optional examples, hooks and schedulers appear only when separately selected:

```text
your-project/
  AGENTS.md
  .github/copilot-instructions.md
  .github/skills/rpi-*/SKILL.md
  .github/agents/rpi-*.agent.md
  .github/instructions/*.instructions.md
  .rpi/copilot/manifest.json
  .rpi/copilot/runtime/
  docs/research/
  docs/plans/
```

For a web application, inspect deployed routes, preview triggers and rollback.
For a library, verify public API and package artifact. For a CLI, test the
installed command and exit codes. For a monorepo, name package boundaries and
shared consumers. Python projects need their own environment and database
fixtures. Documentation projects need link and output checks. The
[setup checklist](templates/setup-checklist.md) covers these adaptations.

Use the [scheduled-job guide](methodology/scheduled-agents.md) only after the
CLI runner has native qualification and the owner has selected a model,
credentials and schedule. Cloud agent delegation is a separate hosted profile
with its own setup and authority; it is not part of a local install.

## Working habits

- Read unfamiliar source before modifying it. A greenfield project with no
  code can start with planning.
- Challenge an inaccurate research document before it shapes a plan.
- Keep the root guidance short and put domain rules in scoped instructions.
- Start a fresh conversation for unrelated work and use a durable handoff
  when a long task continues in a new session.
- Record repeated errors in the catalog with their cause and repair, then
  review whether a rule or deterministic check would prevent recurrence.
- Verify user-visible outcomes and persisted state. A generated report,
  accepted command or passing test is evidence only for what it actually
  observed.

## Reference map

| Topic | Source |
| --- | --- |
| Philosophy and error amplification | [philosophy](methodology/philosophy.md) |
| Context and handoffs | [context engineering](methodology/context-engineering.md) |
| Phase procedure | [four phases](methodology/four-phases.md) |
| Agent roles and bounded parallel work | [agent design](methodology/agent-design.md) |
| Plan notation and test design | [pseudocode](methodology/pseudocode-notation.md), [testing](methodology/testing.md) |
| CI ownership | [push accountability](methodology/push-accountability.md) |
| Error and rule catalogs | [agent errors](patterns/agent-errors.md), [quick reference](patterns/quick-reference.md) |
| Native profiles and controls | [compatibility](docs/compatibility.md), [native policy](docs/native-policy.md) |

The methodology adapts [HumanLayer's RPI and ACE-FCA work](https://humanlayer.dev/)
to GitHub Copilot's repository skills, agents and instructions.

## Learn more

The catalog has 40 documented errors and 55 rules with scope/stack tags.

- [Methodology](methodology/README.md): philosophy, context, testing, release and scheduled jobs.
- [Examples](examples/README.md): research, plans and walkthroughs.
- [Error patterns](patterns/agent-errors.md) and [55 operational rules](patterns/quick-reference.md).
- [Upstream intake](docs/upstream-sync.md): pinned cc-rpi source and deliberate dispositions.
