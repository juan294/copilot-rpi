# copilot-rpi -- GitHub Copilot Reference & Project Intelligence

## One-liner

Blueprint repository for GitHub Copilot projects. Contains the RPI methodology, 38 known agent error patterns, 43 operational rules, and templates for AGENTS.md, prompt files, instructions, chat modes, and project setup.

## Stack

Markdown documentation, shell scripts (bash). CI: GitHub Actions with markdownlint.

## How This Repo Is Used

When starting a new project, the agent is told: "Go check my copilot-rpi repository and set up the environment to follow all the best practices."

The agent should:

1. Read `patterns/quick-reference.md` -- internalize all operational rules
2. Read `methodology/README.md` -- understand the RPI approach (follow reading order for depth)
3. Use `templates/setup-checklist.md` to set up the new project
4. Adapt `templates/AGENTS.md.template` for the new project's AGENTS.md
5. Copy `templates/prompts/` into the new project's `.github/prompts/`
6. Copy relevant `templates/github/instructions/` into `.github/instructions/`
7. Copy `templates/github/chatmodes/` into `.github/chatmodes/`

The full error catalog (`patterns/agent-errors.md`) is available for debugging but not required for onboarding.

## Repo Structure

```text
copilot-rpi/
├── .github/
│   ├── copilot-instructions.md       # Copilot auto-loaded project instructions
│   └── prompts/                      # Prompt files for maintaining THIS repo
│       └── process-errors.prompt.md  # /process-errors -- error screenshot pipeline
├── AGENTS.md                         # This file (repo self-description)
├── GUIDE.md                          # Human-readable quick-start guide
├── README.md                         # Public documentation
├── methodology/                      # The RPI approach
│   ├── README.md                     # Overview and reading order
│   ├── philosophy.md                 # Core tenets, error amplification
│   ├── context-engineering.md        # Context management, compaction, settings
│   ├── four-phases.md                # Research -> Plan -> Implement -> Validate
│   ├── agent-design.md               # Documentarian rule, research catalog, autonomy
│   ├── pseudocode-notation.md        # Plan notation format
│   ├── testing.md                    # Automated-first verification, TDD protocol
│   ├── push-accountability.md        # Post-push CI ownership, background verification
│   ├── ci-and-guardrails.md          # Pre-commit hooks, CI workflows, enforcement
│   ├── scheduled-agents.md           # Recurring quality agents, cron/launchd
│   └── error-success-logging.md      # Systematic improvement framework
├── examples/                         # Sample documents and workflow walkthroughs
├── patterns/                         # Operational knowledge
│   ├── quick-reference.md            # 43 rules to internalize before any work
│   ├── agent-errors.md               # 38-error catalog with solutions
│   └── deployment-safety.md          # Resource efficiency and production deployment
└── templates/                        # Files to adapt for new projects
    ├── AGENTS.md.template            # Starting point for project AGENTS.md
    ├── vscode-settings.json.template # .vscode/settings.json (Copilot config)
    ├── vscode-mcp.json.template      # .vscode/mcp.json (MCP server config)
    ├── setup-checklist.md            # Step-by-step new project setup
    ├── prompts/                      # Prompt file templates (.github/prompts/)
    ├── scripts/                      # Agent shell script templates
    └── github/                       # Copilot-specific templates
        ├── copilot-instructions.md.template
        ├── instructions/             # Path-specific rule templates
        │   ├── tests.instructions.md.template
        │   ├── api.instructions.md.template
        │   ├── migrations.instructions.md.template
        │   ├── deployment-safety.instructions.md.template
        │   └── supabase.instructions.md.template
        └── chatmodes/                # Specialized chat persona templates
            ├── rpi-research.chatmode.md
            ├── rpi-planner.chatmode.md
            └── rpi-auditor.chatmode.md
```

## RPI Workflow

This project follows its own Research-Plan-Implement pattern.

1. /research -- Understand the codebase as-is
2. /plan -- Create a phased implementation spec
3. /implement -- Execute one phase at a time with review gates
4. /validate -- Verify implementation against the plan

Each phase is its own conversation. STOP after each phase.

## Key Commands

```bash
# Verification (CI runs markdownlint)
npx markdownlint '**/*.md' --ignore node_modules --ignore .claude 2>&1
```

Run verification sequentially with `&&` or `;`, NEVER as parallel Bash calls.

## Git Workflow

**`main` is the only branch. Documentation project -- no develop/main split.**

1. All work happens directly on `main`
2. Always run markdownlint before committing
3. Always commit before pulling (hook enforced)
4. Verify current branch before any commit

### Commit Messages

```text
feat: description       # New errors, rules, methodology content
fix: description        # Corrections to existing content
docs: description       # GUIDE.md, README, examples
chore: description      # CI, templates, scripts
release: vX.Y.Z         # Version bumps
```

## Agent Behavior

Exhaust tools before asking the user. Production actions need human authorization.

After pushing, verify CI: `gh run list --branch main --limit 1`. If CI fails, investigate with `gh run view <id> --log-failed`, fix, and re-push.

## Contributing to This Repo

When new error patterns are discovered during work on ANY project:

1. Add them to `patterns/agent-errors.md` following the existing format
2. Add a one-liner to `patterns/quick-reference.md`
3. Update counts in `GUIDE.md` (two locations: prose paragraph + "Where to Go Deeper" table)
4. Update `CHANGELOG.md`
5. Keep entries generic -- no project-specific references

## Project File Locations

Go directly to these paths -- never search the codebase for them.

| Topic | Path | Notes |
|-------|------|-------|
| Error catalog | `patterns/agent-errors.md` | 38 errors, source of truth |
| Operational rules | `patterns/quick-reference.md` | 43 rules with scope/stack tags |
| Deployment safety | `patterns/deployment-safety.md` | Resource efficiency rules |
| Instruction templates | `templates/github/instructions/` | 5 path-specific rule templates |
| Methodology | `methodology/` | 11 files, order in README.md |
| Prompts | `templates/prompts/` | Canonical prompt definitions |
| Active prompts | `.github/prompts/` | This repo's own prompts |
| Research | `docs/research/YYYY-MM-DD-*.md` | RPI research about copilot-rpi |
| Plans | `docs/plans/YYYY-MM-DD-*.md` | RPI plans for copilot-rpi |
