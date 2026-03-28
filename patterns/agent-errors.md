# Known Agent Errors — Universal Catalog

Documented from real recurring issues across projects. Each entry includes the symptom, root cause, and the correct approach to use from the start.

**How to use this file:** This is a debugging reference -- consult when encountering unexpected behavior, tool errors, or CI failures. Not required for onboarding. The operational rules in `patterns/quick-reference.md` provide the essential condensed reference for everyday work.

---

## Error #1: Commit rejected by pre-commit hook (typecheck/lint failure)

**Symptom:** Agent runs `git add <files> && git commit -m "..."` and it fails with exit code 1 because the pre-commit hook triggers a full typecheck/lint across the project and finds errors. Wasted time: the commit fails, the agent must fix errors, then re-stage and re-commit.

**Root cause:** The agent skipped running verification checks before committing. Pre-commit hooks enforce the same checks (typecheck, lint, tests) — discovering failures at commit time means unnecessary rework.

**Correct approach — always do this:**

```bash
# 1. Run the checks FIRST (same ones the pre-commit hook runs):
pnpm run typecheck 2>&1; pnpm run lint 2>&1

# 2. Fix any errors found

# 3. THEN stage and commit (the hook will pass):
git add <files> && git commit -m "fix(scope): description"
```

**Never do this:**

```bash
# Don't go straight to commit without checking first:
git add . && git commit -m "fix: something"  # ← hook fails, wasted time
```

**Key detail:** In monorepos, pre-commit hooks often run typecheck across ALL workspace packages, not just the files you changed. Pre-existing errors in other packages will block your commit even if your changes are clean.

---

## Error #2: Wrong `--json` field names for `gh` CLI commands

**Symptom:** Running `gh pr checks <PR> --json name,state,conclusion` fails with "Unknown JSON field: conclusion". The agent guesses field names that don't exist for that specific subcommand.

**Root cause:** `gh` CLI `--json` field names differ between subcommands. The agent assumes fields from one command (e.g., `gh run view`) work on another (e.g., `gh pr checks`). They don't.

**Correct approach — always do this:**

```bash
# If unsure of available fields, query them first:
gh pr checks <PR> --json 2>&1 | head -5

# Known correct fields for common commands:
# gh pr checks: name, state, bucket, completedAt, description, event, link, startedAt, workflowName
# gh pr view:   number, title, state, body, url, headRefName, baseRefName, mergeable, reviewDecision
# gh run view:  conclusion, status, name, event, headBranch, workflowName
# gh run list:  conclusion, status, name, event, headBranch, workflowName

# For CI status monitoring, use gh run list instead of gh pr checks:
gh run list --branch <branch> --limit 1 --json conclusion,status,name
```

**Never do this:**

```bash
# Don't guess field names across subcommands:
gh pr checks 377 --json name,state,conclusion  # ← "conclusion" doesn't exist here
```

---

## Error #3: SyntaxError running CLI tool with `node dist/index.js`

**Symptom:** Running `node dist/index.js --version` fails with `SyntaxError: Invalid or unexpected token` pointing at the shebang line (`#!/usr/bin/env node`). The stack trace shows `compileSourceTextModule` (ESM loader).

**Root cause:** The built file has a shebang (`#!/usr/bin/env node`) and uses ESM (`"type": "module"` in package.json). Node's ESM loader doesn't strip shebangs the same way as CJS.

**Correct approach — always do this:**

```bash
# Option 1: Execute via the shebang (needs +x permission):
chmod +x dist/index.js && ./dist/index.js --version

# Option 2: Use the package bin entry:
npx . --version

# Option 3: Check package.json "bin" field and use that name:
grep -A2 '"bin"' package.json
```

**Never do this:**

```bash
# Don't run ESM CLI files with node directly:
node dist/index.js --version  # ← SyntaxError on shebang
```

---

## Error #4: Cannot delete branch used by a worktree during PR merge

**Symptom:** Running `gh pr merge <PR> --merge --delete-branch` fails with "cannot delete branch 'fix/...' used by worktree at '/path/to/worktree'". The PR merges on GitHub but the local branch deletion fails.

**Root cause:** Git cannot delete a branch that is currently checked out in any worktree. The agent finished work in the worktree, pushed, created the PR, but forgot to remove the worktree before merging with `--delete-branch`.

**Correct approach — always do this:**

```bash
# 1. Remove the worktree FIRST (after pushing all changes):
git worktree remove --force /path/to/worktree

# 2. THEN merge the PR with branch cleanup:
gh pr merge <PR> --merge --delete-branch
```

---

## Error #5: `execSync(...).trim is not a function` — Buffer vs string

**Symptom:** Tests fail with `TypeError: (0, execSync)(...).trim is not a function` at runtime. Code like `execSync('some command').trim()` throws because `.trim()` doesn't exist on Buffer.

**Root cause:** Node.js `execSync()` returns a **Buffer** by default, not a string. String methods don't exist on Buffer.

**Correct approach — always do this:**

```typescript
// ALWAYS pass encoding to get a string back:
const output = execSync('some command', { encoding: 'utf-8' }).trim();
```

**Never do this:**

```typescript
const output = execSync('some command').trim();  // ← TypeError
```

---

## Error #6: `git push` rejected (non-fast-forward)

**Symptom:** `git push origin develop` fails with "non-fast-forward" — "Updates were rejected because the tip of your current branch is behind its remote counterpart."

**Root cause:** The remote branch has commits the local branch doesn't. The agent pushed without pulling first.

**Correct approach — always do this:**

```bash
# ALWAYS pull before pushing:
git pull --rebase origin <branch> && git push origin <branch>
```

---

## Error #7: Checking CI for multiple PRs in one jumbled command

**Symptom:** Agent chains multiple `gh pr checks` commands in one Bash call. Output is an unreadable mix of all PRs' results.

**Root cause:** Cramming multiple PR checks into one command produces jumbled output, and `gh pr checks` exits non-zero for `review: fail` which just means "needs approval", not CI failure.

**Correct approach — always do this:**

```bash
# Check one PR at a time with structured output:
gh pr checks <PR> --json name,state,bucket

# For multiple PRs, loop with clear labels:
for pr in 1 2 3; do echo "=== PR #$pr ==="; gh pr checks $pr --json name,state,bucket 2>&1; done

# Or just check the CI run directly:
gh run list --branch <branch> --limit 1 --json conclusion,status,name
```

---

## Error #8: `git worktree remove` fails, cascading failures with `&&`

**Symptom:** `git worktree remove .worktrees/foo && git worktree remove .worktrees/bar` fails on the first worktree ("contains modified or untracked files"), and `&&` chaining prevents the second from running.

**Root cause:** Worktrees always have untracked files (build artifacts, node_modules). The default `git worktree remove` refuses to delete them.

**Correct approach — always do this:**

```bash
# ALWAYS use --force and ; (not &&):
git worktree remove --force .worktrees/foo; git worktree remove --force .worktrees/bar; git branch -D branch1 branch2
```

---

## Error #9: Push and forget — CI breaks silently

**Symptom:** Agent pushes code to the development branch, immediately moves on to the next task, and never checks CI status.

**Root cause:** The agent treats `git push` as the end of the workflow. There's no accountability loop.

**Correct approach — always do this:**

```bash
# After every push, verify CI:
gh run list --branch develop --limit 1 --json conclusion,status,databaseId
# If it fails: gh run view <run-id> --log-failed 2>&1 | tail -100
# Fix and re-push
```

---

## Error #10: Skipping TDD — writing implementation before tests

**Symptom:** Agent writes implementation code first, then adds tests as an afterthought that merely assert the implementation is correct rather than specifying behavior.

**Root cause:** The agent defaults to implementation-first development without an explicit TDD mandate.

**Correct approach — always do this:**

```text
1. Write a failing test that describes the expected behavior (Red)
2. Write the minimum implementation to make it pass (Green)
3. Refactor while keeping tests green

For bug fixes: write a test that reproduces the bug FIRST.
```

---

## Error #11: Suggesting manual steps instead of using available tools

**Symptom:** Agent responds with "Go to the dashboard and click..." for operations it could perform itself using CLI tools, shell commands, or MCP servers.

**Root cause:** The agent defaults to instructional mode rather than action mode.

**Correct approach — always do this:**

```text
Before suggesting any manual step:
1. Can I use a CLI tool? (gh, git, curl, project CLIs)
2. Can I use #tool:terminal?
3. Can I use MCP servers?
4. Can I use file operations?
Only suggest manual intervention when genuinely required.
```

---

## Error #12: `git branch -d` fails on worktree branches (not fully merged)

**Symptom:** After removing a worktree, `git branch -d <branch>` fails with "the branch is not fully merged."

**Root cause:** Worktree branches are almost never "fully merged" (squash merges, deleted remotes, abandoned work). Lowercase `-d` safety check fails.

**Correct approach — always do this:**

```bash
# ALWAYS use -D (uppercase, force) for worktree branches:
git worktree remove --force /path/to/worktree; git branch -D <branch-name>
```

---

## Error #13: Missing YAML frontmatter in `.prompt.md` files

**Symptom:** Prompt file doesn't appear in the Copilot `/` command menu in VS Code. Running `/my-prompt` does nothing or shows "command not found."

**Root cause:** `.github/prompts/*.prompt.md` files require valid YAML frontmatter at the top of the file. Without `mode:` and `description:` fields, Copilot ignores the file.

**Correct approach — always do this:**

```markdown
---
mode: agent
description: "Brief description shown in the / menu"
---
# Prompt content here
```

**Key detail:** The `mode` field accepts `agent` (can make changes, run commands) or `ask` (read-only, conversational). If omitted, the file is silently ignored.

---

## Error #14: Using `$ARGUMENTS` instead of `${input:variableName}` in prompts

**Symptom:** The `$ARGUMENTS` placeholder in a prompt file is passed through literally instead of being replaced with user input. The agent receives the string "$ARGUMENTS" rather than what the user typed.

**Root cause:** `$ARGUMENTS` is a Claude Code convention. Copilot prompt files use `${input:variableName}` syntax for parameterized input.

**Correct approach — always do this:**

```markdown
---
mode: agent
description: "Research the codebase"
---
Research the codebase to answer: ${input:question}
```

**Never do this:**

```markdown
---
mode: agent
description: "Research the codebase"
---
Research the codebase to answer: $ARGUMENTS
```

---

## Error #15: Path-specific instructions not loading (missing `applyTo`)

**Symptom:** Rules defined in `.github/instructions/tests.instructions.md` are ignored. The agent doesn't follow test conventions even when test files are open.

**Root cause:** Instruction files require an `applyTo` glob pattern in YAML frontmatter. Without it, Copilot doesn't know when to load the file.

**Correct approach — always do this:**

```markdown
---
applyTo: "**/*.test.{ts,tsx}"
---
# Test conventions here
```

---

## Error #16: Chat mode file in wrong directory

**Symptom:** A `.chatmode.md` file exists but doesn't appear as a selectable chat mode in VS Code's Copilot panel.

**Root cause:** Chat mode files must be in `.github/chatmodes/`. Placing them in `.github/prompts/`, `.github/instructions/`, or project root has no effect.

**Correct approach — always do this:**

```text
.github/chatmodes/rpi-research.chatmode.md  ← correct
.github/prompts/rpi-research.chatmode.md    ← wrong directory, ignored
```

---

## Error #17: Copilot CLI auth expires in scheduled agents

**Symptom:** A scheduled agent script (`copilot -p "..."`) that worked yesterday now fails with an authentication error.

**Root cause:** The Copilot CLI auth token has a limited lifetime. Interactive sessions refresh it automatically, but headless `copilot -p` calls from cron/launchd don't trigger re-authentication.

**Correct approach — always do this:**

```bash
# In agent scripts, check auth status before running:
if ! copilot auth status > /dev/null 2>&1; then
  echo "[$(date)] Auth expired. Run 'copilot auth' interactively to refresh."
  exit 1
fi

# Periodically re-authenticate interactively:
copilot auth
```

**Prevention:** Add an auth check to every scheduled agent script. Log the failure clearly so you know to re-authenticate rather than debugging phantom errors.

---

## Error #18: Agent CLI crashes with "Unexpected" when plist runs script directly

**Symptom:** Agent plist with correct environment variables and auth still fails. The CLI returns a crash or unexpected error even for simple commands. The error is instant (< 1 second). Exit code may be 0 despite the error.

**Root cause:** When launchd directly executes a script located inside a project directory that has configuration folders (`.github/`, `.vscode/`, etc.), the CLI may misidentify the project context from the initial process arguments. This causes an internal crash before any real work begins. The same script works fine when located outside the project tree (e.g., `/tmp`), or when the plist uses `/bin/bash -c "exec /bin/bash <script>"` instead of running the script directly.

**Diagnostic clue:** The failure is **location-dependent**, not content-dependent. The same script at `/tmp/my-agent.sh` works, but at `/project/scripts/agents/my-agent.sh` fails. The error is a CLI bug in how it resolves project context under launchd's process model.

**Correct approach from the start:**

Use `/bin/bash -c "exec /bin/bash <script>"` in ProgramArguments instead of the script path directly:

```xml
<!-- WRONG — direct script execution, causes crash: -->
<key>ProgramArguments</key>
<array>
  <string>/path/to/project/scripts/agents/my-agent.sh</string>
</array>

<!-- ALSO WRONG — /bin/bash without -c exec, same crash: -->
<key>ProgramArguments</key>
<array>
  <string>/bin/bash</string>
  <string>/path/to/project/scripts/agents/my-agent.sh</string>
</array>

<!-- CORRECT — bash -c with exec wrapper: -->
<key>ProgramArguments</key>
<array>
  <string>/bin/bash</string>
  <string>-c</string>
  <string>exec /bin/bash /path/to/project/scripts/agents/my-agent.sh</string>
</array>
```

The `exec` replaces the initial shell process, so the agent script still runs as PID 1 of the launchd job (clean process tree, correct signal handling). The `-c` wrapper changes the initial process context so the CLI doesn't misidentify the project root from the launchd process arguments.

**Never do this:**

```xml
<!-- Don't run scripts directly — even with /bin/bash prefix: -->
<array>
  <string>/bin/bash</string>
  <string>/project/scripts/agents/my-agent.sh</string>
</array>
<!-- CLI may crash if the script is inside a project directory -->
```

**Key detail:** This error has minimal debug output — the CLI crashes before reaching initialization. The exit code may be 0 despite the error, which means auth preflight checks can silently pass, masking the problem. A working launchd agent plist should always use the `-c exec` ProgramArguments wrapper pattern, include `HardResourceLimits`/`SoftResourceLimits` for file descriptors, and set `EnvironmentVariables` for HOME, TERM, and PATH.

---

## Error #19: `git pull --rebase` fails with uncommitted changes

**Symptom:** `git pull --rebase && git push` exits with `error: cannot pull with rebase: You have unstaged changes. Please commit or stash them.` The agent just edited files and tried to pull without committing first.

**Root cause:** `git pull --rebase` requires a clean working tree. The agent finishes editing files, then immediately runs the pull+push sequence without committing the edits first. This is the most-repeated agent error across all observed sessions — in one batch of 16 screenshots, it appeared 6 times (37%).

**Correct approach — always do this:**

```bash
# ALWAYS commit first, then pull, then push:
git add <files> && git commit -m "feat(scope): description"
git pull --rebase && git push

# Or as a single chain:
git add <files> && git commit -m "msg" && git pull --rebase && git push
```

**Never do this:**

```bash
# Don't pull with uncommitted changes:
git pull --rebase && git push
# ← fails if you have any modified or untracked files

# Don't chain pull+push right after editing files:
# [edit files]
git pull --rebase && git push  # ← forgot to commit!
```

**Key detail:** Git itself blocks this operation, so no data is lost — but the agent wastes a turn hitting the error and then fixing it. The push recipe (`commit → pull → push`) should be used as a single compound command every time.

---

## Error #20: `git push --tags` pushes ALL local tags — old tags cause push failure

**Symptom:** `git push origin main --tags` exits non-zero with `! [rejected] v1.0 -> v1.0 (already exists)`. The new commits and new tags pushed fine, but the agent sees exit code 1 and treats the entire push as failed.

**Root cause:** `--tags` pushes every local tag to the remote, not just tags created in this session. If any tag was previously pushed, recreated locally, or already exists on the remote, git rejects it — and the non-zero exit code makes the agent think nothing was pushed. The agent then retries or panics, wasting turns.

**Correct approach — always do this:**

```bash
# Push commits and a specific tag by name:
git push origin main && git push origin v1.3.0

# Or use --follow-tags (only pushes annotated tags reachable from pushed commits):
git push origin main --follow-tags
```

**Never do this:**

```bash
# Don't push all tags blindly:
git push origin main --tags
# ← pushes EVERY local tag, fails if any already exists on remote

# Don't use --force to fix it:
git push origin main --tags --force
# ← force-pushes all tags, potentially overwriting remote tag history
```

**Key detail:** `--tags` and `--follow-tags` are very different. `--tags` pushes all refs under `refs/tags/`. `--follow-tags` only pushes annotated tags that point to commits being pushed. Use `--follow-tags` for release workflows, or push specific tags by name.

---

## Error #21: Agent fabricates filesystem paths — "No such file or directory"

**Symptom:** `git -C /Users/name/Documents/GenAI_Projects/cc-rpi pull --rebase` fails with `fatal: cannot change to '/Users/name/Documents/GenAI_Projects/cc-rpi': No such file or directory`. The actual path was `/Users/name/Documents/code/cc-rpi`.

**Root cause:** The agent guesses or hallucinates a plausible filesystem path instead of using the known working directory or discovering the path. Common fabrications include inventing parent directory names (`Projects`, `GenAI_Projects`, `repos`, `workspace`), getting the nesting level wrong, or mixing up similar project names.

**Correct approach — always do this:**

```bash
# Use the project's working directory (provided by the environment):
git -C /Users/name/Documents/code/cc-rpi pull --rebase

# If you need to find another project, discover it:
ls /Users/name/Documents/code/
# Then use the actual name from the listing

# Or ask the user for the path if it's not discoverable
```

**Never do this:**

```bash
# Don't guess directory names:
git -C /Users/name/Documents/GenAI_Projects/cc-rpi pull --rebase
# ← "GenAI_Projects" is fabricated — the real dir is "code"

# Don't assume paths from previous sessions are still valid:
cd /Users/name/projects/old-name/src
# ← directories may have been renamed, moved, or deleted
```

**Key detail:** The working directory is always available from the environment. For cross-project operations, use `ls` or file search to discover paths — never guess directory names. Even plausible-sounding names like `Projects` or `repos` are often wrong.

---

## Error #22: Scaffolding tool fails on non-empty directory

**Symptom:** `create-next-app`, `create-vite`, or similar scaffolding tools abort with errors like "The directory contains files that could conflict" or "Directory is not empty." The agent created AGENTS.md, `.github/`, or other config files before running the scaffolding tool.

**Root cause:** Most scaffolding tools require an empty directory (or create a new one). When the agent sets up project configuration first — creating AGENTS.md, `.github/prompts/`, instruction files — then tries to run the scaffolding tool, it finds existing files and refuses to proceed. The agent is following the blueprint setup order, but scaffolding tools expect to be first.

**Correct approach — always do this:**

```bash
# Run the scaffolding tool FIRST, in a clean directory:
npx create-next-app@latest my-project
# or: npm create vite@latest my-project

# THEN add project configuration:
cd my-project
# Create AGENTS.md, .github/prompts/, .vscode/settings.json, etc.
```

**Never do this:**

```bash
# Don't create config files before scaffolding:
mkdir my-project && cd my-project
# Create AGENTS.md, .github/prompts/, etc.
npx create-next-app@latest .
# ← FAILS: directory is not empty
```

**Key detail:** This applies to any tool that generates a project skeleton: `create-next-app`, `create-vite`, `create-react-app`, `cargo init`, `django-admin startproject`, `rails new`, `dotnet new`. The rule is always: scaffold first, configure second.

---

## Error #23: Piping API response to JSON parser without error checking

**Symptom:** `curl | jq` or `curl | python3 -c "import json; ..."` crashes with parse errors like "parse error (Invalid numeric literal)" or "json.decoder.JSONDecodeError: Expecting value." The API returned HTML (error page, auth failure, rate limit response) instead of JSON.

**Root cause:** The agent pipes `curl` output directly to a JSON parser without checking the HTTP status code or response content type. When the API returns a non-JSON response (HTML error page, plain-text auth failure, rate limit message), the parser receives invalid input and produces a confusing error that doesn't mention the actual problem.

**Correct approach — always do this:**

```bash
# Save response and check status first:
RESPONSE=$(curl -sf "$URL") || { echo "HTTP error"; exit 1; }
echo "$RESPONSE" | jq '.results'

# Or use curl's built-in failure mode:
curl -sf "$URL" | jq '.results'
# -s = silent, -f = fail on HTTP errors (exit code 22)
```

**Never do this:**

```bash
# Don't pipe curl directly to a parser:
curl -s "$URL" | jq '.results[0].name'
# ← crashes with parse error if API returns HTML/text

# Don't assume API responses are always JSON:
curl "$URL" | python3 -c "import json,sys; print(json.load(sys.stdin)['key'])"
# ← JSONDecodeError if response isn't JSON
```

**Key detail:** This is especially common with API keys passed via environment variables (`$API_KEY`). If the variable is unset or expired, the API returns an auth error in HTML/text format, and the JSON parser produces a confusing traceback that doesn't mention the actual auth problem. Always validate the response before parsing.

---

## Error #24: Agent commits or pushes to the wrong branch

**Symptom:** Agent pushes code to `main`, `master`, or a feature branch other than the intended target. The user discovers the wrong-branch push after the fact, requiring manual branch surgery: cherry-picking commits, resetting branches, and force-pushing to fix the history.

**Root cause:** The agent doesn't verify the current branch before committing. It assumes it's on the right branch based on conversation context, but the actual git state may differ — especially after switching tasks, resuming sessions, or when parallel agents operate independently. This is the git equivalent of "measure twice, cut once" — the agent cuts without measuring.

**Correct approach — always do this:**

```bash
# ALWAYS verify branch before any commit:
git branch --show-current   # Confirm this is the branch you intend to commit to

# If unsure, ask the user which branch to target.
# Then commit and push:
git add <files> && git commit -m "msg" && git pull --rebase && git push
```

**Never do this:**

```bash
# Don't commit without checking the branch:
git add . && git commit -m "feat: add feature" && git push
# ← May push to main, master, or wrong feature branch

# Don't assume the branch from conversation context:
# User said "push to develop" 50 messages ago — verify git state NOW
```

**Key detail:** This is especially damaging when pushing to `main`/`master` (production). The agent should verify before committing to any branch. Parallel agents are particularly prone to this — they don't inherit the parent's conversation context about which branch to target.

---

## Error #25: Parallel agents create git conflicts from overlapping work

**Symptom:** Multiple parallel agents (background `copilot -p` processes, `@copilot` cloud agents, or concurrent sessions) make changes independently. When their work is combined, there are merge conflicts, overlapping file edits, or orphaned references — imports to deleted functions, tests for renamed methods, or duplicate utility files.

**Root cause:** Parallel agents operate in isolated contexts and don't see each other's changes. When two agents edit the same file (or files that reference each other), the results conflict. The orchestrating workflow doesn't enforce file ownership boundaries or centralize git operations.

**Correct approach — always do this:**

```text
When orchestrating parallel agents:
1. Break work so each agent owns DISTINCT files — no overlap
2. Designate one agent or process as the git committer
3. Parallel agents write changes to working directories or /tmp/agent-<name>/
4. The committing process reviews all changes for conflicts before committing
5. Run the full test suite AFTER combining all agent output
```

**Never do this:**

```text
# Don't let parallel agents commit independently to the same branch:
copilot -p "Fix auth module, commit and push" &
copilot -p "Fix API module, commit and push" &
wait
# ← Race condition, merge conflicts, overlapping edits

# Don't assume parallel agents produce compatible output:
# Even if each agent's changes pass tests individually,
# the COMBINED changes may conflict
```

**Key detail:** `@copilot` cloud agents are particularly susceptible because each creates its own branch and PR. If two cloud agents touch related files, their PRs may conflict when merged. For related work, use sequential cloud agent assignments or ensure strict file ownership boundaries in the issue descriptions.

---

## Error #26: Agent skips test suite after config or infrastructure changes

**Symptom:** Agent modifies configuration files (tsconfig, eslint config, package.json, environment variables, database config, CI workflows) and immediately proceeds to the next task without running tests. Later — or in a subsequent session — tests fail due to the config change. The agent then burns multiple rounds debugging failures that could have been caught immediately.

**Root cause:** The agent treats config changes as "not code" and doesn't apply the same verify-after-change discipline it uses for source code. But config changes often have broader blast radius than code changes — a single tsconfig modification can break hundreds of files, and a dependency update can introduce incompatibilities across the entire test suite.

**Correct approach — always do this:**

```bash
# After ANY config or infrastructure change, immediately run the full suite:
pnpm run typecheck 2>&1; pnpm run lint 2>&1; pnpm run test 2>&1

# This applies to ALL of these:
# - tsconfig.json, eslint.config.*, prettier.config.*
# - package.json (dependencies, scripts, engines)
# - .env files, environment variable changes
# - Database migrations, schema changes
# - CI/CD workflow files
# - Docker/container configuration
# - Build configuration (vite.config, next.config, webpack.config)
```

**Never do this:**

```bash
# Don't modify config and move on without testing:
# Edit tsconfig.json to add strict mode
# Edit next.config.js to change build output
# → Immediately start writing new feature code
# ← Tests are now broken but you won't find out until much later
```

**Key detail:** Config changes have a multiplicative failure pattern — they can break files the agent never touched. Running the test suite immediately after a config change costs minutes but saves the multi-round debug cycles that happen when failures are discovered later with more changes stacked on top.

---

## Error #27: CI explosion from parallel agent pushes

**Symptom:** N agents working in parallel worktrees each push their branch independently. Every push triggers M CI workflows (test matrix, dependency review, CodeQL, etc.), resulting in N x M x retries workflow runs that compete for runner minutes. When agents debug and re-push, the runs multiply further. macOS runners (10x cost multiplier) amplify the bill. Additionally, agents pushing independently risk wrong-branch pushes and merge conflicts.

**Root cause:** Each agent autonomously pushes on commit, triggering CI. No central coordination of push timing. The agent treats "commit and push" as a single atomic operation instead of separating local commits from remote pushes.

**Correct approach — always do this:**

```bash
# 1. Spawn agents in worktrees (each gets its own branch)
# Main agent creates worktrees via git worktree add

# 2. Agents commit locally only — never push or create PRs
# Agent deliverable is a local commit on their branch

# 3. Main agent reviews all worktrees after agents complete
git -C /path/to/worktree-1 log --oneline -3
git -C /path/to/worktree-2 log --oneline -3

# 4. Batch push all branches in one command
git push origin branch-1 branch-2 branch-3

# 5. Create all PRs sequentially
gh pr create --head branch-1 --title "..." --body "..."
gh pr create --head branch-2 --title "..." --body "..."

# 6. Single background agent monitors all CI runs
gh run list --branch branch-1 --branch branch-2 --limit 10
```

**Never do this:**

```bash
# Don't let each agent push independently:
# Agent 1: git push origin branch-1  <- triggers CI
# Agent 1: (fix) git push origin branch-1  <- triggers CI again
# Agent 2: git push origin branch-2  <- triggers CI
# Agent 2: (fix) git push origin branch-2  <- triggers CI again
# = 4 push events x M workflows each = CI explosion

# Don't let agents create their own PRs:
# Agent 1: gh pr create --head branch-1
# Agent 2: gh pr create --head branch-2
# <- No central review, wrong-branch risk, API rate limits
```

**Key detail:** The savings compound with retries. If each of 8 agents pushes 3 times (initial + 2 fixes), that's 24 push events x 4 workflows = 96 CI runs. With batch push, the main agent pushes once (8 branches), monitors, and re-pushes only the 2 that failed = 10 push events x 4 workflows = 40 CI runs. The pattern also eliminates the class of bugs where an agent pushes to the wrong branch because only one agent touches the remote.

---

## Error #28: Agent assumes GitHub labels exist when creating issues

**Symptom:** `gh issue create --label "chore"` (or `"security"`, `"bug"`, `"enhancement"`, etc.) fails with `could not add label: 'chore' not found`. When multiple issues are created in quick succession, the first failure can block the rest.

**Root cause:** The agent assumes standard label names exist on the repository. GitHub repos start with no labels by default (or a small default set). Custom repos, forks, and newly created repos often have none of the labels the agent expects. The agent never checks what labels are available before using them.

**Correct approach — always do this:**

```bash
# Check what labels exist before using them:
gh label list

# If the label doesn't exist, create it first:
gh label create "chore" --description "Maintenance tasks" --color "ededed"

# Or omit labels on creation and add them after:
gh issue create --title "..." --body "..."
# Then add labels if they exist:
gh issue edit <number> --add-label "chore" 2>/dev/null || true
```

**Never do this:**

```bash
# Don't assume labels exist:
gh issue create --title "fix: auth bug" --label "bug" --label "security"
# <- fails if either label is missing
```

**Key detail:** This error is especially common after `/pre-launch` audits, where the agent tries to create multiple issues for findings and assigns category labels. The fix is to either create all needed labels upfront (`gh label create`), or omit labels entirely and let the user categorize.

---

## Error #29: Agent runs `gh pr create` without checking for existing PR

**Symptom:** `gh pr create --base main --head develop --title "Release v0.3.0"` fails with `a pull request for branch "develop" into branch "main" already exists: https://github.com/.../pull/36`. The agent then tries to recover by editing or recreating the PR, wasting turns.

**Root cause:** The agent doesn't check whether a PR already exists for the head-to-base branch pair before attempting to create one. This commonly happens during release workflows where a develop-to-main PR may already be open from a previous push, or when a previous agent session created the PR but didn't finish its workflow.

**Correct approach — always do this:**

```bash
# Check if a PR already exists for the branch pair:
EXISTING_PR=$(gh pr list --head develop --base main --json number --jq '.[0].number')

if [ -n "$EXISTING_PR" ]; then
  # Update the existing PR:
  gh pr edit "$EXISTING_PR" --title "Release v0.3.0" --body "..."
else
  # Create a new PR:
  gh pr create --base main --head develop --title "Release v0.3.0" --body "..."
fi
```

**Never do this:**

```bash
# Don't blindly create without checking:
gh pr create --base main --head develop --title "Release v0.3.0" --body "..."
# <- fails if PR already exists for develop -> main
```

**Key detail:** This is especially common in gitflow-style workflows where a develop-to-main PR persists across multiple release cycles, and in CI/CD pipelines where automated agents create PRs. The same pattern applies to any repeated workflow — release PRs, dependency update PRs, sync PRs. Always check first and update if one exists.

---

## Error #30: `git checkout --` fails on unmerged (conflicted) files

**Symptom:** `git checkout -- src/components/chat/chat-interface.tsx` fails with `error: path 'src/components/chat/chat-interface.tsx' is unmerged`. The agent was trying to discard changes during a merge or rebase conflict, but `git checkout --` doesn't work on files in a conflicted state.

**Root cause:** During a merge, rebase, or cherry-pick that hits conflicts, affected files enter an "unmerged" state. `git checkout -- <file>` is designed to restore a file to its last committed version, but it can't do that for unmerged files because git doesn't know which version to restore to — there are multiple candidates (ours, theirs, base). The agent treats `git checkout --` as a universal "discard changes" command without considering the conflict state.

**Correct approach — always do this:**

```bash
# If you want to keep YOUR version of conflicted files:
git checkout --ours src/components/chat/chat-interface.tsx
git add src/components/chat/chat-interface.tsx

# If you want to keep THEIR version of conflicted files:
git checkout --theirs src/components/chat/chat-interface.tsx
git add src/components/chat/chat-interface.tsx

# If you want to abort the entire merge/rebase/cherry-pick:
git merge --abort       # during a merge
git rebase --abort      # during a rebase
git cherry-pick --abort # during a cherry-pick

# To check what state you're in:
git status  # Shows "Unmerged paths" section with conflicted files

# For bulk resolution (all ours or all theirs):
git checkout --ours -- . && git add -A     # keep all our versions
git checkout --theirs -- . && git add -A   # keep all their versions
```

**Never do this:**

```bash
# Don't use plain checkout -- on conflicted files:
git checkout -- src/components/chat/chat-interface.tsx
# <- "error: path '...' is unmerged"

# Don't retry the same command on more files:
git checkout -- file1.tsx file2.tsx file3.tsx
# <- same error for every file, all are unmerged
```

**Key detail:** The error message "is unmerged" means you're in the middle of a conflicted merge/rebase/cherry-pick. Before trying to discard changes, check `git status` to see the conflict state. The three options are: resolve the conflicts (edit + `git add`), pick a side (`--ours`/`--theirs`), or abort the operation entirely. Plain `git checkout --` is only for non-conflicted files.

---

## Error #31: `git merge` blocked by untracked working tree files

**Symptom:** `git merge feature-branch --no-edit` fails with `error: The following untracked working tree files would be overwritten by merge:` followed by a list of files. Git aborts the merge.

**Root cause:** The branch being merged contains files that also exist as untracked files in the current working tree. Git refuses to merge because it would overwrite the untracked copies with no way to recover them. This commonly happens when an agent creates files in the main repo (plans, docs, reports) while a parallel agent independently creates the same files on its branch. When the lead agent tries to merge, the duplicate untracked files block the merge.

**Correct approach — always do this:**

```bash
# 1. Check what untracked files would conflict:
git merge --no-commit --no-ff <branch> 2>&1 | grep "error:"
# Or just attempt the merge and read the error output

# 2. Remove or move the conflicting untracked files:
rm docs/plans/phase2.md docs/plans/phase3.md
# Or move them to a backup:
mkdir -p /tmp/merge-backup && mv <conflicting-files> /tmp/merge-backup/

# 3. Then retry the merge:
git merge <branch> --no-edit

# Prevention: when orchestrating parallel agents, ensure the main repo
# doesn't create files in the same paths the parallel agent will produce
```

**Never do this:**

```bash
# Don't retry the merge without removing the conflicting files:
git merge <branch> --no-edit  # <- same error, files still there

# Don't use git clean -fd blindly (may delete other needed files):
git clean -fd && git merge <branch>
# <- deletes ALL untracked files, not just the conflicting ones

# Don't create the same files in both the main repo and a feature branch:
# Main repo: creates docs/plans/phase2.md (untracked)
# Agent branch: commits docs/plans/phase2.md to branch
# <- merge will fail
```

**Key detail:** This is a coordination problem in multi-agent workflows. When the lead agent and parallel agents work simultaneously, they must not produce files at the same paths. The lead agent should defer creating shared artifacts (plans, docs, reports) until after merging, or the parallel agent should create them in a distinct location. If the conflict occurs, the simplest fix is to delete the local untracked copies (the branch version will replace them on merge).

---

## Error #32: Agent merges to `main` without understanding deployment topology

**Symptom:** Agent is asked to "clean up Dependabot PRs" or "merge the passing PRs." It merges them to `main`, triggering production deployments. One of the merged dependencies contains a production-only bug. The live site goes down. The agent didn't realize that merging to `main` = deploying to production.

**Root cause:** The agent doesn't check what happens when code lands on `main`. In any project with CI/CD connected to `main` (Vercel, AWS, Netlify, Railway, etc.), a merge to `main` is an immediate production deployment. Dependabot PRs target `main` by default. The agent treats "merge the PR" as a git operation without considering the deployment side effects.

**Correct approach — always do this:**

```bash
# Before merging anything, understand the deployment topology:
# 1. Which branches trigger deployments? (check CI/CD config)
# 2. Does main deploy to production? (almost always yes)
# 3. Is there a develop/staging branch? (use that instead)

# For Dependabot PRs (which target main by default):
# Option A: Cherry-pick updates to develop, close the Dependabot PR
git checkout develop
git cherry-pick <dependabot-commit-sha>
# Then close the Dependabot PR without merging

# Option B: Retarget the PR to develop (if repo allows)
gh pr edit <N> --base develop

# Never merge Dependabot PRs directly to main
```

**Never do this:**

```bash
# Don't merge Dependabot PRs to main without explicit production
# deployment authorization:
gh pr merge 171 --squash   # <- triggers production deployment
gh pr merge 170 --squash   # <- triggers another production deployment
# Each merge is a production deployment.

# Don't assume "merge the PRs" means "deploy to production":
# User said "clean up the Dependabot PRs" — that means close/retarget,
# not deploy
```

**Key detail:** "Merge the PRs" is never implicit authorization to deploy to production. The agent must recognize that Dependabot PRs target `main` and that merging them has deployment side effects. The correct interpretation of "clean up" for Dependabot PRs is: assess, cherry-pick to develop, close the PRs. If the user wants a production deployment, they will say "deploy to production" or "merge to main" explicitly.

---

## Error #33: Sequential merge cascade wastes CI resources (O(n^2) rebase storm)

**Symptom:** Agent merges N dependency PRs one-by-one on a branch with "require branches to be up-to-date" branch protection. Each merge invalidates the checks on all remaining PRs, forcing a rebase and full CI re-run for each. For 7 PRs with 9 CI workflows, this creates 30+ unnecessary CI runs from rebases alone — pure waste.

**Root cause:** The agent doesn't consider the cost multiplication of sequential merges. When branch protection requires branches to be up-to-date before merging, each merge to the target branch invalidates every other PR targeting the same branch. The remaining PRs must rebase and re-run all checks. This creates O(n^2) CI runs instead of O(1).

**Correct approach — always do this:**

```bash
# Batch all dependency updates into a single branch:
git checkout -b chore/dependency-updates develop

# Apply all updates to the single branch:
git cherry-pick <dep-1-sha> <dep-2-sha> <dep-3-sha>
# Or manually update package.json/requirements.txt/Cargo.toml and run install

# Run CI once on the combined result:
git push -u origin chore/dependency-updates
gh pr create --base develop --title "chore: batch dependency updates"
# = 1 CI run instead of 30+
```

**Never do this:**

```bash
# Don't merge PRs one-by-one when branch protection requires
# up-to-date checks:
gh pr merge 171 --squash   # <- triggers rebase of all other PRs
gh pr merge 170 --squash   # <- triggers rebase again
# Each step: rebase K remaining PRs x M workflows = waste
```

**Key detail:** The cost formula is: for N PRs with M CI workflows, sequential merging with up-to-date requirements costs approximately N x (N-1) / 2 x M workflow runs in rebases alone. Batching into a single PR costs M runs total. Always batch dependency updates.

---

## Error #34: Agent deploys untested code to production (no staging verification)

**Symptom:** Agent merges a framework upgrade (e.g., Next.js, Django, Rails minor version bump) after CI passes. Build succeeds, tests pass, local server works. But on the deployment platform, the app crashes at runtime. The bug only manifests on the platform's specific runtime — local and CI environments don't reproduce it.

**Root cause:** The agent treats CI passing as sufficient evidence that code is production-ready. But CI tests build correctness, not runtime correctness on the target platform. Build success != runtime success. Local success != production success. Platform-specific behaviors (serverless cold starts, container startup, edge runtimes, module resolution) can cause failures that no local test or CI check would catch.

**Correct approach — always do this:**

```bash
# For framework upgrades and risky changes:
# 1. Push to a non-main branch to trigger a staging/preview deployment
git push -u origin chore/framework-upgrade

# 2. Wait for the staging deployment to complete
# (Most platforms create preview/staging URLs for non-main branches)

# 3. Verify the staging deployment:
# - Site loads, API routes respond, key pages render
# - Health checks pass, serverless functions execute
curl -s -o /dev/null -w "%{http_code}" https://staging-url.example.com

# 4. Only after staging verification passes, create PR to main
gh pr create --base main --title "chore: upgrade framework to X.Y.Z"

# For low-risk changes (dev dependency patches):
# CI passing is sufficient — no staging verification needed
```

**Never do this:**

```bash
# Don't merge framework upgrades after CI alone:
# CI passes -> merge to main -> production crashes
# CI checks build, lint, and tests — not platform runtime behavior

# Don't trust local verification for production readiness:
# npm run build && npm start -> works locally
# But on serverless/container runtime: different module resolution, crash

# Don't merge without checking the risk level of the dependency
```

**Key detail:** Platform-specific bugs are invisible to CI and local testing. A framework that works perfectly in local Node.js/Python can fail on AWS Lambda, ECS, or any serverless/container runtime because module resolution, environment variables, file system access, and startup behavior all differ. A single staging deployment catches what CI cannot.

---

## Error #35: Agent improvises production recovery with repeated failed deployments

**Symptom:** Production is down. The agent promotes a broken deployment "briefly" to capture logs — site goes down again. Deploys a fix with errors — fails. Deploys again with env var issues — fails. Each failed attempt is another billed deployment and another outage window. The investigation took multiple deployments and hours when a simple rollback would have restored service in minutes.

**Root cause:** The agent panics and improvises instead of following a structured recovery protocol. It tries to diagnose and fix simultaneously, using production as its test environment. Each failed recovery attempt extends the outage and costs money (build minutes, compute, bandwidth).

**Correct approach — always do this:**

```text
When production is down, follow this exact sequence:

1. ROLL BACK immediately to the last known good deployment.
   Do not investigate. Do not "try one more thing." Restore service first.

2. VERIFY the rollback — confirm the site is operational.

3. INVESTIGATE on a non-production environment:
   - Read deployment platform logs (they persist after rollback)
   - Deploy the broken code to a staging URL for isolated reproduction
   - Test locally (but remember: local != production)

4. FIX FORWARD on develop:
   - Create the fix on a feature branch
   - Verify on staging deployment
   - Merge to main only after staging verification

5. COUNT THE COST — if you've deployed more than 2 times during recovery,
   stop and re-evaluate your approach. Something is wrong.
```

**Never do this:**

```text
# Don't promote broken deployments to "capture logs":
# Platform logs persist — you don't need to break production to read them

# Don't deploy to diagnose:
# "Let me deploy this to see what error I get" = another billed deploy + outage

# Don't attempt multiple recovery deployments without a plan:
# Each failed attempt is another billed deployment and another outage window
```

**Key detail:** The key insight is that rollback and investigation are separate actions. Roll back first (minutes), then investigate at your own pace (no time pressure, no outage). The worst pattern is investigating while production is down — every minute spent diagnosing is a minute of outage, and the pressure to "fix it fast" leads to more mistakes.

---

## Error #36: Agent treats all dependency updates as equal risk

**Symptom:** Agent processes multiple Dependabot PRs identically — same review depth, same merge strategy, same verification level. The batch includes both a framework upgrade (high risk — affects entire runtime) and a dev-tool patch (zero runtime risk). The framework upgrade breaks production; the dev patches would have been fine.

**Root cause:** The agent doesn't assess dependency risk before merging. It applies a uniform strategy to all dependency updates regardless of: (a) whether the dependency is a runtime or dev dependency, (b) whether it's a patch, minor, or major version bump, (c) whether it's a framework (affects everything) or a utility library (affects one feature).

**Correct approach — always do this:**

```text
Before merging any dependency update, classify it:

| Factor | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| Type | devDependency | dependency (utility) | dependency (framework) |
| Bump | patch (x.y.Z) | minor (x.Y.0) | major (X.0.0) |
| Scope | single tool | single feature | entire runtime |

Verification by risk level:
- Low: CI passing is sufficient
- Medium: CI + local smoke test
- High: CI + staging/preview deployment + manual verification
- Critical (major framework): Full QA cycle, staged rollout

Merge low-risk updates together. High-risk updates get individual attention.
```

**Never do this:**

```text
# Don't treat all updates the same:
# "All 7 PRs passed CI, merge them all" — CI doesn't catch platform issues

# Don't merge framework upgrades in a batch with other updates:
# If the batch breaks production, you can't tell which update caused it

# Don't skip risk assessment because "it's just a minor version":
# Minor versions of frameworks can introduce production-breaking changes
```

**Key detail:** The risk matrix is not just about the version number. A patch to a framework can be higher risk than a major bump to a dev dependency. The factors are: (1) is it in the runtime path? (2) how much of the app does it affect? (3) does the deployment platform have specific behaviors the dependency interacts with? Framework upgrades for serverless/container deployments are always high risk because the deployment runtime differs from local/CI environments.

---

## Error #37: Silent fallback masks production data failure

**Symptom:** The app appears to work fine — pages load, no errors in the console, health checks pass. But users see stock/placeholder content instead of real data. The root cause is a backend failure (database permission error, API auth expiry, missing migration grant) that triggers a fallback code path. The fallback serves default data silently, with no logging, no alerting, and no health check degradation. Nobody knows production is broken until a user reports seeing wrong content.

**Root cause:** The agent writes "resilient" code with graceful degradation — if the primary data fetch fails, return fallback data. This is good practice in theory, but the agent implements it without any observability: no error-level logging when the fallback activates, no health endpoint that detects degraded state, no metrics or alerts. The fallback becomes a silent failure mode that hides real production bugs.

Real example: A Supabase migration created tables but didn't include `GRANT SELECT TO anon`. The fetch function got a 403, silently fell back to hardcoded default data with stock images. The site looked "fine" — it just wasn't showing real content.

**Correct approach — always do this:**

```typescript
// When implementing fallback behavior, ALWAYS add three layers:

// 1. ERROR-LEVEL LOGGING when fallback activates
async function getStoriesServer() {
  const { data, error } = await supabase.from('stories').select('*');
  if (error || !data?.length) {
    // NOT console.log — this must be ERROR level, searchable, alertable
    console.error('[STORIES_FALLBACK] Primary fetch failed, serving fallback data', {
      error: error?.message,
      code: error?.code,
      timestamp: new Date().toISOString(),
    });
    return FALLBACK_STORIES;
  }
  return data;
}

// 2. HEALTH ENDPOINT that detects degraded state
// GET /api/health should check actual data sources, not just "server is up"
async function healthCheck() {
  const stories = await supabase.from('stories').select('id').limit(1);
  return {
    status: stories.error ? 'degraded' : 'healthy',
    stories: { status: stories.error ? 'fallback' : 'ok' },
  };
}

// 3. ALERTING on the health endpoint or error logs
// Configure your monitoring to alert on:
// - Health endpoint returning "degraded"
// - [STORIES_FALLBACK] appearing in function logs
```

**Never do this:**

```typescript
// Don't create silent fallbacks:
async function getStoriesServer() {
  const { data, error } = await supabase.from('stories').select('*');
  if (error || !data?.length) {
    return FALLBACK_STORIES;  // <- silent! no logging, no alerting
  }
  return data;
}

// Don't write health checks that only test connectivity:
async function healthCheck() {
  return { status: 'ok' };  // <- always "ok", even when serving fallback data
}

// Don't log fallbacks at INFO/DEBUG level:
console.log('Using fallback stories');  // <- invisible in production log noise
```

**Key detail:** The pattern applies to any code with fallback behavior — not just database queries. API clients with default responses, feature flags with hardcoded defaults, CDN fallbacks to origin, cache miss handlers that return stale data. Whenever you write a fallback path, ask: "If this fallback activates in production, will anyone know?" If the answer is no, add error logging and health check coverage before shipping.

---

## Error #38: Agent pushes Supabase migration to remote without local testing

**Symptom:** A migration works in the agent's mental model but fails when applied to the remote Supabase project — missing columns, wrong types, RLS policy errors, or broken references. The remote database is now in a partially migrated state. Rolling back requires manual intervention in the Supabase dashboard or a new corrective migration. In the worst case, the broken migration runs on the production database and causes downtime.

**Root cause:** The agent writes a migration SQL file, runs `supabase db push` directly, and treats success (no syntax error) as validation. It never tests the migration against a local Postgres instance. Supabase provides a full local development stack (`supabase start`) with Postgres, RLS, extensions, and auth — but the agent skips it and pushes straight to remote.

Real example: An agent created a migration adding a foreign key to a table that didn't exist yet (the referenced table was in a later migration file). `supabase db push` failed on the remote project with a foreign key constraint error. The agent then wrote a "fix" migration that also failed because it didn't understand the remote state. Two broken migrations had to be manually cleaned up in the Supabase dashboard.

**Correct approach — always do this:**

```bash
# 1. Ensure local Supabase is running (requires Docker Desktop)
supabase start

# 2. Apply all migrations to the local Postgres instance
supabase db reset

# 3. Verify the migration worked (query the local database)
# The container name follows the pattern supabase_db_<project>
# where <project> is the Supabase project name from supabase/config.toml
docker exec supabase_db_myproject psql -U postgres -c "\d my_new_table"
docker exec supabase_db_myproject psql -U postgres -c "SELECT * FROM my_new_table LIMIT 1"

# 4. Only after local verification succeeds, push to remote
supabase db push
```

**Never do this:**

```bash
# Don't push migrations without local testing:
supabase migration new add_stories_table
# ... write SQL ...
supabase db push  # <- directly to remote, no local verification

# Don't assume "no syntax error" means the migration is correct:
supabase db push  # "Applied 1 migration" <- doesn't mean it's right

# Don't write fix-up migrations without testing locally first:
supabase migration new fix_foreign_key  # <- another untested migration
supabase db push  # <- compounds the problem
```

**Key detail:** The local Supabase instance is a full Postgres with RLS, extensions, and auth — it's not a mock. If a migration works locally with `supabase db reset`, it will work on the remote. If `supabase start` fails, Docker Desktop needs to be running. The container name follows the pattern `supabase_db_<project>` where `<project>` comes from `supabase/config.toml`.
