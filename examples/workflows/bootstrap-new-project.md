# Workflow: start a new project

This illustrative walkthrough uses a Node.js REST API. The commands describe
the selected `agent-host` profile; native discovery still needs to be checked
on the installed VS Code and Copilot versions.

## Prepare the repository

Create and open a Git repository. Clone Copilot RPI separately and render a
package for `agent-host` into an empty directory. Review and apply its lifecycle
plan as shown in the [setup checklist](../../templates/setup-checklist.md).
This installs canonical skills in `.github/skills/`, three optional specialist
agents in `.github/agents/`, and selected scoped instructions. It does not
activate hooks, schedulers, MCP servers or a cloud agent.

```text
You: /rpi-bootstrap Set up this empty repository as a Node.js, Express and
     TypeScript API. Use Jest and a conventional src/ directory.
```

The agent inspects the project and asks only for decisions the repository
cannot answer. It uses an ownership-aware plan for any further blueprint
components, adds project-specific code and checks, and reports what it
actually ran. Existing project guidance is preserved. For an established
repository use `/rpi-adopt` and review the gap report first.

## Plan the first feature

An empty codebase can start at planning. Give the desired behavior and answer
the consequential design questions:

```text
You: /rpi-plan Create a todo API with CRUD endpoints, PostgreSQL storage and
     input validation. Put the plan under docs/plans/.
```

For this example, the owner chooses Prisma, no authentication yet, and
`express-validator`. The resulting plan has three testable phases: database
schema, CRUD endpoints, and error handling plus integration tests. Read and
correct the plan before implementation.

## Implement and validate

```text
You: /rpi-implement docs/plans/2026-02-22-todo-api.md
You: /rpi-validate docs/plans/2026-02-22-todo-api.md
```

Each authorized phase gets a failing behavioral test first, implementation,
independent review, repair, simplify and the required local gate. The agent
records exact candidate and check evidence in a durable handoff and pauses at
the phase boundary unless continuation was already authorized. Validation
compares the result with the approved plan. Example test counts and outcomes
are deliberately omitted; use the actual project's output.

`/rpi-describe-pr` can draft a reviewable change description. Creating a PR
or pushing to a remote is a separate authorized action after local integration
and trigger inspection.
