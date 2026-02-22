# Context Engineering

> "The contents of your context window are the ONLY lever you have to affect the quality of your output."

## The Stateless Function Mental Model

At every turn, a coding agent is a stateless function call: the full context window goes in, the next action comes out. There is no hidden memory, no persistent state beyond what's in the window. This means:

- Everything the agent needs to make a good decision must be IN the context window
- Everything that ISN'T needed is noise that degrades decision quality
- The entire RPI workflow is, at its core, a **context management strategy**

## Context Quality Hierarchy

Optimize your context window for these properties, in priority order:

| Priority | Property | Worst Case |
|----------|----------|------------|
| 1 (highest) | **Correctness** | Incorrect information leads to confidently wrong output |
| 2 | **Completeness** | Missing information leads to incomplete or misguided output |
| 3 | **Size / Noise** | Too much irrelevant content drowns the signal |
| 4 | **Trajectory** | Poor trajectory (conversation going off-track) compounds with each turn |

**The equation:** Quality is proportional to (Correctness x Completeness) / Noise.

## What Eats Context

These activities consume large amounts of context window space:

- **File searching** — directory listings, search results
- **Code understanding** — Reading file contents, tracing data flow
- **Applying edits** — Diffs, edit confirmations, error-retry cycles
- **Test/build logs** — Verbose compiler output, test runner output
- **Large tool responses** — JSON blobs, API responses

This is why background `copilot -p` processes are valuable: they consume context in THEIR session and return only the distilled result as a file you can reference.

## Frequent Intentional Compaction

The core technique that makes RPI work at scale.

**What is compaction?** Distilling raw context (file searches, code reads, test logs) into structured artifacts (research documents, plans, status summaries).

**Three forms of compaction:**

### 1. Ad-hoc compaction

When your context starts filling up mid-session, pause and write progress to a markdown file:

> "Write everything we did so far to progress.md — note the end goal, the approach, steps completed, and the current issue we're working on."

Then start a fresh Chat window pointing at that file.

### 2. Background process compaction

Background `copilot -p` processes do file searching, code reading, and analysis in THEIR context and return only the structured summary as a file. This is NOT about "role-playing" — separate processes are a **context control mechanism**.

### 3. Phase compaction (the RPI workflow itself)

Each phase produces a compact artifact:

- Research -> research document (compact summary of codebase state)
- Plan -> implementation spec (compact description of what to change)
- Implement -> committed code + updated plan checkboxes
- Validate -> validation report

Each phase starts with a fresh context window that reads only the compact artifact from the previous phase, not the raw exploration that produced it.

**The ideal compacted output includes:**

- What we're trying to accomplish (goal)
- What we've learned so far (findings with file:line refs)
- What approach we're taking (decisions made)
- What's been done (completed steps)
- What's next (remaining work)
- What's currently blocking (if anything)

### Good vs Bad Compaction

**Good compaction — preserves signal, discards noise:**

> **Goal:** Add rate limiting to the login endpoint.
> **Approach:** Redis sliding window, per-IP (20/15min) and per-email (5/15min). Fail-open on Redis outage.
> **Done:** Phase 1 complete — `src/auth/rate-limiter.ts` implemented with 6 passing unit tests. Uses atomic INCR+EXPIRE via MULTI/EXEC.
> **Key learning:** Redis session storage at `src/auth/session.ts:5` uses the same connection — reuse it instead of creating a new client.
> **Next:** Phase 2 — middleware wrapper at `src/middleware/rate-limit.ts`. Wire into `src/routes/auth.ts:12`.
> **Blocking:** Nothing.

This is 6 lines that let a fresh session continue from exactly where we left off. Every line is actionable.

**Bad compaction — loses critical details:**

> We worked on rate limiting. Made good progress on the first phase. Tests are passing. Need to do the middleware next.

This is useless to a fresh session. No file paths, no design decisions, no specific state. The new session would need to re-research everything.

**Bad compaction — too much noise:**

> [500 lines of test output, full file contents of rate-limiter.ts, conversation about whether to use INCR vs ZADD, 3 failed approaches before the working one, the full Redis documentation we read...]

This defeats the purpose. A compaction that preserves everything is not a compaction — it's a copy. Discard exploration paths, failed approaches, and raw tool output. Keep only the structured findings.

### What Gets Discarded vs Preserved

| Discard (noise) | Preserve (signal) |
|-----------------|-------------------|
| File search results | Which files are relevant and why |
| Raw file contents | Key findings with `file:line` references |
| Failed approaches and dead ends | The working approach and why it was chosen |
| Test output on success | Pass/fail status of each verification step |
| Full test output on failure | The specific error message and root cause |
| Conversation about alternatives | The decision made and its rationale |
| Tool invocation details | The structured result of the investigation |

## Compaction via Commit Messages

Git commit messages are another compaction surface. Well-written commits serve as a compressed log of what changed and why, which future research agents can use to quickly understand project history without reading every file.

## Context Utilization Target

Aim to keep context utilization at **40-60%** of the window. Above 60%, output quality degrades noticeably. If you're approaching this threshold:

1. Compact current progress to a markdown file
2. Start a fresh Chat window
3. Point the new conversation at the compacted artifact

This is why the RPI phases are separate conversations, not one long session.

## Research on Main, Implement in Branches

Research and planning should happen on the `main`/`develop` branch — they don't modify code, so there's no risk. Implementation should happen in a feature branch, keeping the default branch clean. This also means multiple research/planning sessions can happen in parallel without conflicts.

## Multiple Research Passes

Sometimes the first research pass is wrong or incomplete. This is expected. The right response is to:

1. Read the research critically
2. If it's off-base, throw it out entirely
3. Start a new research session with more specific steering
4. Repeat until the research accurately reflects reality

Plans built with accurate research fix problems in the *right* place and prescribe testing aligned with codebase conventions.

## Progressive Disclosure

Not all context is needed at all times. AGENTS.md is loaded every session, so it should contain only **universally applicable** instructions. Everything else should live in supplementary files that the agent loads on demand.

**The hierarchy:**

| Layer | When Loaded | What Goes Here |
|-------|-------------|----------------|
| **AGENTS.md** | Every session (all tools) | Build/test commands, git workflow, operational rules, stack overview |
| **`.github/copilot-instructions.md`** | Every Copilot session | Copilot-specific addenda (if any rules only apply to Copilot) |
| **Path-specific instructions** (`.github/instructions/*.instructions.md`) | Auto-loaded when matching files are open | Domain rules: test patterns, API conventions, migration guidelines |
| **Supplementary docs** (`docs/`, `agent_docs/`) | When agent decides to read | Architecture details, database schemas, service patterns |
| **Research artifacts** (`docs/research/`) | When starting a related task | Previous investigation results, codebase maps |

**Why this matters:** The more non-universal content in AGENTS.md, the higher the chance the agent deprioritizes your actual instructions. Keep AGENTS.md lean; put specialized knowledge in path-specific instructions and docs.

**In supplementary files:** Use `file:line` references instead of code snippets. Snippets go stale; references can be verified at read time.

## AGENTS.md as Context Surface

AGENTS.md is your highest-leverage context engineering tool — it's the only file guaranteed to be in every conversation across all tools (Copilot, Claude Code, Cursor, Gemini CLI). Treat it accordingly:

**Capacity:** Frontier models can follow ~150-200 instructions with consistency. The tool's system prompt already uses some of those. Budget wisely.

**What to include vs exclude:**

| Include | Exclude |
|---------|---------|
| Bash commands the agent can't guess | Anything the agent can infer from code |
| Code style rules that differ from defaults | Standard language conventions |
| Test runners and verification commands | Detailed API docs (link instead) |
| Branch naming, PR conventions | Information that changes frequently |
| Architectural decisions specific to the project | Long explanations or tutorials |
| Environment quirks (required env vars) | File-by-file codebase descriptions |
| Common gotchas and non-obvious behaviors | Self-evident practices like "write clean code" |

**Authoring principles:**

- Manually craft every line. Don't auto-generate — bad instructions compound through research, plans, and code.
- For each line, ask: "Would removing this cause the agent to make mistakes?" If not, cut it.
- Don't use the agent for linting — it's expensive and slow vs. deterministic tools. Use automated formatters + hooks instead.
- Use emphasis (IMPORTANT, CRITICAL, NEVER) sparingly for rules that truly matter. Overuse dilutes everything.
- Check AGENTS.md into git. It compounds in value as the team contributes.
- Review it when things go wrong — if the agent ignores a rule, the file is probably too long.

## Session Lifecycle

Context doesn't have to be managed only through RPI phases. Copilot provides session-level techniques:

- **New Chat window** — Reset context between unrelated tasks. The single most underused technique.
- **Handoff documents** — When context is heavy, write a progress doc and start a new session pointing at it. Copilot auto-compacts at ~95% context usage, but proactive compaction at ~60% produces much better results.
- **`#codebase` reference** — In Copilot Chat, use `#codebase` to let the agent search the full codebase without you manually finding files. This is similar to an Explore subagent.
- **File references** — Use `#file:path/to/file.ts` to add specific files to context without pasting their contents.

**When to start fresh vs continue:**

- Switching to an unrelated task → New Chat window
- Same task but context is heavy → Write handoff doc, start fresh
- Tried an approach that failed → Start fresh with a better initial prompt
- After two failed corrections on the same issue → Start fresh

## Headless Mode and Fan-out

For CI pipelines, batch operations, and scaling beyond a single session:

- **`copilot -p "prompt"`** — Run Copilot headlessly without an interactive session. The `@github/copilot` CLI.
- **Fan-out pattern** — Generate a task list, then loop: `for file in $(cat files.txt); do copilot -p "Migrate $file"; done`
- **Writer/Reviewer pattern** — Run two sessions: one implements, another reviews the implementation in fresh context (unbiased by having written it).
- **`@copilot` cloud agent** — Assign a GitHub Issue to the `@copilot` cloud agent for async implementation. Unique to Copilot — not possible in other tools.

## Configuration Surfaces

Copilot has 7 distinct configuration files, each serving a different purpose:

| File | Scope | Purpose |
|------|-------|---------|
| **`AGENTS.md`** | Cross-tool (root) | Primary instruction file. Read by Copilot, Claude Code, Cursor, Gemini CLI. |
| **`.github/copilot-instructions.md`** | Copilot-only (global) | Copilot-specific addenda. Loaded every Copilot session alongside AGENTS.md. |
| **`.github/instructions/*.instructions.md`** | Copilot-only (path-specific) | Auto-loaded when files matching the `applyTo` glob are in context. |
| **`.github/prompts/*.prompt.md`** | Copilot-only (commands) | Reusable prompts invoked with `/` in chat. YAML frontmatter for metadata. |
| **`.github/chatmodes/*.chatmode.md`** | Copilot-only (personas) | Specialized chat personas with behavioral constraints and tool restrictions. |
| **`.vscode/settings.json`** | VS Code (shared) | Model selection, Copilot feature flags, editor behavior. |
| **`.vscode/mcp.json`** | VS Code (shared) | MCP server configuration for external tool access. |

**The progressive disclosure principle applies:** AGENTS.md → path-specific instructions → supplementary docs. Each layer adds more specialized context without polluting the universal layer.

## Copilot Settings & Permissions

### VS Code Settings

Configure `.vscode/settings.json` to control Copilot behavior:

```json
{
  "chat.agent.enabled": true,
  "github.copilot.chat.agent.thinkingTool": true,
  "github.copilot.chat.agent.autoFix": true
}
```

### Model Selection

Different tasks benefit from different models. Configure in VS Code settings or select per-session:

- **Complex reasoning** (architecture, debugging, planning) → most capable model available (e.g., GPT-4.1, o3)
- **Routine tasks** (formatting, simple edits, file operations) → faster model
- **Bulk operations** (migrating many files, batch formatting) → fastest model

Leave the `model` field empty in `.prompt.md` files — let VS Code settings control model selection centrally. This keeps prompt files portable.

### MCP Servers

Configure external tools via `.vscode/mcp.json`:

```json
{
  "servers": {
    "my-tool": {
      "command": "npx",
      "args": ["-y", "@my-org/my-mcp-server"],
      "env": {
        "API_KEY": "${input:apiKey}"
      }
    }
  }
}
```

MCP servers extend Copilot's capabilities with project-specific tools — database access, API clients, custom validators.

### Environment Variables

Agents inherit environment variables from the VS Code terminal. For projects that need API keys, database URLs, or service credentials:

- Store them in `.env` (gitignored) for local development
- Document required variables in AGENTS.md so agents know what's available
- Never hardcode secrets in AGENTS.md or instructions — reference `.env` instead

## You Need a Domain Expert

For complex codebases, at least one person on the team should be an expert in the codebase (or the relevant area). The RPI pattern amplifies expert knowledge — it doesn't replace it. When both participants are unfamiliar with the codebase, research tends to miss critical dependency chains and architectural constraints.
