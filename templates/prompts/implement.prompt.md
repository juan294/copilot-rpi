---
mode: agent
description: "Execute an implementation plan phase by phase with verification gates"
---
Model tier: **sonnet** — invoke this prompt in a Sonnet session.

Implement the plan at: ${input:planPath}

Process:

1. Read the plan completely. Check for existing checkmarks.
2. Use #codebase to gather relevant context.
3. Create a feature branch for implementation.
   Research and planning happen on the default branch -- implementation must be isolated
   to avoid conflicts with other agents or uncommitted work on the default branch.
4. Check if remaining phases are marked `[batch-eligible]` in the plan.
   - If ALL remaining phases are batch-eligible, inform the user they can run those phases
     in parallel via separate Copilot agent sessions or `@copilot` issues, then STOP.
   - If phases have dependencies, continue sequentially below.
5. For the CURRENT phase only:
   a. Implement the changes as specified.
   b. Self-review: re-read your changes critically for plan compliance.
   c. If issues found, fix them before proceeding.
   d. Run ALL automated verification commands via #tool:terminal.
   e. Update checkboxes in the plan file.
   f. Recommend running `/quality-review` for a second-pass review (code reuse, quality, efficiency). This is a separate concern from plan compliance — self-review checks "did I follow the plan?" while quality review checks "is the code good?"
6. STOP. Report results and wait for human confirmation.
7. Do NOT proceed to the next phase without confirmation.

If plan doesn't match reality:

- STOP and present: Expected vs Found vs Why it matters.
- Ask how to proceed.
