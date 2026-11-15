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

The hook configuration runs `.rpi/copilot/runtime/rpi-hook.py` from the target, and lifecycle apply does not install runtime files. Activation therefore copies the running `rpi-hook.py` to that path and writes `.rpi/copilot/runtime/rpi-hook.install.json` with the profile, the configuration path, whether activation wrote the configuration, and the runtime hash. Every write goes through a new exclusive temporary file in the same directory. Running activation again from a newer package refreshes a runtime whose bytes still match the record. Activation refuses a symlinked path, an unrecorded or edited runtime, the other active profile and an owner hook at the destination, and preserves their bytes.

Deactivate before you detach. Lifecycle detach does not own these files and leaves them in place:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-hook.py" install \
  --target "$project_dir" --profile cli --deactivate
```

Deactivation removes the runtime copy and the record, and the configuration only when activation wrote it, when the record exists and their bytes are unchanged; it refuses a symlinked configuration, and otherwise removes nothing and names the file to review. The installer preserves an existing owner hook instead of replacing it. A
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

The wrapper runs `.rpi/copilot/runtime/rpi-prepush.py` from the target, so activation also copies `rpi-prepush.py`, `rpi-candidate.py` and `rpi-verify.py` from the running package runtime there and writes `.rpi/copilot/runtime/rpi-prepush.install.json` with their hashes, the wrapper hash and whether it saved a prior hook. The gate requires a clean candidate, so add `.rpi/copilot/` to `.gitignore` (this repository does). Do not commit it: the manifest and the activation records hold absolute paths for this checkout, so a committed copy breaks `check` and activation in other clones. Deactivate before detach:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-prepush.py" install \
  --target "$project_dir" --deactivate
```

Deactivation restores the saved prior hook or removes the wrapper, then removes the runtime copies and the record, only when their bytes are unchanged. It keeps `.rpi/policy.json`. The adapter chains a prior pre-push hook through a preserved backup when it
can do so safely. Diagnose missing, edited or inactive hooks separately from a
valid receipt. A hook block must report `BLOCKED / WHY / FIX` and an actionable
local command. CI and exact-commit remote checks remain separate gates after
an authorized push.

## Scheduled Copilot jobs

The runner keeps each session local and unexported. Its preflight reads `copilot --help`: when the client advertises `--no-remote` and `--no-remote-export` (Copilot CLI 1.0.88), the run passes both; when it advertises `--sync-session` without `--no-remote` (1.0.112, which removed `--no-remote`), the run passes `--sync-session=off`. Copilot CLI 1.0.112 documents incoming remote control only as an in-session `/remote` setting, and `--sync-session` without a value "does not enable incoming control". A client that advertises neither form is blocked before inference with the client version. The agent installer preflight and the native harness use the same rule.

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
