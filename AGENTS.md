# copilot-rpi — GitHub Copilot Reference & Project Intelligence

## What This Is

This is the blueprint repository for projects that use GitHub Copilot. It contains:

- The RPI (Research-Plan-Implement) methodology adapted for GitHub Copilot
- A catalog of known agent errors with proven solutions
- Operational rules that prevent recurring mistakes
- Templates for AGENTS.md, prompt files, path-specific instructions, and project setup

## How This Repo Is Used

When starting a new project, the agent is told: "Go check my copilot-rpi repository and set up the environment to follow all the best practices."

The agent should:

1. Read `patterns/quick-reference.md` — internalize all operational rules
2. Read `patterns/agent-errors.md` — know every known error pattern
3. Read `methodology/README.md` — understand the RPI approach (follow reading order for depth)
4. Use `templates/setup-checklist.md` to set up the new project
5. Adapt `templates/AGENTS.md.template` for the new project's AGENTS.md
6. Copy `templates/prompts/` into the new project's `.github/prompts/`
7. Copy `templates/github/instructions/` into `.github/instructions/`
8. Copy `templates/github/chatmodes/` into `.github/chatmodes/`

## Repo Structure

```text
copilot-rpi/
├── .github/
│   ├── copilot-instructions.md       # Copilot auto-loaded project instructions
│   └── prompts/                      # Prompt files for maintaining THIS repo
│       └── process-errors.prompt.md  # /process-errors — error screenshot pipeline
├── AGENTS.md                         # This file (repo self-description)
├── GUIDE.md                          # Human-readable quick-start guide
├── README.md                         # Public documentation
├── methodology/                      # The RPI approach
│   ├── README.md                     # Overview and reading order
│   ├── philosophy.md                 # Core tenets, error amplification
│   ├── context-engineering.md        # Context management, compaction, settings
│   ├── four-phases.md                # Research → Plan → Implement → Validate
│   ├── agent-design.md               # Documentarian rule, research catalog, autonomy
│   ├── pseudocode-notation.md        # Plan notation format
│   ├── testing.md                    # Automated-first verification, TDD protocol
│   ├── push-accountability.md        # Post-push CI ownership, background verification
│   ├── ci-and-guardrails.md          # Pre-commit hooks, CI workflows, enforcement
│   ├── scheduled-agents.md           # Recurring quality agents, cron/launchd
│   └── error-success-logging.md      # Systematic improvement framework
├── examples/                         # Sample documents and workflow walkthroughs
│   ├── README.md                     # Index of all examples
│   ├── research-document.md          # Sample research phase output
│   ├── implementation-plan.md        # Sample plan with phases and pseudocode
│   ├── implementation-plan-phases/   # Per-phase detail files
│   │   └── phase-1.md
│   ├── error-log.md                  # Sample error log entry
│   ├── success-log.md                # Sample success log entry
│   ├── pseudocode-examples.md        # Additional pseudocode notation examples
│   └── workflows/                    # End-to-end developer interaction walkthroughs
│       ├── bootstrap-new-project.md  # New project setup + first feature
│       ├── add-new-feature.md        # Adding rate limiting with full RPI cycle
│       └── refactor-existing-code.md # Auth service extraction with phased refactor
├── patterns/                         # Operational knowledge
│   ├── quick-reference.md            # Rules to internalize before any work
│   └── agent-errors.md               # Detailed error catalog with solutions
└── templates/                        # Files to adapt for new projects
    ├── AGENTS.md.template            # Starting point for project AGENTS.md
    ├── README-header.md              # Standard README header (badges, Chapa, divider)
    ├── vscode-settings.json.template # .vscode/settings.json (Copilot config)
    ├── vscode-mcp.json.template      # .vscode/mcp.json (MCP server config)
    ├── setup-checklist.md            # Step-by-step new project setup
    ├── prompts/                      # Prompt file templates (.github/prompts/)
    │   ├── bootstrap.prompt.md       # /bootstrap — new project setup
    │   ├── adopt.prompt.md           # /adopt — existing project migration
    │   ├── update.prompt.md          # /update — blueprint sync
    │   ├── research.prompt.md        # /research — codebase research
    │   ├── plan.prompt.md            # /plan — implementation planning
    │   ├── implement.prompt.md       # /implement — phased execution
    │   ├── validate.prompt.md        # /validate — verification
    │   ├── describe-pr.prompt.md     # /describe-pr — PR description
    │   └── pre-launch.prompt.md      # /pre-launch — production audit
    ├── scripts/                      # Agent shell script templates
    │   └── copilot-rpi-update-agent.sh  # Nightly blueprint sync agent
    └── github/                       # Copilot-specific templates
        ├── copilot-instructions.md.template
        ├── instructions/             # Path-specific rule templates
        │   ├── tests.instructions.md.template
        │   ├── api.instructions.md.template
        │   └── migrations.instructions.md.template
        └── chatmodes/                # Specialized chat persona templates
            ├── rpi-research.chatmode.md
            ├── rpi-planner.chatmode.md
            └── rpi-auditor.chatmode.md
```

## Contributing to This Repo

When new error patterns are discovered during work on ANY project:

1. Add them to `patterns/agent-errors.md` following the existing format
2. Add a one-liner to `patterns/quick-reference.md`
3. Keep entries generic — no project-specific references

When new best practices or methodology refinements are confirmed:

1. Add them to the appropriate file under `methodology/`
2. Or create a new file under `patterns/` if it's a distinct topic
