# Agent Operational Rules — Quick Reference

These rules must be internalized before starting any work. They prevent the most common recurring errors across all projects.

## Git Rules

1. **Always run typecheck/lint BEFORE committing** — pre-commit hooks run the same checks. Fix errors first, then commit. Don't discover failures at commit time.

2. **Always `git pull --rebase` before pushing** — remote may have advanced from other sessions, merged PRs, or parallel agents.

3. **Remove worktrees BEFORE merging PRs with `--delete-branch`** — Git can't delete a branch checked out in a worktree.

4. **Always `git worktree remove --force`** — worktrees have build artifacts/node_modules. Use `;` not `&&` for multiple removals. Apply fixes to ALL instances in a chain, not just the first.

5. **Always `git branch -D` (uppercase) for worktree branches** — worktree branches are almost never "fully merged" in git's view (squash merges, deleted remotes, abandoned work). Full cleanup idiom: `git worktree remove --force <path>; git branch -D <branch>`

6. **Commit or stash before `git pull --rebase`** — `git pull --rebase` requires a clean working tree. Always commit your changes first. The push recipe is: `git add <files> && git commit -m "msg" && git pull --rebase && git push`. This is the single most-repeated agent error.

7. **Use `git push origin <tag>` instead of `--tags`** — `--tags` pushes ALL local tags. If any old tag already exists on the remote, git exits non-zero even though commits and new tags pushed fine. Push specific tags by name, or use `--follow-tags`.

8. **Don't fabricate filesystem paths — use the working directory or discover with `ls`** — the agent invents plausible directory names (`Projects`, `GenAI_Projects`, `repos`) that don't exist. Use the environment's working directory for the current project, and `ls` or file search to discover paths for other projects.

## GitHub CLI Rules

1. **Don't guess `gh` CLI `--json` field names** — fields differ per subcommand. Run `gh <cmd> --json 2>&1 | head -5` first if unsure. `conclusion` exists on `gh run` but NOT `gh pr checks`.

2. **Check CI per-PR with `--json`, not chained human-readable output** — jumbled output is unreadable. `review: fail` means "needs approval", NOT a CI failure — always filter it out.

## Node.js / TypeScript Rules

1. **Always pass `{ encoding: 'utf-8' }` to `execSync`/`spawnSync`** — they return Buffers by default. `.trim()` and other string methods fail on Buffer.

2. **Don't run ESM CLI tools with `node <file>`** — shebang + ESM = SyntaxError. Use `chmod +x && ./<file>` or `npx .` instead.

## CI & Workflow Rules

1. **Never push and forget** — after every push to the development branch, verify CI passes. If CI fails, investigate, fix, and re-push. The push isn't done until CI is green.

2. **Always write tests before implementation (TDD)** — Red-Green-Refactor, every time. Bug fixes need a regression test first. No "tests later." Tests written after implementation tend to be tautological.

3. **Exhaust all tools before suggesting manual steps** — before telling the user "go to the dashboard and...", check if you can use CLI tools, shell commands, MCP servers, or terminal commands to do it yourself. Only escalate when genuinely impossible.

## Copilot-Specific Rules

1. **Always include YAML frontmatter in `.prompt.md` files** — prompt files without frontmatter won't appear in the `/` command menu. At minimum include `mode: agent` (or `mode: ask` for read-only prompts). The `description` field is required for discoverability.

2. **Use `${input:variableName}` for prompt parameters, not `$ARGUMENTS`** — Copilot prompt files use `${input:varName}` syntax for user input. The `$ARGUMENTS` pattern is Claude Code-specific and won't work.

3. **Path-specific instruction files need `applyTo` in frontmatter** — `.github/instructions/*.instructions.md` files are ignored if they lack the `applyTo` glob pattern in their YAML frontmatter. No `applyTo` = never loaded.

4. **Authenticate the Copilot CLI before using it in cron/launchd** — `copilot -p` in headless mode requires pre-authenticated credentials. Run `copilot auth` interactively first, then verify from a non-interactive shell.

5. **Proactive compaction before auto-compaction** — Copilot auto-compacts at ~95% context usage, but quality degrades well before that. Write a handoff document and start a new Chat window at ~60% usage for best results.

6. **Chat mode files must be in `.github/chatmodes/`** — placing them anywhere else (e.g., `.github/prompts/` or project root) means they won't appear as selectable chat modes in VS Code.

## launchd Rules

1. **launchd plist must NOT run project scripts directly** — `<string>/project/scripts/agent.sh</string>` in ProgramArguments causes CLI crashes when the script is inside a project directory. Use `/bin/bash -c "exec /bin/bash <script>"` wrapper instead. Exit code may be 0 despite the error, so preflight checks silently pass.

---

For detailed symptoms, root causes, and examples, see [agent-errors.md](agent-errors.md).
