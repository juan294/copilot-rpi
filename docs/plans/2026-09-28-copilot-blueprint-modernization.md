# Copilot RPI modernization plan

Status: `/rpi-plan` completed; implementation contract proposed for owner acceptance. Date: 2026-09-28. Input: `docs/research/2026-09-28-blueprint-sync-state.md`. This invocation authorizes planning only. Proposed release family: Copilot RPI 2.0, subject to successful qualification and separate publication authorization.

## Outcome and evidence

Bring Copilot RPI forward from its cc-rpi v1.28.2 synchronization baseline to the applicable behavior in cc-rpi source 2.1.0, using current native GitHub Copilot surfaces. Keep Copilot RPI independently usable, preserve adopter customizations, and make future upstream intake auditable.

The [research report](../research/2026-09-28-blueprint-sync-state.md) contains source citations, primary-source URLs E01-E16, baseline checks and evidence limits. Implementation starts from Copilot `main` at `56efd8e1fe242054123761f92a74a0ae86d13eca`, reconciling remote `b2a502a20fe935a776fbbf42ee5ab283ecb2ce44` before changes. Pin cc-rpi intake to `aa3ea57fb26ae2e1e167acada4b769e073a417f4`, source version 2.1.0. Its latest published release is v2.0.2; do not label this intake as a published 2.1.0 tag.

Current gaps are R01 ownership/provenance, R02 workflow semantics, R03 publication/evidence, R04 native surfaces and automation, and R05 verification coverage. Existing E2E Pro, audit domains, regression-risk reporting and Copilot-specific knowledge must survive.

## Design decisions

1. **Primary targets:** Copilot CLI and the Copilot harness in VS Code Agent Host. Support VS Code Local through an explicit compatibility profile. Keep cloud-agent setup as an opt-in documented profile; no cloud job or remote branch is implicit in local RPI. Other IDEs are documentation-only until separately qualified.
2. **Skills are the workflow source.** Author canonical `templates/skills/rpi-*/SKILL.md` plus bundled resources. Render project skills into `.github/skills/`, role profiles into `.github/agents/`, path rules into `.github/instructions/`, and minimal root guidance. Generate legacy Local prompt wrappers only when that profile is selected. E03-E08 establish why prompt-only distribution is insufficient.
3. **Separate methodology from harness metadata.** Reuse cc-rpi workflow contracts, handoffs and suitable portable scripts through pinned, attributed imports. Copilot owns tools, locations, native metadata, hook adapters and compatibility fixtures. No runtime dependency on a sibling checkout; no change to cc-rpi is required by this plan.
4. **Keep source intake distinct from adopter updates.** A checked-in `upstream/cc-rpi.lock.json` maps every reviewed upstream component and rule/error item to adopted, adapted, deferred or inapplicable status, with source SHA/path/hash, destination/hash and rationale. A checked-in inventory snapshot and original imported source snapshots make local consistency verification self-contained. Inspect a supplied upstream checkout only during explicit maintainer intake; the default gate does not fetch or depend on a sibling repository. A separate installation manifest records what a particular adopter owns. Neither manifest grants execution or publication authority.
5. **Port proven lifecycle code with explicit patches.** Adapt the cc-rpi distribution/lifecycle/config modules in Copilot's own source tree, retaining attribution, upstream hashes and behavioral tests. Do not introduce a new shared package or pretend the current Claude/Codex renderer already supports Copilot. Favor reused transaction/path/ownership code over reimplementing those algorithms.
6. **Preserve local policy boundaries.** Complete local work and verification before an authorized push. No preview deployments, remote issue delegation, automatic issue creation, auto-merge or fix-and-repush loop. Keep external actions possible when explicitly authorized; do not turn routine work into repeated permission prompts.
7. **Models inherit interactively.** Remove mandatory tier prose and obsolete model pins. Scheduled jobs may record an owner-selected model for reproducibility; the installer neither chooses a paid model nor starts inference. E06 and E14 support this distinction.
8. **Native hooks are optional supplemental controls.** Implement only a narrow destructive-operation adapter after contract tests. Keep permissions native and candidate receipts in an opt-in Git pre-push hook. A configured hook is not proven enforcement; timeout behavior and inactive hooks must be visible (R03, E09-E10).
9. **Preserve catalog identity.** Copilot error/rule IDs are independent of cc-rpi IDs. Match by meaning, retain Copilot-specific entries, and record supersession/retirement with version-bound evidence. Never replace the catalog merely to obtain cc-rpi's count.
10. **Keep curated knowledge versioned.** During implementation, narrow the research/plan ignores to retain this selected report, plan, phases and subsequent handoff. Raw observations and receipts go under ignored `.rpi/local/`. This does not authorize bulk staging historical research.

These are concrete proposed defaults. No unresolved technical choice blocks plan review. Client versions and native results are measurements required during execution, not invented compatibility promises.

## Options considered

| Option | Benefit | Cost and decision |
| --- | --- | --- |
| Refresh existing prompts and chatmodes only | Smallest migration | Leaves Agent Host discovery, ownership and recurring drift unresolved; rejected |
| Add Copilot to cc-rpi and retire the sibling | One upstream product | Changes product scope and couples releases; not requested and rejected for this update |
| Copilot-owned adapters with pinned upstream intake | Native behavior plus independent product and traceable learning transfer | Requires maintained adapter patches and conformance tests; selected |

Plugins are a later optional distribution route. Direct repository installation is the initial supported route so no plugin-cache mutation, marketplace publication or global profile changes are prerequisites.

## Sequential phases

| Phase | Deliverable | Acceptance gate |
| --- | --- | --- |
| [1. Source intake and workflow contracts](2026-09-28-copilot-blueprint-modernization-phases/phase-1.md) | Complete upstream disposition map, canonical workflows and catalog crosswalk | Every upstream item and old Copilot workflow accounted for; source provenance and behavioral rubrics pass |
| [2. Copilot native rendering](2026-09-28-copilot-blueprint-modernization-phases/phase-2.md) | Skills, custom agents, scoped instructions and selected compatibility outputs | Deterministic render, valid metadata/resources, no discovery collisions or broad tool defaults |
| [3. Ownership and migration](2026-09-28-copilot-blueprint-modernization-phases/phase-3.md) | Plan/apply/check/rollback/detach and legacy migration | Real filesystem fixtures prove preservation, conflict recovery and idempotence |
| [4. Verification and automation](2026-09-28-copilot-blueprint-modernization-phases/phase-4.md) | Candidate receipts, validated findings, opt-in native guards and bounded Copilot jobs | Positive/negative controls, failure recovery and complete sequential local gate pass |
| [5. Qualification and release preparation](2026-09-28-copilot-blueprint-modernization-phases/phase-5.md) | Native evidence, coherent docs/self-application and migration guide | Named primary clients pass discovery/authority fixtures; local package is reviewable |

Each phase uses implement -> independent review -> repair -> simplify -> verify, then stops for acceptance unless continuation is explicitly authorized. All required checks run sequentially with failure aggregation. A later pass cannot erase a failed required check. Use local isolated worktrees during implementation, one integration owner and at most three implementers. Phase 1 resolves the existing `AGENTS.md:91` direct-main instruction versus `CONTRIBUTING.md:15` branch guidance in the documented topology; integrate locally into `main`, never publish working branches.

## Workflow inventory and dispositions

The following mapping covers all 20 old canonical prompts. Full workflow bodies come from the pinned source with the decisions above applied.

| Existing Copilot prompt | Planned skill |
| --- | --- |
| adopt, bootstrap, detach, update | `rpi-adopt`, `rpi-bootstrap`, `rpi-detach`, `rpi-update`; explicit lifecycle invocation |
| brainstorm, research, plan, implement, validate | Same names with `rpi-` prefix |
| describe-pr, explore-release, fix-ci, pre-launch, release | Same names with `rpi-` prefix |
| remediate, status, triage, update-docs | Same names with `rpi-` prefix |
| debug | `rpi-debug`, preserving the entry point and using systematic-debugging resources |
| quality-review | `rpi-quality-review`, preserving reuse/quality/efficiency review and fixing actionable findings |

Add `rpi-assess` and `rpi-tool-design` from cc-rpi. Keep this repo's `process-errors` maintenance workflow as a local skill with its existing ingestion purpose. Preserve maintenance-only divergence explicitly. Upstream `codex-simplify` contributes review semantics to `rpi-quality-review`; it is not installed under a Codex name. Audit all 12 upstream domain skills for portable content; select stack-specific Supabase/WebMCP guidance only when applicable. Existing API/migration/test instruction content is not discarded just because cc-rpi groups it differently. Lifecycle skills can be selected explicitly for a target repo; no global installation is implicit.

## Consumer sweep

Commands used against the recorded baseline: `git ls-files`, `rg --files templates/prompts`, `rg -n 'copilot-rpi-sync|lastSyncCommit|chatmode|mode:|Model tier|CLAUDE_BIN|preflight_claude' templates .github methodology patterns AGENTS.md GUIDE.md README.md`, plus direct reads of update/detach and the three validators. Repeat after new schemas are introduced.

| Shared contract and current readers/writers | Coverage |
| --- | --- |
| Workflow bodies in `templates/prompts/*.prompt.md`; `.github/prompts/{remediate,triage}.prompt.md` copies; local `process-errors` | P1-P2 canonicalization and explicit local extension |
| Prompt paths referenced by setup, AGENTS templates, README/GUIDE, examples and methodology | P2 paths and P5 complete link/discovery sweep |
| `.github/copilot-rpi-sync.json` in bootstrap/adopt/update/detach prompts and update scheduler | P3 legacy provenance adapter; P4 scheduler consumes new plan/status only |
| Chatmode filenames and tool identifiers in setup/update/detach/docs/validator | P2 migration inventory; P3 owned retirement; P5 docs |
| Instruction names, `applyTo`, AGENTS headings and VS Code settings in lifecycle prompts | P2 one manifest mapping; P3 per-key/block ownership and JSONC preservation |
| `CLAUDE_BIN`, `preflight_claude`, updater, morning-triage, installer and shared agent utilities | P4 real Copilot runner plus non-inference preflight; no hidden Claude fallback |
| Count/version/prompt scripts, Markdown workflow, Validate workflow, retirement ledger | P1 provenance/identity, P2 schema tests, P4 one local gate, P5 release consistency |
| Existing E2E Pro and eight-domain findings consumers | P1 preserve contracts; P4 findings validator; P5 qualification |
| Remote Sutura workflow absent locally | Preserve the three-commit remote delta in P1; no monitor reconfiguration |
| New fixtures, importer, renderer, lifecycle, scheduler and receipts | P1-P4 tests are writers/readers too; schema-change checks require complete enumeration |

## Stuck states and recovery

| State | Who sees what | Exit and required oracle |
| --- | --- | --- |
| Upstream SHA/hash mismatch | Maintainer receives source/path and mismatch | Pin/review a new source, regenerate intake; test mismatch prevents import and corrected pin passes |
| Unsupported surface or hidden skill/tool | User receives client/profile and missing capability | Select a qualified profile or repair discovery; native negative fixture proves diagnosis, positive fixture proves re-entry |
| Customized legacy file or unproven ownership | Adopter receives per-path conflict and preserved diff | Import exact legacy bytes or accept a reviewed merge; fixture proves no initial write and successful resolved re-plan |
| Stale apply plan or concurrent edit | Operator receives changed input and regenerate command | Re-plan against current bytes; test stale rejection followed by successful fresh apply |
| Interrupted transaction or rollback conflict | Operator receives journal and runnable recovery command | Safe rollback/re-plan; fixture preserves newer owner edits and explains any refusal |
| Missing/failed/stale verification receipt | Publisher sees candidate/runtime difference and local gate command | Re-run gate on final candidate; tests cover failure, interruption and recovered pass without stale success |
| Hook missing, disabled, malformed or timed out | Diagnostics states unobserved/degraded enforcement | Correct registration/runtime and rerun native probe; timeout never reported as blocked or safe by default |
| Missing CLI/auth, denied tool, timeout or scheduler lock | Operator sees bounded failure and exact next action | Install/authenticate through supported tooling, adjust authorized scope or recover owned stale lock; fake-process fixtures prove bounded recovery |
| Cloud setup failure | Opt-in operator sees failed prerequisite even if agent starts | Repair setup before dependent task; negative setup fixture proves disclosure instead of a success claim |

## Completion and handoff

### Requirement-to-evidence map

All rows below are implementation acceptance requirements, not completed results. A phase passes only when its applicable requirements have evidence for unchanged inputs. Artifact lint and source inspection alone cannot satisfy a native row.

| ID | Requirement and research basis | Phase and evidence | Pass condition |
| --- | --- | --- | --- |
| A01 | Complete source intake, R01-R02 | P1 inventory/lock checker and workflow map | All 61 upstream components, each catalog entry and all 20 old prompts have an explicit disposition; no unknown hash or destination |
| A02 | Portable workflow semantics, R02-R03 | P1 deterministic fixture validation; P5 native scenario rubric | All six P1 scenarios have required fields, positive/negative examples and independent native scoring; no missing-review or recovery gap accepted |
| A03 | Native output and bounded context, R04/R06 | P2 renderer/schema tests | Two renders are byte-identical; every resource resolves; zero name collisions or unsupported metadata; managed root text at most 8,192 bytes |
| A04 | Preserve adopter ownership, R01 | P3 real filesystem/Git fixture matrix | Every listed conflict leaves original bytes intact; documented resolution succeeds; second apply is a no-op; rollback preserves newer owner edits |
| A05 | Reliable verification and findings, R03/R05 | P4 verifier/findings/pre-push failure tests | No failed, interrupted or changed candidate retains valid success; malformed findings block remediation; corrected inputs recover |
| A06 | Copilot automation, R04 | P4 external-process fixtures; P5 real CLI programmatic probe | No Claude fallback or default publication; real allowed-report and denied-write controls match captured argv, exit and disk/report evidence |
| A07 | Primary native compatibility, R06 | P5 CLI and VS Code Agent Host fixtures | Each primary profile passes discovery, arguments/resources, tool boundaries, model behavior and handoff tests on recorded versions |
| A08 | Reusable standalone product, R01/R05 | P1 offline provenance fixture; P5 fresh/customized installs and full gate | Clean checkout verifies without a sibling repo or network after dependency setup; lifecycle examples pass; self-application matches source |

Manual/visual acceptance is limited to observing VS Code's selected harness and discovery UI, and any unavoidable interactive trust/authentication step. The agent automates available CLI and UI paths first. Optional Local/hooks/cloud profiles have separate results; an unqualified optional profile cannot be advertised as supported. Lack of access to a mandatory primary test is an explicit qualification blocker, not a waived criterion.

### Executable verification contract

The commands here are planned interfaces, not checks already run on new code. P1 creates a basic `scripts/verify-local.sh` aggregator immediately; P4 adds candidate receipts to it. Set up a project-local environment with `uv sync --locked` and `npm ci`. P1 checks in `pyproject.toml`, `uv.lock`, `.python-version`, and a private `package.json`/`package-lock.json`. Pin the observed tooling baseline: Python 3.14.7, PyYAML 6.0.3, markdownlint-cli2 0.23.3; record uv 0.12.19, Node 24.21.0 and ShellCheck 0.11.0 in receipts. Keep product Python support at 3.11+ and test the minimum supported interpreter as well during qualification. Package metadata must match the current declared Copilot version until release acceptance. Narrowly unignore the development lockfile.

Every phase ends with `bash scripts/verify-local.sh`. It executes these commands sequentially, captures every exit, and returns nonzero if any fails:

```bash
uv run --locked python -m unittest discover -s tests -p 'test_*.py'
bash templates/scripts/verify-counts.sh
bash templates/scripts/verify-version.sh
bash templates/scripts/verify-prompts.sh
shellcheck --severity=warning templates/scripts/*.sh templates/scripts/agents/*.sh templates/scripts/agents/lib/*.sh scripts/*.sh
npm exec -- markdownlint-cli2 '**/*.md' '#node_modules' '#.venv' '#.claude' '#graphify-out' '#.rpi/local'
uv run --locked python scripts/check-upstream.py --lock upstream/cc-rpi.lock.json --inventory upstream/cc-rpi.inventory.json --check
uv run --locked python scripts/check-links.py
```

The default upstream check validates the recorded inventory, imported source snapshots and local destination hashes; it does not claim to detect a newer upstream release. Maintainer intake separately runs `uv run --locked python scripts/check-upstream.py --source /Users/juan/code/cc-rpi --lock upstream/cc-rpi.lock.json --check` against the supplied source and reports drift without applying it. P2 additionally registers `uv run --locked python templates/scripts/rpi-distribution.py validate --source .` and `uv run --locked python templates/scripts/rpi-distribution.py check-generated --source .`; profile render comparisons and malformed fixtures run inside the unittest suite. P3 lifecycle tests create and clean their own disposable targets; no acceptance command points at a real adopter. P4 extends the same suite/runner rather than adding a second conflicting gate. Native probes are separately named in P5 and never run implicitly during lint or static CI.

Automated completion requires all phase tests, lint, ShellCheck, metadata/link checks, deterministic rendering, filesystem migration tests, verifier failure cases and declared mutation oracles to pass on the final candidate. Native primary-profile acceptance requires exact CLI/VS Code/Copilot versions, discovered files/tools, requested actions, observed results and preserved sanitized evidence. Static checks cannot substitute for native proof. Cloud stays unqualified until an explicitly authorized cloud test runs.

No deployment or registry build is needed for this documentation/tooling product. Release preparation includes a candidate-local changelog and migration notes; actual version tagging, push, GitHub release, downstream rollout, cloud runs, paid inference and global/scheduler activation retain separate authorization. Do not claim this task updated either blueprint: only the research and plan files exist now.

Next entry: owner accepts this plan or supplies scoped revisions, then revalidate both repos and begin P1. Preserve `.summon` and any newer work. These artifacts currently follow Copilot's ignored local-plan policy; P1 proposes narrowly versioning them. There are no outstanding design questions, and native qualification is explicitly pending implementation.

### Planning handoff, 2026-09-28

This explicit `/rpi-plan` invocation re-read the entire input report and verified its artifact hash against the prior research receipt. Both repository HEADs and cached Copilot `origin/main` still match the baselines above; cc-rpi is clean and Copilot's only visible untracked item remains `.summon`. The six existing plan files were unchanged before this pass. Earlier same-day source/web evidence and resolved review findings were reused; no new native capability or remote-release claim was measured in this planning pass.

The pass added A01-A08, clarified snapshot exclusion from active discovery, moved native schema validation into P2 so its new outputs do not conflict with the old `mode` checker, and made P5 qualification sequential after the documentation freeze. These are planning refinements, not product changes. The prior review's exact-command, real programmatic-CLI and sibling-dependency findings remain resolved. Implementation, release and downstream installation have not started; all A01-A08 results remain pending. On resume, revalidate this contract and actual files before using any prior check result.
