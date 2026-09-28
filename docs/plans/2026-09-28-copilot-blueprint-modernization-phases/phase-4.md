# Phase 4: Verification, controls and scheduled automation

Entry: P3 accepted. Read current native hook/programmatic CLI references; do not use Claude event shapes or permission switches by analogy.

## Changes

1. Adapt `rpi-verify.py` and extend P1's `scripts/verify-local.sh` with candidate receipts as the single sequential, failure-aggregating gate. Record candidate tree, Git identity, relevant untracked candidate files, tool versions, command list and every exit in `.rpi/local/copilot/verification.json`. Write running/non-success before any check. Detect input/runtime changes during checks. Keep native and database receipts separate.
2. Integrate P2's tested schema/semantic validators into candidate receipts while preserving count/version/retirement checks and no-emoji policy. Keep P1's pinned development dependencies and lockfiles. Validate generated output, links, selected profiles and self-application; no static success claims native loading. Add an executable finding parser and preserve each finding's resolved/rejected/strategic disposition before remediation.
3. Port the current narrow destructive-operation guard as an optional Copilot hook adapter, with separate Local versus SDK schemas and explicit native activation. Return normal allowed operations to native permissions. Test destructive operations, legitimate lookalikes, malformed input, runtime errors and timeouts. Document the actual timeout fail-open limit; avoid shell-parser claims of complete authorization enforcement.
4. Provide opt-in `rpi-prepush.py` integration that checks exact Git ref/candidate evidence and coexists with existing hooks through a reviewed installer. Never silently modify `.git`, bypass another hook or infer owner approval from a receipt. Run push fixtures against local bare repositories only.
5. Replace `CLAUDE_BIN`, Claude flags and `preflight_claude` with a tested Copilot runner. Non-inference preflight checks executable version/help and required configuration; any inference probe is explicit. Scheduled jobs default to discovery/report or ready-plan output, never fixes/pushes/merges. A later expressly configured apply mode may only apply a reviewed plan. Remove default standing auto-approval text.
6. Add bounded timeout, owned lock recovery, controlled cwd/environment, sanitized logs, atomic reports and last-known-good preservation. A denied tool, missing authentication, unsupported CLI flag or absent model produces an actionable result. No Claude fallback. Scheduler installers render a preview and require explicit activation. Test cron/launchd-like environment without starting a persistent job.
7. Keep optional cloud setup minimal and pinned, with a prerequisite check inside the task because setup failure need not prevent agent startup. Do not copy template stacks into every adopter or activate the workflow implicitly.

Evidence: `templates/scripts/copilot-rpi-update-agent.sh:87`, `templates/scripts/morning-triage.sh:179`, `templates/scripts/agents/lib/agent-utils.sh:66`, `.github/workflows/validate.yml:3`; cc-rpi `templates/scripts/rpi-verify.py:163`, `docs/native-policy.md:85`; research E09-E14.

## Tests and recovery

Create `tests/test_verification.py`, `test_findings.py`, `test_policy.py`, `test_prepush.py` and `test_automation.py` before implementation. Use real owned modules/files; fake only external Copilot/GitHub process boundaries. A fake executable captures argv/environment and supplies success, denial, timeout, malformed output and partial-output outcomes. Native contract probes remain P5.

Required oracles: early failure is retained after later success; changed input invalidates receipt; interruption removes stale green state; unexpected untracked candidate files cannot evade identity; invalid finding report blocks dependent work; corrupted report never replaces last good report; scheduler does not invoke Claude or grant blanket tools; stale lock recovery does not kill another job; no remote call is attempted by default; local pre-push refuses a stale receipt and accepts the corrected exact candidate.

```text
@ verify(candidate, checks) -> receipt
ctx: local commands and runtime versions
pre: required checks and candidate scope are explicit
do:
  1. write running receipt and capture initial identity
  2. compute every check result sequentially
  3. validate final identity against initial identity
  4. write aggregate success only when every requirement holds
fail: failure, interruption or identity drift -> non-success and recovery command
```

## Acceptance and coordination

Automated: all cases above and the complete local gate pass; emitted hook decisions match each profile schema; default jobs have no permission to publish; source adaptation changes update the upstream lock. Persist all failed then repaired evidence. Coverage metrics may be measured but test counts are never called source coverage.

Commands: `uv run --locked python -m unittest discover -s tests -p 'test_*.py'`, then `bash scripts/verify-local.sh`. The suite includes verification/findings/policy/pre-push/automation modules and local-bare-remote fixtures. P5 separately runs the real noninteractive CLI contract, since a fake executable cannot establish supported native flags or permission behavior.

Native hook blocking is not accepted from script tests alone. P5 must show the actual host reaching the hook, a blocked tool with no side effect, a legitimate allowed tool and recovery/timeout disclosure on exact versions. If unavailable, keep activation unqualified and do not advertise enforcement.

Independent units: `[batch-eligible]` verifier/findings; hooks/Git pre-push; scheduler/cloud template. No file overlap after shared schema is frozen; one integration owner updates the full runner and CI. Independent review, repair, simplify, sequential gate, then acceptance stop.
