# Native controls and authority

The package renders repository skills, agents and instructions. Their text
guides a client; it does not itself grant tool permission, prove that a native
hook ran, or authorize an external action. Review the [compatibility matrix](compatibility.md)
for each client. Copilot's own permission controls remain active.

## Optional pre-tool hook

`rpi-hook.py` recognizes a narrow set of destructive commands and emits a deny
decision for positive matches. Unknown shell forms pass through to native
permissions. Hook loading, disabled state, malformed input and timeouts need
separate native probes; configuration alone is not enforcement evidence.
GitHub's [hook reference](https://docs.github.com/en/copilot/reference/hooks-reference)
defines the client contract. The installer offers `cli` and `vscode-local`
configurations. There is no `agent-host` installation profile for this hook;
Agent Host support must not be inferred from the CLI schema. `sdk` is an
adapter evaluation profile, not an install target. Preview first, then activate
only for an explicitly selected target/profile:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-hook.py" install \
  --target "$project_dir" --profile cli
python3 "$package_dir/.rpi/copilot/runtime/rpi-hook.py" install \
  --target "$project_dir" --profile cli --activate
```

The installer preserves an existing owner hook instead of replacing it. A
native probe must show a safe command succeeding and a disposable destructive
fixture denied before any side effect before advertising this profile.

## Optional Git pre-push receipt gate

The local verifier writes `.rpi/local/copilot/verification.json` for the
tested candidate. It records all required checks and invalidates success for
changed inputs or a failed/interrupted run. The Git pre-push adapter is a
separate opt-in gate; neither package rendering nor verification installs it.
The receipt is an editable local file. The adapter detects stale or failed
ordinary runs, but it cannot authenticate the check results against someone who
can rewrite local files. Exact-commit CI results remain the publication gate.
It acts on the exact refs Git is about to publish and requires a reviewed
`.rpi/policy.json` check inventory. Preview and inspect the existing Git hook
path and policy before activation:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-prepush.py" install \
  --target "$project_dir" --checks "$checks_file"
python3 "$package_dir/.rpi/copilot/runtime/rpi-prepush.py" install \
  --target "$project_dir" --checks "$checks_file" --activate
```

The adapter chains a prior pre-push hook through a preserved backup when it
can do so safely. Diagnose missing, edited or inactive hooks separately from a
valid receipt. A hook block must report `BLOCKED / WHY / FIX` and an actionable
local command. CI and exact-commit remote checks remain separate gates after
an authorized push.

## Scheduled Copilot jobs

`rpi-automation.py schedule-preview` prints cron and launchd commands without
installing or starting them. `run` requires an explicit owner model, a working
authenticated Copilot CLI and supported flags. It limits time and tool scope,
writes a local report only on success, keeps the last good copy, and reports
missing auth, denial or timeout. Review the project, environment and selected
model before any scheduler activation or paid inference.

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-automation.py" schedule-preview \
  --job update --project "$project_dir" --model "$selected_model"
```

Cloud execution, global Copilot settings, remote issue/PR actions, pushes and
release publication are separate actions. No default installation activates
them. The [v2 migration guide](migrations/v2.md) covers package rollback and
detach; it does not remove an independently installed scheduler or Git hook.
