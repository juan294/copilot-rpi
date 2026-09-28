---
name: rpi-debug
description: Reproduce, isolate, explain, repair and verify a non-obvious bug.
---

# Debug a non-obvious bug

Read the relevant project instructions and existing error catalog first. Use
`patterns/agent-errors.md` and `patterns/quick-reference.md` for known failures.
For a new or recurring bug, follow this loop:

1. Reproduce it with exact inputs, command, candidate identity and expected versus
   actual result. If reproduction is impossible, state the observed limit.
2. Isolate the smallest failing case. Use `git bisect` for a regression with a
   known good revision when it is cheaper than manual search.
3. State one falsifiable root-cause hypothesis and the observation that would
   refute it. Test the hypothesis before editing the proposed fix.
4. Write a failing regression test for the confirmed mechanism. Fix the root
   cause and rerun the original reproduction plus surrounding tests.
5. Record the result and any unresolved case in the project handoff. A green
   unrelated check does not prove the reported failure resolved.

Keep work local through review, simplify and the applicable verification gate.
Remote publication requires the authority specified by the project.
