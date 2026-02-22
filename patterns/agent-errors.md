# Known Agent Errors — Universal Catalog

Documented from real recurring issues across projects. Each entry includes the symptom, root cause, and the correct approach to use from the start.

**How to use this file:** Read this before starting any work. These are patterns coding agents hit repeatedly — the solutions are known and should be applied from the first attempt, not rediscovered.

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
```
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
```
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
```
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
