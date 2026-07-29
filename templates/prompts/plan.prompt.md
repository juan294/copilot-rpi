---
mode: agent
description: "Create a phased implementation plan with pseudocode and success criteria"
---
Model tier: **opus** — invoke this prompt in an Opus session.

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
10. When the plan specifies behavior, prefer pointing at an executable or checkable
    artifact (a failing test, a module with the semantics to match, a mockup, a rubric)
    over describing the behavior in prose.
11. Separate automated vs. manual success criteria.
12. Assess phase independence: mark phases that have no file overlap and no dependency on another phase's output as `[batch-eligible]`. These can be executed in parallel via separate `copilot -p` processes or `@copilot` issues.
13. Maximum 3 [NEEDS CLARIFICATION] markers.
14. Iterate with user until all questions resolved.

Save to docs/plans/YYYY-MM-DD-[description].md
Phase files: docs/plans/YYYY-MM-DD-[description]-phases/phase-N.md

No unresolved questions in the final plan.
