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

The key advantage is that rules fire automatically based on what files are open — no manual invocation needed. TDD rules activate when test files are in context. API conventions activate when route files are open.

### Interface Design Over Worked Examples

The strongest lever for correct tool use is the interface itself, not a demonstration of it. Design parameters, enums, `applyTo` globs, and file layouts so the correct path is implied by the shape of the interface — a parameter named `mode: "read" | "write" | "append"` teaches the three valid states and rules out a fourth, at a fraction of the context cost of three worked examples showing each mode in use. Reach for a worked example only when the interface genuinely cannot carry the meaning — an escaping quirk, an exact error string, an ordering constraint no type signature expresses.

The reason isn't just cost. A worked example is a demonstration, and a capable model tends to follow the demonstrated path literally — extrapolating from one shown shape constrains it to that shape instead of the full space the interface actually allows. A well-named enum with three valid values teaches more than three worked examples and leaves the model free to combine them in ways no single example showed.

This does not contradict the wrong/right example pairs used throughout this blueprint's prompts and error catalog. Those pairs mostly encode an **environment fact** — this exact flag, this exact frontmatter key, this exact error string a real tool actually produces — and a fact isn't something interface design can imply; it has to be stated. Keep those. The distinction to apply going forward: if an example merely demonstrates a shape a well-designed interface could have implied instead (which enum value to pass, which file goes where), replace it with better interface design; if it records a fact the model has no other way to learn, keep the example.

### Role Profiles and Legacy Local Chatmodes

Canonical workflows render to `.github/skills/`; scoped specialist roles render to `.github/agents/`. The old `.github/chatmodes/` entries are retained only for the optional VS Code Local compatibility profile until migration and native qualification. A role description is guidance, not mechanical enforcement of read-only tool boundaries. Verify the selected client's actual discovery and permissions.

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

Copilot achieves parallelism through multiple independent processes and the `@copilot` cloud agent.

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

### Optional `@copilot` Cloud Agent

Cloud-agent issue delegation is an opt-in external profile. Use it only when the owner explicitly authorizes the issue, branch and PR actions, and its setup is qualified for the target project. Local RPI work does not create GitHub issues or cloud jobs by default. The local integration and exact-candidate verification contract remains controlling.

### Quality Review Pattern

After each implementation phase, run a quality review pass. This is separate from self-review:

- **Self-review** checks plan compliance — "did I follow the plan?"
- **Quality review** (`/quality-review`) checks code reuse, quality, and efficiency — "is the code good?"

Plan compliance needs an independent reviewer, not only the implementation author. After repairing that review, run a separate simplify pass for reuse, quality and efficiency. A fresh context or qualified reviewer can supply independent review; missing reviewer evidence blocks acceptance.

The `rpi-quality-review` skill reviews the `git diff` for three concerns: code reuse opportunities (existing utilities that could replace new code), code quality issues (redundant state, copy-paste, leaky abstractions), and efficiency problems (unnecessary work, missed concurrency, hot-path bloat). Unlike a full `/pre-launch` audit, this is scoped to changed files only.

### Batch-Eligible Independent Units

A plan may mark independent units **within one authorized phase** `[batch-eligible]` when their file ownership does not overlap and their outputs do not depend on each other. Give each unit a bounded objective, owned files, evidence, resource limit and terminal condition. Keep at most three implementers and use fewer when the task or available slots do not justify three. One integration owner combines and verifies the local result. Phase execution and acceptance remain sequential even when the user authorizes continuation across all phases. Do not publish working branches or PRs as batch output.

### Pre-Launch Audit Pattern

The most common parallel pattern. Run all 8 specialist domains as parallel
`copilot -p` processes, each writing to its own report file. Synthesize
into a 16-section pre-launch report afterward.

| Specialist | Code | Focus |
|------------|------|-------|
| **Principal Architect** | AR | Architecture, module boundaries, coupling, dependency health, circular deps, dead code, typecheck |
| **Staff Frontend Engineer** | FE | Component structure, state management, routing, client-side perf, hydration, bundle composition |
| **Staff Backend Engineer** | BE | API design, validation, error handling, retry/idempotency, DB access, transactions, queues |
| **Performance Engineer** | PE | Bundle sizes, unused exports, code splitting, cache strategy, CPU/memory/IO inefficiencies |
| **DevOps / SRE Lead** | DO | Deployment safety, rollback, env config, secrets, migrations, CI/CD, health checks, observability |
| **Security Reviewer** | SE | Dependency audit, hardcoded secrets, auth/authz gaps, injection (SQL/XSS/SSRF), unsafe defaults |
| **QA / Reliability Lead** | QA | Full test suite (sole domain authorized), coverage, graceful degradation, retry/idempotency |
| **Product Designer / UX Lead** | UX | Visual hierarchy, design system, a11y (ARIA, focus, keyboard nav), error/loading/empty states |

Rule #44: QA/Reliability Lead is the ONLY specialist authorized to run
the full `$TEST_CMD`. Other 7 domains must not run it in parallel.

Each specialist:

1. Reports a **Domain Model** first (entry points, data flow, key files)
2. Lists findings using a structured format with Finding IDs
   (`<DOMAIN>-(B|H|M|L|S)<COUNTER>`, e.g., `SE-B1`, `UX-M3`, `BE-H2`)
3. Categorizes by severity: launch-blocker | high | medium | low | strategic
4. Tags by time horizon: Before launch | After launch | Later

The report drives `/remediate` which processes findings in 3 waves:
Wave 1 (Before launch), Wave 2 (After launch), Wave 3 (Later/strategic).
Wave 3 strategic items receive a local disposition and owner review. Creating GitHub issues requires separate authorization.

---

## Git Protocol for Multi-Agent Work

One integration owner manages the local `main` result. Give independent agents distinct files, a resource budget, scoped checks, and a terminal condition. A worktree agent can commit only to its local task branch; the integration owner reviews and integrates that branch after verification. Working branches stay local. Only the completed integration branch may be published, after local gates, trigger inspection, and explicit authorization. The owner checks the exact pushed commit and reports failed remote runs without autonomous reruns or fix-and-repush cycles.

Before each commit, verify the current branch. Before removing a task worktree, inspect dirty and untracked files, preserve intended work, and verify integration. Do not delete another agent's worktree or an unproven branch.

### Scope Discipline and the Watchdog

The most expensive multi-agent failure is not a wrong fix — it is a **runaway
agent** that keeps working after its job is done, or a **duplicate agent** that
redoes work a sibling already committed. Both burn hours and premium requests
silently.

Three orchestrator obligations prevent it:

| Obligation | Rule |
|------------|------|
| **Scoped spawn** | Every agent gets a single-sentence task and an explicit terminal condition ("stop the moment X is true"). Never spawn with open-ended verbs like "look into" or "investigate" — they have no natural stopping point. |
| **Watchdog budget** | Assign a wall-clock budget (~15–20 min for a focused fix). If a `copilot -p` agent is still running past it, kill it and inspect rather than assuming progress. Require periodic status checkpoints on long fan-outs so a stuck agent is visible. |
| **Dedup gate** | Before an agent does or continues work, it checks real repo state (`git log`, `git status`, `grep` for the artifact). If the work already landed on the branch, it stops and reports instead of producing a duplicate. |

This pairs with the central-commit pattern: the main agent owns the watchdog
because it owns the merge. A worktree `copilot -p` agent cannot see its
siblings — so the orchestrator, not the agent, is responsible for noticing
redundant work.

**Scope a spawn — wrong vs. right:**

```text
Wrong (open-ended, no stop condition — the agent investigates for hours):
"Look into the rate-limit failures and fix what you find."

Right (one-sentence scope + explicit terminal condition):
"Fix the failing applyRateLimit test in src/rate-limit.test.ts so the suite
is green. STOP the moment that test passes — do not investigate other
failures, refactor, or open new threads. Report back with the diff."
```

**Dedup before continuing — check actual repo state first:**

```bash
git log --oneline -10              # has a sibling already landed this?
git status                         # is the change already staged/committed?
grep -rn "applyRateLimit" test/    # does the artifact already exist?
```

If the work is already done, stop and report — do not redo it (a second copy
of a test block a sibling already committed is the classic duplicate).

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
| **Medium** | Installing development dependencies, local branch integration | Autonomous with local verification |
| **High** | Pushing to `main`, creating PRs, deploying, modifying external services | Requires explicit authorization; use authorization already given for the concrete action |
| **Critical** | Force-pushing, dropping databases, or changing remote infrastructure | Requires explicit authorization for the concrete destructive action |

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
