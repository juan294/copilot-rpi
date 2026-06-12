# Cost Monitoring & Model Economics

> Loop engineering is the biggest lever on your AI coding bill. Explore once, at frontier cost. Then reuse the workflow that pays back.

Under usage-based billing, the question stops being "is the agent good?" and becomes "does this loop deliver net-positive ROI per dollar of inference?" This document covers how the blueprint controls that — model tiers as the primary lever, access tiers for who spends where, and measurement so you can tell which loops pay back.

The RPI methodology is itself loop engineering: a `/research` + `/plan` pass spends frontier tokens once to produce a reusable, reviewable artifact, and every subsequent `/implement`, `/validate`, and `/triage` run executes that artifact on a cheaper model. The expensive thinking happens once; the cheap execution repeats.

## The Four Cost Pools

Treat AI spend as four distinct pools, each with its own budget and rules. Mixing them is how bills surprise you.

| Pool | What it funds | Metered? | Model tier |
|------|---------------|----------|------------|
| **Frontier R&D** | Authoring and improving workflows; one-time exploration of a hard problem | Capped budget for the people building loops | opus / frontier |
| **Per-workflow run** | Approved, codified workflows running in production (CI, scheduled agents, `/implement` at scale) | Metered **by outcome** — cost per merged PR, per fixed bug, per passing build | sonnet / mid |
| **Everyday prompting** | The default developer loop — chat, small edits, `/status`, `/describe-pr` | Capped to the floor model | haiku / floor |
| **Local models** | Bulk/offline work on owned hardware | Unmetered, free at the margin | local |

The single most important rule: **the everyday floor is cheap by default, and frontier access is the exception, not the baseline.** Most prompting does not need a frontier model. Reserve frontier spend for exploration that produces something reusable.

## The Primary Lever: Model Tiers

Pinning the right model tier to each workflow is where most of the savings live — see [context-engineering.md](context-engineering.md#model-selection--tier-each-workflow) for the full tier system and how to bind tiers to your org's concrete models. The short version:

- `/research`, `/plan`, `/pre-launch` → **frontier**. A bad plan amplifies into thousands of bad lines; spend here.
- Everything that executes a reviewed plan → **mid**.
- Mechanical read-and-summarize (`/status`, `/describe-pr`) → **floor**.
- Subagents inherit their workflow's tier — a frontier parent spawning 8 frontier children multiplies the bill by 8.

## Access Tiers — Who Spends Where

The cost pools imply an access policy. The mistake is giving every developer open access to frontier models for everyday work — the floor stops being a floor.

- **Frontier access is for authoring loops, not running them.** The people researching and codifying workflows (anyone doing `/research` and `/plan` on a genuinely new problem) need frontier models. That is a deliberate, budgeted investment in a reusable artifact.
- **Everyone else consumes proven workflows on the floor.** Once a loop is codified and its tier is pinned, running it does not require frontier access. A developer running `/implement` against a reviewed plan, or `/triage` on the morning queue, runs at the tier the workflow declares.
- **Override is explicit and logged, not ambient.** A developer can bump a session up a tier when a task proves harder than expected (see the override rule in context-engineering.md) — but that is a noted exception, not the default that every session silently inherits.

This is the difference between "everyone can reach Opus, so everything quietly runs on Opus" and "Opus is where we explore; the codified loop runs on the floor." Only the second is affordable at scale.

## Measure Cost Per Outcome

You cannot tune what you cannot see. Before betting on any investment beyond this playbook, get measurement in place — otherwise you cannot tell whether AI usage is net-positive.

Track spend **per outcome**, not per token:

- **Cost per merged PR** — total inference cost attributable to a change, divided by changes shipped.
- **Cost per workflow run** — average cost of a `/implement`, `/triage`, `/fix-ci` cycle, trended over time. A workflow whose per-run cost is climbing is a signal to re-tier or re-codify it.
- **Tier adherence** — what fraction of runs executed at or below their declared tier. Frequent upward overrides on a given workflow mean its tier (or its plan quality) is wrong.
- **Floor ratio** — share of total spend going to the everyday floor vs. frontier. A healthy system spends most tokens on the floor.

The **cost-report scheduled agent** (see [scheduled-agents.md](scheduled-agents.md#common-agent-types)) automates this: it parses your provider's usage export weekly and reports cost-per-outcome trends, flagging any workflow drifting above its tier or its historical per-run cost. Data sources vary by provider (Copilot premium-request counts, API usage exports); the agent's job is to turn raw usage into per-workflow, per-outcome numbers you can act on.

## Approval Gates Tied to Cost

[deployment-safety.md](../patterns/deployment-safety.md) already requires justifying every external action before triggering it (Rule #35: *is this needed, justified, verifiable?*). Cost monitoring extends that from CI/deployment actions to **inference itself**:

- **Frontier exploration is gated by expected payback.** Before kicking off a frontier `/research` + `/plan` cycle on a large problem, the expected outcome should justify the inference bill — the same bar as triggering a deployment. A throwaway question does not warrant a frontier loop.
- **Scaled fan-out is gated explicitly.** `/pre-launch` (8 specialists) and `/remediate` (parallel agents) multiply cost. Run them when the outcome — a production launch, a remediation wave — justifies the spend, not as a casual check.
- **Investment beyond the playbook is an intentional bet.** Any AI investment past this baseline (custom agents, larger fan-outs, new frontier workflows) should be a deliberate decision made *after* monitoring is in place — so you can confirm it delivers net-positive ROI rather than assuming it does.

## Order of Operations

1. **Pin tiers** to every workflow (done in this blueprint — see the `Model tier` line on each prompt).
2. **Bind tiers** to your org's concrete models and set the everyday floor as the default.
3. **Stand up measurement** — the cost-report agent — so cost-per-outcome is visible.
4. **Only then** make intentional bets beyond the playbook, validated against the numbers.

Everything before step 4 is the cheap, high-leverage work. Skipping straight to step 4 — buying frontier access for everyone, spawning large fan-outs — without tiers or measurement is how the bill runs away.
