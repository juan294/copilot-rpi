# Agent Operational Rules -- Quick Reference

Scope: `[universal]` `[frequent]` `[situational]` `[rare]`
Stack: `[node]` `[python]` `[macos]` `[github]` (omitted = all stacks)

## Shell & Tools

1. **Run typecheck/lint before committing** `[universal]` -- pre-commit hooks run the same checks. Fix first, commit second.

2. **Exhaust all tools before suggesting manual steps** `[universal]` -- check CLI tools, shell commands, MCP servers, file tools before escalating to the user.

3. **Don't fabricate filesystem paths** `[universal]` -- the agent invents plausible names (`Projects`, `repos`). Use the working directory or discover with `ls`/Glob.

4. **Save curl output before parsing** `[universal]` -- `curl | jq` crashes with unhelpful errors when the API returns HTML or auth failures. Save response first and check HTTP status, or use `curl -sf`.

## Git

5. **Reconcile before an authorized push** `[universal]` -- preserve local work, inspect the current remote integration ref, and reconcile divergence before publishing the completed integration branch.

6. **Preserve and integrate work before removing worktrees** `[frequent]` -- Git cannot delete a checked-out branch, but cleanup follows proof that task work, untracked files, and handoffs are preserved.

7. **Inspect worktrees before cleanup** `[frequent]` -- preserve intended changes and unknown artifacts. Remove only task-owned worktrees after verified integration; use `--force` only after reviewing what it would discard.

8. **Delete task branches after verified integration** `[frequent]` -- try safe deletion first. Use `-D` only when squash integration is proven and the branch has no unique work.

9. **Commit or preserve intended work before pulling** `[universal]` -- `git pull --rebase` refuses a dirty tree. Reconcile only after inspecting both refs; push needs separate authority.

10. **Push specific tags, not `--tags`** `[universal]` -- `--tags` pushes ALL local tags. If any old tag exists on remote, git exits non-zero. Use `git push origin <tag>` or `--follow-tags`.

11. **Verify current branch before committing** `[universal]` -- run `git branch --show-current` before `git commit`. Don't assume from conversation context.

## GitHub CLI

12. **Don't guess `gh --json` field names** `[universal]` `[github]` -- fields differ per subcommand. Run `gh <cmd> --json 2>&1 | head -5` first. `conclusion` exists on `gh run` but not `gh pr checks`.

13. **Check CI per-PR with `--json`** `[universal]` `[github]` -- jumbled human-readable output is unreadable. `review: fail` means "needs approval", not CI failure -- filter it out.

14. **Don't assume GitHub labels exist** `[frequent]` `[github]` -- `gh issue create --label "chore"` fails if the label doesn't exist. Run `gh label list` first, or `gh label create`.

15. **Check for existing PRs before `gh pr create`** `[frequent]` `[github]` -- fails if a PR already exists for the branch pair. Check with `gh pr list --head <branch>` first; use `gh pr edit` to update.

## CI & Verification

16. **Verify CI after an authorized push** `[universal]` -- inspect every expected workflow for the exact pushed commit. Diagnose failures from logs and reproduce locally; report the failed remote result before another remote action.

17. **Write tests before implementation (TDD)** `[universal]` -- Red-Green-Refactor. Bug fixes need a regression test first.

18. **Run full test suite after config changes** `[universal]` -- config changes (tsconfig, eslint, package.json, .env, CI workflows) have broader blast radius than code changes. Run typecheck + lint + test immediately.

19. **Run scaffolding tools before adding config files** `[situational]` `[node]` -- `create-next-app`, `create-vite`, etc. require an empty directory. Creating AGENTS.md first causes the scaffolder to abort.

## Copilot-Specific

20. **Legacy Local prompt files need YAML frontmatter** `[situational]` -- when the optional VS Code Local prompt profile is selected, keep valid `description` and supported mode metadata. Canonical workflows use `.github/skills/`.

21. **Use Copilot inputs in legacy Local prompts** `[situational]` -- optional `.prompt.md` wrappers use `${input:varName}` rather than Claude Code `$ARGUMENTS`; canonical skills carry the workflow body.

22. **Path-specific instruction files need `applyTo` in frontmatter** `[frequent]` -- `.github/instructions/*.instructions.md` files are ignored if they lack the `applyTo` glob pattern. No `applyTo` = never loaded.

23. **Authenticate the Copilot CLI before using it in cron/launchd** `[situational]` `[macos]` -- `copilot -p` in headless mode requires pre-authenticated credentials. Run `copilot auth` interactively first, then verify from a non-interactive shell.

24. **Proactive compaction before auto-compaction** `[universal]` -- Copilot auto-compacts at ~95% context usage, but quality degrades well before that. Write a handoff document and start a new Chat window at ~60% usage.

25. **Treat chatmode files as legacy Local surfaces** `[situational]` -- preserve existing `.github/chatmodes/` entries until migration and native qualification; current role profiles render as `.github/agents/`.

## Node.js / TypeScript

26. **Pass `{ encoding: 'utf-8' }` to `execSync`/`spawnSync`** `[frequent]` `[node]` -- they return Buffers by default. `.trim()` and other string methods fail on Buffer.

27. **Don't run ESM CLI tools with `node <file>`** `[situational]` `[node]` -- shebang + ESM = SyntaxError. Use `chmod +x && ./<file>` or `npx .`.

## Multi-Agent

28. **Designate one agent as the git committer** `[universal]` -- sub-agents write changes; the committing agent reviews, tests, and commits centrally. Prevents wrong-branch pushes and merge conflicts.

29. **Only the integration owner publishes** `[universal]` -- working branches stay local. After full local gates and trigger inspection, the owner makes the single authorized integration push and monitors its exact commit.

44. **Parallel agents run scoped tests only -- full suite runs once at integration** `[universal]` -- N agents each running the full test suite creates N x workers processes that exhaust CPU/memory. Agents test only their changed files; limit concurrent agents to 3-4; run the full suite once after merging.

48. **Spawn agents with a terminal condition, watchdog the rest** `[situational]` -- every spawned `copilot -p` agent gets a single-sentence task and an explicit stop condition ("stop the moment X is true"); never open-ended "look into"/"investigate". Set a ~15-20 min wall-clock budget and kill agents that overrun rather than assuming progress. Prevents the runaway agent that works hours past completion. See [agent-design.md](../methodology/agent-design.md).

49. **Dedup against repo state before doing or continuing work** `[situational]` -- before an agent starts or resumes, check `git log`/`git status`/`grep` for the artifact. If a sibling already landed it, stop and report -- don't produce a duplicate (e.g. a second copy of a test block already on the branch). The orchestrator owns this check; worktree agents can't see each other.

## Code & Edit Discipline

50. **Verify an API supports a call before chaining on it** `[frequent]` -- confirm a method/type actually exists (docs, types, or a tiny probe) before building on it, and run the targeted test BEFORE committing the first attempt, not after. About a quarter of sessions started with a fix that didn't typecheck and needed a full revert (e.g. chaining `.abortSignal()` after a Supabase `.single()` that doesn't return it).

51. **Format markdown tables programmatically, never by hand** `[universal]` -- run `markdownlint --fix` / `prettier --write` to align tables; never byte-tweak column padding to satisfy the linter. Hand-alignment is slow and regresses on the next edit.

## Deployment & Resources

30. **Inspect deployment topology before merging** `[universal]` -- a main merge can deploy production in some projects. This blueprint integrates locally to main; remote publication requires separate authority and trigger inspection.

31. **Batch dependency updates into a single PR** `[frequent]` -- merging N PRs one-by-one with "require up-to-date" creates O(n^2) CI waste. Create one branch, apply all updates, run CI once.

32. **Every CI run costs money -- count before triggering** `[universal]` -- estimate runs before starting. If >2-3, find a more efficient approach. Work locally until confident, push once.

33. **Framework upgrades need runtime verification** `[frequent]` -- CI and build checks cannot prove runtime behavior. Use local or already authorized test environments; never create a Vercel Preview for an experiment.

34. **When production is down: roll back first** `[universal]` -- restore service through the authorized recovery path, then investigate locally or in an authorized test environment.

35. **Justify every external action before triggering** `[universal]` -- before any CI run, deployment, or API call: Is this needed? Is this justified? Is this verifiable? If any answer is "no", stop.

52. **No CodeQL workflow without GHAS** `[github]` -- a code-scanning workflow fails CI on every push unless GitHub Advanced Security is enabled. Confirm first (`gh api repos/{owner}/{repo}/code-scanning/alerts` returns non-403) before adding the workflow. GHAS is free on public repos but a paid add-on on private repos -- on private, enabling it is a human cost decision, not an autonomous fix. Querying existing alerts (what `/triage` does) is always safe; creating the scanner is not. See [ci-and-guardrails.md](../methodology/ci-and-guardrails.md).

53. **Review GitHub repo settings per project** `[universal]` `[github]` -- inspect merge methods, branch protection, Dependabot, and deployment environments against that project's topology. Changing remote settings requires explicit authority; do not enable auto-merge as a blueprint default.

## Cost & Models

46. **Inherit the interactive model and effort** `[universal]` -- workflows use the owner-selected session model. Scheduled jobs may record an owner-selected model for reproducibility; installation never chooses a paid model or starts inference. See [cost-monitoring.md](../methodology/cost-monitoring.md).

47. **Measure cost per outcome** `[frequent]` -- use observed billing data and completed outcomes where available. Mark unavailable attribution unmeasured; require an explicit decision before paid fan-out or scheduled inference.

## Supabase

36. **Test migrations locally before pushing to remote** `[frequent]` -- run `supabase start` + `supabase db reset` locally, verify with `docker exec ... psql`, then `supabase db push`. The local instance has full Postgres with RLS and extensions -- treat it as UAT.

## Quality & Process

37. **Disposition every confirmed finding** `[universal]` -- resolve actionable findings, reject false positives with evidence, and record strategic decisions for owner review.

54. **No emojis in documentation** `[universal]` -- use text equivalents (PASS, `[x]`, `->`), not emoji/pictographs. Arrows, dashes, and box-drawing characters are allowed. Markdown CI lints structure but does not block emoji, so this is a discipline rule -- keep docs plain text.

55. **A finding's recommendation is a hypothesis, not a work order** `[universal]` -- an audit diagnoses well and prescribes narrowly. Authors state a **Regression risk** on every finding (invariants that must hold, assumptions the fix depends on, properties traded away); implementers verify those assumptions against real code before writing anything, and the failing test guards the invariant the fix could break, not the symptom the finding named. When a non-functional goal (perf, bundle size, build time) conflicts with a correctness, security, or UX invariant, default to the invariant and escalate the trade -- never decide it autonomously. A recommendation that fails verification **halts**. See [agent-errors.md](agent-errors.md) Error #40.

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

45. **Triage discovers Dependabot PRs** `[frequent]` `[github]` -- inspect PRs and checks read-only. Record risk and a proposed disposition; merge, rebase, issue mutation, and automatic fixes require their own authority.

---

For detailed symptoms, root causes, and examples, see [agent-errors.md](agent-errors.md).

For the full deployment safety guide and resource efficiency patterns, see [deployment-safety.md](deployment-safety.md).
