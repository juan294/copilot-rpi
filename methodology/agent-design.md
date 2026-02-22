# Agent Design Principles

## The Documentarian Rule

Every research-phase agent follows one absolute constraint:

> **Describe what EXISTS. Never suggest what SHOULD BE.**

This means:
- No improvement suggestions
- No problem identification
- No root cause analysis (unless explicitly asked)
- No code quality commentary
- No performance concerns
- No security warnings
- No refactoring recommendations
- No "better approaches"

**Why:** Research agents that mix observation with opinion produce noisy, biased output. Keeping them purely descriptive ensures the human gets clean, factual data to make their own decisions.

### Good vs Bad Examples

**Authentication research — GOOD (describes what IS):**
> The login endpoint at `src/auth/login.ts:8` accepts email and password in the request body. Passwords are hashed with bcrypt at cost factor 12 (`src/auth/password.ts:6`). There is no rate limiting middleware on this route — requests go directly from the router to the handler. The test suite covers 12 cases for login (`tests/auth/login.test.ts`) and 0 cases for logout.

**Same topic — BAD (suggests what SHOULD BE):**
> The login endpoint lacks rate limiting, which is a security vulnerability that should be addressed. The bcrypt cost factor of 12 is adequate but could be increased to 14 for better security. The test coverage is poor — the logout flow has no tests and needs them urgently.

**Why the bad version is harmful:**
- "Security vulnerability" is a judgment, not an observation. The human may already know and have reasons.
- "Could be increased to 14" is a recommendation the human didn't ask for.
- "Poor" and "urgently" are opinions that bias the human before they've formed their own assessment.
- The good version gives the same facts — the human can draw the same conclusions themselves.

**Database patterns — GOOD:**
> Queries use the repository pattern. `UserRepository` at `src/repos/user.ts:12` wraps Prisma calls. All read queries go through `findUnique` or `findMany` (lines 15-48). Write queries use `prisma.$transaction` (lines 52-78). There are 3 raw SQL queries in `src/repos/analytics.ts:20-45` that bypass the repository pattern.

**Same topic — BAD:**
> The repository pattern is used inconsistently — most queries go through the proper abstraction but there are 3 raw SQL queries in analytics that break the pattern and should be refactored to use the repository. The transaction handling is good but could benefit from a shared helper.

**API research — GOOD:**
> The `/api/orders` endpoint returns all orders for the authenticated user with no pagination. The response includes the full order object with nested line items. Average response size for a user with 50 orders is approximately 45KB based on the schema at `src/types/order.ts:8-32`.

**Same topic — BAD:**
> The orders endpoint has a performance problem — it returns all orders without pagination, which will cause issues at scale. The response is bloated because it includes nested line items that could be loaded lazily. This should be refactored to add pagination and sparse fieldsets.

## Tool Usage by Role

| Role | Can Read/Search | Can Write/Edit | Can Run Shell | Can Access Web |
|------|:-:|:-:|:-:|:-:|
| Research (read-only) | Yes | No | No | No |
| Implementation | Yes | Yes | Yes | No |
| Validation | Yes | No (report only) | Yes (tests only) | No |

**In Copilot terms:** During research, only use `#codebase`, `#file:`, and read operations. During implementation, use full agent mode with `#tool:terminal` access. During validation, run verification commands but don't modify code.

## Research Approach Best Practices

1. **Be specific about what to search for**, not how to search. The agent knows its tools.
2. **Specify the output format** you expect in research prompts.
3. **Remind the agent of the documentarian constraint** in every research prompt.
4. **Request file:line references** in every response.
5. **Use `#codebase` for broad searches** — it indexes the full repository.
6. **Use `#file:path` for targeted reads** — when you know which files matter.
7. **Verify results** — if something seems off, ask for deeper investigation.

---

## Research Role Catalog

All research roles mapped to Copilot execution patterns:

| Role | Copilot Pattern | Phase | Purpose |
|------|----------------|-------|---------|
| Codebase Locator | `#codebase` search | Research | Find WHERE files live |
| Codebase Analyzer | `#file:` reads | Research | Understand HOW code works |
| Pattern Finder | `#codebase` + examples | Research | Find EXAMPLES of similar patterns |
| Docs Locator | `#codebase` in docs/ | Research | Find relevant historical docs |
| Docs Analyzer | `#file:` for specific docs | Research | Extract INSIGHTS from docs |
| Web Researcher | Web search in chat | Research | Find external documentation |
| Parallel Researcher | `copilot -p` background | Research | Independent parallel investigation |

**Key patterns:**
- **In-session research** uses `#codebase` and `#file:` references — fast, stays in your context.
- **Background research** uses `copilot -p "prompt" > output.md` — runs in a separate terminal, writes results to a file you can reference later. Keeps your main session's context clean.
- **Parallel research** runs multiple `copilot -p` processes simultaneously for independent questions. Each writes to a separate output file.

### Codebase Locator

**Purpose:** Find WHERE files live. Given a topic or feature, returns all relevant file paths grouped by purpose.

**Copilot:** Use `#codebase` with a focused query like "find all files related to authentication."

**Output:** Organized list of files by category (implementation, tests, config, types, docs) with full paths and counts.

**Does NOT:** Read file contents, analyze code, critique organization.

### Codebase Analyzer

**Purpose:** Understand HOW code works. Traces data flow, explains implementation, maps component interactions.

**Copilot:** Use `#file:src/auth/login.ts` and related file references to read specific files and ask for analysis.

**Output:** Structured analysis with entry points, core implementation breakdown, data flow trace, patterns, configuration, and error handling — all with `file:line` references.

**Does NOT:** Suggest improvements, identify problems, comment on quality.

### Pattern Finder

**Purpose:** Find EXAMPLES of similar implementations. Shows concrete code snippets that can serve as templates.

**Copilot:** Use `#codebase` to search for similar patterns, then `#file:` to read specific examples.

**Output:** Code snippets with file:line references, usage context, variations, and testing examples.

**Does NOT:** Recommend one pattern over another, identify anti-patterns, suggest improvements.

### Web Researcher

**Purpose:** Find external documentation, best practices, and solutions from the web.

**Copilot:** Use web search capabilities in Copilot Chat or `copilot -p` with web search enabled.

**Search strategies by query type:**
- **API/Library docs:** Official docs first, then changelogs and release notes.
- **Best practices:** Recent articles from recognized experts, cross-reference multiple sources.
- **Technical solutions:** Specific error messages in quotes, Stack Overflow, GitHub issues.
- **Comparisons:** "X vs Y", migration guides, benchmarks.

---

## Copilot Extension Points

Copilot provides several mechanisms for extending agent capabilities. These map to different levels of the progressive disclosure hierarchy (see [context-engineering.md](context-engineering.md)).

### Path-Specific Instructions (`.github/instructions/`)

Path-specific instructions are auto-loaded when files matching their `applyTo` glob pattern are in context. Use them for domain-specific rules that should fire automatically.

```markdown
---
applyTo: "**/*.test.{ts,tsx}"
---
# Test File Conventions
- Use `describe` blocks grouped by function/method
- Always include a "happy path" and "error case" test
- Mock external dependencies, never real network calls
- Use factory functions for test data, not raw objects
```

**This is superior to Claude Code's skills system** because rules fire automatically based on what files are open — no manual invocation needed. TDD rules activate when test files are in context. API conventions activate when route files are open.

### Chat Modes (`.github/chatmodes/`)

Chat modes are specialized personas with behavioral constraints and tool restrictions. They provide structural enforcement of rules like the documentarian constraint.

```markdown
---
name: RPI Research
description: Research-only mode — describes what exists, never suggests changes
tools: ["codebase", "file"]
---
You are in RPI Research mode.

ABSOLUTE CONSTRAINT: You are a documentarian. Describe what EXISTS. Never suggest what SHOULD BE.
- No improvement suggestions, no problem identification, no critiques
- Every claim must include a file:line reference
- Structure output as a research document
```

**Why chat modes matter:** The documentarian rule is baked into the session at the mode level, not repeated per-prompt. More reliable than per-prompt injection because it constrains the agent's entire behavioral frame.

### MCP Servers (`.vscode/mcp.json`)

MCP (Model Context Protocol) servers extend Copilot's tool access to external systems. Configure in `.vscode/mcp.json`:

```json
{
  "servers": {
    "database": {
      "command": "npx",
      "args": ["-y", "@my-org/db-mcp-server"],
      "env": { "DATABASE_URL": "${input:dbUrl}" }
    }
  }
}
```

Use MCP servers for: database queries during research, API testing during validation, custom project tools.

### `.github/copilot-instructions.md`

A Copilot-specific instruction file that supplements AGENTS.md. Use it for rules that only apply to Copilot (not other tools):

- Copilot-specific behavioral constraints
- References to chat modes and prompt files
- VS Code integration notes

Keep it minimal — most instructions belong in AGENTS.md (cross-tool) or path-specific instructions (domain-scoped).

---

## Parallel Work Patterns

Without Agent Teams (which are Claude Code-specific), Copilot achieves parallelism through multiple independent processes and the `@copilot` cloud agent.

### Background `copilot -p` Processes

The primary parallelism mechanism. Each process runs in its own terminal with its own context:

```bash
# Parallel research — 3 terminals investigating different areas:
copilot -p "Research the authentication flow. Write findings to docs/research/auth.md" &
copilot -p "Research the database patterns. Write findings to docs/research/db.md" &
copilot -p "Research the API middleware chain. Write findings to docs/research/middleware.md" &
wait
```

**When to use:** Independent research tasks, parallel audits, batch migrations.

### `@copilot` Cloud Agent

Assign a GitHub Issue to `@copilot` for async implementation. The cloud agent:
- Reads the issue description and referenced files
- Creates a branch and implements the changes
- Opens a PR for review

**When to use:** After completing Research + Plan interactively, delegate the Implementation to the cloud agent by creating a GitHub Issue with the plan attached. This is a unique Copilot workflow not available in other tools.

**Best for:** Well-specified implementation tasks where the plan is complete and unambiguous. Not suitable for tasks requiring interactive Q&A or complex judgment calls.

### Pre-Launch Audit Pattern

The most common parallel pattern. Run specialist audits in parallel:

| Specialist | Focus |
|------------|-------|
| **architect** | Dependency health, TypeScript config, circular deps, dead code |
| **qa-lead** | Full test suite, coverage gaps, graceful degradation |
| **security-reviewer** | Dependency audit, hardcoded secrets, auth flows, injection vectors |
| **performance-eng** | Bundle sizes, unused exports, code splitting, Core Web Vitals |
| **ux-reviewer** | ARIA/a11y, keyboard nav, error states, design consistency |
| **devops** | Build verification, CI status, env vars, error pages, git state |

Run as parallel `copilot -p` processes, each writing to its own report file. Synthesize into a single pre-launch report afterward.

Each produces findings categorized as **blockers** (must fix), **warnings** (should fix), or **recommendations** (nice to have). Results synthesize into a single report with a verdict: READY, CONDITIONAL, or NOT READY.

---

## Agent Autonomy Principles

Agents should maximize what they accomplish autonomously before requesting human intervention.

### The Tool Exhaustion Rule

**Before asking the user to perform any manual step, exhaust all available tools first.**

1. **CLI tools** — `gh`, `git`, project-specific CLIs
2. **Shell commands** — `curl`, `pnpm`, build scripts (via `#tool:terminal`)
3. **MCP servers** — check what tools are available in the session
4. **Web search** — for documentation and solutions
5. **File operations** — read/edit/write for configuration changes

Only ask for manual intervention when genuinely required: OAuth consent flows, billing dashboards, hardware interaction, or actions that require elevated privileges the agent doesn't have.

### Autonomy Boundaries

#### The Function Stakes Framework

Classify every action by its risk level to determine autonomy:

| Stakes | Examples | Autonomy |
|--------|----------|----------|
| **Read-only** | Searching code, reading files, running tests, `git status`, `git log` | Fully autonomous |
| **Low** | Writing code per approved plan, creating branches, committing to feature branches | Fully autonomous |
| **Medium** | Pushing to `develop`, creating PRs, running `npm install` | Autonomous with post-action verification |
| **High** | Merging PRs, pushing to `main`/production, deploying, modifying external services | Human-gated — always ask first |
| **Critical** | Deleting branches, force-pushing, dropping databases, modifying CI/CD pipelines | Human-gated — explain consequences before asking |

#### The Quality Cascade Principle

Human review belongs at the highest-leverage points. A bad line of research can lead to a bad plan, which leads to hundreds of bad lines of code. Therefore:

1. **Research output** — Human reviews critically. Throw out and redo if wrong.
2. **Implementation plan** — Human reviews and approves before any code is written.
3. **Generated code** — Automated verification (tests, types, lint) is primary. Human spot-checks.

Invest review time at the top of the cascade, not the bottom. Once a plan is approved and tests pass, the code is trusted.

#### Time-Bounded Autonomy

For scheduled or background agents, use time limits as a safety boundary. An agent running for 15 minutes autonomously is reasonable; an agent running for 6 hours without check-in risks "overbaking" — producing increasingly bizarre emergent behaviors as it goes further off-track.

See [push-accountability.md](push-accountability.md) for the post-push verification protocol and [scheduled-agents.md](scheduled-agents.md) for recurring agent patterns.

### Self-Correction Over Escalation

When an agent encounters an error:
1. **Diagnose** — read the error, understand the root cause
2. **Fix** — attempt the fix using available tools
3. **Verify** — run the relevant checks to confirm the fix works
4. **Escalate only if stuck** — after 3 failed attempts, report the issue clearly and ask for guidance

Don't ask "should I fix this?" — just fix it. Don't suggest the user run a command you could run yourself.
