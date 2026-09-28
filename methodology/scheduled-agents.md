# Scheduled Copilot jobs

Scheduled jobs are optional. The blueprint ships a bounded, report-only
Copilot runner for `update` and `triage` discovery. Package installation does
not authenticate a CLI, select a paid model, install a scheduler or start
inference. Activate a schedule only after the selected client, model, target,
credentials, permissions and cost are reviewed. See [native policy](../docs/native-policy.md).

## Architecture and scope

The scheduler starts a local process; it does not grant the process new
authority. A run checks client/version/flags, obtains a project lock, asks
Copilot for read-only discovery, and atomically writes a report only after a
successful bounded response. A human or an explicitly authorized later task
reviews that report. Failed runs preserve the last good report as historical
data and report current failure separately.

```text
cron or launchd -> rpi-automation.py -> bounded Copilot CLI -> local report
                                              | failure -> diagnostic only
                                              | success -> last-good copy
```

The available jobs are `update` (inspect local blueprint drift and prepare a
reviewable report) and `triage` (discover operational reports and findings).
Neither job applies a lifecycle plan, edits product files, pushes, creates an
issue or publishes a release. A completed report is an input to the
interactive `rpi-update` or `rpi-triage` workflow, not proof that remediation
occurred.

## Runner contract

The rendered package contains `.rpi/copilot/runtime/rpi-automation.py`.
`schedule-preview` prints a cron line and launchd `ProgramArguments`; it
changes no scheduler state. `run` checks the Copilot executable and supported
flags, invokes `copilot -p` with read-only tool scope, limits wall-clock time,
and saves a sanitized report and last-good copy only after success. The
runner uses a project-local lock to avoid overlapping runs. Missing auth,
denied tools, unsupported flags, malformed output and timeouts are failures
with a repair hint; they cannot be counted as a successful report.

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-automation.py" schedule-preview \
  --job update --project "$project_dir" --model "$selected_model"
```

The model is an explicit owner selection for reproducibility. `COPILOT_MODEL`
can supply it to a qualified job. The interactive RPI skills continue to
inherit the active session's model and effort. The runner is not a route for
unattended code edits, pushes, issue creation or cloud delegation.

An explicit run can select a report inside the project. Use this only after
the native programmatic fixture and inference authority are satisfied:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-automation.py" run \
  --job triage --project "$project_dir" --model "$selected_model" \
  --report "$project_dir/docs/agents/triage-report.md" --timeout 900
```

The CLI uses an available read tool and limits the run to 1-3,600 seconds.
The selected report path must remain inside the project. It is replaced only
after a successful result; the `.last-good` neighbor preserves that result.
The lock under `.rpi/local/copilot/locks/` prevents overlapping runs. Inspect
the exit code, timestamp, report and last-good copy before calling a job
healthy.

## Qualification before activation

1. Record the Copilot CLI version, relevant `--help` flags, selected model,
   target repository and sanitized environment. Verify noninteractive
   authentication without copying credentials into an artifact.
2. Run the native programmatic fixture in an isolated repository with a
   disposable Copilot home and restricted tools. Its allowed report case must
   write only the permitted report. Its denied-write case must leave the
   prohibited path unchanged. Inspect exit status and disk state.
3. Review `schedule-preview` output. Use absolute paths and a dedicated
   report location under the target. Test the actual cron or launchd
   environment after explicit activation; an interactive terminal success
   does not prove a scheduled run can authenticate.
4. Monitor the first run's exit, report timestamp and last-good behavior.
   Missing or failed jobs remain degraded until a later successful observed
   run. Do not infer health from a saved old report.

See [native fixture instructions](../tests/native/README.md). Client access
or paid inference that has not been authorized remains an explicit
qualification blocker.

## Report lifecycle

Operational reports can contain security findings or internal metrics.
Default to local ignored `docs/agents/` and `.rpi/local/copilot/` storage for
public projects. Determine actual repository visibility with
`gh repo view --json visibility --jq .visibility` when an authenticated remote
is available. A missing CLI, remote or visibility result defaults to private
operational storage. A private project may version curated reports under its
own policy. Do not commit logs, raw credentials or security details to a
public repository. Keep the source report, its timestamp, the tested candidate
and a readback of any claimed outcome. Mark unavailable metrics unmeasured.

`rpi-triage` scans every relevant report and failure, existing GitHub alerts
and Dependabot PRs, then stops at a read-only briefing. Its bundled
`rpi-triage-state.py` combines file hashes, timestamps and prior dispositions;
the `.last-triage` timestamp alone cannot prove a report was processed. A
failed or unprocessed report stays eligible for the next scan. Partial scans
do not advance the global marker. Later remediation or publication needs its
own authorized scope. See the skill's
[checkpoint contract](../templates/skills/rpi-triage/references/triage-state.md).

When a project chooses to archive reports, keep runs distinguishable by date
and candidate. Retain the current runner's last-good file as a recovery aid,
but never present it as today's result after a failure.

## Which reports to schedule

| Report | Useful inputs | Boundary |
| --- | --- | --- |
| Test health | Exact test command, repeated failures and measured coverage | A passing wrapper or stale receipt does not establish current coverage. |
| Security | Dependency audit, source locations, configuration checks | Redact secret values; remote alert queries need actual access and outcome. |
| Code quality | Lint/typecheck output, file sizes, dead-code candidates | A candidate is a finding to verify, not an automatic deletion. |
| Dependency health | Lockfile and available update data | Do not install, merge or publish updates from a report-only run. |
| Performance | Measured build, route or bundle baseline | Mark absent or incomparable measurements unmeasured. |
| Documentation | Changed public APIs and broken internal links | Suggest changes; do not rewrite owner docs unattended. |
| Cost | Provider usage export and attributable completed outcomes | Do not infer spend from request counts when billing attribution is absent. |

The shipped `update` and `triage` jobs have bounded discovery prompts. Other
report types in this table are design patterns for a separately reviewed job;
they are not implemented runner choices. The owner chooses a schedule based on
report value, time and inference cost.

## Scheduling and environment

`schedule-preview` prints a cron example and launchd arguments for the
selected `update` or `triage` job. Inspect the project path, model, executable,
environment and report location before copying either form to a scheduler.
Cron and launchd have a smaller environment than an interactive terminal;
PATH, home, authentication and selected model must be present for the job.
Test the actual scheduler after activation and inspect its logs and report.
An interactive command succeeding does not establish scheduled health.

The repository also contains legacy-compatible shell wrappers and a macOS
`templates/scripts/agents/install-agents.sh` helper. These are not part of
the rendered direct-install package. That helper discovers only scripts
marked `# RPI_AUTOMATION_MODE: report-only` with a valid `# SCHEDULE:` line.
Its default is preview; `--activate` explicitly registers launchd jobs,
`--status` inspects them and `--unload` removes only registrations it owns.
It refuses to replace an unowned plist or a symlinked scheduler path. Review
the preview and selected model before activation. A registered plist is not
proof that the process authenticated or produced a fresh report.

Run jobs at staggered times when they share a project, report directory or
external rate limit. Bound the number of unreviewed reports; pause new jobs
when the owner's review queue grows beyond its capacity. The runner's local
lock handles the same job in one project, while the schedule design handles
cross-job resource contention.

## Shared context and handoff

`templates/scripts/agents/lib/agent-utils.sh` has optional helpers for a
`docs/agents/shared-context.md` file. A report can include
`SHARED_CONTEXT_START` and `SHARED_CONTEXT_END` delimiters; the helper
extracts that block, timestamps it, and keeps the latest three entries for
that agent. Read only relevant entries and keep them free of secrets. This
compatibility helper is separate from the Python runner's report output;
the runner does not automatically update shared context.

The next interactive `rpi-triage` or `rpi-update` pass reads the actual report,
failed-run logs, project state and prior handoff. It records each finding's
disposition and a candidate-bound outcome. A summary copied from another
agent is context, not verification.

## Recovery

- **CLI or authentication missing:** install or authenticate through the
  supported client path, then rerun the isolated native fixture before a
  schedule is activated.
- **Unsupported flag or model:** compare actual `copilot --help` and the
  owner's model choice; update the runner contract only with tests and a new
  qualification result.
- **Timeout or lock:** inspect the current process and lock ownership. The
  runner limits runtime to 3,600 seconds. Preserve a live owner's lock and
  do not run a second job over it.
- **Failure after a previous success:** retain the last-good report as
  historical data and disclose the current failed state. Repair, then rerun.
- **Unreviewed backlog:** pause the schedule or reduce its frequency until
  reports have owners and dispositions. Avoid producing repeated findings
  that nobody can assess.
- **Interrupted multi-step follow-up:** persist a handoff after each completed
  local step and re-read current state before resuming. Do not retry an
  external mutation or skip a failed local gate merely because a checkpoint
  names an earlier completed step.

The legacy `templates/scripts/agents/` shell wrappers and
`install-agents.sh` have a preview-first compatibility path. Review their
actual `--help` and installed client behavior before using them. The direct
Python runner is the package's stable entry point for this release candidate.
