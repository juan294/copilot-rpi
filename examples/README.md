# Examples

Sample documents and workflow walkthroughs illustrating the RPI methodology in practice. These are reference patterns — adapt structure and depth to your project's needs.

## Artifact Samples

What the outputs of each phase look like:

| File | Illustrates |
|------|------------|
| `research-document.md` | Research phase output: descriptive, no opinions, file:line references |
| `implementation-plan.md` | Plan phase output: phases, pseudocode notation, success criteria |
| `implementation-plan-phases/` | Per-phase detail files referenced by the plan |
| `error-log.md` | Error log entry: root cause analysis focused on user skill |
| `success-log.md` | Success log entry: what worked and why it's repeatable |
| `pseudocode-examples.md` | Additional pseudocode notation examples beyond the single one in the methodology |

## Workflow Walkthroughs

Illustrative examples showing how a developer interacts with the methodology.
Names, dates, test counts and outcomes in the transcripts are examples, not
qualification evidence for a native client or a real project:

| File | Scenario |
|------|----------|
| `workflows/bootstrap-new-project.md` | Setting up a new project with `/rpi-bootstrap`, then building the first feature with `/rpi-plan` and `/rpi-implement` |
| `workflows/add-new-feature.md` | Adding rate limiting to an existing API using `/rpi-research`, `/rpi-plan`, `/rpi-implement` and `/rpi-validate` |
| `workflows/refactor-existing-code.md` | Refactoring scattered auth logic into a dedicated service — where the phased approach prevents cascading breakage |
