# Native Copilot qualification

These probes are separate from the portable local gate. Run them only after the
candidate is frozen and the owner has approved any Copilot inference. They use a
disposable Git repository, a local bare remote, and a new `COPILOT_HOME`. They do
not install a client, authenticate, activate a scheduler, publish a branch, or
start a cloud job. An isolated home cannot use a saved login from the normal
Copilot configuration. Supply an already authorized credential through a
supported environment variable if the client requires one. The receipt records
variable names, never values.

The initial 2026-09-28 local inventory found VS Code 1.137.0 and no `copilot`
executable. Native observations must record the client and app versions used in
their receipts because later installs or updates can change this inventory.

## CLI entry points

From the blueprint root:

```sh
uv run --locked python tests/native/run_cli.py --profile cli --timeout-seconds 120
uv run --locked python tests/native/run_cli.py --profile cli-programmatic --timeout-seconds 120
```

Set `COPILOT_BIN` to an approved local executable if `copilot` is not on `PATH`.
Set `COPILOT_MODEL` to the owner-selected model for `cli-programmatic`; the CLI
skill probe does not pass a model flag. Both profiles capture `copilot --version`
and `copilot --help` before inference. Missing flags, authentication, a model,
and any timeout produce a blocked receipt with a recovery action. Each external
process is bounded by an independent wall clock and its process group is stopped
on timeout. The shipped automation runner also has its own timeout.

The `cli` probe checks `copilot skill list --json` for the enabled project skill,
then invokes `/rpi-research` in the rendered fixture with read tools only. It
asks for the randomly generated marker in `README.md` without placing the
marker in the prompt. It then moves the skill outside the fixture and checks
that it is absent from the native skill list. A marker in the answer alone
does not prove skill invocation; the JSONL trace must also contain a native
`tool.execution_start` for `skill` with `rpi-research` as its argument, a
matching successful completion, and the marker answer after completion.
The `cli-programmatic` probe runs the shipped
`templates/scripts/rpi-automation.py` against a local agent report. It checks
that the allowed report contains the marker, then requests an attempted write to
an existing denied file with `write` available to the model but explicitly
denied. The receipt saves sanitized argv, exit codes and output for both cases.
The denied file and the local bare remote must remain byte-for-byte unchanged.
The negative control requires linked JSONL `permission.requested` and
`permission.completed` events with a write request for the denied file and a
`denied-by-rules` result. It also requires CLI exit 0 and a denial report in an
`assistant.message` event. This shape follows the
[Copilot SDK streaming event reference](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/streaming-events).
The CLI JSONL schema is not specified there. If a client emits a different
shape, the probe blocks and preserves output for inspection; prose refusal
alone never passes. Review the event against the recorded client version before
qualification.

Each run writes `.rpi/local/copilot/native/<profile>-receipt.json` by default,
so the two required profile results survive sequential runs. Set
`RPI_NATIVE_EVIDENCE_DIR` to an isolated local directory to keep separate runs.
The receipt includes the blueprint tracked and untracked content digest, index
tree and Git HEAD before and after the probe. A changed candidate blocks pass.
It also records the fixture commit, client version, command exits and bounded
output. Raw credentials are never written. A passed fake-process test validates
the harness only; it is not a
Copilot compatibility result. Run the harness tests with:

```sh
uv run --locked python -m unittest tests.native.test_run_cli -v
```

## CLI manual matrix

Use a disposable render of the `cli` profile and record the client version,
profile, blueprint commit, selected model, exact invocation, observed files and
tool results under `.rpi/local/copilot/native/`. Inspect the actual transcript
and disk state. These steps complete the cases beyond the two automated probes:

1. Invoke `/rpi-research` with the fixture's evaluative request from
   `tests/fixtures/workflows/evaluative_research.json`. Check skill discovery,
   arguments, bundled resources and research-only output. Rename the skill or
   remove a required resource in a second disposable render and confirm that
   discovery or resource loading fails visibly.
2. Select a custom role from `.github/agents/` and inspect the tool list the
   client grants. Attempt a harmless write to a denied fixture path. Record
   the native permission event, exit and unchanged bytes. Run a subagent and
   inspect whether repository instructions load in its context.
3. Change a fixture instruction file, start a fresh session and check that the
   new instruction is used. Record the selected model without a workflow model
   pin. Resume from a handoff and check that its candidate and evidence are
   revalidated before any action.
4. Run all six scenarios in `tests/fixtures/workflows/` against their recorded
   rubrics. Save the artifact and independent score for required fields and
   prohibited claims. Confirm that a skill invocation does not publish or
   start the next phase.

## VS Code Agent Host procedure

1. Open a disposable project rendered with `--profile agent-host` in VS Code.
   Record `code --version` or the application's About screen, GitHub Copilot
   extension version, and the selected Agent Host harness shown in the UI.
   Save a screenshot or diagnostic export under `.rpi/local/copilot/native/`.
2. In a fresh chat, inspect discovered skills and agents. Invoke
   `/rpi-research` with the same fixture marker and a direct argument. Check
   loaded resource content, output and candidate Git status. Rename the skill
   in a second disposable project and confirm the command disappears or fails
   visibly. Restore it and confirm recovery.
3. Select a custom role and inspect available tools in the UI. Request a
   harmless write to an existing denied fixture file. Capture the permission
   result and compare file bytes. Record whether repository instructions reach
   a delegated subagent. Change a scoped instruction, open a new chat and
   confirm refresh.
4. Confirm the selected model is inherited from the session, not forced by a
   skill. Resume a recorded handoff and verify its commit and receipts before
   accepting further work. Run the six workflow rubrics and save artifacts and
   independent scores. Confirm no automatic publication or phase continuation.

The selected harness and discovery UI require visual observation. If the app,
extension, account or selected harness is unavailable, record the exact missing
prerequisite and mark Agent Host qualification blocked. A static render or CLI
result does not stand in for this primary profile.

## Optional profiles

For `vscode-local`, render that profile into a separate disposable project.
Inspect its legacy wrappers, `agent` metadata, migration from chatmodes, command
deduplication and optional hook schema. Use renamed and malformed negatives.
Advertise it only after observed qualification. Native hooks require a separate
enabled safe-command and destructive-denial test, plus disabled, malformed and
timeout disclosures. Cloud requires a separately authorized hosted run with
setup success and failure evidence. These optional profiles remain unqualified
until their own tests run.
