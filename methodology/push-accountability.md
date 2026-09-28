# Push Accountability

Complete local verification on the final candidate before any publication. Inspect workflow and deployment triggers, then publish only the completed integration branch when the owner has authorized that remote action. Working branches and worktrees stay local.

## Exact-commit verification

After an authorized push, record the pushed commit SHA and inspect every expected workflow for that SHA. A green run for another commit, a pending run, or an absent run does not prove this push passed. Read failed logs and reproduce the failure locally. Report the remote result and local diagnosis to the owner. A rerun, fix-and-repush cycle, PR, tag, release, or deployment is a new remote action and needs its own authorization.

The monitor is read-only. It may use `gh run list --commit <sha>` and `gh run view <run-id> --log-failed`, then compare the expected workflow names and conclusions to the recorded push. If no workflow is expected, record the trigger inspection and mark CI N/A rather than inventing a pass.

## Local repair

For a failed remote check, fix the diagnosed cause locally, run the complete local gate again on the changed candidate, and provide the failed run plus new local evidence. Keep the repaired candidate local until the owner authorizes another push. Do not let a background agent publish or retry by itself.

## Integration with RPI

1. Implement and review the phase locally.
2. Run the local gate on the final candidate and integrate completed work locally.
3. Inspect publication triggers and obtain the required remote authorization.
4. After the authorized push, verify expected workflows for the exact pushed SHA.
5. Record the result, including failures and coverage gaps, in the handoff.
