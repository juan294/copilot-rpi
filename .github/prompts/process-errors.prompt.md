---
mode: agent
description: "Process error screenshots from the error screenshots folder"
---
# Process Error Screenshots

You are processing new agent error patterns from screenshots that the user has saved.

## Steps

1. List all image files in `~/Desktop/agent-errors/` (or the configured error screenshots folder)
2. For each image, examine it to identify the error pattern
3. Read `patterns/agent-errors.md` to check for existing entries
4. Read `patterns/quick-reference.md` for the current rule count
5. For each **new** error (skip duplicates):
   - Add to `patterns/agent-errors.md` following the exact format of existing entries:
     - **Error #N — Short Descriptive Title**
     - Symptom: what the agent or user sees
     - Root Cause: why this happens
     - Correct Approach: the fix
     - What NOT to Do: common wrong approaches
   - Add a one-liner to `patterns/quick-reference.md` with the next rule number
6. Commit all changes with message: `fix: add Error #N — short description`
7. Push to remote
8. Delete ALL processed images from the error screenshots folder
9. Report what was added and what was skipped as duplicates

## Rules

- **Skip duplicates** — if the error is already covered, don't add it again
- **Keep entries generic** — no project-specific references
- **Follow existing format exactly** — consistency matters
- **Delete images after processing** — the folder should be empty when done
