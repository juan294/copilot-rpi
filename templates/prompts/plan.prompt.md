---
mode: agent
description: "Create a phased implementation plan with pseudocode and success criteria"
---
Create an implementation plan for: ${input:feature}

Process:

1. Read ALL mentioned files completely.
2. Use #codebase to find relevant code, patterns, and docs.
3. Read everything identified.
4. Present your understanding with focused questions — only ask what code can't answer.
5. After clarifications, search deeper if needed.
6. Present design options with trade-offs.
7. Propose phase structure, get feedback.
8. Write detailed plan with separate phase files.
9. Use pseudocode notation for changes.
10. Separate automated vs. manual success criteria.
11. Assess phase independence: mark phases that have no file overlap and no dependency on another phase's output as `[batch-eligible]`. These can be executed in parallel via separate `copilot -p` processes or `@copilot` issues.
12. Maximum 3 [NEEDS CLARIFICATION] markers.
13. Iterate with user until all questions resolved.

Save to docs/plans/YYYY-MM-DD-[description].md
Phase files: docs/plans/YYYY-MM-DD-[description]-phases/phase-N.md

No unresolved questions in the final plan.
