# Agent Operational Rules -- Quick Reference

Scope: `[universal]` `[frequent]` `[situational]` `[rare]`
Stack: `[node]` `[python]` `[macos]` `[github]` (omitted = all stacks)

## Shell & Tools

1. **Run typecheck/lint before committing** `[universal]` -- pre-commit hooks run the same checks. Fix first, commit second.

2. **Exhaust all tools before suggesting manual steps** `[universal]` -- check CLI tools, shell commands, MCP servers, file tools before escalating to the user.

3. **Don't fabricate filesystem paths** `[universal]` -- the agent invents plausible names (`Projects`, `repos`). Use the working directory or discover with `ls`/Glob.

4. **Save curl output before parsing** `[universal]` -- `curl | jq` crashes with unhelpful errors when the API returns HTML or auth failures. Save response first and check HTTP status, or use `curl -sf`.

## Git

5. **Pull before push** `[universal]` -- remote may have advanced from other sessions or parallel agents.

6. **Remove worktrees before merging PRs with `--delete-branch`** `[frequent]` -- Git can't delete a branch checked out in a worktree.

7. **Force-remove worktrees** `[frequent]` -- worktrees have build artifacts/node_modules. Use `git worktree remove --force` with `;` not `&&` for multiple removals.

8. **Use `git branch -D` (uppercase) for worktree branches** `[frequent]` -- squash merges and deleted remotes make `-d` fail with "not fully merged." Full cleanup: `git worktree remove --force <path>; git branch -D <branch>`.

9. **Commit or stash before `git pull --rebase`** `[universal]` -- fails with a dirty working tree. Push recipe: `git add <files> && git commit -m "msg" && git pull --rebase && git push`. Single most-repeated agent error.

10. **Push specific tags, not `--tags`** `[universal]` -- `--tags` pushes ALL local tags. If any old tag exists on remote, git exits non-zero. Use `git push origin <tag>` or `--follow-tags`.

11. **Verify current branch before committing** `[universal]` -- run `git branch --show-current` before `git commit`. Don't assume from conversation context.

## GitHub CLI

12. **Don't guess `gh --json` field names** `[universal]` `[github]` -- fields differ per subcommand. Run `gh <cmd> --json 2>&1 | head -5` first. `conclusion` exists on `gh run` but not `gh pr checks`.

13. **Check CI per-PR with `--json`** `[universal]` `[github]` -- jumbled human-readable output is unreadable. `review: fail` means "needs approval", not CI failure -- filter it out.

14. **Don't assume GitHub labels exist** `[frequent]` `[github]` -- `gh issue create --label "chore"` fails if the label doesn't exist. Run `gh label list` first, or `gh label create`.

15. **Check for existing PRs before `gh pr create`** `[frequent]` `[github]` -- fails if a PR already exists for the branch pair. Check with `gh pr list --head <branch>` first; use `gh pr edit` to update.

## CI & Verification

16. **Verify CI after every push** `[universal]` -- if CI fails, investigate and re-push. The push is not done until CI is green.

17. **Write tests before implementation (TDD)** `[universal]` -- Red-Green-Refactor. Bug fixes need a regression test first.

18. **Run full test suite after config changes** `[universal]` -- config changes (tsconfig, eslint, package.json, .env, CI workflows) have broader blast radius than code changes. Run typecheck + lint + test immediately.

19. **Run scaffolding tools before adding config files** `[situational]` `[node]` -- `create-next-app`, `create-vite`, etc. require an empty directory. Creating AGENTS.md first causes the scaffolder to abort.

## Copilot-Specific

20. **Include YAML frontmatter in `.prompt.md` files** `[universal]` -- prompt files without frontmatter won't appear in the `/` command menu. At minimum include `mode: agent` (or `mode: ask` for read-only prompts). The `description` field is required for discoverability.

21. **Use `${input:variableName}` for prompt parameters, not `$ARGUMENTS`** `[universal]` -- Copilot prompt files use `${input:varName}` syntax. The `$ARGUMENTS` pattern is Claude Code-specific and won't work.

22. **Path-specific instruction files need `applyTo` in frontmatter** `[frequent]` -- `.github/instructions/*.instructions.md` files are ignored if they lack the `applyTo` glob pattern. No `applyTo` = never loaded.

23. **Authenticate the Copilot CLI before using it in cron/launchd** `[situational]` `[macos]` -- `copilot -p` in headless mode requires pre-authenticated credentials. Run `copilot auth` interactively first, then verify from a non-interactive shell.

24. **Proactive compaction before auto-compaction** `[universal]` -- Copilot auto-compacts at ~95% context usage, but quality degrades well before that. Write a handoff document and start a new Chat window at ~60% usage.

25. **Chat mode files must be in `.github/chatmodes/`** `[universal]` -- placing them anywhere else (e.g., `.github/prompts/` or project root) means they won't appear as selectable chat modes in VS Code.

## Node.js / TypeScript

26. **Pass `{ encoding: 'utf-8' }` to `execSync`/`spawnSync`** `[frequent]` `[node]` -- they return Buffers by default. `.trim()` and other string methods fail on Buffer.

27. **Don't run ESM CLI tools with `node <file>`** `[situational]` `[node]` -- shebang + ESM = SyntaxError. Use `chmod +x && ./<file>` or `npx .`.

## Multi-Agent

28. **Designate one agent as the git committer** `[universal]` -- sub-agents write changes; the committing agent reviews, tests, and commits centrally. Prevents wrong-branch pushes and merge conflicts.

29. **Only the main agent pushes -- worktree agents commit locally** `[universal]` -- N independent pushes trigger N x M CI runs. Agents commit locally, main agent batch-pushes all branches, creates PRs, monitors CI centrally.

44. **Parallel agents run scoped tests only -- full suite runs once at integration** `[universal]` -- N agents each running the full test suite creates N x workers processes that exhaust CPU/memory. Agents test only their changed files; limit concurrent agents to 3-4; run the full suite once after merging.

## Deployment & Resources

30. **Merging to main IS deploying to production** `[universal]` -- in projects with CI/CD, a merge is a deployment. Dependabot PRs target main by default -- merging them deploys to production.

31. **Batch dependency updates into a single PR** `[frequent]` -- merging N PRs one-by-one with "require up-to-date" creates O(n^2) CI waste. Create one branch, apply all updates, run CI once.

32. **Every CI run costs money -- count before triggering** `[universal]` -- estimate runs before starting. If >2-3, find a more efficient approach. Work locally until confident, push once.

33. **Framework upgrades need preview verification** `[frequent]` -- CI passing is necessary but not sufficient. Build != Runtime. Deploy to a preview URL and verify the site loads before merging.

34. **When production is down: roll back first** `[universal]` -- restore service immediately. Investigate on a non-production environment. Fix forward on develop, verify on preview, release to main.

35. **Justify every external action before triggering** `[universal]` -- before any CI run, deployment, or API call: Is this needed? Is this justified? Is this verifiable? If any answer is "no", stop.

## Supabase

36. **Test migrations locally before pushing to remote** `[frequent]` -- run `supabase start` + `supabase db reset` locally, verify with `docker exec ... psql`, then `supabase db push`. The local instance has full Postgres with RLS and extensions -- treat it as UAT.

## Quality & Process

37. **Fix everything, always** `[universal]` -- categorize by severity, but fix 100%. With AI agents, fix cost is near-zero.

## Observability

38. **Every fallback path must be observable** `[universal]` -- add ERROR-level logging when fallbacks activate, health endpoint coverage for degraded state, and alerting hooks. A silent fallback is a silent production bug.

## launchd

39. **launchd plist must not run project scripts directly** `[rare]` `[macos]` -- `<string>/project/scripts/agent.sh</string>` causes CLI crashes when the script is inside a project directory. Use `/bin/bash -c "exec /bin/bash <script>"` wrapper. Exit code may be 0 despite the error.

## Git Conflict Resolution

40. **Use `--ours`/`--theirs` for unmerged files** `[situational]` -- `git checkout --` fails on unmerged files during merge/rebase conflicts. Use `git checkout --ours <file>` or `--theirs`, or abort entirely. Check `git status` first.

41. **Remove conflicting untracked files before merge** `[situational]` -- untracked files at the same paths as incoming files cause git to abort. Delete or move them first.

## Agent Reports

42. **Agent report commit policy depends on repo visibility** `[universal]` -- check `gh repo view --json visibility` at setup time. **Public repos:** gitignore `docs/agents/`, `logs/`, `scripts/agents/` so operational details (security findings, internal metrics, agent status) don't leak. Reports stay local; only code fixes are committed. **Private repos:** track all three directories. Triage commits reports alongside code fixes as historical artifacts. Missing remote or `gh` unavailable fail-safes to PUBLIC behavior.

43. **Use timestamp-based discovery for triage, not git status** `[universal]` -- touch `docs/agents/.last-triage` after each triage run. Next triage discovers new reports with `find docs/agents/ -name "*-report.md" -newer docs/agents/.last-triage`. On first run (no marker), process all reports.

45. **Triage processes Dependabot PRs** `[frequent]` `[github]` -- `/triage` scans `gh pr list --author "app/dependabot"` in Step 1 Discovery and processes them after the triage commit is pushed. Patch and minor with green CI auto-merge via `gh pr merge --squash --auto --delete-branch`. Major bumps defer for human review. CI red with an obvious fix (snapshot/lockfile drift, generated files) gets one fix attempt before deferring. Conflicts get one rebase via `gh pr update-branch`, then re-evaluated. Dependabot processing happens last so a flaky dependency PR can't block triage code fixes.

---

For detailed symptoms, root causes, and examples, see [agent-errors.md](agent-errors.md).

For the full deployment safety guide and resource efficiency patterns, see [deployment-safety.md](deployment-safety.md).
