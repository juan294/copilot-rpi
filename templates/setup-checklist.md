# New Project Setup Checklist

Use this when setting up a project with the Copilot RPI blueprint. Resolve the
local package and target from actual paths. Review an ownership-aware plan before
changing the target.

## Project facts

- [ ] Record the project's name, purpose, stack, package manager, integration
  branch, release target, test commands, deployment triggers and owners.
- [ ] Inspect existing `AGENTS.md`, `.github/`, `.vscode/`, settings and legacy
  `.github/copilot-rpi-sync.json`. A matching name does not prove ownership.
- [ ] Choose a qualified profile: `cli` for Copilot CLI, `agent-host` for the VS
  Code Copilot harness, or `vscode-local` for Local compatibility. Choose only
  relevant components and domain instructions.
- [ ] Keep existing project facts and custom rules. Managed always-loaded root
  text has an 8,192 UTF-8 byte limit; report other active instruction sources
  separately. Use scoped instructions for domain-specific guidance.

## Plan, apply and check

Render the selected profile from a verified blueprint checkout into an empty
`package_dir` first. The package's `.rpi/copilot-render.json` records its
profile and every rendered file hash; the lifecycle plan checks that receipt.
Keep its `.rpi/copilot/runtime/` with the package. Use actual absolute paths
for `source_dir`, `package_dir`, `project_dir` and `plan_file`. The bundled
runtime uses Python 3.11+ without repository development dependencies. The
example selects Copilot CLI. Keep `selected_profile` unchanged through render,
plan, check and detach; set it to `agent-host` or `vscode-local` for those
profiles:

```bash
selected_profile=cli
python3 "$source_dir/templates/scripts/rpi-distribution.py" render \
  --source "$source_dir" --profile "$selected_profile" --target "$package_dir"
```

Then preview the target installation:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" plan \
  --package "$package_dir" --target "$project_dir" --profile "$selected_profile" \
  --output "$plan_file"
```

- [ ] Review source SHA, target identity, selected components, current input
  hashes, create/update/remove actions, conflicts, capability changes and the
  recovery path. Resolve unknown ownership before dependent writes.
- [ ] Apply the unchanged reviewed plan within the authorization already given.
  A stale plan requires a new review.

  ```bash
  python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" apply \
    --plan "$plan_file"
  python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" check \
    --package "$package_dir" --target "$project_dir" \
    --profile "$selected_profile"
  ```

- [ ] Verify installed skills and bundled resources under `.github/skills/`,
  roles under `.github/agents/`, and path instructions under
  `.github/instructions/`. Check actual client discovery before claiming a file
  loaded. Keep legacy prompt and chatmode copies until their exact ownership is
  proven.
- [ ] Preserve the project's `.rpi/manifest.json` if cc-rpi also uses the
  repository. Copilot RPI owns only `.rpi/copilot/manifest.json`, its baselines
  and local recovery journals under `.rpi/local/copilot/`.
- [ ] Select MCP, native hooks, Git hooks, global customization and schedulers
  separately. Example JSON files are inert; do not rename one to an active
  configuration without reviewing its server, credentials and capability scope.

## Native workflows and instructions

- [ ] Select the relevant `rpi-*` skills. `rpi-research`, `rpi-assess`,
  `rpi-plan`, `rpi-implement` and `rpi-validate` cover the core lifecycle.
  Invoke publication workflows explicitly and verify their authority.
- [ ] Use `.github/agents/` research, planner and auditor roles with their
  declared tools. A read-only role returns cited findings; its parent writes
  artifacts and runs checks.
- [ ] For `vscode-local`, use generated `.prompt.md` wrappers with current
  `agent` metadata. Do not install a wrapper and skill with the same command
  name in one profile. Native `/plan` and `/status` are distinct from
  `rpi-plan` and `rpi-status`.
- [ ] Review `applyTo` globs against the actual target paths for tests, API,
  migrations, deployment and selected domains. Verify the chosen harness loads
  them. Preserve existing custom globs and instruction content.

## Repository setup

- [ ] Add curated `docs/research/`, `docs/plans/` and `docs/decisions/` when
  useful. Keep raw runtime receipts in local ignored storage. Public projects
  should not publish operational agent reports by default.
- [ ] Structure the README with a project description, relevant badges and
  verified commands. Adapt the release playbook using actual project facts;
  Wave A checks the exact release candidate and blocks a required skip/failure.
- [ ] Configure local checks and CI for the project's stack. Run typecheck,
  lint, tests and build where applicable. Record every result against the final
  candidate. Add branch protection only through an authorized remote change.
- [ ] Use local task branches/worktrees and integrate completed work into the
  documented local integration branch. Inspect CI and deployment triggers
  before an authorized push. Verify expected workflows for the exact pushed
  commit. Diagnose failure locally; a rerun or another push needs authority.
- [ ] Test any selected pre-commit or native hook against a deliberate local
  failure. A configured hook is not proof it ran or prevented an earlier edit.

## Optional scheduled agents

Scheduled agents are an opt-in project capability pending client and scheduler
qualification. Record the owner's selection and target platform. Do not copy
old Claude-specific scripts, install a launchd/cron schedule, start paid
inference, or promise unattended updates as a side effect of project setup.

## Removal and recovery

Review a removal plan before detaching. Detach removes only unchanged, proven
owned entries and preserves custom work:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" detach \
  --package "$package_dir" --target "$project_dir" \
  --profile "$selected_profile" --output "$plan_file"
python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" apply \
  --plan "$plan_file"
```

On an interrupted transaction, use the journal path printed by the engine.
Rollback refuses to overwrite a newer edit:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" rollback \
  --journal "$journal_file"
```

## Workflow habits

- [ ] Read existing code before research; use `rpi-assess` for evaluation and
  `rpi-plan` for phased implementation. Greenfield work can start at planning.
- [ ] Use a failing test first for behavioral changes. Complete independent
  review, repair, simplify and all required local checks before phase
  acceptance. An explicit all-phases request permits continuation after each
  verified boundary.
- [ ] Give every confirmed finding a disposition. Fix actionable findings,
  reject false positives with evidence, and send strategic decisions for owner
  review. Preserve the durable handoff and revalidate state on resume.
- [ ] Use `rpi-pre-launch`, `rpi-remediate`, `rpi-update-docs` and `rpi-release`
  for the pre-release sequence. `rpi-explore-release` supplies exploratory
  evidence only for an existing authorized immutable candidate.

## Project-type adaptation

- **Web application:** Inspect deployment and preview triggers, route safety,
  authorization, UI checks and production recovery.
- **Library or package:** Verify public API, package artifact, compatibility
  and publication preflight.
- **CLI:** Test the installed command, arguments, errors and exit codes.
- **Monorepo:** Record package boundaries and verify shared consumers/writers.
- **Python:** Use the project's Python environment, formatter, type checker
  and database fixtures.
- **Static site or documentation:** Verify build output and internal links.
