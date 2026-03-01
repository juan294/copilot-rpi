---
mode: agent
description: "Run a comprehensive multi-specialist audit before production release"
---
# Pre-Launch Audit

Run a comprehensive audit before any production release. Investigate each domain and report findings categorized as blockers, warnings, or recommendations.

## The Audit Domains

Investigate all 6 domains:

1. **Architecture** — Run typecheck, check for outdated/conflicting dependencies, circular dependencies, dead code detection, duplicate code patterns.

2. **Quality Assurance** — Run tests, typecheck, lint. Report total test count, pass rate, failures. Check coverage for critical paths. Identify high-risk untested files.

3. **Security** — Run dependency audit. Search for hardcoded secrets (API keys, tokens, passwords). Verify auth implementation. Check for injection vectors (XSS, SQL). Verify no secrets in client-visible env vars.

4. **Performance** — Run build and parse output for bundle/artifact sizes. Flag oversized artifacts. Check for unused exports. Assess code splitting.

5. **UX/Accessibility** — Check heading hierarchy, ARIA labels, focus indicators, `prefers-reduced-motion` support, alt text, keyboard navigation, error/empty/loading states.

6. **Infrastructure** — Verify build succeeds, check CI status on develop (`gh run list --branch develop --limit 5`), audit env var documentation vs actual usage, check error pages exist, verify git state is clean.

## Report

Write the report to `docs/agents/pre-launch-report.md`:

```markdown
# Pre-Launch Audit Report
> Generated on [date] | Branch: `develop`

## Verdict: READY / CONDITIONAL / NOT READY

## Blockers (must fix before release)

## Warnings

## Detailed Findings
### 1. Quality Assurance — GREEN/YELLOW/RED
### 2. Security — GREEN/YELLOW/RED
### 3. Infrastructure — GREEN/YELLOW/RED
### 4. Architecture — GREEN/YELLOW/RED
### 5. Performance — GREEN/YELLOW/RED
### 6. UX/Accessibility — GREEN/YELLOW/RED
```

## After the Audit

If the verdict is CONDITIONAL or NOT READY with code quality findings (dead code, duplicates,
inefficiencies, reuse opportunities), recommend running `/quality-review` as the first fix action.
`/quality-review` checks for code reuse, quality, and efficiency issues and applies fixes
interactively — it handles the bulk of architecture and performance findings.

For findings that `/quality-review` can't address (security, infrastructure, accessibility), those
require manual implementation or a targeted `/implement` cycle.

## Rules

- **Read-only.** Do not modify files — audit and report only.
- **Do NOT auto-fix during the audit.** Present the full audit to the user. The user decides what to fix and what to accept as risk. After review, `/quality-review` may be used as a first fix step (see "After the Audit" above).
- **Verdict thresholds:** Any blocker = NOT READY. Warnings only = CONDITIONAL. Clean = READY.
