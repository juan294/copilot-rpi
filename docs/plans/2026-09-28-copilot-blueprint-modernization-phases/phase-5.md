# Phase 5: Qualification and release preparation

Entry: P4 accepted and final local gate passes. Source baseline and official rolling documentation must be refreshed if either changed during implementation.

## Changes and acceptance package

1. Self-apply from canonical templates through the same ownership engine used by adopters. Keep local maintenance skills explicit and preserve unrelated `.summon`, Sutura and owner configuration. Reconcile AGENTS, Copilot instructions, README, GUIDE, CONTRIBUTING, setup checklist, methodology, examples, changelog, catalog pointers and tests.
2. Write `docs/compatibility.md`, `docs/migrations/v2.md`, `docs/upstream-sync.md` and `docs/native-policy.md`. State each profile's supported files, discovery invocation, permissions, hook status, argument delivery, resource layout, model behavior and recovery route. No historical no-hooks claim remains active; historical changelog is preserved and contextualized.
3. Add `tests/native/README.md` and fixtures with explicit client/build/extension/model, profile and candidate recording. Use disposable repositories with local remotes, no secrets and restricted capabilities. Do not install or authenticate globally, spend paid inference, start cloud jobs, or change policy as an implicit test prerequisite. Exhaust authorized automated setup before escalating a genuine access requirement.
4. Prepare release notes for a breaking layout migration under proposed Copilot RPI 2.0. Do not bump a released header or create a tag until acceptance; keep work in Unreleased while qualification is pending. Package direct-install artifacts locally and document rollback and compatibility selection. No marketplace publication is included.

## Native qualification matrix

| Profile | Required observed probes | Acceptance |
| --- | --- | --- |
| CLI | Skill discovery and explicit `/rpi-research`; argument/resource loading; custom role tools; subagent repository instructions; permission denial; instructions refresh; model inheritance; handoff resume | Required for primary support; record exact client version |
| CLI noninteractive runner | Actual bounded `copilot -p` via the shipped runner; real argv/stdin delivery, minimal permissions, report/output capture and exit handling; denied-write negative control; missing-auth/timeout disclosure | Required for scheduled-runner support, with sanitized real-process evidence and no scheduled service activation |
| VS Code Agent Host Copilot | Skills/agent discovery; actual selected harness; no reliance on prompt wrappers; resource/argument loading; tool restriction; handoff where supported; no automatic next-phase execution | Required for primary support; record app and Copilot build/extension |
| VS Code Local | Legacy compatibility wrappers and `agent` metadata; chatmode migration; no duplicate commands; hook schema if selected | Qualify this optional profile or label unsupported; no primary claim depends on it |
| Native optional hooks | Host loads configured hook; safe local command succeeds; destructive fixture is denied before side effect; disabled/malformed/timeout state disclosed; recovery restores expected behavior | Required only before advertising/activating that hook profile |
| Cloud | Setup success/failure disclosure, instructions/skills/agent loading, no reliance on interactive handoffs, evidence artifact | Separate explicitly authorized hosted test; otherwise documented and unqualified |

For each positive discovery test include a negative control with the file renamed, field malformed or resource removed. For tool restrictions, attempt a harmless write to a disposable denied path and inspect disk; prose refusal alone is not enforcement proof. For workflow behavior, run the P1 scenarios and independently score the resulting artifacts. Research must not modify product files; any permitted research artifact is written by the authorized parent. A skill invocation must not itself trigger publication or a new phase.

Installed VS Code 1.137.0 is only an initial inventory observation. No working CLI or extension version was established in research. If a required primary probe cannot run, report qualification blocked with the exact missing prerequisite. Do not silently downgrade a mandatory probe to a static check or change this plan's acceptance contract.

Provide the exact native entry points `uv run --locked python tests/native/run_cli.py --profile cli --timeout-seconds 120` and `uv run --locked python tests/native/run_cli.py --profile cli-programmatic --timeout-seconds 120`. They require an explicit execution decision, create isolated fixtures and invoke the shipped runner with a disposable `COPILOT_HOME` or equivalent isolated configuration without copying credentials into artifacts. Before inference, capture `copilot --version` and relevant `copilot --help`; reject unsupported flags with a recovery hint. The programmatic success case reads a fixture and writes only the allowed report. Its negative control attempts a harmless denied write and proves the destination unchanged; assert both native exit/report behavior and no publication attempt. Use an independent wall-clock timeout with process-group cleanup. A credential/access requirement is reported, never bypassed. UI-only VS Code probes have step-by-step actions and saved diagnostics in `tests/native/README.md` because the selected harness and discovery UI must be observed.

## Final local gates

Run the full portable gate sequentially on the final integrated candidate, then native probes on unchanged output. Validate every internal Markdown/resource link, schema, command mapping, count/version reference, retirement entry, source hash and generated byte. Confirm the docs' runnable install/update/check/rollback/detach examples in fresh and customized fixture repositories. Ensure optional profiles are absent unless selected. Preserve complete results and failures in `.rpi/local/copilot/`.

Commands: `bash scripts/verify-local.sh`, then the two authorized native CLI entry points above, then the recorded VS Code native procedure. For minimum-Python qualification run `uv run --locked --python 3.11 python -m unittest discover -s tests -p 'test_*.py'`; a disposable Linux environment runs the same portable gate. No hosted workflow is needed or triggered by these local commands.

Review all remaining findings: fix actionable ones, reject false positives with evidence, and give architectural exceptions an explicit owner disposition. Perform independent plan-compliance review and simplify before the final run. No unresolved material finding or missing primary native result may be called release-ready.

## Repeatable future upstream intake

The upstream checker compares the pinned manifest/catalog against a supplied new cc-rpi SHA, reports each changed/new/removed item with the current Copilot disposition, and fails if an item lacks a decision. It creates no issue, PR, push or automatic import. Every Copilot release review runs this check and records deliberate deferrals. Test it with a synthetic new component and changed rule: both must appear, and an empty accepted diff must be a real no-op.

Run the documentation/link sweep, self-application and portable gate before freezing the candidate for native qualification. These steps are sequential because edits invalidate candidate-bound evidence. After that freeze, CLI and VS Code native fixture execution may be `[batch-eligible]` only in disjoint disposable targets with no shared app/configuration mutation. Native tests are bounded. The integration owner records qualification evidence under ignored runtime paths; any subsequent tracked compatibility/release-document change gets a new portable gate and affected native requalification before final acceptance.

Exit: deliver local candidate identity, migration preview, source-intake coverage, automated results, native profile results, known limits and release notes. Stop before push, tag, release, cloud execution or downstream rollout. The owner can then authorize a concrete publication action without reopening completed local work.
