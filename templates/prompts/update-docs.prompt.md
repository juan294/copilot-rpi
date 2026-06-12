---
mode: agent
description: "Research all changes since last release and update every document, diagram, and version reference"
---
Model tier: **sonnet** — invoke this prompt in a Sonnet session.

# Update All Documentation

Research all changes since the last release and update every document,
diagram, version reference, and inline code comment in the project.

## Step 1: Discovery

Investigate 4 areas -- all read-only. No files are modified during this step.

### The Investigation

Cover all 4 areas:

1. **Change analysis** -- Find the last release tag (or first commit if
   no tags). Get the full diff and commit log since then. Categorize all
   changes by area: new features, bug fixes, refactors, config changes.
   For each changed file, summarize what changed and why (from commit
   messages). Identify breaking changes, new APIs, removed functionality.

2. **Documentation inventory** -- Find ALL documentation in the project:
   - Markdown files (`*.md`) and their purpose
   - RST/txt doc files if they exist
   - README, GUIDE, CHANGELOG, CONTRIBUTING, API docs
   - Doc site configs (docusaurus.config.js, mkdocs.yml, vitepress, etc.)
   - Inline doc patterns: JSDoc blocks, Python docstrings, Rust `///`
     doc comments, Go doc comments
   - Map each doc to what code or feature it documents
   - Flag docs that reference changed files or modules

3. **Diagram analysis** -- Find all diagrams in the project:
   - Mermaid code blocks in markdown files
   - Standalone diagram files (`*.mmd`, `*.mermaid`)
   - For each diagram: identify what components, modules, or flows
     it depicts
   - Cross-reference with changed files: which diagrams show stale info?
   - Identify diagrams that need new or removed nodes/edges

4. **Version reference scan** -- Find all version references:
   - Search for current version string across all files
   - Search for previous version strings that may be stale
   - Find shield.io/badge URLs with version numbers
   - Find installation instructions with version-pinned examples
   - Find constants files (`__version__`, `VERSION`, `version.ts`)
   - Find docker tags, CI matrix versions, compatibility tables
   - Classify each as: current, stale, or intentionally pinned

### Synthesis

After investigating all 4 areas, synthesize into an update plan:

```markdown
## Documentation Update Plan

### Changes Since [last-tag]:
[Categorized summary]

### Documents to Update:
| Document | Reason | Update Type |
|----------|--------|-------------|
| README.md | New feature X not documented | Content + badge |
| docs/architecture.md | Module Y refactored | Content + diagram |
| src/api.ts | JSDoc for methodZ is stale | Inline docs |

### Diagrams to Update:
| Location | Diagram Type | Change Needed |
|----------|-------------|---------------|
| docs/arch.md:45 | Mermaid flowchart | Add new service node |

### Version References:
| File:Line | Current | Should Be | Status |
|-----------|---------|-----------|--------|
| README.md:4 | v1.5.0 | v1.7.0 | stale |

### No Update Needed:
[List docs that were checked and are already current]
```

Present this plan to the user.

**STOP.** Wait for approval before making changes.

## Step 2: Documentation Updates

After user approval, update documents one at a time.

For each document in the approved plan:

1. Read the full document.
2. Apply content updates: document new features, changed behavior,
   removed items.
3. Update Mermaid diagrams to match current code structure.
4. Update version references and counts.
5. Preserve existing document structure, voice, and formatting.
6. For inline docs (JSDoc, docstrings, doc comments):
   - Update `@param`, `@returns`, `@example` to match current signatures.
   - Update Python docstrings (match existing style).
   - Update Rust `///` and Go `//` doc comments.
   - Do NOT add new docstrings to functions that do not already have them.
     Scope is refresh, not expansion.
7. Verify lint passes on each changed file.

For diagrams that cannot be confidently updated, add a comment:
`<!-- [NEEDS REVIEW] Diagram may not reflect recent changes to [component]. -->`
and include it in the final report.

**STOP.** Present a summary of all changes for human review.

## Step 3: Finalization

1. Run verification commands sequentially (lint, markdownlint, etc.).

2. Present the full diff of all changed files.

3. Save the update report to `docs/agents/update-docs-report.md`:

   ```markdown
   # Documentation Update Report
   > Generated on [date] | Branch: [branch] | Changes since [last-tag]

   ## Summary
   - [N] documents updated
   - [N] diagrams refreshed
   - [N] version references corrected
   - [N] inline doc blocks updated
   - [N] items flagged [NEEDS REVIEW]

   ## Changes by File
   [For each file: what was changed and why]

   ## Flagged for Review
   [List of [NEEDS REVIEW] items with context]
   ```

4. Tell the user to review the changes and commit when satisfied.
   - Recommend running `/release` next if preparing a new version.
   - If any items are flagged `[NEEDS REVIEW]`, advise reviewing those
     before running `/release`.
   - Mention that `/pre-launch` catches issues that `/update-docs`
     does not (security, performance, accessibility).

## Rules

- **Read-only discovery.** Do not modify any files during Step 1.
- **Present plan before changes.** Never update a document without
  user approval of the plan (Step 1 gate).
- **Preserve voice and structure.** Update content within the existing
  document format. Do not rewrite the style or reorganize sections.
- **Refresh, not expand.** Do NOT create new documentation files unless
  changes clearly warrant it. Do NOT add new inline docstrings -- only
  update existing ones.
- **Flag uncertainty.** Mark diagrams as `[NEEDS REVIEW]` rather than
  guessing when the change is too complex to confidently update.
- **Trace to real changes.** Every update must trace back to an actual
  code change. No speculative or cosmetic updates.
- **Sequential verification.** Run verification commands sequentially.
- **Save the report.** Always write the update report to
  `docs/agents/update-docs-report.md`.
