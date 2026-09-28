---
name: rpi-quality-review
description: Review and fix recently changed code for reuse, quality and efficiency while preserving behavior.
---

# Review changed code

Read the complete current diff, relevant tests and project instructions. If the
work is already committed, compare against the intended base or recent commit.
Review reuse, code quality and efficiency as distinct concerns:

- Find existing helpers before accepting duplicate logic.
- Check redundant state, parameter sprawl, copy-paste, leaky abstractions and
  unnecessary complexity.
- Inspect avoidable repeated work or resource use without trading away
  correctness, security or user experience for a metric.

Fix confirmed actionable findings in the authorized scope. Keep the behavioral
contract and run focused tests after each repair. Finish with the complete
applicable local gate on the final candidate. Record each finding and its
disposition. An independent plan-compliance review remains separately required
when the implementation workflow calls for one.
