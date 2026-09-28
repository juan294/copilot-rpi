---
name: process-errors
description: Classify saved agent error screenshots and update the local Copilot RPI catalog.
---

# Process local error evidence

This is a copilot-rpi maintenance skill. Inspect image files in the configured
error screenshot folder, defaulting to `~/Desktop/agent-errors/`. For each
image, identify the observed symptom and compare it with
`patterns/agent-errors.md` and `patterns/quick-reference.md`. Skip duplicates.

For each new generic error, assign the next permanent error and rule IDs. Keep
the catalog format: Symptom, Root Cause, Correct Approach, and What NOT to Do.
Update both catalogs and their documented counts, then run the repository's
count and Markdown checks. Record source screenshots, catalog decisions and
verification in a local handoff.

Retain originals until the user has explicitly authorized deletion and the
derived catalog entry is preserved. Commit locally under the repository Git
workflow. Push and other outward actions require explicit authorization.
