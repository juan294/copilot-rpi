# The copilot-rpi Guide

A practical guide to using the copilot-rpi blueprint for AI-assisted software development with GitHub Copilot.

## What Is This?

copilot-rpi is a blueprint repository. You clone it once, and every time you start a new project, you point GitHub Copilot at it and say "set this project up." The agent reads the blueprint, learns the rules, and configures your new project with battle-tested practices — prompt files, error prevention rules, CI setup, the works.

At its core, copilot-rpi teaches GitHub Copilot to work the way experienced developers have found works best: research first, plan second, implement third. This sounds obvious, but without explicit structure, AI coding agents tend to skip straight to writing code — and that's where things go wrong.

## The Big Idea: Research-Plan-Implement

The methodology is called RPI, and it's built on one insight that changes everything:

**Errors amplify as they move downstream.**

A mistake in your research becomes a wrong assumption in your plan, which becomes hundreds of lines of code solving the wrong problem. But a mistake in a single line of code is just... a bug. So the system is designed to focus your attention where it matters most: reviewing the research and the plan, not reading every line of generated code.

Here's what the pipeline looks like:

```text
Research  ──human reviews──▶  Plan  ──human reviews──▶  Implement  ──human reviews──▶  Validate
   │                           │                           │                            │
   ▼                           ▼                           ▼                            ▼
 "What exists?"           "What do we change?"        "Make the changes"         "Did it work?"
```

Each phase runs in its own Copilot Chat window. This is intentional — it keeps the AI's context window clean. A fresh conversation reading a well-written plan performs dramatically better than a long conversation that's been going for an hour.

## The Philosophy in Five Minutes

**1. Research before you act.** Never modify code you haven't read. Every change starts with understanding what exists today, described factually — no opinions, no suggestions, just "here's how the code works right now."

**2. Plan before you implement.** Write a phased plan with explicit success criteria before touching production code. Plans are broken into phases, and each phase has automated tests that prove it works.

**3. Humans gate every transition.** The agent stops between phases and waits for you. You read the research before approving the plan. You read the plan before approving implementation. You confirm each implementation phase before the next one starts.

**4. Context is your only lever.** Every time the AI takes a turn, it's a stateless function: the context window goes in, the next action comes out. There's no hidden memory. The quality of what's in that window is literally the only thing that determines output quality. The entire methodology is designed around this constraint.

**5. Specs are the new code.** In AI-assisted development, your plans and research documents are effectively your source code. The generated code is more like a compiled artifact. Treat your specs with the same rigor you'd treat source files — review them carefully, version them in git, iterate on them until they're right.

## Getting Started

### Step 1: Clone the Blueprint

```bash
git clone https://github.com/juan294/copilot-rpi.git
```

Keep this repository somewhere permanent on your machine. You'll reference it from every project.

### Step 2: Set Up Your Project

**Starting a new project?** Open Copilot Chat in VS Code and run:

```text
/bootstrap
```

Point it at the copilot-rpi directory. The agent reads the blueprint, asks you about your project (type, stack, conventions), then creates AGENTS.md, .vscode/settings.json, prompt files, path-specific instructions, chat modes, directory structure, and walks you through CI and git setup.

**Migrating an existing project?** Run:

```text
/adopt
```

The agent reads the blueprint, audits your project, presents a report showing what's already in place and what's missing, and you choose what to adopt.

### Step 3: Start Working

Once your project is set up, your daily workflow uses four prompt commands:

```text
/research [topic]     →  Understand the codebase
/plan [feature]       →  Create an implementation plan
/implement [plan]     →  Execute the plan phase by phase
/validate [plan]      →  Verify everything works
```

That's it. Those four commands are 90% of your interaction with the methodology.

## Command Cheat Sheet

### Setup Commands

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/bootstrap` | Reads the copilot-rpi blueprint, asks about your project, creates AGENTS.md, settings, prompt files, instructions, chat modes, and full directory structure. | New projects. Run once at the start. |
| `/adopt` | Reads the blueprint, audits the existing project, presents a gap report, then migrates what you approve. | Existing projects you want to bring up to standard. |

### The Core Four

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/research [question]` | Searches the codebase systematically. Produces a research document at `docs/research/`. | Before any change. Understanding comes first. |
| `/plan [feature]` | Creates a phased implementation plan with pseudocode, success criteria, and test requirements. Saves to `docs/plans/`. | After research is reviewed and approved. |
| `/implement [plan path]` | Executes the plan one phase at a time. Stops after each phase for your approval. | After the plan is reviewed and approved. |
| `/validate [plan path]` | Runs every automated check from the plan, verifies all phases are complete, produces a validation report. | After implementation is done. |

### Supporting Commands

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/quality-review` | Reviews changed files for code reuse, quality, and efficiency. Finds issues and fixes them interactively. | After each implementation phase, or after a `/pre-launch` audit. |
| `/describe-pr` | Generates a PR description from the current branch's diff and commit history. | Before opening or updating a PR. |
| `/pre-launch` | Runs a comprehensive multi-domain audit (QA, security, performance, architecture, UX, devops). Recommends `/quality-review` for code quality findings. | Before any production release. |

### Copilot-Specific Features

| Feature | What It Does | When to Use |
|---------|-------------|-------------|
| **Chat modes** (`.github/chatmodes/`) | Specialized personas with behavioral constraints. RPI Research mode bakes in the documentarian rule. | Select at the start of a research or planning session. |
| **Path-specific instructions** (`.github/instructions/`) | Auto-loaded rules based on which files are open. Test conventions fire when test files are in context. | Always active — no manual invocation needed. |
| **`#codebase`** | Full-repository search in Copilot Chat. | During research to find relevant files. |
| **`#file:path`** | Add a specific file to the chat context. | When you know which file the agent needs. |
| **`copilot -p "prompt"`** | Headless CLI mode for background tasks and automation. | CI monitoring, scheduled agents, parallel research. |
| **`@copilot` cloud agent** | Assign GitHub Issues to Copilot for async implementation. | After completing Research+Plan, delegate Implementation. |

## How the Four Phases Actually Work

### Phase 1: Research

You type `/research how does authentication work in this app?` and the agent:

1. Uses `#codebase` to find all relevant files — locating where auth code lives.
2. Reads key files to understand how the authentication flow works.
3. Searches for similar patterns elsewhere in the codebase.
4. Synthesizes findings into a structured research document.
5. Saves it to `docs/research/YYYY-MM-DD-auth-flow.md`.

The critical rule here is **documentarian, not critic**. The research describes what exists — it doesn't suggest improvements or identify problems. This keeps the research factual and prevents the agent from jumping to solutions before understanding the problem.

**Your job:** Read the research document. If it's wrong or incomplete, throw it out and run `/research` again with more specific steering. Multiple passes are normal. Don't approve bad research — it poisons everything downstream.

### Phase 2: Plan

You type `/plan add rate limiting to the login endpoint` and the agent:

1. Reads the research document.
2. Explores the codebase for additional context.
3. Asks you focused questions (only things the code can't answer).
4. Proposes design options with trade-offs.
5. Writes a phased implementation plan with pseudocode, file-by-file changes, and success criteria.
6. Saves it to `docs/plans/` with separate files for each phase.

**Your job:** Read the plan carefully. This is where your time has the highest leverage. A bad plan leads to hundreds of bad lines of code. Push back, ask questions, iterate until the plan is right.

### Phase 3: Implement

You type `/implement docs/plans/2026-02-21-rate-limiting.md` and the agent:

1. Reads the plan.
2. Starts with Phase 1 only.
3. Implements the changes, self-reviews for plan compliance, runs all automated verification.
4. Recommends running `/quality-review` for a second-pass review (code reuse, quality, efficiency).
5. Updates the plan's checkboxes.
6. **Stops and waits for your confirmation.**

You review, approve, and it moves to Phase 2. One phase at a time. Never auto-proceeding. If the plan marks phases as `[batch-eligible]`, you can run them in parallel via `copilot -p` or `@copilot` issues.

**Your job:** Confirm each phase. If something doesn't look right, say so.

### Phase 4: Validate

You type `/validate docs/plans/2026-02-21-rate-limiting.md` and the agent:

1. Re-reads the plan.
2. Runs every automated verification command.
3. Checks that all marked-complete items are actually done.
4. Thinks about edge cases.
5. Produces a validation report.

**Your job:** Review the report. Then you're done.

## Key Concepts

### Context Engineering

The entire methodology is a context management strategy. Copilot has a fixed-size context window. Everything the agent needs to make a good decision must fit in that window. If the window fills up with noise, the agent's decisions degrade.

RPI manages this by:

- **Running each phase in its own Chat window.** Fresh context every time.
- **Producing compact artifacts between phases.** A research doc is a compressed summary of hours of exploration.
- **Using `#codebase` for focused searches.** Let the search engine do the heavy lifting instead of browsing files manually.
- **Starting new conversations between unrelated tasks.** Context hygiene is key.
- **Writing handoff documents proactively.** Don't wait for auto-compaction at 95% — write a handoff doc at 60%.

### The Documentarian Rule

During research, agents describe what IS — never what SHOULD BE. No improvement suggestions, no code critiques, no "this could be refactored." Just factual descriptions with file and line references.

Use the **RPI Research** chat mode to enforce this structurally at the session level.

### Error Prevention

The blueprint includes 18 operational rules learned from real sessions — including 6 Copilot-specific rules covering prompt file frontmatter, `${input:var}` syntax, instruction file globs, CLI auth, auto-compaction, and chatmode directories.

When your project is set up via the blueprint, these rules are baked into the AGENTS.md file that every tool reads every session.

### Path-Specific Instructions

Copilot's `applyTo` glob system is one of its strongest features. Rules defined in `.github/instructions/` fire automatically based on which files are open in context:

- Test conventions activate when test files are open
- API conventions activate when route files are open
- Migration rules activate when migration files are open

This is progressive disclosure in action — the agent gets domain-specific rules exactly when it needs them, without bloating AGENTS.md.

### The `@copilot` Cloud Agent

A unique Copilot capability: assign a GitHub Issue to `@copilot` for async implementation. The workflow:

1. Complete Research + Plan interactively in VS Code
2. Create a GitHub Issue with the plan attached
3. Assign `@copilot` to the issue
4. The cloud agent creates a branch, implements, and opens a PR

This lets you delegate well-specified implementation work and review the result asynchronously.

### Pre-Launch Audit

Before any production release, run `/pre-launch` to audit 6 domains: QA, security, performance, architecture, UX/accessibility, and infrastructure. The audit produces a single report with a verdict: READY, CONDITIONAL, or NOT READY.

## Project Structure After Setup

After bootstrapping, your project will have:

```text
your-project/
├── AGENTS.md                         # Cross-tool instruction file
├── .github/
│   ├── copilot-instructions.md       # Copilot-specific addenda (optional)
│   ├── prompts/                      # Prompt files (invoked with /)
│   │   ├── research.prompt.md
│   │   ├── plan.prompt.md
│   │   ├── implement.prompt.md
│   │   ├── validate.prompt.md
│   │   ├── describe-pr.prompt.md
│   │   └── pre-launch.prompt.md
│   ├── instructions/                 # Path-specific rules (auto-loaded)
│   │   ├── tests.instructions.md
│   │   └── api.instructions.md
│   └── chatmodes/                    # Specialized personas
│       ├── rpi-research.chatmode.md
│       └── rpi-planner.chatmode.md
├── .vscode/
│   ├── settings.json                 # Copilot feature flags + model selection
│   └── mcp.json                      # MCP server configuration (optional)
├── docs/
│   ├── research/                     # Research documents
│   ├── plans/                        # Implementation plans
│   └── decisions/                    # Architecture decision records
└── ... your code ...
```

## Tips for Getting the Most Out of It

**Start every task with `/research`.** Even if you think you know the answer. The research phase often reveals things you didn't expect.

**Read your research and plans critically.** This is where your time has 10x leverage compared to reviewing code.

**Start a new Chat window liberally.** Switching tasks? New window. Finished a phase? New window. Context hygiene is the single biggest factor in output quality.

**Use chat modes.** Select RPI Research mode for research sessions. The documentarian constraint works much better when enforced at the session level.

**Don't fight the phases.** The phased approach produces better results in less total time because you avoid rework cycles from misunderstood requirements.

**Throw out bad research.** If the research document doesn't accurately describe the codebase, don't try to salvage it. Run `/research` again with better steering.

**Invest in your AGENTS.md.** This file is the highest-leverage configuration point. Every session reads it. Craft every line manually.

**Use path-specific instructions for domain rules.** Don't put test conventions or API patterns in AGENTS.md — put them in `.github/instructions/` where they fire automatically.

**Log your errors and successes.** After 3 instances of the same pattern, promote it to a rule.

## Advanced Setup

### Scheduled Agents

For production projects, set up agents that run on a schedule using `copilot -p "prompt"` invoked from cron/launchd. Ensure the CLI is pre-authenticated (`copilot auth`). See `methodology/scheduled-agents.md` for templates.

### Adapting for Different Project Types

The blueprint adapts to six project archetypes: web applications, libraries, CLI tools, monorepos, Python projects, and static sites. Each has specific adjustments for git workflow, CI configuration, testing strategy, and AGENTS.md content. The setup checklist walks you through the differences.

## Where to Go Deeper

| Topic | File | What You'll Learn |
|-------|------|-------------------|
| Core philosophy | `methodology/philosophy.md` | Error amplification, mental alignment, key lessons |
| Context management | `methodology/context-engineering.md` | Compaction, progressive disclosure, configuration surfaces |
| The four phases | `methodology/four-phases.md` | Detailed process for each phase, handoffs, failure recovery |
| Agent design | `methodology/agent-design.md` | Research catalog, autonomy boundaries, parallel patterns |
| Plan notation | `methodology/pseudocode-notation.md` | How to write and read implementation plans |
| Testing approach | `methodology/testing.md` | TDD protocol, verification hierarchy |
| CI ownership | `methodology/push-accountability.md` | Background CI monitoring, fix-and-repush |
| Error patterns | `patterns/agent-errors.md` | 17 documented errors with symptoms and solutions |
| Operational rules | `patterns/quick-reference.md` | 18 rules to prevent known mistakes |
| Worked examples | `examples/README.md` | Sample research docs, plans, logs, pseudocode |

## Credits

The RPI methodology is adapted from HumanLayer's opencode-rpi implementation and their ACE-FCA (Advanced Context Engineering for Coding Agents) framework, tailored for GitHub Copilot's native capabilities.
