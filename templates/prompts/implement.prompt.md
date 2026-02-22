---
mode: agent
description: "Execute an implementation plan phase by phase with verification gates"
---
Implement the plan at: ${input:planPath}

Process:

1. Read the plan completely. Check for existing checkmarks.
2. Use #codebase to gather relevant context.
3. For the CURRENT phase only:
   a. Implement the changes as specified.
   b. Self-review: re-read your changes critically.
   c. If issues found, fix them before proceeding.
   d. Run ALL automated verification commands via #tool:terminal.
   e. Update checkboxes in the plan file.
4. STOP. Report results and wait for human confirmation.
5. Do NOT proceed to the next phase without confirmation.

If plan doesn't match reality:

- STOP and present: Expected vs Found vs Why it matters.
- Ask how to proceed.
